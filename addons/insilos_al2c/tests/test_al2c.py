from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged

SKUS = [
    'ERP-STARTER', 'ERP-GROWTH', 'ERP-ENT', 'SAAS-USER-M', 'SAAS-HOSTING-PRO', 'SAAS-SLA-PLUS',
    'GRC-ESSENTIALS', 'GRC-RISK-REGISTER', 'GRC-AUDIT-PACK', 'AI-DISCOVERY', 'AI-POC', 'AI-PILOT',
    'AI-PROD', 'MOJO-APP-SUB', 'MOJO-TOKENS', 'MOJO-ONPREM', 'AMS-BRONZE', 'AMS-SILVER', 'AMS-GOLD',
    'TRAINING-DAY', 'CONSULT-HOUR',
]
PHASES = ['Prepare', 'Explore', 'Realize', 'Deploy', 'Run']


def _isolate_dev_db(cls):
    """Keep these tests independent from unrelated data on the shared dev database:
    archive loyalty programs (their product relation table is missing on the dev DB)
    and use an item-less pricelist in company currency (explicit prices are set on
    lines, which also sidesteps a pricelist rule-signature mismatch in subscriptions)."""
    if 'loyalty.program' in cls.env:
        # the dev DB lacks the loyalty <-> product relation tables after the catalog
        # model rename; loyalty is unrelated to AL2C, so skip reward recomputation.
        SaleOrder = cls.registry['sale.order']
        for method in ('_update_programs_and_rewards', '_auto_apply_rewards'):
            if hasattr(SaleOrder, method):
                cls.classPatch(SaleOrder, method, lambda self, *a, **k: None)
    cls.pricelist = cls.env['product.pricelist'].create({
        'name': 'AL2C test pricelist',
        'currency_id': cls.env.company.currency_id.id,
        'item_ids': [Command.clear()],
    })


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cData(TransactionCase):

    def _product(self, sku):
        return self.env['product.template'].search([('default_code', '=', sku)], limit=1)

    def test_catalog_loaded(self):
        for sku in SKUS:
            tmpl = self._product(sku)
            self.assertTrue(tmpl, "SKU %s missing" % sku)
            self.assertEqual(tmpl.type, 'service')
            self.assertTrue(tmpl.invoice_policy and tmpl.service_policy, "%s has no policy" % sku)
            self.assertTrue(tmpl.al2c_knowledge_article_id, "%s has no knowledge article" % sku)
            self.assertTrue(tmpl.al2c_vat_class, "%s has no VAT class" % sku)
            if tmpl.service_tracking in ('project_only', 'task_in_project'):
                self.assertTrue(tmpl.project_template_id.is_template, "%s has no project template" % sku)
                self.assertEqual(tmpl.project_template_id.milestone_ids.mapped('name'), PHASES)
        for sku in ('SAAS-USER-M', 'MOJO-APP-SUB', 'AMS-GOLD'):
            self.assertTrue(self._product(sku).recurring_invoice)
        self.assertEqual(self._product('ERP-GROWTH').service_policy, 'delivered_milestones')
        self.assertEqual(self._product('CONSULT-HOUR').service_policy, 'delivered_timesheet')
        self.assertTrue(self._product('ERP-STARTER').categ_id.complete_name.startswith('Insilos ERP'))
        self.assertEqual(self._product('ERP-STARTER').al2c_vat_class, 'kct')
        self.assertEqual(self._product('SAAS-HOSTING-PRO').al2c_vat_class, 'vat_10')
        self.assertEqual(self._product('AMS-SILVER').al2c_vat_class, 'vat_8')

    def test_quotation_templates(self):
        names = ['ERP Starter', 'ERP Growth', 'ERP Enterprise', 'GRC Essentials', 'AI PoC', 'AI Pilot',
                 'AI Production', 'Mojo App Subscription']
        templates = self.env['sale.order.template'].search([('name', 'in', names)])
        self.assertEqual(sorted(set(templates.mapped('name'))), sorted(names))
        for tpl in templates:
            lines = tpl.sale_order_template_line_ids.filtered(lambda l: not l.display_type)
            self.assertTrue(lines)
            for line in lines:
                self.assertIn(line.product_id.default_code, SKUS)
        self.assertTrue(self.env.ref('insilos_al2c.sot_mojo_sub').plan_id)

    def test_knowledge_tree(self):
        Article = self.env['knowledge.article']
        for name in ['Products', 'Industries', 'Playbooks', 'Battlecards', 'RFP Library', 'Post-mortems', 'Compliance']:
            self.assertTrue(Article.search([('name', '=', name), ('parent_id', '=', False)]), name)
        products = self.env.ref('insilos_al2c.kb_products')
        self.assertEqual(
            set(products.child_ids.mapped('name')), {'ERP', 'GRC', 'AI Solutions', 'Mojo AI Apps', 'Services'})
        playbooks = self.env.ref('insilos_al2c.kb_playbooks')
        self.assertEqual(set(playbooks.child_ids.mapped('name')), {'Sales', 'Delivery'})
        for sku in SKUS:
            article = self._product(sku).al2c_knowledge_article_id
            self.assertEqual(article.root_article_id, products)

    def test_documents_structure(self):
        root = self.env.ref('insilos_al2c.folder_product_docs')
        self.assertEqual(root.type, 'folder')
        self.assertEqual(len(root.children_ids.filtered(lambda d: d.type == 'folder')) if 'children_ids' in root._fields
                         else self.env['documents.document'].search_count([('folder_id', '=', root.id), ('type', '=', 'folder')]), 5)
        contracts = self.env.ref('insilos_al2c.folder_contracts')
        self.assertEqual((contracts.access_internal, contracts.access_via_link), ('none', 'none'))
        self.assertTrue(self.env.ref('insilos_al2c.tag_conf_confidential'))


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cDelivery(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _isolate_dev_db(cls)
        cls.partner = cls.env['res.partner'].create({'name': 'AL2C Test Customer'})

    def _so(self, *skus, user=None):
        env = self.env(user=user) if user else self.env
        lines = []
        for sku in skus:
            product = self.env['product.product'].search([('default_code', '=', sku)], limit=1)
            lines.append(Command.create({
                'product_id': product.id, 'product_uom_qty': 1, 'price_unit': product.list_price,
            }))
        return env['sale.order'].create({
            'partner_id': self.partner.id, 'pricelist_id': self.pricelist.id, 'order_line': lines,
        })

    def test_erp_starter_creates_project_with_phases(self):
        so = self._so('ERP-STARTER')
        so.action_confirm()
        project = so.order_line.project_id
        self.assertTrue(project, "confirming ERP-STARTER must create a project")
        self.assertFalse(project.is_template)
        self.assertEqual(project.milestone_ids.sorted('sequence').mapped('name'), PHASES)
        self.assertEqual(len(project.tasks), 5)
        self.assertEqual(set(project.tasks.mapped('milestone_id')), set(project.milestone_ids))

    def test_erp_growth_milestones_billed_on_line(self):
        so = self._so('ERP-GROWTH')
        so.action_confirm()
        line = so.order_line
        project = line.project_id
        self.assertTrue(project.allow_milestones)
        self.assertEqual(len(project.milestone_ids), 5)
        self.assertEqual(project.milestone_ids.sale_line_id, line, "every Activate milestone bills the SO line")
        doc = self.env['documents.document'].create({
            'name': 'ERP_Growth_Prepare_Signoff.pdf',
            'mimetype': 'application/pdf',
        })
        ms0 = project.milestone_ids.sorted('sequence')[0]
        ms0.write({'al2c_signoff_document_id': doc.id, 'is_reached': True})
        self.assertAlmostEqual(line.qty_delivered, 0.15, places=2)


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cGovernance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env['ir.config_parameter'].sudo()
        cls.icp.set_param('al2c.autonomy_enabled', 'True')
        cls.icp.set_param('al2c.agent_daily_budget', '0')
        cls.icp.set_param('al2c.max_discount', '10')
        cls.icp.set_param('al2c.max_tcv', '500000000')
        cls.agent = new_test_user(
            cls.env, login='al2c_cpq_agent', name='CPQ Agent Bot',
            groups='sales_team.group_sale_salesman,insilos_al2c.group_al2c_agent')
        cls.manager = new_test_user(
            cls.env, login='al2c_deal_desk', name='Deal Desk Manager', groups='sales_team.group_sale_manager')
        cls.human = new_test_user(
            cls.env, login='al2c_human_ae', name='Human AE', groups='sales_team.group_sale_salesman')
        cls.partner = cls.env['res.partner'].create({'name': 'AL2C Gov Customer', 'email': 'gov@example.com'})
        cls.product = cls.env['product.product'].search([('default_code', '=', 'TRAINING-DAY')], limit=1)
        _isolate_dev_db(cls)
        cls.pricelist_vnd = cls.env['product.pricelist'].create({
            'name': 'AL2C test pricelist VND',
            'currency_id': cls.env.ref('base.VND').id,
        })

    def _so(self, user, discount=0.0, price=None, pricelist=None):
        pl = pricelist or getattr(self, 'pricelist_vnd', False) or getattr(self, 'pricelist', False) or self.env.company.partner_id.property_product_pricelist
        unit_price = (self.product.list_price or 100.0) if price is None else price
        return self.env['sale.order'].with_user(user).create({
            'partner_id': self.partner.id,
            'user_id': user.id,
            'pricelist_id': pl.id,
            'order_line': [Command.create({
                'product_id': self.product.id, 'product_uom_qty': 1,
                'price_unit': unit_price, 'discount': discount, 'tax_ids': [Command.clear()],
            })],
        })

    # GOV-001 ---------------------------------------------------------
    def test_guard_refuses_when_disabled(self):
        guard = self.env['al2c.autonomy.guard']
        self.assertTrue(guard._al2c_check_autonomy('Librarian'))
        self.icp.set_param('al2c.autonomy_enabled', 'False')
        with self.assertRaises(UserError):
            guard._al2c_check_autonomy('Librarian')
        # agent quotation actions are refused too
        so = self._so(self.agent)
        with self.assertRaises(UserError):
            so.with_user(self.agent).action_quotation_sent()

    def test_guard_daily_budget(self):
        self.icp.set_param('al2c.agent_daily_budget', '2')
        guard = self.env['al2c.autonomy.guard']
        guard._al2c_check_autonomy('Budget Agent')
        guard._al2c_check_autonomy('Budget Agent')
        with self.assertRaises(UserError):
            guard._al2c_check_autonomy('Budget Agent')
        # other agents keep their own budget
        self.assertTrue(guard._al2c_check_autonomy('Other Agent'))

    # GOV-002 ---------------------------------------------------------
    def test_agent_discount_requires_approval(self):
        so = self._so(self.agent, discount=15.0)
        self.assertTrue(so.al2c_approval_required)
        with self.assertRaises(UserError):
            so.with_user(self.agent).action_quotation_send()
        with self.assertRaises(UserError):
            so.with_user(self.agent).action_quotation_sent()
        with self.assertRaises(UserError):
            so.with_user(self.agent).action_confirm()
        # the agent cannot approve itself
        with self.assertRaises(AccessError):
            so.with_user(self.agent).write({'al2c_approved': True})
        # a deal-desk manager approves, then the agent may send and confirm
        so.with_user(self.manager).write({'al2c_approved': True})
        so.with_user(self.agent).action_quotation_send()
        so.with_user(self.agent).action_confirm()
        self.assertEqual(so.state, 'sale')

    def test_agent_tcv_requires_approval(self):
        so = self._so(self.agent)
        limit = so._al2c_max_tcv_company_currency()
        company = so.company_id or self.env.company
        if so.currency_id != company.currency_id:
            so.order_line.price_unit = company.currency_id._convert(
                limit * 1.5, so.currency_id, company, fields.Date.today()
            )
        else:
            so.order_line.price_unit = limit * 1.5
        self.assertGreater(so._al2c_amount_total_company_currency(), limit)
        with self.assertRaises(UserError):
            so.with_user(self.agent).action_confirm()
        so.with_user(self.manager).al2c_approved = True
        so.with_user(self.agent).action_confirm()
        self.assertEqual(so.state, 'sale')

    def test_agent_tcv_in_vnd(self):
        """Threshold is 500M VND whatever the quotation currency."""
        above = self._so(self.agent, price=600_000_000, pricelist=self.pricelist_vnd)
        self.assertEqual(above.currency_id, self.env.ref('base.VND'))
        self.assertTrue(above.al2c_approval_required)
        with self.assertRaises(UserError):
            above.with_user(self.agent).action_confirm()
        below = self._so(self.agent, price=400_000_000, pricelist=self.pricelist_vnd)
        self.assertFalse(below.al2c_approval_required)

    def test_within_thresholds_and_human_orders_pass(self):
        so = self._so(self.agent, discount=5.0)
        self.assertFalse(so.al2c_approval_required)
        so.with_user(self.agent).action_confirm()
        self.assertEqual(so.state, 'sale')
        human_so = self._so(self.human, discount=30.0)
        self.assertFalse(human_so.al2c_approval_required)
        human_so.with_user(self.human).action_confirm()
        self.assertEqual(human_so.state, 'sale')

    def test_salesman_cannot_approve(self):
        so = self._so(self.agent, discount=20.0)
        with self.assertRaises(AccessError):
            so.with_user(self.human).write({'al2c_approved': True})
