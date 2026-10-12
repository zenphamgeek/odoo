# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging

import werkzeug.urls
from werkzeug.exceptions import BadRequest

from odoo import SUPERUSER_ID, _, api
from odoo.exceptions import AccessDenied
from odoo.http import Controller, request, route
from odoo.http.requestlib import fragment_to_query_string
from odoo.http.router import db_filter
from odoo.http.session import authenticate
from odoo.modules.registry import Registry
from odoo.tools.misc import clean_context

from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
from odoo.addons.web.controllers.utils import _get_login_redirect_url, ensure_db

_logger = logging.getLogger(__name__)


def _is_safe_local_redirect(target_url):
    """Fail-closed validation verifying target_url is strictly local, cannot escape origin,
    and does not route to raw unbranded /web or /odoo paths. Canonicalizes before matching
    to prevent case-folding, percent-encoding, or separator tricks (CWE-20, CWE-601).
    """
    if not target_url or not isinstance(target_url, str):
        return False

    candidates = [target_url]
    current = target_url
    for _ in range(3):
        unquoted = werkzeug.urls.url_unquote(current)
        if unquoted == current:
            break
        candidates.append(unquoted)
        current = unquoted

    for s in candidates:
        if any(c in s for c in ('\r', '\n', '\t', '\0', ' ')):
            return False
        if '\\' in s:
            return False
        parsed = werkzeug.urls.url_parse(s)
        if parsed.scheme or parsed.netloc:
            return False
        if not s.startswith('/') or s.startswith('//'):
            return False
        norm_path = parsed.path.lower()
        if norm_path.startswith('//'):
            return False
        if norm_path in ('', '/web', '/odoo', 'web', 'odoo') or norm_path.startswith(('/web/', '/odoo/')):
            return False
    return True


# ----------------------------------------------------------
# Controller
# ----------------------------------------------------------
class OAuthLogin(Home):
    def list_providers(self):
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
        except Exception:
            providers = []
        for provider in providers:
            return_url = request.httprequest.url_root + 'auth_oauth/signin'
            state = self.get_state(provider)
            params = dict(
                response_type='token',
                client_id=provider['client_id'],
                redirect_uri=return_url,
                scope=provider['scope'],
                state=json.dumps(state),
                # nonce=base64.urlsafe_b64encode(os.urandom(16)),
            )
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))
        return providers

    def get_state(self, provider):
        redirect = request.params.get('redirect') or '/insilos'
        if not _is_safe_local_redirect(redirect):
            redirect = '/insilos'
        parsed = werkzeug.urls.url_parse(redirect)
        clean_path = parsed.path
        if clean_path in ('', '/web', '/odoo', 'web', 'odoo') or clean_path.startswith(('/web/', '/odoo/', '/web?', '/odoo?')):
            redirect = '/insilos'
        else:
            query_part = ('?' + parsed.query) if parsed.query else ''
            redirect = clean_path + query_part

        # Strictly prefix with current instance url_root
        redirect_url = '%s%s' % (request.httprequest.url_root, redirect[1:])
        state = dict(
            d=request.session.db,
            p=provider['id'],
            r=werkzeug.urls.url_quote_plus(redirect_url),
        )
        token = request.params.get('token')
        if token:
            state['t'] = token
        return state

    @route()
    def web_login(self, *args, **kw):
        ensure_db()
        if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
            # Redirect if already logged in and redirect param is present
            return request.redirect(request.params.get('redirect'))
        providers = self.list_providers()

        response = super().web_login(*args, **kw)
        if response.is_qweb:
            error = request.params.get('oauth_error')
            if error == '1':
                error = _("Sign up is not allowed on this database.")
            elif error == '2':
                error = _("Access Denied")
            elif error == '3':
                error = _("You do not have access to this database or your invitation has expired. Please ask for an invitation and be sure to follow the link in your invitation email.")
            else:
                error = None

            response.qcontext['providers'] = providers
            if error:
                response.qcontext['error'] = error

        return response

    def get_auth_signup_qcontext(self):
        result = super().get_auth_signup_qcontext()
        result["providers"] = self.list_providers()
        return result


class OAuthController(Controller):

    @route('/auth_oauth/signin', type='http', auth='none', readonly=False)
    @fragment_to_query_string
    def signin(self, **kw):
        state = json.loads(kw['state'])

        # make sure request.session.db and state['d'] are the same,
        # update the session and retry the request otherwise
        dbname = state['d']
        if not db_filter([dbname]):
            return BadRequest()
        ensure_db(db=dbname)

        provider = state['p']
        request.update_context(**clean_context(state.get('c', {})))
        try:
            # auth_oauth may create a new user, the commit makes it
            # visible to authenticate()'s own transaction below
            _, login, key = request.env['res.users'].with_user(SUPERUSER_ID).auth_oauth(provider, kw)
            request.env.cr.commit()

            action = state.get('a')
            menu = state.get('m')
            raw_redirect = werkzeug.urls.url_unquote_plus(state['r']) if state.get('r') else False
            url = '/insilos'
            if raw_redirect:
                parsed_r = werkzeug.urls.url_parse(raw_redirect)
                root_parsed = werkzeug.urls.url_parse(request.httprequest.url_root)
                is_safe_local = _is_safe_local_redirect(raw_redirect)
                is_safe_same_origin = (
                    parsed_r.scheme in ('http', 'https')
                    and parsed_r.netloc == root_parsed.netloc
                    and _is_safe_local_redirect(parsed_r.path)
                )
                if is_safe_local or is_safe_same_origin:
                    clean_target_path = parsed_r.path
                    if clean_target_path not in ('', '/web', '/odoo', 'web', 'odoo') and not clean_target_path.startswith(('/web/', '/odoo/', '/web?', '/odoo?')):
                        query_part = ('?' + parsed_r.query) if parsed_r.query else ''
                        url = clean_target_path + query_part
            elif action:
                url = '/insilos/action-%s' % action
            elif menu:
                url = '/insilos?menu_id=%s' % menu

            credential = {'login': login, 'token': key, 'type': 'oauth_token'}
            auth_info = authenticate(request.session, request.env, credential)
            resp = request.redirect(_get_login_redirect_url(auth_info['uid'], url), 303)
            resp.autocorrect_location_header = False

            # Since /web is hardcoded, verify user has right to land on it
            if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user._is_internal():
                resp.location = '/'
            return resp
        except AttributeError:  # TODO juc master: useless since ensure_db()
            # auth_signup is not installed
            _logger.error("auth_signup not installed on database %s: oauth sign up cancelled.", dbname)
            url = "/web/login?oauth_error=1"
        except AccessDenied:
            # oauth credentials not valid, user could be on a temporary session
            _logger.info('OAuth2: access denied, redirect to main page in case a valid session exists, without setting cookies')
            url = "/web/login?oauth_error=3"
        except Exception:
            # signup error
            _logger.exception("Exception during request handling")
            url = "/web/login?oauth_error=2"

        redirect = request.redirect(url, 303)
        redirect.autocorrect_location_header = False
        return redirect

    @route('/auth_oauth/oea', type='http', auth='none', readonly=False)
    def oea(self, **kw):
        """login user via Odoo Account provider"""
        dbname = kw.pop('db', None)
        if not dbname:
            dbname = request.db
        if not dbname:
            raise BadRequest()
        if not db_filter([dbname]):
            raise BadRequest()

        registry = Registry(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, {})
                provider = env.ref('auth_oauth.provider_openerp')
            except ValueError:
                redirect = request.redirect(f'/web?db={dbname}', 303)
                redirect.autocorrect_location_header = False
                return redirect
            assert provider._name == 'auth.oauth.provider'

        state = {
            'd': dbname,
            'p': provider.id,
            'c': {'no_user_creation': True},
        }

        kw['state'] = json.dumps(state)
        return self.signin(**kw)
