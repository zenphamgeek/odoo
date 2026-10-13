# -*- coding: utf-8 -*-
# Part of Insilos AL2C Enterprise Architecture (SOP-12 & SOP-11)
import json
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.insilos_al2c.controllers.ai_concierge import InnoriaAiConciergeController


@tagged('post_install', '-at_install', 'insilos_al2c', 'ai_concierge')
class TestAiConciergePortal(TransactionCase):
    """
    Test Suite for Executive AI Concierge & Lead Qualification Gateway (innoria.com).
    Verifies:
    1. Grounded RAG queries across the 4 core product pillars with citation chips.
    2. Entailment Gate compliance (threshold >= 0.75).
    3. Autonomous B2B Lead Scoring and crm.lead registration with chatter dossier.
    4. Health and capability telemetry.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = InnoriaAiConciergeController()
        cls.controller.env = cls.env
        cls.company = cls.env.company

        # Ensure active RAG chunks exist for grounding
        RagChunk = cls.env['al2c.rag.chunk'].sudo()
        cls.chunk_erp = RagChunk.create({
            'name': 'Insilos ERP Architecture Blueprint',
            'source_model': 'knowledge.article',
            'source_id': 101,
            'source_ref': 'knowledge.article,101',
            'section_header': 'Products > ERP > Core',
            'chunk_seq': 0,
            'content': (
                "Insilos ERP là nền tảng quản trị doanh nghiệp toàn diện tuân thủ chế độ kế toán Việt Nam "
                "(VAS Thông tư 200/133) và IFRS. Tự động hóa Lead-to-Cash, quản lý kho WMS đa địa điểm, "
                "kết nối thanh toán Napas247 VietQR, và phát hành hóa đơn điện tử Nghị định 70/2025/NĐ-CP. "
                "Quy trình triển khai tuân theo phương pháp luận SAP Activate qua 5 pha chuẩn."
            ),
            'chunk_hash': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            'token_count': 65,
            'company_id': cls.company.id,
        })

        cls.chunk_grc = RagChunk.create({
            'name': 'Vertical Resilience Compliance Manual',
            'source_model': 'knowledge.article',
            'source_id': 102,
            'source_ref': 'knowledge.article,102',
            'section_header': 'Products > GRC > Security',
            'chunk_seq': 0,
            'content': (
                "Vertical Resilience cung cấp giải pháp quản trị rủi ro doanh nghiệp ERM, kiểm soát nội bộ RCM, "
                "tuân thủ an toàn thông tin ISO/IEC 27001, SOC 2 Type II, và bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP."
            ),
            'chunk_hash': '7d793037a0760186574b0282f2f435e7b1e51a4cb5e5e54d86b8b0e7a17730e1',
            'token_count': 45,
            'company_id': cls.company.id,
        })

    def test_01_concierge_status_endpoint(self):
        """Verifies health check and telemetry status."""
        res = self.controller.ai_concierge_status(env=self.env)
        self.assertEqual(res['status'], 'healthy')
        self.assertEqual(res['service'], 'innoria_ai_concierge')
        self.assertIn('insilos_erp', res['pillars'])
        self.assertIn('vertical_resilience', res['pillars'])
        self.assertGreaterEqual(res['rag_chunks_active'], 2)

    def test_02_concierge_query_grounded_erp(self):
        """Inquiry about ERP & SAP Activate returns grounded answer with citation chips."""
        query = "Doanh nghiệp chúng tôi muốn tìm hiểu về hệ thống ERP, chuẩn kế toán VAS và phương pháp triển khai SAP Activate."
        res = self.controller.ai_concierge_query(query=query, env=self.env)

        self.assertTrue(res['success'])
        self.assertTrue(res['grounded'])
        self.assertGreaterEqual(res['entailment_score'], 0.75)
        self.assertEqual(res['matched_pillar'], 'erp')
        self.assertTrue(len(res['citations']) > 0)
        self.assertIn("Insilos ERP", res['answer'])
        self.assertIn("Nghị định 70/2025/NĐ-CP", res['answer'])

    def test_03_concierge_query_grounded_grc(self):
        """Inquiry about risk & compliance returns Vertical Resilience answer."""
        query = "Giải pháp của công ty có đáp ứng kiểm toán ISO 27001 và Nghị định 13/2023 về bảo vệ dữ liệu cá nhân không?"
        res = self.controller.ai_concierge_query(query=query, env=self.env)

        self.assertTrue(res['success'])
        self.assertTrue(res['grounded'])
        self.assertGreaterEqual(res['entailment_score'], 0.75)
        self.assertEqual(res['matched_pillar'], 'grc')
        self.assertIn("Vertical Resilience", res['answer'])

    def test_04_concierge_query_grounded_mojo_ai_zencode(self):
        """Inquiry about AI swarms & code modernization returns Mojo AI and Zencode points."""
        query = "Tư vấn về giải pháp AI agent bóc tách timesheet tự động và công nghệ Zencode fleet."
        res = self.controller.ai_concierge_query(query=query, env=self.env)

        self.assertTrue(res['success'])
        self.assertTrue(res['grounded'])
        self.assertIn("Mojo AI", res['answer'])
        self.assertIn("Zencode Ent", res['answer'])

    def test_05_concierge_book_lead_enterprise_fit_score(self):
        """Booking lead with enterprise scale calculates high B2B fit score and schedules priority."""
        vals = {
            'name': 'Nguyễn Văn Minh',
            'email': 'minh.nguyen@vietport-logistics.vn',
            'phone': '0908123456',
            'company_name': 'Tổng Công ty Cảng Biển Quốc Tế Việt Port',
            'product_interest': 'Insilos ERP + Vertical Resilience GRC',
            'employee_count': '1000+ nhân viên (Tập đoàn)',
            'notes': 'Cần tư vấn triển khai ERP thay thế hệ thống cũ và đáp ứng chuẩn kế toán VAS, kiểm toán ISO 27001.',
            'env': self.env,
        }
        res = self.controller.ai_concierge_book_lead(**vals)

        self.assertTrue(res['success'])
        self.assertGreaterEqual(res['fit_score'], 80.0)
        self.assertEqual(res['qualification_state'], 'qualified')

        lead = self.env['crm.lead'].browse(res['lead_id'])
        self.assertTrue(lead.exists())
        self.assertEqual(lead.priority, '3')
        self.assertEqual(lead.contact_name, 'Nguyễn Văn Minh')
        self.assertEqual(lead.partner_name, 'Tổng Công ty Cảng Biển Quốc Tế Việt Port')

        # Verify chatter dossier contains B2B Fit Score
        messages = lead.message_ids.mapped('body')
        chatter_text = " ".join(messages)
        self.assertIn("Hồ Sơ Cơ Hội B2B Từ Executive AI Concierge", chatter_text)
        self.assertIn("Điểm Đánh Giá Tiềm Năng (B2B Fit Score)", chatter_text)

    def test_06_concierge_book_lead_sme_fit_score(self):
        """Booking lead with SME scale calculates proportional score."""
        vals = {
            'name': 'Trần Thị Thu',
            'email': 'thu.tran@innocafe.vn',
            'phone': '0912345678',
            'company_name': 'InnoKafe Chuỗi Cà Phê Thủ Công',
            'product_interest': 'ERP Starter',
            'employee_count': '50 nhân sự',
            'notes': 'Khảo sát giải pháp bán hàng và quản lý kho.',
            'env': self.env,
        }
        res = self.controller.ai_concierge_book_lead(**vals)

        self.assertTrue(res['success'])
        self.assertGreaterEqual(res['fit_score'], 50.0)
        lead = self.env['crm.lead'].browse(res['lead_id'])
        self.assertTrue(lead.exists())

    def test_07_concierge_empty_inputs_fail_safe(self):
        """Empty query and missing contact details fail safely without server crash."""
        res_q = self.controller.ai_concierge_query(query='', env=self.env)
        self.assertFalse(res_q['success'])
        self.assertEqual(res_q['status'], 'empty_query')

        res_l = self.controller.ai_concierge_book_lead(name='Test User', email='', phone='', env=self.env)
        self.assertFalse(res_l['success'])
        self.assertEqual(res_l['status'], 'missing_contact_info')

    def test_08_concierge_widget_assets_and_templates(self):
        """Verify OWL 2 template, JS, SCSS assets and manifest bundle registrations for AI Concierge."""
        import os
        from odoo.modules.module import get_module_path, get_manifest

        mod_path = get_module_path('insilos_al2c')
        self.assertTrue(mod_path and os.path.isdir(mod_path))

        # 1. Verify XML template file exists and has valid QWeb/OWL structure
        xml_file = os.path.join(mod_path, 'static', 'src', 'xml', 'ai_concierge_widget.xml')
        self.assertTrue(os.path.isfile(xml_file), "ai_concierge_widget.xml must exist")
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        self.assertIn('t-name="innoria.ai_concierge_widget"', xml_content)
        self.assertIn('al2c-concierge-launcher', xml_content)
        self.assertIn('al2c-concierge-drawer', xml_content)
        self.assertIn('al2c-lead-section', xml_content)

        # 2. Verify JS component exists
        js_file = os.path.join(mod_path, 'static', 'src', 'js', 'ai_concierge_widget.js')
        self.assertTrue(os.path.isfile(js_file), "ai_concierge_widget.js must exist")
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
        self.assertIn('class AiConciergeWidget extends Component', js_content)
        self.assertIn('/innoria/ai_concierge/query', js_content)
        self.assertIn('/innoria/ai_concierge/book_lead', js_content)
        self.assertIn('#innoria_ai_concierge_root', js_content)

        # 3. Verify SCSS files exist
        scss_file = os.path.join(mod_path, 'static', 'src', 'scss', 'ai_concierge_widget.scss')
        dark_scss_file = os.path.join(mod_path, 'static', 'src', 'scss', 'ai_concierge_widget.dark.scss')
        self.assertTrue(os.path.isfile(scss_file), "ai_concierge_widget.scss must exist")
        self.assertTrue(os.path.isfile(dark_scss_file), "ai_concierge_widget.dark.scss must exist")

        # 4. Verify manifest registers view and asset bundles
        manifest = get_manifest('insilos_al2c')
        self.assertIn('views/website_ai_concierge_templates.xml', manifest.get('data', []))
        assets_frontend = manifest.get('assets', {}).get('web.assets_frontend', [])
        assets_dark = manifest.get('assets', {}).get('web.assets_web_dark', [])
        self.assertIn('insilos_al2c/static/src/xml/ai_concierge_widget.xml', assets_frontend)
        self.assertIn('insilos_al2c/static/src/js/ai_concierge_widget.js', assets_frontend)
        self.assertIn('insilos_al2c/static/src/scss/ai_concierge_widget.scss', assets_frontend)
        self.assertIn('insilos_al2c/static/src/scss/ai_concierge_widget.dark.scss', assets_dark)

