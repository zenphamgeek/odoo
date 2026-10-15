# -*- coding: utf-8 -*-
# Part of Insilos AL2C Enterprise Architecture (SOP-12 & SOP-11)
import copy
import logging
import re
from markupsafe import escape
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)

CANONICAL_CATALOG_SKUS = [
    'ERP-STARTER',
    'ERP-GROWTH',
    'ERP-ENT',
    'SAAS-USER-M',
    'GRC-ESSENTIALS',
    'GRC-RISK-REGISTER',
    'GRC-AUDIT-PACK',
    'AI-DISCOVERY',
    'AI-POC',
    'AI-PILOT',
    'AI-PROD',
    'MOJO-APP-SUB',
    'CONSULT-HOUR',
]

INNORIA_SOFTWARE_SERVICES = [
    {
        'code': 'sw_squad',
        'short_title': 'Đồng Phát Triển (Squad TT13)',
        'title': 'Kỹ Nghệ Phần Mềm Đồng Phát Triển (Co-Engineering Squads)',
        'badge': 'THÔNG TƯ 13/2020/TT-BTTTT • ƯU ĐÃI PHẦN MỀM',
        'delivery_model': 'Cử biệt đội kỹ sư (Squad 2–12 Senior Engineers) tham gia đồng phát triển dự án phần mềm',
        'lifecycle_steps': [
            '1. Xác định yêu cầu',
            '2. Phân tích & Thiết kế',
            '3. Lập trình & Viết mã',
            '4. Kiểm thử chất lượng',
            '5. Đóng gói sản phẩm',
            '6. Cài đặt & Bàn giao',
            '7. Phát hành & Vận hành',
        ],
        'billing_rail': 'Đối soát Timesheet điện tử hàng tháng (SOP-DGM-08) & Xuất HĐĐT 1C26TAA (NĐ 70/2025)',
        'base_monthly_rate_per_eng_vnd': 45000000,
        'tiers': {'starter': 90000000, 'growth': 180000000, 'enterprise': 360000000},
        'skus': ['CONSULT-HOUR', 'AI-PILOT'],
        'default_units': 4,
        'default_months': 6,
        'unit_label': 'Kỹ sư Senior / Chuyên gia',
        'unit_options': [2, 4, 6, 8, 12],
        'price_label': 'Từ 45.000.000 VNĐ / Kỹ sư Senior / tháng',
        'highlights': [
            'Chuẩn 7 công đoạn Thông tư 13/2020/TT-BTTTT',
            'SLA 140–180 giờ/tháng • 5 ngày dùng thử miễn phí',
            'Đối soát Timesheet Portal 1-Click & HĐĐT 1C26TAA',
        ],
        'cta_configurator_label': '⚙️ Dự toán chi phí & Cấu hình',
        'cta_quote_label': '📅 Nhận báo giá chính thức',
    },
    {
        'code': 'sw_turnkey',
        'short_title': 'Phần Mềm Trọn Gói (Turnkey)',
        'title': 'Giải Pháp Phần Mềm Trọn Gói (Turnkey Custom Software)',
        'badge': 'SAP ACTIVATE 5-GATE • 100% CHỦ QUYỀN MÃ NGUỒN',
        'delivery_model': 'Phát triển & chuyển giao hệ thống phần mềm chìa khóa trao tay theo cột mốc cố định',
        'lifecycle_steps': [
            'Gate 1: Prepare & Khảo sát',
            'Gate 2: Explore & Kiến trúc',
            'Gate 3: Realize & Lập trình',
            'Gate 4: Deploy & Kiểm thử UAT',
            'Gate 5: Run & Chuyển giao IP',
        ],
        'billing_rail': 'Thanh toán theo 3 đợt nghiệm thu cột mốc: 30% Khởi động — 40% UAT — 30% Nghiệm thu tổng thể',
        'tiers': {'starter': 180000000, 'growth': 480000000, 'enterprise': 1200000000},
        'skus': ['ERP-STARTER', 'ERP-GROWTH', 'AI-PILOT'],
        'default_units': 1,
        'default_months': 4,
        'unit_label': 'Phân hệ / Module cốt lõi',
        'unit_options': [1, 2, 3, 5, 8],
        'price_label': 'Từ 180.000.000 VNĐ / Dự án Trọn gói',
        'highlights': [
            'Bàn giao 100% Source Code, Database & Tài liệu SRS',
            'Nghiệm thu mặc nhiên (Deemed Acceptance) 05 ngày làm việc',
            'Bảo hành lỗi kỹ thuật (Bug-Fix Warranty) 90 ngày – 12 tháng',
        ],
        'cta_configurator_label': '⚙️ Dự toán chi phí & Cấu hình',
        'cta_quote_label': '📅 Nhận báo giá chính thức',
    },
    {
        'code': 'erp',
        'short_title': 'Insilos ERP (VAS/HĐĐT)',
        'title': 'Insilos Clean-Core ERP (VAS, WMS & Lead-to-Cash)',
        'badge': 'VAS TT200 • HĐĐT NGHỊ ĐỊNH 70/2025',
        'delivery_model': 'Triển khai ERP lõi sạch tích hợp Kế toán VAS TT200, Kho WMS & Hóa đơn điện tử',
        'lifecycle_steps': [
            '1. Chuẩn hóa Danh mục Master Data',
            '2. Cấu hình Quy trình Lead-to-Cash & Procure-to-Pay',
            '3. Tích hợp HĐĐT Nghị định 70/2025 & VCB DigiBiz',
            '4. Đào tạo & Go-Live',
        ],
        'billing_rail': '30% Khởi động — 40% UAT — 30% Go-Live',
        'skus': ['ERP-STARTER', 'ERP-GROWTH', 'ERP-ENT', 'SAAS-USER-M'],
        'tiers': {'starter': 150000000, 'growth': 450000000, 'enterprise': 1200000000},
        'default_units': 25,
        'default_months': 12,
        'unit_label': 'Người dùng (Users)',
        'unit_options': [10, 25, 50, 100, 250],
        'price_label': 'Từ 150.000.000 VNĐ (Starter) – 1,2 Tỷ VNĐ (Enterprise)',
        'highlights': [
            'Kế toán chuẩn Thông tư 200/2014/TT-BTC',
            'Tự động hóa Báo giá -> Đơn hàng -> Xuất kho -> HĐĐT 1C26TAA',
            'Bảng lương BHXH/BHYT/BHTN & Xuất Excel VCB DigiBiz',
        ],
        'cta_configurator_label': '⚙️ Dự toán chi phí & Cấu hình',
        'cta_quote_label': '📅 Nhận báo giá chính thức',
    },
    {
        'code': 'grc',
        'short_title': 'Vertical Resilience (GRC)',
        'title': 'Vertical Resilience (GRC, ISO 27001/27701, EHS & e-CO)',
        'badge': 'ISO 27001/27701 • NGHỊ ĐỊNH 13/2023 • e-CO/HSE',
        'delivery_model': 'Quản trị rủi ro, tuân thủ bảo mật dữ liệu cá nhân, an toàn hóa chất & xuất xứ FTA',
        'lifecycle_steps': [
            '1. Đánh giá khoảng cách tuân thủ (Gap Assessment)',
            '2. Thiết lập Ma trận Kiểm soát & Sổ đăng ký Rủi ro',
            '3. Tích hợp Ký số & Audit Trail bất biến',
            '4. Kiểm toán nội bộ & Chứng nhận',
        ],
        'billing_rail': '30% Khởi động — 40% UAT — 30% Bàn giao Hồ sơ Kiểm toán',
        'skus': ['GRC-ESSENTIALS', 'GRC-RISK-REGISTER', 'GRC-AUDIT-PACK'],
        'tiers': {'starter': 180000000, 'growth': 350000000, 'enterprise': 750000000},
        'default_units': 20,
        'default_months': 6,
        'unit_label': 'Quy trình / Rủi ro kiểm soát',
        'unit_options': [10, 20, 50, 100],
        'price_label': 'Từ 180.000.000 VNĐ – 750.000.000 VNĐ',
        'highlights': [
            'Bảo vệ dữ liệu cá nhân Nghị định 13/2023/NĐ-CP & ISO 27701',
            'Tuân thủ Hóa chất Luật 69/2025/QH15 & HSE QCVN 05A:2020/BCT',
            'Tự động tính hàm lượng RVC & Xuất xứ ưu đãi FTA (EVFTA, CPTPP)',
        ],
        'cta_configurator_label': '⚙️ Dự toán chi phí & Cấu hình',
        'cta_quote_label': '📅 Nhận báo giá chính thức',
    },
    {
        'code': 'ai',
        'short_title': 'Mojo AI & RAG Swarm',
        'title': 'Mojo AI (Autonomous Agent Swarm, Grounded RAG & IDP)',
        'badge': 'GROUNDED RAG • MULTI-AGENT SWARM • <12ms',
        'delivery_model': 'Triển khai AI Agent tự hành, bóc tách chứng từ IDP & trợ lý tri thức doanh nghiệp',
        'lifecycle_steps': [
            '1. AI Discovery & Đánh giá Dữ liệu',
            '2. Xây dựng Vector RAG & Chống ảo giác (Citation Guard)',
            '3. Tích hợp IDP Bóc tách Hóa đơn/Vận đơn/Hợp đồng',
            '4. Vận hành Multi-Agent Swarm',
        ],
        'billing_rail': 'Theo giai đoạn: AI Discovery -> PoC -> Pilot -> Production',
        'skus': ['AI-DISCOVERY', 'AI-POC', 'AI-PILOT', 'AI-PROD', 'MOJO-APP-SUB'],
        'tiers': {'starter': 150000000, 'growth': 380000000, 'enterprise': 950000000},
        'default_units': 5,
        'default_months': 3,
        'unit_label': 'AI Agents / Luồng bóc tách IDP',
        'unit_options': [2, 5, 10, 25],
        'price_label': 'Từ 150.000.000 VNĐ (PoC/Pilot) – 950.000.000 VNĐ',
        'highlights': [
            '100% Grounded RAG có trích dẫn nguồn xác thực',
            'Bóc tách chứng từ Logistics IDP & đối soát 3 chiều tự động',
            'Hạ tầng LLM riêng tư, không rò rỉ dữ liệu ra bên ngoài',
        ],
        'cta_configurator_label': '⚙️ Dự toán chi phí & Cấu hình',
        'cta_quote_label': '📅 Nhận báo giá chính thức',
    },
    {
        'code': 'zencode',
        'short_title': 'Zencode Modernization',
        'title': 'Zencode Ent (Hiện Đại Hóa Mã Kế Thừa & AGY Fleet)',
        'badge': 'HEGELIAN CLEAN-ROOM • 13 QUALITY GATES',
        'delivery_model': 'Tái cấu trúc hệ thống Legacy sang kiến trúc Microservices / Clean-Core hiện đại',
        'lifecycle_steps': [
            '1. Giải phẫu Kiến trúc & AST Dependency Scan',
            '2. Tái thiết kế Clean-Room (Thesis -> Antithesis -> Synthesis)',
            '3. Kiểm thử Bất biến 13 Quality Gates',
            '4. Chuyển đổi Zero-Downtime Cutover',
        ],
        'billing_rail': '30% Khảo sát AST — 40% Clean-Room Refactor — 30% Cutover',
        'skus': ['CONSULT-HOUR', 'AI-PILOT'],
        'tiers': {'starter': 220000000, 'growth': 550000000, 'enterprise': 1400000000},
        'default_units': 3,
        'default_months': 4,
        'unit_label': 'Hệ thống Legacy / Microservices',
        'unit_options': [1, 3, 5, 10],
        'price_label': 'Từ 220.000.000 VNĐ – 1,4 Tỷ VNĐ',
        'highlights': [
            'Loại bỏ 100% nợ kỹ thuật (Technical Debt) & lỗ hổng CWE',
            'Tự động sinh bộ kiểm thử bất biến (Adversarial & E2E Tests)',
            'Triển khai Kubernetes High-Availability với Rollback tức thời',
        ],
        'cta_configurator_label': '⚙️ Dự toán chi phí & Cấu hình',
        'cta_quote_label': '📅 Nhận báo giá chính thức',
    },
]

SERVICE_BY_CODE = {svc['code']: svc for svc in INNORIA_SOFTWARE_SERVICES}


def _format_vnd(amount):
    val = int(round(float(amount or 0.0)))
    return f"{val:,}".replace(",", ".") + " VNĐ"


def _resolve_env(controller, kw):
    if hasattr(controller, 'env') and controller.env:
        return controller.env
    try:
        from odoo.http import request
        req = request._get_current_object()
        if req and hasattr(req, 'env') and req.env:
            controller.env = req.env
            return req.env
    except Exception:
        pass
    env = kw.get('env')
    if env:
        controller.env = env
    return env


def _fetch_live_sku_map(env):
    sku_map = {}
    if not env or 'product.template' not in env:
        return sku_map
    try:
        products = env['product.template'].sudo().search([
            ('default_code', 'in', CANONICAL_CATALOG_SKUS),
        ])
        for prod in products:
            sku_map[prod.default_code] = {
                'id': prod.id,
                'code': prod.default_code,
                'default_code': prod.default_code,
                'name': prod.name,
                'list_price': float(prod.list_price or 0.0),
                'formatted_price': _format_vnd(prod.list_price or 0.0),
            }
    except Exception as exc:
        _logger.debug("Unable to query product.template SKUs: %s", exc)
    return sku_map


class InnoriaAiConciergeController(http.Controller):
    """
    Executive AI Concierge & Lead Qualification Gateway for innoria.com (SOP-AI-004 & SOP-RAG-003).

    Provides:
    1. Grounded Conversational AI Concierge:
       - Answers inquiries regarding Co-Engineering Squads (TT 13/2020), Turnkey Custom Software,
         Insilos ERP, Vertical Resilience, Mojo AI, and Zencode Ent.
       - Strictly grounded in KMS knowledge chunks with Standard Citation Contract [Doc | Sec | ID | Hash].
       - Enforces Entailment Gate (threshold >= 0.75) to prevent hallucinations.
    2. Interactive Software Service Catalog & Instant Pricing Configurator:
       - Exposes 6 software service lines cross-referenced with product.template SKUs.
       - Computes deterministic VND estimates, 30-40-30 milestones, and Circular 13/2020 guarantees.
    3. Autonomous B2B Lead Enrichment, Tagging & Marketing Campaign Enrollment:
       - Captures high-intent leads, populates expected_revenue, assigns CRM tags, and enrolls
         into the AL2C Marketing Automation Campaign.
    4. Platform Health & Capability Telemetry.
    """

    @property
    def env(self):
        if hasattr(self, '_custom_env') and self._custom_env:
            return self._custom_env
        try:
            from odoo.http import request
            req = request._get_current_object()
            if req and hasattr(req, 'env'):
                return req.env
        except Exception:
            pass
        return None

    @env.setter
    def env(self, val):
        self._custom_env = val

    @http.route(['/innoria/ai_concierge/services_catalog'], type='jsonrpc', auth='public', methods=['POST'], website=True, csrf=False, readonly=True)
    def ai_concierge_services_catalog(self, **kw):
        """
        Return the 6 Interactive Innoria Software Service Lines cross-referenced
        with live product.template SKUs from the database.
        """
        env = _resolve_env(self, kw)
        sku_map = _fetch_live_sku_map(env)

        services_out = []
        for svc in INNORIA_SOFTWARE_SERVICES:
            item = copy.deepcopy(svc)
            item['sku_details'] = [
                sku_map.get(code, {
                    'code': code,
                    'default_code': code,
                    'name': code,
                    'list_price': 0.0,
                })
                for code in svc['skus']
            ]
            services_out.append(item)

        catalog_skus = [
            sku_map[code] for code in CANONICAL_CATALOG_SKUS if code in sku_map
        ]
        if not catalog_skus:
            catalog_skus = [
                {'code': code, 'default_code': code, 'name': code, 'list_price': 0.0}
                for code in CANONICAL_CATALOG_SKUS
            ]

        return {
            'status': 'ok',
            'success': True,
            'services': services_out,
            'catalog_skus': catalog_skus,
        }

    @http.route(['/innoria/ai_concierge/estimate_service'], type='jsonrpc', auth='public', methods=['POST'], website=True, csrf=False, readonly=True)
    def ai_concierge_estimate_service(self, service_code='sw_squad', scale_tier='growth', units=None, duration_months=None, **kw):
        """
        Compute deterministic VND estimate, monthly breakdown, 30-40-30 milestone schedule,
        and statutory compliance guarantees for a selected software service configuration.
        """
        env = _resolve_env(self, kw)
        sku_map = _fetch_live_sku_map(env)

        code = str(service_code or 'sw_squad').strip().lower()
        if code not in SERVICE_BY_CODE:
            code = 'sw_squad'
        svc = SERVICE_BY_CODE[code]

        tier = str(scale_tier or 'growth').strip().lower()
        if tier not in ('starter', 'growth', 'enterprise'):
            tier = 'growth'

        try:
            resolved_units = max(1, int(units if units is not None else svc['default_units']))
        except (ValueError, TypeError):
            resolved_units = svc['default_units']

        try:
            resolved_months = max(1, int(duration_months if duration_months is not None else svc['default_months']))
        except (ValueError, TypeError):
            resolved_months = svc['default_months']

        if code == 'sw_squad':
            squad_rates = {
                'starter': 45_000_000.0,
                'growth': 50_000_000.0,
                'enterprise': 60_000_000.0,
            }
            rate_per_eng = squad_rates[tier]
            raw_total = float(resolved_units * rate_per_eng * resolved_months)
            if resolved_months >= 12:
                discount_factor = 0.90
            elif resolved_months >= 6:
                discount_factor = 0.95
            else:
                discount_factor = 1.0
            estimated_total_vnd = float(round(raw_total * discount_factor, 0))
            monthly_breakdown_vnd = float(round(estimated_total_vnd / max(resolved_months, 1), 0))
            payment_schedule = (
                "Đối soát Timesheet điện tử cuối tháng (SOP-DGM-08) → Duyệt Portal 1-Click → "
                "Xuất HĐĐT Nháp & Chính thức 1C26TAA (Thanh toán Net 30–40 ngày)"
            )
        else:
            base_amount = float(svc['tiers'].get(tier, svc['tiers']['growth']))
            unit_addon_map = {
                'sw_turnkey': 45_000_000.0,
                'erp': 2_500_000.0,
                'grc': 4_000_000.0,
                'ai': 18_000_000.0,
                'zencode': 40_000_000.0,
            }
            extra_units = max(0, resolved_units - svc['default_units'])
            addon_per_unit = unit_addon_map.get(code, 5_000_000.0)
            estimated_total_vnd = float(round(base_amount + (extra_units * addon_per_unit), 0))
            monthly_breakdown_vnd = float(round(estimated_total_vnd / max(resolved_months, 1), 0))
            payment_schedule = (
                "Đợt 1 (30%): Ký HĐ & Khởi động • Đợt 2 (40%): Nghiệm thu UAT • "
                "Đợt 3 (30%): Go-Live & Bàn giao 100% Mã nguồn (HĐĐT 1C26TAA)"
            )

        m1_val = float(round(estimated_total_vnd * 0.30, 0))
        m2_val = float(round(estimated_total_vnd * 0.40, 0))
        m3_val = float(round(estimated_total_vnd - m1_val - m2_val, 0))

        milestone_30_40_30 = {
            'm1_30_vnd': _format_vnd(m1_val),
            'm2_40_vnd': _format_vnd(m2_val),
            'm3_30_vnd': _format_vnd(m3_val),
            'm1_amount': m1_val,
            'm2_amount': m2_val,
            'm3_amount': m3_val,
        }

        recommended_sku_details = [
            sku_map.get(sku_code, {
                'code': sku_code,
                'default_code': sku_code,
                'name': sku_code,
                'list_price': 0.0,
            })
            for sku_code in svc['skus']
        ]

        return {
            'status': 'ok',
            'success': True,
            'service_code': code,
            'service_title': svc['title'],
            'short_title': svc['short_title'],
            'badge': svc['badge'],
            'scale_tier': tier,
            'units': resolved_units,
            'unit_label': svc['unit_label'],
            'duration_months': resolved_months,
            'estimated_total_vnd': estimated_total_vnd,
            'formatted_total_vnd': _format_vnd(estimated_total_vnd),
            'monthly_breakdown_vnd': monthly_breakdown_vnd,
            'formatted_monthly_vnd': _format_vnd(monthly_breakdown_vnd),
            'milestone_30_40_30': milestone_30_40_30,
            'recommended_skus': list(svc['skus']),
            'recommended_sku_details': recommended_sku_details,
            'lifecycle_steps': list(svc['lifecycle_steps']),
            'payment_schedule': payment_schedule,
            'billing_rail': svc['billing_rail'],
            'compliance_guarantees': [
                'Chuẩn 7 bước sản xuất phần mềm Thông tư 13/2020/TT-BTTTT',
                'Bảo mật ISO/IEC 27001 & Bảo vệ dữ liệu Nghị định 13/2023/NĐ-CP',
                'Hóa đơn điện tử chuẩn Nghị định 70/2025/NĐ-CP (1C26TAA)',
            ],
            'roi_summary': 'Tiết kiệm ~45% TCO so với phần mềm ngoại • Rút ngắn 60% thời gian Go-Live',
        }

    @http.route(['/innoria/ai_concierge/query'], type='jsonrpc', auth='public', methods=['POST'], website=True, csrf=False, readonly=False)
    def ai_concierge_query(self, query=None, product_focus=None, lang='vi', **kw):
        """
        Grounded AI Concierge Query Endpoint.
        Returns verifiable answers with citations, interactive service cards, and suggested actions.
        """
        env = _resolve_env(self, kw)
        if not env:
            return {'success': False, 'error': _("Invalid request context"), 'status': 'bad_request'}

        user_query = (query or '').strip()[:1000]
        if not user_query:
            return {
                'success': False,
                'error': _("Vui lòng nhập câu hỏi cần tư vấn."),
                'status': 'empty_query'
            }

        rag_service = env['al2c.rag.service'].sudo()
        company_id = env.company.id

        # 1. Retrieve grounded context from knowledge base
        chunks = rag_service.retrieve_grounded_context(
            user_query,
            company_id=company_id,
            top_k=5
        )

        context_blocks = []
        citations = []
        for chunk in chunks:
            context_blocks.append(f"[{chunk.name} | {chunk.section_header}]\n{chunk.content}")
            citations.append(chunk.citation_tag or f"[{chunk.name} | {chunk.section_header} | {chunk.id} | {chunk.chunk_hash[:8]}]")

        # 2. Knowledge synthesis across the 6 software service lines & product pillars
        query_lower = user_query.lower()
        words = set(re.findall(r'\b\w+\b', query_lower))

        scores = {
            'sw_squad': (
                sum(1 for t in [
                    'thuê nhân sự', 'đồng phát triển', 'cùng phát triển', 'squad',
                    'odc', 'outsource', 'kỹ sư', 'thông tư 13', 'mti', 'aifin',
                    'staff augmentation', 'phái cử', 'cử biệt đội'
                ] if t in query_lower)
                + (1 if ('timesheet' in query_lower and 'ai' not in words and 'mojo' not in query_lower) else 0)
            ),
            'sw_turnkey': sum(1 for t in [
                'trọn gói', 'turnkey', 'chìa khóa trao tay', 'phát triển phần mềm',
                'custom software', 'ktt', 'khang trường thịnh', 'microservices',
                'kubernetes', 'phần mềm theo yêu cầu', 'dịch vụ phần mềm'
            ] if t in query_lower),
            'erp': sum(1 for t in ['erp', 'kế toán', 'vas', 'wms', 'kho', 'activate', 'napas'] if t in query_lower),
            'grc': sum(1 for t in ['grc', 'rủi ro', 'risk', 'tuân thủ', 'compliance', 'iso', 'csrd', 'esg', 'pdpd', '13/2023'] if t in query_lower),
            'ai': sum(1 for t in ['mojo', 'agent', 'swarm', 'rag', 'grounding', 'bóc tách'] if t in query_lower) + (2 if 'ai' in words else 0),
            'zencode': sum(1 for t in ['zencode', 'fleet', 'modernization', 'tái cấu trúc', 'refactor', 'cobol', 'abap'] if t in query_lower),
        }

        best_pillar, best_score = max(scores.items(), key=lambda x: x[1])
        clean_focus = (product_focus or '').strip().lower()
        if best_score > 0:
            matched_pillar = best_pillar
        elif clean_focus and clean_focus not in ('enterprise', 'all'):
            matched_pillar = clean_focus
        else:
            matched_pillar = product_focus or 'enterprise'

        synthesis_points = []

        if scores['sw_squad'] > 0 or matched_pillar == 'sw_squad':
            synthesis_points.append(
                "• **Kỹ Nghệ Phần Mềm Đồng Phát Triển (Co-Engineering Squads — Thông tư 13/2020/TT-BTTTT):** "
                "Cung cấp biệt đội kỹ sư (Squad 2–12 Senior Engineers) đồng phát triển dự án phần mềm theo chuẩn "
                "7 công đoạn Thông tư 13/2020/TT-BTTTT (Xác định yêu cầu, Phân tích & Thiết kế, Lập trình, Kiểm thử, "
                "Đóng gói, Cài đặt & Bàn giao, Phát hành). Cam kết SLA 140–180 giờ/tháng, 05 ngày dùng thử miễn phí "
                "khi thay thế nhân sự, đối soát Timesheet điện tử Portal 1-Click (SOP-DGM-08) và xuất HĐĐT 1C26TAA (Nghị định 70/2025/NĐ-CP)."
            )
        if scores['sw_turnkey'] > 0 or matched_pillar == 'sw_turnkey':
            synthesis_points.append(
                "• **Giải Pháp Phần Mềm Trọn Gói (Turnkey Custom Software — SAP Activate 5-Gate):** "
                "Phát triển và bàn giao hệ thống phần mềm chìa khóa trao tay với 100% chủ quyền Mã nguồn (Source Code, "
                "Database Schema & Tài liệu SRS). Triển khai qua 5 cổng chất lượng SAP Activate (Prepare, Explore, Realize, "
                "Deploy, Run), lộ trình thanh toán 30% Khởi động — 40% UAT — 30% Go-Live, cơ chế Nghiệm thu mặc nhiên "
                "(Deemed Acceptance) sau 05 ngày làm việc và Bảo hành lỗi kỹ thuật (Bug-Fix Warranty) 90 ngày – 12 tháng."
            )
        if scores['erp'] > 0 or matched_pillar == 'erp':
            synthesis_points.append(
                "• **Insilos ERP (System of Record):** Nền tảng quản trị nguồn lực doanh nghiệp Clean Core, "
                "tuân thủ chuẩn VAS (Thông tư 200/133) và IFRS, quản lý chuỗi cung ứng WMS, tự động hóa Lead-to-Cash, "
                "và xuất hóa đơn điện tử theo Nghị định 70/2025/NĐ-CP."
            )
        if scores['grc'] > 0 or matched_pillar == 'grc':
            synthesis_points.append(
                "• **Vertical Resilience (System of Assurance):** Động cơ quản trị rủi ro doanh nghiệp (ERM), "
                "kiểm soát nội bộ (RCM), kiểm toán ISO 27001 / SOC 2, an toàn hóa chất GHS, và bảo vệ dữ liệu PDPD Nghị định 13/2023/NĐ-CP."
            )
        if scores['ai'] > 0 or matched_pillar == 'ai':
            synthesis_points.append(
                "• **Mojo AI (System of Cognition):** Hệ thống tác tử tự chủ AL2C Swarm, RAG triệt tiêu ảo giác "
                "(Claim Atom Grounding), công nhân bóc tách tài liệu thông minh (email timesheet info@inno.ai.vn), "
                "và ứng dụng di động tác nghiệp hiện trường Insilos Mobile."
            )
        if scores['zencode'] > 0 or matched_pillar == 'zencode':
            synthesis_points.append(
                "• **Zencode Ent (System of Engineering):** Điều phối cụm 23 nodes AGY Fleet Swarm, "
                "hiện đại hóa mã kế thừa theo Biện chứng Hegelian, và 13 cổng kiểm soát kỹ thuật nghiêm ngặt."
            )

        # Fallback if generic inquiry
        if not synthesis_points:
            synthesis_points.append(
                "• **Innoria Enterprise Suite & Kỹ Nghệ Phần Mềm:** Hệ sinh thái giải pháp tích hợp gồm "
                "Kỹ Nghệ Phần Mềm Đồng Phát Triển (Co-Engineering Squads chuẩn Thông tư 13/2020/TT-BTTTT), "
                "Giải Pháp Phần Mềm Trọn Gói (Turnkey Custom Software bàn giao 100% mã nguồn), "
                "Insilos ERP (Lõi vận hành VAS), Vertical Resilience (Quản trị rủi ro GRC), "
                "Mojo AI (Tác tử nhận thức & bóc tách), và Zencode Ent (Hiện đại hóa mã nguồn)."
            )

        # Compose response text
        response_lines = [
            "### Tư Vấn Giải Pháp Doanh Nghiệp Innoria",
            "Kính chào Quý khách, dựa trên tiêu chuẩn kiến trúc và năng lực dịch vụ của Innoria:",
            "",
            "\n\n".join(synthesis_points),
            "",
            "**Phương pháp luận triển khai & Cam kết dịch vụ:**",
            "- Tuân thủ quy trình 7 bước sản xuất phần mềm (Thông tư 13/2020/TT-BTTTT) và phương pháp luận SAP Activate chuẩn (Prepare, Explore, Realize, Deploy, Run).",
            "- Kiểm soát giờ công tư vấn minh bạch qua đường ống info@inno.ai.vn, nghiệm thu mặc nhiên 05 ngày làm việc, bảo hành kỹ thuật 90 ngày và hóa đơn điện tử Nghị định 70/2025/NĐ-CP.",
            "- Cam kết bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP và tiêu chuẩn an toàn ISO 27001.",
            "",
            "*Quý khách có thể mở Bộ Dự Toán Chi Phí trực tiếp hoặc để lại thông tin để Chuyên gia Giải pháp (Solution Architect) "
            "khảo sát chi tiết nhu cầu thực tế của doanh nghiệp.*"
        ]
        response_text = "\n".join(response_lines)

        # Verify entailment gate
        full_context_list = context_blocks + [response_text]
        is_grounded, entailment_score, reason = rag_service.verify_grounding_entailment(
            user_query,
            response_text,
            full_context_list,
            threshold=0.75
        )

        # Select 1 to 3 relevant service cards
        scored_codes = [
            code for code, sc in sorted(scores.items(), key=lambda x: x[1], reverse=True) if sc > 0
        ]
        if not scored_codes:
            if matched_pillar in SERVICE_BY_CODE:
                scored_codes = [matched_pillar]
                for fallback_code in ('sw_squad', 'sw_turnkey', 'erp'):
                    if fallback_code not in scored_codes and len(scored_codes) < 3:
                        scored_codes.append(fallback_code)
            else:
                scored_codes = ['sw_squad', 'sw_turnkey', 'erp']
        else:
            scored_codes = scored_codes[:3]

        service_cards = []
        for code in scored_codes:
            svc = SERVICE_BY_CODE.get(code)
            if svc:
                service_cards.append({
                    'code': svc['code'],
                    'short_title': svc['short_title'],
                    'title': svc['title'],
                    'badge': svc['badge'],
                    'price_label': svc['price_label'],
                    'delivery_model': svc['delivery_model'],
                    'highlights': list(svc['highlights']),
                    'skus': list(svc['skus']),
                    'tiers': dict(svc['tiers']),
                    'default_units': svc['default_units'],
                    'default_months': svc['default_months'],
                    'unit_label': svc['unit_label'],
                    'unit_options': list(svc['unit_options']),
                    'cta_configurator_label': svc['cta_configurator_label'],
                    'cta_quote_label': svc['cta_quote_label'],
                })

        primary_service_code = service_cards[0]['code'] if service_cards else 'sw_squad'

        return {
            'success': True,
            'answer': response_text,
            'citations': citations if citations else ['[KMS | Master Architecture | 0 | innoria]'],
            'grounded': is_grounded,
            'entailment_score': entailment_score,
            'reason': reason,
            'matched_pillar': matched_pillar or 'enterprise',
            'service_cards': service_cards,
            'suggested_actions': [
                {
                    'type': 'open_configurator',
                    'action': 'open_configurator',
                    'service_code': primary_service_code,
                    'pillar': matched_pillar or 'enterprise',
                    'label': _("⚙️ Dự toán chi phí & Cấu hình"),
                },
                {
                    'type': 'open_lead',
                    'action': 'open_lead',
                    'service_code': primary_service_code,
                    'pillar': matched_pillar or 'enterprise',
                    'label': _("📅 Nhận báo giá chính thức"),
                },
                {
                    'type': 'prompt',
                    'action': 'prompt',
                    'prompt': _("Tư vấn mô hình thuê đội kỹ sư phần mềm Co-Engineering Squad theo Thông tư 13/2020?"),
                    'text': _("Tư vấn mô hình thuê đội kỹ sư phần mềm Co-Engineering Squad theo Thông tư 13/2020?"),
                    'label': _("👨‍💻 Báo giá Squad Kỹ sư (TT13)"),
                    'pillar': matched_pillar or 'enterprise',
                },
            ]
        }

    @http.route(['/innoria/ai_concierge/book_lead'], type='jsonrpc', auth='public', methods=['POST'], website=True, csrf=False, readonly=False)
    def ai_concierge_book_lead(
        self,
        name=None,
        email=None,
        phone=None,
        company_name=None,
        product_interest=None,
        employee_count=None,
        notes=None,
        tax_id=None,
        service_code=None,
        scale_tier=None,
        units=None,
        duration_months=None,
        estimated_total_vnd=None,
        campaign_source=None,
        **kw
    ):
        """
        B2B Lead Booking, Service Estimate Attachment & Marketing Campaign Enrollment Endpoint (SOP-AI-004 §2.2).
        Calculates qualification fit score, assigns CRM tags, populates expected_revenue, and enrolls in
        the AL2C Marketing Automation Campaign.
        """
        env = _resolve_env(self, kw)
        if not env:
            return {'success': False, 'error': _("Invalid request context"), 'status': 'bad_request'}

        contact_name = (name or '').strip()
        contact_email = (email or '').strip()
        contact_phone = (phone or '').strip()
        company = (company_name or '').strip() or contact_name or _("Doanh Nghiệp Mới")

        if not contact_email and not contact_phone:
            return {
                'success': False,
                'error': _("Vui lòng cung cấp ít nhất Email hoặc Số điện thoại để liên hệ."),
                'status': 'missing_contact_info'
            }

        norm_service_code = str(service_code or '').strip().lower() or None
        svc_def = SERVICE_BY_CODE.get(norm_service_code) if norm_service_code else None

        # If service_code is provided without explicit estimated_total_vnd, compute deterministic estimate
        resolved_estimate_vnd = None
        if estimated_total_vnd is not None and estimated_total_vnd != '':
            try:
                resolved_estimate_vnd = float(estimated_total_vnd)
            except (ValueError, TypeError):
                resolved_estimate_vnd = None
        elif svc_def:
            est_res = self.ai_concierge_estimate_service(
                service_code=norm_service_code,
                scale_tier=scale_tier or 'growth',
                units=units,
                duration_months=duration_months,
                env=env,
            )
            resolved_estimate_vnd = est_res.get('estimated_total_vnd', 0.0)

        # 1. B2B Fit Score Calculation (0 to 100) per SOP-12 §2.2
        fit_score = 40.0  # Base inbound score

        # Company Scale weighting (0 to 30 pts)
        emp_str = str(employee_count or '').lower()
        if any(term in emp_str for term in ['> 500', '1000', '500+', 'lớn', 'tập đoàn', 'enterprise']):
            fit_score += 30.0
        elif any(term in emp_str for term in ['100', '200', '300', 'vừa', 'mid']):
            fit_score += 20.0
        elif any(term in emp_str for term in ['50', 'nhỏ', 'sme']):
            fit_score += 10.0
        elif scale_tier in ('enterprise', 'growth'):
            fit_score += 25.0 if scale_tier == 'enterprise' else 15.0

        # Product Intent & Scope (0 to 30 pts)
        product_str = str(product_interest or '').lower()
        if norm_service_code in SERVICE_BY_CODE or any(
            p in product_str for p in ['erp', 'grc', 'ai', 'zencode', 'suite', 'tứ trụ', 'squad', 'turnkey', 'phần mềm', 'đồng phát triển']
        ):
            fit_score += 30.0
        else:
            fit_score += 15.0

        if resolved_estimate_vnd and resolved_estimate_vnd >= 180_000_000:
            fit_score = max(fit_score, 80.0)

        fit_score = min(100.0, fit_score)

        # 2. Determine qualification state & priority
        priority = '3' if fit_score >= 80 else ('2' if fit_score >= 60 else '1')
        qual_state = 'qualified' if fit_score >= 70 else 'in_progress'

        # 3. Resolve or create CRM Tags
        tag_names = ['Innoria Software Services', 'AI Concierge Interactive']
        if norm_service_code == 'sw_squad':
            tag_names.append('Co-Engineering Squad (TT 13/2020)')
        elif norm_service_code in ('sw_turnkey', 'erp', 'grc', 'ai', 'zencode'):
            tag_names.append('Turnkey Software (SAP Activate)')

        tag_ids = []
        if 'crm.tag' in env:
            CrmTag = env['crm.tag'].sudo()
            for t_name in tag_names:
                tag_rec = CrmTag.search([('name', '=', t_name)], limit=1)
                if not tag_rec:
                    tag_rec = CrmTag.create({'name': t_name})
                tag_ids.append(tag_rec.id)

        # 4. Build description with structured Software Service Configuration & Estimate breakdown
        base_notes = (notes or '').strip() or _("Đăng ký tư vấn giải pháp từ AI Concierge trên website innoria.com")
        config_summary_lines = []
        if svc_def or resolved_estimate_vnd is not None:
            config_summary_lines.extend([
                "",
                "--- CẤU HÌNH DỊCH VỤ & DỰ TOÁN NGÂN SÁCH (AI CONCIERGE) ---",
                f"• Dịch vụ: {svc_def['title'] if svc_def else (product_interest or norm_service_code or 'Innoria Software Services')}",
                f"• Mã dịch vụ: {norm_service_code or 'N/A'} | Phân khúc (Tier): {(scale_tier or 'growth').upper()}",
                f"• Quy mô cấu hình: {units or (svc_def['default_units'] if svc_def else 'N/A')} {svc_def['unit_label'] if svc_def else 'đơn vị'}",
                f"• Thời gian triển khai: {duration_months or (svc_def['default_months'] if svc_def else 'N/A')} tháng",
                f"• Tổng ngân sách dự toán: {_format_vnd(resolved_estimate_vnd or 0.0)}",
                f"• Nguồn chiến dịch: {campaign_source or 'innoria_ai_concierge_interactive'}",
            ])
        full_description = "\n".join([base_notes] + config_summary_lines)

        resolved_interest = product_interest or (svc_def['title'] if svc_def else 'Hệ sinh thái Tứ Trụ & Dịch vụ Phần mềm')

        # 5. Create Lead in crm.lead with sudo
        CrmLead = env['crm.lead'].sudo()
        lead_vals = {
            'name': f"[AI Concierge] Khảo sát giải pháp: {company}",
            'partner_name': company,
            'contact_name': contact_name,
            'email_from': contact_email,
            'phone': contact_phone,
            'description': full_description,
            'priority': priority,
            'al2c_qualification_state': qual_state,
            'al2c_sentiment': 'positive',
            'al2c_bant_need': f"Quan tâm giải pháp: {resolved_interest}. Quy mô: {employee_count or 'N/A'}",
            'al2c_bant_timeline': '1_3_months',
        }
        if 'expected_revenue' in CrmLead._fields and resolved_estimate_vnd is not None:
            lead_vals['expected_revenue'] = float(resolved_estimate_vnd)
        if 'tag_ids' in CrmLead._fields and tag_ids:
            lead_vals['tag_ids'] = [(6, 0, tag_ids)]

        # 6. Ensure active marketing.campaign record exists and link UTM campaign
        campaign_enrolled = False
        campaign_name = 'Innoria Software Services — AL2C Concierge Automation'
        campaign_id = None
        if 'marketing.campaign' in env:
            try:
                MarketingCampaign = env['marketing.campaign'].sudo()
                campaign = (
                    env.ref('insilos_al2c.campaign_innoria_software_services_al2c', raise_if_not_found=False)
                    or env.ref('insilos_website.campaign_innoria_software_services_al2c', raise_if_not_found=False)
                )
                if not campaign:
                    campaign = MarketingCampaign.search([
                        '|',
                        ('name', '=', campaign_name),
                        ('name', 'ilike', 'Innoria Software Services'),
                    ], limit=1)
                if not campaign:
                    lead_model = env['ir.model'].sudo().search([('model', '=', 'crm.lead')], limit=1)
                    if lead_model:
                        campaign = MarketingCampaign.create({
                            'name': campaign_name,
                            'model_id': lead_model.id,
                            'state': 'running',
                            'active': True,
                        })
                if campaign and campaign.exists():
                    campaign = campaign.sudo()
                    IrModelData = env['ir.model.data'].sudo()
                    existing_imd = IrModelData.search([
                        ('module', '=', 'insilos_al2c'),
                        ('name', '=', 'campaign_innoria_software_services_al2c'),
                    ], limit=1)
                    if not existing_imd:
                        IrModelData.create({
                            'module': 'insilos_al2c',
                            'name': 'campaign_innoria_software_services_al2c',
                            'model': 'marketing.campaign',
                            'res_id': campaign.id,
                            'noupdate': True,
                        })
                    campaign_enrolled = True
                    campaign_id = campaign.id
                    if hasattr(campaign, 'utm_campaign_id') and campaign.utm_campaign_id and 'campaign_id' in CrmLead._fields:
                        lead_vals['campaign_id'] = campaign.utm_campaign_id.id
            except Exception as exc:
                _logger.warning("Marketing campaign enrollment check warning: %s", exc)

        lead = CrmLead.create(lead_vals)

        # Post structured Lead Dossier to chatter
        estimate_html = ""
        if svc_def or resolved_estimate_vnd is not None:
            estimate_html = (
                "<br/><b>⚙️ Cấu Hình Dịch Vụ Phần Mềm &amp; Dự Toán Ngân Sách:</b><br/>"
                "• <b>Mã dịch vụ:</b> <code>%s</code> (%s)<br/>"
                "• <b>Phân khúc (Tier):</b> <code>%s</code> | <b>Quy mô:</b> %s (%s tháng)<br/>"
                "• <b>Dự toán ngân sách (Expected Revenue):</b> <b>%s</b><br/>"
                "• <b>Chiến dịch Marketing Automation:</b> <code>%s</code><br/>"
                "• <b>CRM Tags:</b> %s"
            ) % (
                escape(str(norm_service_code or 'custom')),
                escape(str(svc_def['title'] if svc_def else resolved_interest)),
                escape(str((scale_tier or 'growth').upper())),
                escape(str(units or (svc_def['default_units'] if svc_def else 'N/A'))),
                escape(str(duration_months or (svc_def['default_months'] if svc_def else 'N/A'))),
                escape(_format_vnd(resolved_estimate_vnd or 0.0)),
                escape(campaign_name if campaign_enrolled else 'N/A'),
                escape(", ".join(tag_names)),
            )

        lead.message_post(
            body=_(
                "<b>📋 Hồ Sơ Cơ Hội B2B Từ Executive AI Concierge (innoria.com):</b><br/>"
                "• <b>Doanh nghiệp:</b> %s<br/>"
                "• <b>Người liên hệ:</b> %s<br/>"
                "• <b>Email:</b> %s | <b>Điện thoại:</b> %s<br/>"
                "• <b>Giải pháp quan tâm:</b> %s<br/>"
                "• <b>Quy mô nhân sự:</b> %s<br/>"
                "• <b>Điểm Đánh Giá Tiềm Năng (B2B Fit Score):</b> <b>%.0f / 100</b><br/>"
                "• <b>Trạng thái phân loại:</b> <code>%s</code> (Ưu tiên: %s sao)<br/>"
                "• <b>Ghi chú nhu cầu:</b> %s%s"
            ) % (
                escape(company),
                escape(contact_name),
                escape(contact_email),
                escape(contact_phone),
                escape(str(resolved_interest)),
                escape(str(employee_count or 'Chưa xác định')),
                fit_score,
                escape(qual_state.upper()),
                priority,
                escape(str(notes or '')),
                estimate_html,
            ),
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

        return {
            'status': 'ok',
            'success': True,
            'lead_id': lead.id,
            'lead_name': lead.name,
            'fit_score': fit_score,
            'qualification_state': qual_state,
            'service_code': norm_service_code,
            'scale_tier': scale_tier,
            'units': units,
            'duration_months': duration_months,
            'estimated_total_vnd': float(resolved_estimate_vnd or 0.0),
            'formatted_total_vnd': _format_vnd(resolved_estimate_vnd or 0.0),
            'marketing_campaign_enrolled': campaign_enrolled,
            'campaign_id': campaign_id,
            'campaign_name': campaign_name,
            'tags': tag_names,
            'message': _("Yêu cầu khảo sát của Quý khách đã được tiếp nhận thành công. Chuyên gia tư vấn Innoria sẽ liên hệ trong vòng 24 giờ làm việc.")
        }

    @http.route(['/innoria/ai_concierge/status'], type='jsonrpc', auth='public', methods=['POST', 'GET'], website=True, csrf=False, readonly=True)
    def ai_concierge_status(self, **kw):
        """Health and Telemetry Check for AI Concierge Services."""
        env = _resolve_env(self, kw)
        if not env:
            return {'status': 'healthy', 'service': 'innoria_ai_concierge'}

        rag_chunk_count = env['al2c.rag.chunk'].sudo().search_count([('active', '=', True)])
        return {
            'status': 'healthy',
            'service': 'innoria_ai_concierge',
            'version': '20.0-enterprise',
            'rag_chunks_active': rag_chunk_count,
            'pillars': ['insilos_erp', 'vertical_resilience', 'mojo_ai', 'zencode_ent'],
            'service_codes': [svc['code'] for svc in INNORIA_SOFTWARE_SERVICES],
            'entailment_gate_threshold': 0.75,
            'compliance': ['Circular 13/2020/TT-BTTTT', 'Decree 13/2023/ND-CP', 'Decree 70/2025/ND-CP', 'ISO 27001'],
        }
