# Part of Insilos. See LICENSE file for full copyright and licensing details.
import threading

from werkzeug.exceptions import NotFound, BadRequest

from insilos import http
from insilos.http import request
from insilos.service.model import call_kw

from .utils import clean_action


class DataSet(http.Controller):

    def _call_kw_readonly(self, rule, args):
        data = request.get_json_data() or {}
        params = data.get('params', {})
        model_name = params.get('model') or args.get('model')
        method_name = params.get('method') or args.get('method')
        if not model_name or not method_name:
            return False
        try:
            model_class = request.registry[model_name]
        except KeyError as e:
            raise NotFound() from e
        for cls in model_class.mro():
            method = getattr(cls, method_name, None)
            if method is not None and hasattr(method, '_readonly'):
                return method._readonly
        return False

    @http.route(['/api/model/call', '/api/model/call/<path:path>', '/web/dataset/call_kw', '/web/dataset/call_kw/<path:path>', '/insilos/dataset/call_kw'], type='jsonrpc', auth="user", readonly=_call_kw_readonly)
    def call_kw(self, model=None, method=None, args=None, kwargs=None, path=None):
        if not model and request.get_json_data():
            p = request.get_json_data().get('params', {})
            model = p.get('model')
            method = p.get('method')
            args = p.get('args', [])
            kwargs = p.get('kwargs', {})
        if not model or not method:
            raise BadRequest("Missing required 'model' or 'method' parameter for RPC dispatch")
        if path != f'{model}.{method}':
            threading.current_thread().rpc_model_method = f'{model}.{method}'
        return call_kw(request.env[model], method, args or [], kwargs or {})

    @http.route(['/api/model/call_button', '/api/model/call_button/<path:path>', '/web/dataset/call_button', '/web/dataset/call_button/<path:path>', '/insilos/dataset/call_button'], type='jsonrpc', auth="user", readonly=_call_kw_readonly)
    def call_button(self, model=None, method=None, args=None, kwargs=None, path=None):
        if not model and request.get_json_data():
            p = request.get_json_data().get('params', {})
            model = p.get('model')
            method = p.get('method')
            args = p.get('args', [])
            kwargs = p.get('kwargs', {})
        if not model or not method:
            raise BadRequest("Missing required 'model' or 'method' parameter for RPC dispatch")
        if path != f'{model}.{method}':
            threading.current_thread().rpc_model_method = f'{model}.{method}'
        action = call_kw(request.env[model], method, args or [], kwargs or {})
        if isinstance(action, dict) and action.get('type') != '':  # noqa: PLC1901
            return clean_action(action, env=request.env)
        return False
