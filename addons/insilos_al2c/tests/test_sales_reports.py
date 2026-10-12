# -*- coding: utf-8 -*-
# Part of Insilos Enterprise. See LICENSE file for full copyright and licensing details.

import re
from datetime import datetime
from lxml import html as lxml_html
from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'insilos_al2c', 'TestSalesReports')
class TestSalesReports(TransactionCase):
    """Automated unit test suite verifying compilation, structure, statutory compliance,
    and strict anti-genesis invariance across all 4 AL2C enterprise sales document reports:
    1. report_sales_proposal (Sales Proposal)
    2. report_commercial_quotation (Commercial Quotation)
    3. report_statement_of_work (Statement of Work - SOW)
    4. report_sla_contract (SLA & Managed Services Contract)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'name': 'CÔNG TY TNHH ỨNG DỤNG SÁNG TẠO',
            'vat': '0317654321',
            'phone': '+84 28 7300 8888',
            'street': 'Tòa nhà Innovation Hub, Khu Công Nghệ Cao',
            'city': 'TP. Thủ Đức, TP. Hồ Chí Minh',
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Tập Đoàn Thép Pomina - Chi Nhánh Cảng Biển',
            'is_company': True,
            'vat': '0301456789',
            'street': 'Đường số 1B, KCN Phú Mỹ 1',
            'city': 'Bà Rịa - Vũng Tàu',
            'email': 'procurement@pomina-port.vn',
            'phone': '+84 254 389 1234',
        })

        # Ensure pricelist is available
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Bảng Giá B2B Tiêu Chuẩn VND',
            'currency_id': cls.company.currency_id.id,
        })

        # Fetch or create products covering statutory VAT classes
        ProductTemplate = cls.env['product.template']
        cls.prod_erp = cls.env.ref('insilos_al2c.product_erp_growth', raise_if_not_found=False)
        if not cls.prod_erp:
            cls.prod_erp = ProductTemplate.search([('default_code', '=', 'ERP-GROWTH')], limit=1)
        if not cls.prod_erp:
            cls.prod_erp = ProductTemplate.create({
                'name': 'Triển Khai ERP Activate Growth',
                'default_code': 'ERP-GROWTH',
                'type': 'service',
                'service_policy': 'delivered_milestones',
                'list_price': 450000000.0,
                'al2c_vat_class': 'kct',
            })
        cls.prod_erp.write({'al2c_vat_class': 'kct'})

        cls.prod_ams = cls.env.ref('insilos_al2c.product_ams_silver', raise_if_not_found=False)
        if not cls.prod_ams:
            cls.prod_ams = ProductTemplate.search([('default_code', '=', 'AMS-SILVER')], limit=1)
        if not cls.prod_ams:
            cls.prod_ams = ProductTemplate.create({
                'name': 'Dịch Vụ Vận Hành AMS Silver 12x5',
                'default_code': 'AMS-SILVER',
                'type': 'service',
                'list_price': 35000000.0,
                'al2c_vat_class': 'vat_8',
            })
        cls.prod_ams.write({'al2c_vat_class': 'vat_8'})

        cls.prod_cloud = cls.env.ref('insilos_al2c.product_saas_hosting_pro', raise_if_not_found=False)
        if not cls.prod_cloud:
            cls.prod_cloud = ProductTemplate.search([('default_code', '=', 'SAAS-HOSTING-PRO')], limit=1)
        if not cls.prod_cloud:
            cls.prod_cloud = ProductTemplate.create({
                'name': 'Hạ Tầng Cloud Dedicated Pro (NVMe)',
                'default_code': 'SAAS-HOSTING-PRO',
                'type': 'service',
                'list_price': 18000000.0,
                'al2c_vat_class': 'vat_10',
            })
        cls.prod_cloud.write({'al2c_vat_class': 'vat_10'})

        # Setup Value Case linked to partner
        cls.value_case = cls.env['al2c.value.case'].create({
            'name': 'Pomina Port ERP Modernization & HSE Automation Value Case',
            'partner_id': cls.partner.id,
            'tco_current_vnd': 2000000000.0,
            'tco_future_vnd': 1310000000.0,
            'driver_ids': [
                Command.create({
                    'name': 'HSE Automation & PPE Camera Detection Benefit',
                    'category': 'efficiency',
                    'annual_benefit_vnd': 450000000.0,
                }),
            ],
        })

        # Create comprehensive sale order
        cls.order = cls.env['sale.order'].create({
            'name': 'SO-2026-POMINA-001',
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
            'date_order': datetime(2026, 10, 12, 10, 0, 0),
            'value_case_id': cls.value_case.id,
            'al2c_approved': True,
            'order_line': [
                Command.create({
                    'product_id': cls.prod_erp.product_variant_id.id,
                    'name': 'Gói Triển Khai ERP Activate Growth (Chuẩn Clean-Core 5 Giai Đoạn)',
                    'product_uom_qty': 1.0,
                    'price_unit': 450000000.0,
                }),
                Command.create({
                    'product_id': cls.prod_ams.product_variant_id.id,
                    'name': 'Dịch Vụ Vận Hành & Bảo Trì Ứng Dụng AMS Silver (Hợp đồng 12 tháng)',
                    'product_uom_qty': 12.0,
                    'price_unit': 35000000.0,
                }),
                Command.create({
                    'product_id': cls.prod_cloud.product_variant_id.id,
                    'name': 'Thuê Hạ Tầng Cloud Dedicated NVMe SLA 99.9% (12 tháng)',
                    'product_uom_qty': 12.0,
                    'price_unit': 18000000.0,
                }),
            ],
        })
        cls.order.write({'al2c_approved': True})

        # Setup Clean Core FTS items linked to sale order
        cls.fts_item_1 = cls.env['al2c.fts.item'].create({
            'sale_order_id': cls.order.id,
            'name': 'Quy Trình Quản Lý Cảng Biển & e-PTW',
            'clean_core_class': 'class_a',
            'description': 'Cấu hình tiêu chuẩn OOTB trên phân hệ Logistics & An toàn',
        })
        cls.fts_item_2 = cls.env['al2c.fts.item'].create({
            'sale_order_id': cls.order.id,
            'name': 'Giao Diện Shop Floor Tablet Điều Hành Bãi Xe',
            'clean_core_class': 'class_b',
            'description': 'Low-code Studio tùy biến giao diện trạm cân và cổng cảng',
        })
        cls.fts_item_3 = cls.env['al2c.fts.item'].create({
            'sale_order_id': cls.order.id,
            'name': 'Tích Hợp AI CCTV Camera PPE Detection Bằng Decoupled Webhook',
            'clean_core_class': 'class_c',
            'description': 'Kiến trúc Decoupled API kết nối hệ thống Directus GRC và Computer Vision',
        })

        cls.FORBIDDEN_TOKENS = ['odoo', 'openerp', 'todo', 'tbd', 'fixme', 'lorem ipsum']
        cls.REPORT_REFS = [
            'insilos_al2c.action_report_sales_proposal',
            'insilos_al2c.action_report_commercial_quotation',
            'insilos_al2c.action_report_statement_of_work',
            'insilos_al2c.action_report_sla_contract',
        ]

    def _assert_zero_branding_tells(self, html_text, context_name):
        """Strictly assert that rendered HTML contains ZERO platform genesis or placeholder tokens."""
        # Scan the FULL document (head included — titles/meta are prime leak sites),
        # but surgically strip only known framework-internal noise so we don't false-positive
        # on tokens the platform injects regardless of our branding (e.g. __odooAssetError).
        content_to_check = re.sub(
            r'__odooAssetError[A-Za-z0-9_]*',
            '',
            html_text,
        )

        # Layer 1: explicit forbidden-token membership check (restored).
        lower_html = content_to_check.lower()
        for forbidden in self.FORBIDDEN_TOKENS:
            self.assertNotIn(
                forbidden,
                lower_html,
                f"Branding violation in {context_name}: forbidden token '{forbidden}' detected in rendered document.",
            )

        # Layer 2: regex word-boundary check for absolute precision.
        pattern = re.compile(r'\b(odoo|openerp|todo|fixme|tbd|lorem\s+ipsum)\b', re.IGNORECASE)
        match = pattern.search(content_to_check)
        self.assertIsNone(match, f"Regex anti-genesis failed in {context_name}: matched '{match.group(0) if match else ''}'")

        # Layer 3: Negative-selection escaping invariant (XSS & markup correctness guard)
        self.assertNotRegex(
            html_text,
            r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)",
            f"Escaping regression in {context_name}: raw QWeb output contains an unescaped '&'.",
        )

        # Layer 4: Over-escaping invariant (double-escape regression guard)
        self.assertNotIn(
            "&amp;amp;",
            html_text,
            f"Over-escaping regression in {context_name}: '&' was escaped twice (&amp;amp;).",
        )
        self.assertNotIn(
            "&amp;lt;",
            html_text,
            f"Over-escaping regression in {context_name}: '<' was double-escaped.",
        )
        self.assertNotIn(
            "&amp;gt;",
            html_text,
            f"Over-escaping regression in {context_name}: '>' was double-escaped.",
        )

        # Layer 5: Positive render oracle — ensure all ampersands form valid HTML entities
        if "&" in html_text:
            bad_entities = re.findall(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9A-Fa-f]+;)", html_text)
            self.assertFalse(
                bad_entities,
                f"Under-escaping in {context_name}: bare '&' not forming a valid entity ({len(bad_entities)} found).",
            )

    def test_01_report_sales_proposal_render(self):
        """Test Executive Sales Proposal (Bản Đề Xuất Giải Pháp) compilation and content depth."""
        report_ref = 'insilos_al2c.action_report_sales_proposal'
        html_bytes, report_format = self.env['ir.actions.report']._render_qweb_html(report_ref, [self.order.id])
        self.assertEqual(report_format, 'html')
        html_text = html_bytes.decode('utf-8')

        self.assertGreater(len(html_text), 1500, "Rendered Proposal must have substantial executive content.")
        self.assertIn("BẢN ĐỀ XUẤT GIẢI PHÁP CHUYỂN ĐỔI SỐ", html_text)
        self.assertIn("Enterprise Solution Architecture Proposal", html_text)
        # Raw markup strictly asserts properly escaped &amp;
        self.assertIn("Mục Tiêu &amp; Phạm Vi Fit-to-Standard (Clean Core)", html_text)
        self.assertIn("Class A: Chuẩn OOTB", html_text)
        self.assertIn("Class B: Low-Code Studio", html_text)
        self.assertIn("Class C: Decoupled API", html_text)
        self.assertIn("Lập Luận Giá Trị Kinh Tế &amp; TCO / ROI", html_text)
        self.assertIn("34.5", html_text)
        self.assertIn("Lộ Trình Triển Khai 5 Giai Đoạn SAP Activate", html_text)
        self.assertIn("1. Prepare", html_text)
        self.assertIn("5. Run", html_text)
        self.assertIn("Nghị định 13/2023/NĐ-CP", html_text)
        self.assertIn("ĐẠI DIỆN INNORIA ENTERPRISE", html_text)

        # Decoded text content verifies human-readable decoded &
        doc_text = lxml_html.fromstring(html_text).text_content()
        self.assertIn("Mục Tiêu & Phạm Vi Fit-to-Standard (Clean Core)", doc_text)
        self.assertIn("Lập Luận Giá Trị Kinh Tế & TCO / ROI", doc_text)

        self._assert_zero_branding_tells(html_text, "Sales Proposal")

    def test_02_report_commercial_quotation_render(self):
        """Test Official Commercial Quotation (Báo Giá Thương Mại) compilation and tax schedule."""
        report_ref = 'insilos_al2c.action_report_commercial_quotation'
        html_bytes, report_format = self.env['ir.actions.report']._render_qweb_html(report_ref, [self.order.id])
        self.assertEqual(report_format, 'html')
        html_text = html_bytes.decode('utf-8')

        self.assertGreater(len(html_text), 1500, "Rendered Quotation must have substantial commercial content.")
        self.assertIn("BÁO GIÁ THƯƠNG MẠI CHÍNH THỨC", html_text)
        self.assertIn("Official Commercial Quotation", html_text)
        self.assertIn("DEAL DESK VERIFIED · SOD COMPLIANT", html_text)
        self.assertIn("KCT", html_text)
        self.assertIn("VAT 8%", html_text)
        self.assertIn("VAT 10%", html_text)
        self.assertIn("CỔNG THANH TOÁN NAPAS247 CHÍNH THỨC", html_text)
        self.assertIn("0071001234567", html_text)
        self.assertIn("Vietcombank", html_text)
        self.assertIn("Nghị định 70/2025/NĐ-CP", html_text)
        self.assertIn("TỔNG CỘNG THANH TOÁN", html_text)

        self._assert_zero_branding_tells(html_text, "Commercial Quotation")

    def test_03_report_statement_of_work_render(self):
        """Test Statement of Work (Phụ Lục SOW) compilation and 5 Activate delivery phases."""
        report_ref = 'insilos_al2c.action_report_statement_of_work'
        html_bytes, report_format = self.env['ir.actions.report']._render_qweb_html(report_ref, [self.order.id])
        self.assertEqual(report_format, 'html')
        html_text = html_bytes.decode('utf-8')

        self.assertGreater(len(html_text), 1500, "Rendered SOW must have comprehensive scope deliverables.")
        self.assertIn("PHỤ LỤC PHẠM VI CÔNG VIỆC (SOW)", html_text)
        self.assertIn("SAP Activate Project Scope Annex", html_text)
        self.assertIn("GĐ 1: Prepare", html_text)
        self.assertIn("15%", html_text)
        self.assertIn("GĐ 2: Explore", html_text)
        self.assertIn("25%", html_text)
        self.assertIn("GĐ 3: Realize", html_text)
        self.assertIn("35%", html_text)
        self.assertIn("GĐ 4: Deploy", html_text)
        self.assertIn("15%", html_text)
        self.assertIn("GĐ 5: Run", html_text)
        self.assertIn("10%", html_text)
        # Raw markup strictly asserts properly escaped &amp;
        self.assertIn(
            "Biên bản nghiệm thu UAT &amp; Biên bản Go-Live chính thức",
            html_text,
            "SOW must include UAT and Go-Live acceptance clause (properly HTML-escaped)",
        )

        # Decoded text content verifies human-readable decoded &
        doc_text = lxml_html.fromstring(html_text).text_content()
        self.assertIn(
            "Biên bản nghiệm thu UAT & Biên bản Go-Live chính thức",
            doc_text,
            "SOW decoded text must contain UAT and Go-Live clause",
        )

        self._assert_zero_branding_tells(html_text, "Statement of Work (SOW)")

    def test_04_report_sla_contract_render(self):
        """Test SLA & Support Contract compilation and severity resolution matrix."""
        report_ref = 'insilos_al2c.action_report_sla_contract'
        html_bytes, report_format = self.env['ir.actions.report']._render_qweb_html(report_ref, [self.order.id])
        self.assertEqual(report_format, 'html')
        html_text = html_bytes.decode('utf-8')

        self.assertGreater(len(html_text), 1500, "Rendered SLA must contain complete operational commitments.")
        self.assertIn("THỎA THUẬN CAM KẾT MỨC DỊCH VỤ (SLA)", html_text)
        self.assertIn("Enterprise Service Level Agreement", html_text)
        self.assertIn("SLA-GOLD · 24/7", html_text)
        self.assertIn("P1 - Thảm Họa", html_text)
        self.assertIn("P2 - Nghiêm Trọng", html_text)
        self.assertIn("P3 - Trung Bình", html_text)
        self.assertIn("P4 - Thấp", html_text)
        self.assertIn("99.9%", html_text)
        self.assertIn("Service Credits", html_text)
        self.assertIn("Decree 13/2023/NĐ-CP DPA", html_text)
        self.assertIn("AES-256", html_text)
        self.assertIn("TLS 1.3", html_text)

        self._assert_zero_branding_tells(html_text, "SLA Contract")

    def test_05_batch_anti_genesis_audit_all_reports(self):
        """Cross-cutting batch invariant audit across all 4 reports ensuring zero legacy tokens."""
        for report_ref in self.REPORT_REFS:
            with self.subTest(report_ref=report_ref):
                html_bytes, _ = self.env['ir.actions.report']._render_qweb_html(report_ref, [self.order.id])
                html_text = html_bytes.decode('utf-8')
                self.assertGreater(len(html_text), 1000, f"Report {report_ref} rendered output is suspiciously small.")
                self._assert_zero_branding_tells(html_text, report_ref)

                # Verify lookup by direct report_name
                report_action = self.env.ref(report_ref)
                html_by_name_bytes, _ = self.env['ir.actions.report']._render_qweb_html(report_action.report_name, [self.order.id])
                self.assertEqual(len(html_bytes), len(html_by_name_bytes), f"Resolution mismatch on {report_ref}")

    def test_06_report_boundary_conditions_and_escaping(self):
        """Adversarial security test for QWeb proposal report templates:
        1. XSS Escaping: doc.user_id.name containing malicious script tags must be safely entity-escaped.
        2. Clean Omission: value_case_id of False must omit Section 3 cleanly with no traceback.
        3. Empty Lines: empty doc.order_line must render commercial tables cleanly with 0 lines.
        4. Content-Hash Idempotency: doc._get_al2c_report_content_hash produces deterministic non-repudiation key.
        """
        # 1. XSS Escaping Guard: inject malicious username
        malicious_name = '<script>alert("XSS")</script>"><img onerror=alert(1)>'
        self.order.user_id.sudo().write({'name': malicious_name})
        html_bytes, _ = self.env['ir.actions.report']._render_qweb_html(
            'insilos_al2c.action_report_sales_proposal', [self.order.id]
        )
        html_text = html_bytes.decode('utf-8')
        self.assertNotIn('<script>alert("XSS")</script>', html_text, "Unescaped script tag leaked into rendered HTML!")
        self.assertNotIn('"><img onerror=alert(1)>', html_text, "Unescaped img tag leaked into rendered HTML!")
        self.assertTrue(
            '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;' in html_text
            or '&lt;script&gt;alert(&#34;XSS&#34;)&lt;/script&gt;' in html_text,
            "t-out escaping must convert to safe HTML entities",
        )

        # 2. Clean Omission Guard: value_case_id = False
        self.order.write({'value_case_id': False})
        html_bytes, _ = self.env['ir.actions.report']._render_qweb_html(
            'insilos_al2c.action_report_sales_proposal', [self.order.id]
        )
        html_text = html_bytes.decode('utf-8')
        self.assertNotIn('Lập Luận Giá Trị Kinh Tế &amp; TCO / ROI', html_text, "Section 3 must be omitted when value_case_id is False")

        # 3. Empty Lines Guard: empty order_line
        empty_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
        })
        html_bytes, _ = self.env['ir.actions.report']._render_qweb_html(
            'insilos_al2c.action_report_commercial_quotation', [empty_order.id]
        )
        html_text = html_bytes.decode('utf-8')
        self.assertIn("BÁO GIÁ THƯƠNG MẠI CHÍNH THỨC", html_text)

        # 4. Content-Hash Idempotency Invariant
        h1 = empty_order._get_al2c_report_content_hash('insilos_al2c.report_commercial_quotation')
        h2 = empty_order._get_al2c_report_content_hash('insilos_al2c.report_commercial_quotation')
        self.assertEqual(h1, h2, "Content hash must be deterministic for identical document state")
        self.assertEqual(len(h1), 64, "Content hash must be valid 64-char SHA-256")

    def test_07_clock_drift_and_monotonic_ordering_invariant(self):
        """Swarm Invariant Audit:
        Ensure SaleOrder._get_cached_report_attachment resolves multi-node proposal
        and report attachment deduplication monotonically by primary key sequence (`id asc`),
        NEVER relying on wall-clock timestamps (`create_date`) which are vulnerable
        to NTP clock drift across distributed multi-node fleet workers.
        """
        import inspect
        from unittest.mock import MagicMock
        from odoo.addons.insilos_al2c.models.sale_order import SaleOrder

        src = inspect.getsource(SaleOrder._get_cached_report_attachment)

        # Invariant 1: Monotonic ID ordering must be strictly specified in attachment search
        self.assertRegex(
            src,
            r"order=['\"]id\s+asc['\"]",
            "_get_cached_report_attachment must enforce order='id asc' for monotonic deduplication",
        )

        # Invariant 2: Wall-clock timestamp ordering is strictly forbidden due to clock drift risk
        self.assertNotRegex(
            src,
            r"order=['\"][^'\"]*create_date",
            "_get_cached_report_attachment must NEVER order by create_date due to clock drift vulnerability",
        )

        # Invariant 3: Savepoint concurrency guard must be present around attachment creation
        self.assertIn(
            "self.env.cr.savepoint()",
            src,
            "Attachment creation must be wrapped inside a transaction savepoint to handle race collisions safely",
        )

        # Invariant 4: Functional contract test with simulated clock drift / multi-node race
        mock_order = MagicMock()
        mock_order._name = 'sale.order'
        mock_order.id = 999
        mock_order.company_id.id = 1
        mock_order.amount_total = 1000.0
        mock_order.currency_id.id = 1
        mock_order.write_date = datetime(2026, 10, 15, 12, 0, 0)
        mock_order.ensure_one.return_value = True

        mock_att_model = MagicMock()
        mock_env = MagicMock()
        mock_env['ir.attachment'].sudo.return_value = mock_att_model
        mock_order.env = mock_env

        mock_existing = MagicMock(id=42, create_date=datetime(2026, 10, 15, 12, 5, 0))
        mock_att_model.search.return_value = mock_existing

        res = SaleOrder._get_cached_report_attachment(mock_order, 'insilos_al2c.report_sales_proposal')
        self.assertEqual(res, mock_existing)

        search_calls = mock_att_model.search.call_args_list
        self.assertTrue(len(search_calls) > 0, "Attachment search must be called")
        for sc in search_calls:
            _, kwargs = sc
            self.assertEqual(kwargs.get('order'), 'id asc', "Search must enforce order='id asc'")

    def test_08_template_audit_zero_t_raw_sinks(self):
        """Swarm Invariant Audit:
        Audit all sales report XML templates to ensure:
        1. Zero `t-raw` or `raw=` sinks (prevention of XSS / template injection).
        2. Zero synthetic `<t t-out="'&amp;'"/>` noise (use standard valid XML &amp;).
        3. All XML report views are well-formed and parse without error.
        """
        import os
        import lxml.etree

        views_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'views'))
        report_xmls = [
            os.path.join(views_dir, 'report_sales_documents.xml'),
            os.path.join(views_dir, 'report_templates.xml'),
        ]

        for xml_path in report_xmls:
            self.assertTrue(os.path.exists(xml_path), f"Report template file missing: {xml_path}")
            with open(xml_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 1. Zero t-raw or raw= sinks
            self.assertNotIn('t-raw', content, f"Insecure t-raw sink detected in {xml_path}")
            self.assertNotIn('raw=', content, f"Insecure raw= sink detected in {xml_path}")

            # 2. Zero artificial t-out ampersand noise
            self.assertNotIn(
                't-out="\'&amp;\'"',
                content,
                f"Synthetic t-out ampersand noise detected in {xml_path}; standard '&amp;' must be used",
            )
            self.assertNotIn(
                't-out=\'"&amp;"\'',
                content,
                f"Synthetic t-out ampersand noise detected in {xml_path}; standard '&amp;' must be used",
            )

            # 3. XML must parse cleanly
            try:
                lxml.etree.fromstring(content.encode('utf-8'))
            except Exception as e:
                self.fail(f"XML parse failure in {xml_path}: {e}")
