# -*- coding: utf-8 -*-
# Part of Insilos Enterprise. See LICENSE file for full copyright and licensing details.

import re
from datetime import datetime
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
        lower_html = html_text.lower()
        for forbidden in self.FORBIDDEN_TOKENS:
            self.assertNotIn(
                forbidden,
                lower_html,
                f"Branding violation in {context_name}: forbidden token '{forbidden}' detected in rendered document.",
            )
        # Regex word-boundary check for absolute precision
        pattern = re.compile(r'\b(odoo|openerp|todo|fixme|tbd|lorem\s+ipsum)\b', re.IGNORECASE)
        match = pattern.search(html_text)
        self.assertIsNone(match, f"Regex anti-genesis failed in {context_name}: matched '{match.group(0) if match else ''}'")

    def test_01_report_sales_proposal_render(self):
        """Test Executive Sales Proposal (Bản Đề Xuất Giải Pháp) compilation and content depth."""
        report_ref = 'insilos_al2c.action_report_sales_proposal'
        html_bytes, report_format = self.env['ir.actions.report']._render_qweb_html(report_ref, [self.order.id])
        self.assertEqual(report_format, 'html')
        html_text = html_bytes.decode('utf-8')

        self.assertGreater(len(html_text), 1500, "Rendered Proposal must have substantial executive content.")
        self.assertIn("BẢN ĐỀ XUẤT GIẢI PHÁP CHUYỂN ĐỔI SỐ", html_text)
        self.assertIn("Enterprise Solution Architecture Proposal", html_text)
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
        self.assertIn("Nghị định 70/2025/NĐ-CP", html_text)
        self.assertIn("Biên bản nghiệm thu UAT &amp; Biên bản Go-Live chính thức", html_text)

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
