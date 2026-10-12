#!/usr/bin/env python3
"""AL2C catalog / structure lint for the insilos_al2c addon.

Modes:
  shell : python3 odoo-bin shell -c insilos.conf -d DB --no-http < tools/al2c_catalog_lint.py
  rpc   : python3 tools/al2c_catalog_lint.py --url URL --db DB --user U [--password P] [--json]
Read-only. Exit code 0 = no failures, 1 = failures.
"""
import json
import os
import sys

MODULE = 'insilos_al2c'
PHASES = ['Prepare', 'Explore', 'Realize', 'Deploy', 'Run']
CATEG_PREFIXES = ('Insilos ERP', 'GRC', 'AI', 'Services')


def _p(inv, stype, track, tmpl=False, rec=False, glob=False):
    return dict(invoice_policy=inv, service_type=stype, service_tracking=track,
                template=tmpl, recurring=rec, global_project=glob)


SKUS = {
    'ERP-STARTER': _p('order', 'manual', 'project_only', True),
    'ERP-GROWTH': _p('delivery', 'milestones', 'project_only', True),
    'ERP-ENT': _p('delivery', 'milestones', 'project_only', True),
    'SAAS-USER-M': _p('order', 'manual', 'no', rec=True),
    'SAAS-HOSTING-PRO': _p('order', 'manual', 'no', rec=True),
    'SAAS-SLA-PLUS': _p('order', 'manual', 'no', rec=True),
    'GRC-ESSENTIALS': _p('order', 'manual', 'project_only', True),
    'GRC-RISK-REGISTER': _p('order', 'manual', 'project_only', True),
    'GRC-AUDIT-PACK': _p('delivery', 'milestones', 'project_only', True),
    'AI-DISCOVERY': _p('order', 'manual', 'project_only', True),
    'AI-POC': _p('order', 'manual', 'project_only', True),
    'AI-PILOT': _p('delivery', 'milestones', 'project_only', True),
    'AI-PROD': _p('delivery', 'timesheet', 'task_in_project', True),
    'MOJO-APP-SUB': _p('order', 'manual', 'no', rec=True),
    'MOJO-TOKENS': _p('delivery', 'manual', 'no', rec=False),
    'MOJO-ONPREM': _p('order', 'manual', 'project_only', True),
    'AMS-BRONZE': _p('order', 'manual', 'no', rec=True),
    'AMS-SILVER': _p('order', 'manual', 'no', rec=True),
    'AMS-GOLD': _p('order', 'manual', 'no', rec=True),
    'TRAINING-DAY': _p('order', 'manual', 'no'),
    'CONSULT-HOUR': _p('delivery', 'timesheet', 'task_global_project', glob=True),
}
KB_ROOTS = ['Products', 'Industries', 'Playbooks', 'Battlecards', 'RFP Library', 'Post-mortems', 'Compliance']
KB_CHILDREN = {'Products': ['ERP', 'GRC', 'AI Solutions', 'Mojo AI Apps', 'Services'],
               'Playbooks': ['Sales', 'Delivery']}
DOC_ROOTS = ['Product Docs', 'Proposals', 'Contracts', 'Deliverables', 'Marketing Assets', 'Compliance Evidence']
DOC_CHILDREN = {'Product Docs': ['ERP', 'GRC', 'AI Solutions', 'Mojo AI Apps', 'Services']}
DOC_TAGS = ['L2C > Proposal', 'L2C > Contract', 'L2C > Deliverable', 'L2C > Marketing Asset',
            'L2C > Compliance Evidence', 'L2C > Product Spec', 'Confidentiality > Public',
            'Confidentiality > Internal', 'Confidentiality > Confidential']
PARAMS = ['al2c.autonomy_enabled', 'al2c.agent_daily_budget', 'al2c.max_discount', 'al2c.max_tcv']
SO_TEMPLATES = ['ERP Starter', 'ERP Growth', 'ERP Enterprise', 'GRC Essentials', 'AI PoC',
                'AI Pilot', 'AI Production', 'Mojo App Subscription']


class OrmBackend:
    def __init__(self, env):
        self.env = env

    def has_model(self, model):
        try:
            self.env[model]
            return True
        except KeyError:
            return False

    def fields(self, model):
        return set(self.env[model]._fields)

    def search_read(self, model, domain, fields):
        return self.env[model].with_context(active_test=False).search_read(domain, fields)


class RpcBackend:
    def __init__(self, url, db, user, password):
        import xmlrpc.client
        common = xmlrpc.client.ServerProxy(url.rstrip('/') + '/xmlrpc/2/common', allow_none=True)
        self.uid = common.authenticate(db, user, password, {})
        if not self.uid:
            raise SystemExit('authentication failed for %s@%s' % (user, db))
        self.obj = xmlrpc.client.ServerProxy(url.rstrip('/') + '/xmlrpc/2/object', allow_none=True)
        self.db, self.pw = db, password

    def _call(self, model, method, args, kw=None):
        return self.obj.execute_kw(self.db, self.uid, self.pw, model, method, args, kw or {})

    def has_model(self, model):
        return bool(self._call('ir.model', 'search_count', [[('model', '=', model)]]))

    def fields(self, model):
        return set(self._call(model, 'fields_get', [], {'attributes': ['type']}))

    def search_read(self, model, domain, fields):
        return self._call(model, 'search_read', [domain],
                          {'fields': fields, 'context': {'active_test': False}})


def m2o(v):
    return v[0] if v else False


class Lint:
    def __init__(self, be):
        self.be, self.results, self.section = be, [], None

    def check(self, ok, label, reason=''):
        self.results.append({'section': self.section, 'ok': bool(ok), 'check': label,
                             'reason': '' if ok else reason})
        return ok

    def sec(self, name):
        self.section = name

    def xmlid_ids(self, model):
        env = getattr(self.be, 'env', None)
        real = env[model]._name if env is not None else model
        rows = self.be.search_read('ir.model.data', [('module', '=', MODULE), ('model', 'in', list({model, real}))],
                                   ['res_id'])
        return {r['res_id'] for r in rows}

    # ------------------------------------------------------------------ checks
    def catalog(self):
        self.sec('CATALOG')
        be = self.be
        pf = be.fields('product.template')
        want = ['default_code', 'type', 'invoice_policy', 'service_type', 'service_tracking',
                'recurring_invoice', 'project_template_id', 'project_id', 'al2c_knowledge_article_id',
                'al2c_vat_class', 'categ_id', 'active']
        missing = [f for f in want if f not in pf]
        self.check(not missing, 'product.template fields present', 'missing: %s' % ', '.join(missing))
        fields = [f for f in want if f in pf]
        rows = be.search_read('product.template', [('default_code', 'in', list(SKUS))], fields)
        by_code = {r['default_code']: r for r in rows}
        categs = {c['id']: c['complete_name'] for c in be.search_read(
            'product.category', [('id', 'in', list({m2o(r.get('categ_id')) for r in rows} - {False}))],
            ['complete_name'])}
        prod_root = self._kb_products_root()
        self.templates_needed = {}
        for code, exp in SKUS.items():
            r = by_code.get(code)
            if not self.check(r, '%s exists' % code, 'no product.template with this default_code'):
                continue
            errs = []
            if r.get('type') != 'service':
                errs.append('type=%s' % r.get('type'))
            for f in ('invoice_policy', 'service_type', 'service_tracking'):
                if r.get(f) != exp[f]:
                    errs.append('%s=%s (want %s)' % (f, r.get(f), exp[f]))
            if bool(r.get('recurring_invoice')) != exp['recurring']:
                errs.append('recurring_invoice=%s' % r.get('recurring_invoice'))
            if r.get('al2c_vat_class') not in ('kct', 'vat_8', 'vat_10'):
                errs.append('al2c_vat_class=%s (want kct/vat_8/vat_10)' % r.get('al2c_vat_class'))
            tmpl = m2o(r.get('project_template_id'))
            if exp['template'] and not tmpl:
                errs.append('project_template_id not set')
            elif tmpl:
                self.templates_needed.setdefault(tmpl, []).append(code)
            if exp['global_project'] and not m2o(r.get('project_id')):
                errs.append('project_id (global project) not set')
            cname = categs.get(m2o(r.get('categ_id')), '')
            if not cname.startswith(CATEG_PREFIXES):
                errs.append('category "%s" outside AL2C trees' % cname)
            art = m2o(r.get('al2c_knowledge_article_id'))
            if not art:
                errs.append('al2c_knowledge_article_id not set')
            elif be.has_model('knowledge.article'):
                a = be.search_read('knowledge.article', [('id', '=', art)], ['active', 'parent_path'])
                if not a or not a[0]['active']:
                    errs.append('knowledge article inactive/missing')
                elif prod_root and ('/%s/' % prod_root) not in '/' + (a[0]['parent_path'] or ''):
                    errs.append('knowledge article not under "Products"')
            self.check(not errs, '%s policy' % code, '; '.join(errs))
        if 'CONSULT-HOUR' in by_code and m2o(by_code['CONSULT-HOUR'].get('project_id')):
            pid = m2o(by_code['CONSULT-HOUR']['project_id'])
            p = be.search_read('project.project', [('id', '=', pid)], ['is_template'])
            self.check(p and not p[0].get('is_template'), 'CONSULT-HOUR global project is not a template',
                       'project %s is a template or missing' % pid)

    def project_templates(self):
        self.sec('PROJECT TEMPLATES')
        be = self.be
        if not self.check(getattr(self, 'templates_needed', None), 'project templates referenced',
                          'no SKU references a project template'):
            return
        projs = {p['id']: p for p in be.search_read('project.project', [('id', 'in', list(self.templates_needed))],
                                                     ['name', 'is_template', 'allow_milestones'])}
        for pid, codes in sorted(self.templates_needed.items()):
            p = projs.get(pid)
            label = 'template %s (%s)' % (p['name'] if p else pid, ', '.join(codes))
            if not p:
                self.check(False, label, 'project missing')
                continue
            errs = []
            if not p.get('is_template'):
                errs.append('is_template=False')
            if not p.get('allow_milestones'):
                errs.append('allow_milestones=False')
            names = {m['name'] for m in be.search_read('project.milestone', [('project_id', '=', pid)], ['name'])}
            miss = [n for n in PHASES if n not in names]
            if len(names) < 5 or miss:
                errs.append('milestones %d, missing: %s' % (len(names), ', '.join(miss) or '-'))
            self.check(not errs, label, '; '.join(errs))

    def _kb_products_root(self):
        if not self.be.has_model('knowledge.article'):
            return None
        r = self.be.search_read('knowledge.article', [('name', '=', 'Products'), ('parent_id', '=', False),
                                                      ('active', '=', True)], ['id'])
        return r[0]['id'] if r else None

    def knowledge(self):
        self.sec('KNOWLEDGE')
        be = self.be
        if not self.check(be.has_model('knowledge.article'), 'knowledge.article model', 'app not installed'):
            return
        dom = [('active', '=', True)]
        if 'to_delete' in be.fields('knowledge.article'):
            dom.append(('to_delete', '=', False))
        roots = {}
        for r in be.search_read('knowledge.article', dom + [('parent_id', '=', False)], ['name']):
            roots.setdefault(r['name'], r['id'])
        for name in KB_ROOTS:
            self.check(name in roots, 'root article "%s"' % name, 'missing')
        for parent, kids in KB_CHILDREN.items():
            if parent not in roots:
                continue
            have = {r['name'] for r in be.search_read('knowledge.article', dom + [('parent_id', '=', roots[parent])], ['name'])}
            for k in kids:
                self.check(k in have, '"%s > %s"' % (parent, k), 'missing')

    def documents(self):
        self.sec('DOCUMENTS')
        be = self.be
        if not self.check(be.has_model('documents.document'), 'documents.document model', 'app not installed'):
            return
        own = self.xmlid_ids('documents.document')
        rows = be.search_read('documents.document', [('type', '=', 'folder'), ('folder_id', '=', False),
                                                     ('name', 'in', DOC_ROOTS)],
                              ['name', 'access_internal', 'access_via_link'])
        roots = {}
        for r in sorted(rows, key=lambda r: r['id'] not in own):  # module-owned first
            roots.setdefault(r['name'], r)
        for name in DOC_ROOTS:
            r = roots.get(name)
            self.check(r, 'root folder "%s"%s' % (name, ' [module]' if r and r['id'] in own else ''), 'missing')
        c = roots.get('Contracts')
        if c:
            self.check(c.get('access_internal') == 'none' and c.get('access_via_link') == 'none',
                       '"Contracts" restricted',
                       'access_internal=%s access_via_link=%s' % (c.get('access_internal'), c.get('access_via_link')))
        for parent, kids in DOC_CHILDREN.items():
            if parent not in roots:
                continue
            have = {r['name'] for r in be.search_read('documents.document', [
                ('type', '=', 'folder'), ('folder_id', '=', roots[parent]['id'])], ['name'])}
            for k in kids:
                self.check(k in have, 'folder "%s / %s"' % (parent, k), 'missing')
        tags = {t['name'] for t in be.search_read('documents.tag', [('name', 'in', DOC_TAGS)], ['name'])}
        for t in DOC_TAGS:
            self.check(t in tags, 'tag "%s"' % t, 'missing')

    def config(self):
        self.sec('CONFIG')
        have = {r['key'] for r in self.be.search_read('ir.config_parameter', [('key', 'in', PARAMS)], ['key'])}
        for k in PARAMS:
            self.check(k in have, 'param %s' % k, 'missing')

    def quotation_templates(self):
        self.sec('QUOTATION TEMPLATES')
        be = self.be
        if not self.check(be.has_model('sale.order.template'), 'sale.order.template model', 'not installed'):
            return
        tmpls = {t['name']: t['id'] for t in be.search_read('sale.order.template', [('name', 'in', SO_TEMPLATES)], ['name'])}
        for name in SO_TEMPLATES:
            if not self.check(name in tmpls, 'template "%s"' % name, 'missing'):
                continue
            lines = be.search_read('sale.order.template.line', [('sale_order_template_id', '=', tmpls[name]),
                                                                ('display_type', '=', False)], ['product_id'])
            pids = list({m2o(l['product_id']) for l in lines} - {False})
            codes = {p['id']: p['default_code'] for p in be.search_read(
                'product.product', [('id', 'in', pids)], ['default_code'])}
            bad = [codes.get(m2o(l['product_id'])) or 'no product' for l in lines
                   if codes.get(m2o(l['product_id'])) not in SKUS]
            self.check(lines and not bad, 'template "%s" lines (%d)' % (name, len(lines)),
                       'no product lines' if not lines else 'non-catalog products: %s' % ', '.join(map(str, bad)))

    def run(self):
        for step in (self.catalog, self.project_templates, self.knowledge, self.documents,
                     self.config, self.quotation_templates):
            try:
                step()
            except Exception as e:  # keep going; record as failure
                self.check(False, '%s crashed' % step.__name__, repr(e)[:300])
        return sum(1 for r in self.results if not r['ok'])

    def report(self, as_json=False):
        fails = sum(1 for r in self.results if not r['ok'])
        if as_json:
            print(json.dumps({'failures': fails, 'results': self.results}, indent=2))
            return fails
        cur = None
        for r in self.results:
            if r['section'] != cur:
                cur = r['section']
                print('\n== %s ==' % cur)
            print('  %s  %s%s' % ('PASS' if r['ok'] else 'FAIL', r['check'],
                                  '' if r['ok'] else ' -- ' + r['reason']))
        print('\nAL2C LINT: %d failures' % fails)
        return fails


def main_rpc(argv):
    import argparse
    from urllib.parse import urlparse
    ap = argparse.ArgumentParser(description='AL2C catalog lint (XML-RPC mode)')
    ap.add_argument('--url', default='http://127.0.0.1:28069')
    ap.add_argument('--db', default='insilos20_dev')
    ap.add_argument('--user', default='admin')
    ap.add_argument('--password', default=os.environ.get('AL2C_PASSWORD'))
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)

    # Loopback Guard & Strict Stealth Enforcement (SSRF & Outbound Data Leak Prevention)
    parsed = urlparse(a.url)
    hostname = (parsed.hostname or '').lower()
    ALLOWED_LOOPBACKS = {'127.0.0.1', 'localhost', '::1', '0.0.0.0'}
    if hostname not in ALLOWED_LOOPBACKS:
        sys.stderr.write(
            f"Security Error (Loopback Guard): Refusing connection to non-loopback host '{hostname}'. "
            f"AL2C tooling strictly enforces zero outbound network requests and local isolation.\n"
        )
        return 1

    if not a.password:
        ap.error('password required (--password or AL2C_PASSWORD)')
    lint = Lint(RpcBackend(a.url, a.db, a.user, a.password))
    lint.run()
    return 1 if lint.report(a.json) else 0


if 'env' in globals():  # shell mode
    _lint = Lint(OrmBackend(env))  # noqa: F821
    _lint.run()
    _code = 1 if _lint.report('--json' in os.environ.get('AL2C_LINT_ARGS', '')) else 0
    env.cr.rollback()  # noqa: F821  read-only: never let the shell commit
    raise SystemExit(_code)
else:
    sys.exit(main_rpc(sys.argv[1:]))
