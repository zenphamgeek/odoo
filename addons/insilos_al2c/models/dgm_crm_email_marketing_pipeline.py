# -*- coding: utf-8 -*-
"""
SOP-DGM-13 & SOP-DGM-15: Canonical B2B CRM Pipeline, Maintain Sale & Outsourcing
Man-Hour Governance, Rapid CPQ Lead-to-Quote Handoff, and Segmented Email Marketing
& 4-Touch ABM Automation Engine for Innoria & Digimate JSC (MST: 0317958465).
"""

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

CRM_CUSTOMER_ARCHETYPE_SELECTION = [
    ('outsourcing_partner', '1. Đối tác Outsourcing & Cung ứng Man-Hour (Staff Augmentation)'),
    ('ktt_finance_ops', '2. Kế toán Trưởng (KTT) & Tự động hóa Tài chính - Thuế - Lương'),
    ('erp_insilos_enterprise', '3. Doanh nghiệp Triển khai ERP Đóng gói (Insilos Clean-Core ERP)'),
    ('grc_vertical_resilience', '4. Doanh nghiệp Quản trị Rủi ro & Tuân thủ GRC (Vertical Resilience)'),
    ('mojo_ai_automation', '5. Doanh nghiệp Chuyển đổi AI & Tự động hóa Tri thức (Mojo AI Tools)'),
    ('hybrid_full_stack', '6. Tổ hợp Toàn diện (ERP Insilos + GRC Vertical Resilience + Mojo AI + KTT)'),
]

CRM_SERVICE_PILLAR_SELECTION = [
    ('sw_squad', '1. Dedicated Agile Squad & Man-Hour Outsourcing'),
    ('sw_turnkey', '2. Chief Accountant (KTT) & Turnkey Finance Software'),
    ('erp', '3. Packaged Insilos Clean-Core ERP (SAP Activate)'),
    ('grc', '4. Packaged Vertical Resilience GRC (ISO 27001/27701 & NĐ 13)'),
    ('ai', '5. Mojo AI Tools, Sovereign RAG & IDP Automation'),
    ('zencode', '6. ZenCode Autonomous Engineering & Cloud DevSecOps'),
]

CRM_DEAL_MOTION_SELECTION = [
    ('new_logo_hunt', 'New Logo Acquisition (Săn Khách hàng Mới)'),
    ('account_maintenance_renewal', 'Maintain Sale — Gia hạn Hợp đồng, Timesheet & Đối soát Thanh toán'),
    ('account_expansion_upsell', 'Maintain Sale — Mở rộng / Cross-Sell (ERP · GRC · Mojo AI · KTT)'),
    ('inbound_ai_concierge', 'Inbound AI Concierge & ABM 4-Touch'),
]

CRM_BILLING_GOVERNANCE_SELECTION = [
    ('monthly_timesheet_1c26taa', 'Đối soát Timesheet trước ngày 05 & Xuất HĐĐT 1C26TAA'),
    ('sap_activate_5gate', 'Nghiệm thu 5 Cổng SAP Activate (15/25/35/15/10%)'),
    ('swift_24h_export_sla', 'Xuất khẩu 0% GTGT & Xuất HĐĐT trong 24h nhận SWIFT USD/AUD'),
    ('annual_saas_amc', 'Thuê bao SaaS / Bảo trì AMC Hàng năm'),
]


def _render_carbon_email_html(eyebrow, headline, lead_copy, kpi_items, bullet_points, cta_label, cta_url):
    """Render an executive B2B HTML email body compliant with IBM Carbon v11 & Poppins typography."""
    kpi_cells = "".join(
        f"""
        <td style="width:33.3%;padding:12px 14px;background-color:#f4f4f4;border:1px solid #e0e0e0;border-radius:2px;">
            <div style="font-size:11px;font-weight:600;color:#525252;text-transform:uppercase;letter-spacing:0.5px;">{k_label}</div>
            <div style="font-size:18px;font-weight:700;color:#0f62fe;margin-top:4px;">{k_val}</div>
        </td>
        """
        for k_label, k_val in kpi_items
    )
    bullets_html = "".join(
        f'<li style="margin-bottom:8px;color:#161616;font-size:14px;line-height:1.6;">{bp}</li>'
        for bp in bullet_points
    )
    return f"""
<div style="font-family:'Poppins',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background-color:#f4f4f4;padding:24px;color:#161616;">
  <div style="max-width:680px;margin:0 auto;background-color:#ffffff;border:1px solid #e0e0e0;border-radius:2px;">
    <div style="background-color:#161616;color:#f4f4f4;padding:18px 24px;border-bottom:3px solid #0f62fe;">
      <div style="font-size:11px;font-weight:600;color:#78a9ff;text-transform:uppercase;letter-spacing:0.8px;">{eyebrow}</div>
      <h1 style="margin:6px 0 0 0;font-size:20px;font-weight:600;color:#ffffff;line-height:1.35;">{headline}</h1>
    </div>
    <div style="padding:24px;">
      <p style="margin:0 0 16px 0;font-size:14px;line-height:1.65;color:#161616;">{lead_copy}</p>
      <table role="presentation" style="width:100%;border-collapse:separate;border-spacing:8px;margin:16px 0;">
        <tr>{kpi_cells}</tr>
      </table>
      <div style="margin:18px 0;padding:16px 20px;background-color:#f4f4f4;border-left:4px solid #0f62fe;">
        <div style="font-size:13px;font-weight:600;color:#161616;margin-bottom:8px;">Trọng tâm Giá trị &amp; Quy chuẩn Vận hành (SOP-DGM-13 / SOP-DGM-15):</div>
        <ul style="margin:0;padding-left:18px;">{bullets_html}</ul>
      </div>
      <div style="margin-top:24px;">
        <a href="{cta_url}" style="display:inline-block;background-color:#0f62fe;color:#ffffff;text-decoration:none;font-size:14px;font-weight:600;padding:12px 24px;border-radius:0px;">{cta_label}</a>
      </div>
    </div>
    <div style="padding:14px 24px;background-color:#f4f4f4;border-top:1px solid #e0e0e0;font-size:12px;color:#525252;">
      <strong>INNORIA GROUP · Digimate JSC (MST: 0317958465)</strong> — Clean-Core Enterprise ERP · Vertical Resilience GRC · Mojo AI · KTT Finance &amp; Dedicated Man-Hour Squad.<br/>
      <a href="/unsubscribe_from_list" style="color:#0f62fe;text-decoration:underline;">Quản lý tùy chọn nhận bản tin B2B</a>
    </div>
  </div>
</div>
""".strip()


class CrmLeadPipelineMarketingExtension(models.Model):
    _inherit = 'crm.lead'

    customer_business_archetype = fields.Selection(
        selection=CRM_CUSTOMER_ARCHETYPE_SELECTION,
        string='Đặc thù Kinh doanh Khách hàng (Business Archetype)',
        default='hybrid_full_stack',
        tracking=True,
    )
    service_pillar = fields.Selection(
        selection=CRM_SERVICE_PILLAR_SELECTION,
        string='Trụ cột Giải pháp Chính',
        default='erp',
        index=True,
        tracking=True,
    )
    deal_motion = fields.Selection(
        selection=CRM_DEAL_MOTION_SELECTION,
        string='Loại hình Bán hàng (Sales Motion)',
        default='new_logo_hunt',
        index=True,
        tracking=True,
    )
    billing_governance_mode = fields.Selection(
        selection=CRM_BILLING_GOVERNANCE_SELECTION,
        string='Quy chuẩn Đối soát Timesheet & Thanh toán',
        default='sap_activate_5gate',
        tracking=True,
    )
    account_health_score = fields.Integer(
        string='Chỉ số Sức khỏe Tài khoản (Account Health 0-100)',
        default=88,
        tracking=True,
    )
    next_qbr_or_renewal_date = fields.Date(
        string='Ngày Họp QBR / Gia hạn Tiếp theo',
    )
    rapid_quote_order_id = fields.Many2one(
        'sale.order',
        string='Báo giá Nhanh CPQ Liên kết',
        copy=False,
    )

    def action_generate_rapid_quote_from_lead(self):
        """One-click Lead -> Rapid CPQ Quotation (< 5m SLA) & Quantified Value Case generator:
        1. Ensures `partner_id` exists on the lead.
        2. Creates or reuses `rapid_quote_order_id` (`sale.order` linked via `opportunity_id`).
        3. Runs `order.action_generate_rapid_quote_and_roi(archetype=lead.customer_business_archetype)`.
        4. Links `lead.value_case_id = order.value_case_id.id` and syncs `fts_item_ids`.
        5. Updates `lead.expected_revenue` and advances early stages (< 40) to Stage 04 Rapid CPQ (`sequence = 40`).
        """
        Partner = self.env['res.partner'].sudo()
        SaleOrder = self.env['sale.order'].sudo()
        Stage = self.env['crm.stage'].sudo()

        cpq_stage = Stage.search([('sequence', '=', 40)], limit=1)
        last_order = SaleOrder.browse()

        for lead in self:
            lead_sudo = lead.sudo()
            archetype = lead_sudo.customer_business_archetype or 'hybrid_full_stack'

            partner = lead_sudo.partner_id
            if not partner:
                partner_label = (lead_sudo.partner_name or lead_sudo.contact_name or lead_sudo.name or 'Doanh nghiệp B2B').strip()
                domain = [('name', '=', partner_label)]
                if lead_sudo.email_from:
                    domain = ['|', ('name', '=', partner_label), ('email', '=', lead_sudo.email_from)]
                partner = Partner.search(domain, limit=1)
                if not partner:
                    partner = Partner.create({
                        'name': partner_label,
                        'email': lead_sudo.email_from or False,
                        'phone': lead_sudo.phone or False,
                        'is_company': True,
                        'company_id': lead_sudo.company_id.id if lead_sudo.company_id else False,
                    })
                lead_sudo.partner_id = partner.id

            order = lead_sudo.rapid_quote_order_id
            if not order:
                order = SaleOrder.search([('opportunity_id', '=', lead_sudo.id)], order='id desc', limit=1)
            if not order:
                order_vals = {
                    'partner_id': partner.id,
                    'opportunity_id': lead_sudo.id,
                    'customer_business_archetype': archetype,
                    'company_id': lead_sudo.company_id.id if lead_sudo.company_id else self.env.company.id,
                }
                if lead_sudo.team_id:
                    order_vals['team_id'] = lead_sudo.team_id.id
                if lead_sudo.user_id:
                    order_vals['user_id'] = lead_sudo.user_id.id
                order = SaleOrder.create(order_vals)
            else:
                update_order_vals = {'customer_business_archetype': archetype}
                if not order.opportunity_id:
                    update_order_vals['opportunity_id'] = lead_sudo.id
                if lead_sudo.team_id and order.team_id != lead_sudo.team_id:
                    update_order_vals['team_id'] = lead_sudo.team_id.id
                order.write(update_order_vals)

            order.action_generate_rapid_quote_and_roi(archetype=archetype)

            if order.fts_item_ids:
                unlinked_fts = order.fts_item_ids.filtered(lambda f: f.lead_id != lead_sudo)
                if unlinked_fts:
                    unlinked_fts.write({'lead_id': lead_sudo.id})

            target_rev = max(float(lead_sudo.expected_revenue or 0.0), float(order.amount_untaxed or 0.0))
            if order.value_case_id:
                if order.value_case_id.lead_id != lead_sudo:
                    order.value_case_id.write({'lead_id': lead_sudo.id})
                if target_rev > 0.0 and order.value_case_id.quotation_price_vnd != target_rev:
                    order.value_case_id.action_calibrate_archetype_roi(quotation_price_override=target_rev)

            lead_vals = {
                'rapid_quote_order_id': order.id,
                'value_case_id': order.value_case_id.id if order.value_case_id else lead_sudo.value_case_id.id,
                'expected_revenue': target_rev,
            }
            if (
                cpq_stage
                and not self.env.context.get('preserve_lead_stage')
                and (not lead_sudo.stage_id or (lead_sudo.stage_id.sequence or 0) < 40)
            ):
                lead_vals['stage_id'] = cpq_stage.id

            lead_sudo.write(lead_vals)
            last_order = order

        return last_order

    @api.model
    def action_configure_canonical_crm_and_email_marketing(self):
        """Idempotently configures and reconciles across the current database:
        1. 3 Specialized B2B CRM Sales Teams (`crm.team`) — Hunter, Farmer, SDR.
        2. 7 Canonical B2B CRM Pipeline Stages (`crm.stage`, sequence 10..70).
        3. 8 Canonical CRM Tags (`crm.tag`) & 6 Lost Reasons (`crm.lost.reason`).
        4. 12 Calibrated B2B CRM Opportunities (`crm.lead`) across all 7 stages & 5 pillars
           with full BANT/MEDDICC qualification, Value Case ROI, and Rapid CPQ quotations.
        5. 6 Segmented Email Marketing Lists (`mailing.list`), 18 B2B Contacts (`mailing.contact`),
           8 Executive Email Marketing Broadcasts (`mailing.mailing`), and 4-Touch `marketing.activity`
           chains across all `marketing.campaign` records (#1..#8).
        6. Triggers `cron_dgm_autonomous_marketing_and_research()` for closed-loop attribution.
        """
        Team = self.env['crm.team'].sudo()
        Stage = self.env['crm.stage'].sudo()
        Tag = self.env['crm.tag'].sudo()
        LostReason = self.env['crm.lost.reason'].sudo()
        Lead = self.env['crm.lead'].sudo()
        Partner = self.env['res.partner'].sudo()
        MailingList = self.env['mailing.list'].sudo()
        MailingContact = self.env['mailing.contact'].sudo()
        MailingSubscription = self.env['mailing.subscription'].sudo()
        Mailing = self.env['mailing.mailing'].sudo()
        MarketingCampaign = self.env['marketing.campaign'].sudo()
        MarketingActivity = self.env['marketing.activity'].sudo()
        UtmCampaign = self.env['utm.campaign'].sudo()
        IrModel = self.env['ir.model'].sudo()
        ServerAction = self.env['ir.actions.server'].sudo()

        company = self.env.company or self.env['res.company'].sudo().search([], limit=1)

        # ------------------------------------------------------------------
        # 1. Configure 3 Specialized B2B CRM Sales Teams
        # ------------------------------------------------------------------
        MailAlias = self.env['mail.alias'].sudo()
        hunter_name = 'Enterprise Solution Sales — Insilos ERP · GRC · Mojo AI · KTT (Hunter)'
        farmer_name = 'Key Account Maintenance, Outsourcing Man-Hour & Renewals (Farmer)'
        sdr_name = 'Autonomous AI Concierge & ABM Inbound Desk (SDR)'

        def _ensure_b2b_team(preferred_id, exact_name, kw_match, alias_str, seq_num):
            team_rec = Team.browse(preferred_id).exists() if preferred_id else Team.browse()
            if not team_rec:
                team_rec = Team.with_context(active_test=False).search(
                    [('name', '=', exact_name)], order='id asc', limit=1
                )
            if not team_rec:
                team_rec = Team.with_context(active_test=False).search(
                    [('name', 'ilike', kw_match)], order='id asc', limit=1
                )
            conflicting_aliases = MailAlias.search([
                ('alias_name', '=', alias_str),
                ('id', '!=', team_rec.alias_id.id if team_rec and team_rec.alias_id else 0),
            ])
            if conflicting_aliases:
                conflicting_aliases.write({'alias_name': False})

            vals = {
                'name': exact_name,
                'use_leads': True,
                'use_opportunities': True,
                'alias_name': alias_str,
                'sequence': seq_num,
                'active': True,
            }
            if team_rec:
                team_rec.write(vals)
            else:
                team_rec = Team.create(vals)
            return team_rec

        team_hunter = _ensure_b2b_team(1, hunter_name, 'Hunter', 'solutions', 10)
        team_farmer = _ensure_b2b_team(None, farmer_name, 'Farmer', 'accounts', 20)
        team_sdr = _ensure_b2b_team(None, sdr_name, 'Inbound Desk', 'concierge', 30)

        b2b_team_ids = {team_hunter.id, team_farmer.id, team_sdr.id}
        other_teams = Team.with_context(active_test=False).search([
            ('id', 'not in', list(b2b_team_ids)),
        ])
        for oteam in other_teams:
            orphan_leads = Lead.with_context(active_test=False).search([('team_id', '=', oteam.id)])
            if orphan_leads:
                t_name_low = (oteam.name or '').lower()
                fallback_team = (
                    team_farmer if 'farmer' in t_name_low
                    else (team_sdr if 'sdr' in t_name_low or 'inbound' in t_name_low else team_hunter)
                )
                orphan_leads.write({'team_id': fallback_team.id})
            if oteam.active:
                oteam.write({'active': False, 'alias_name': False})

        # ------------------------------------------------------------------
        # 2. Configure 7 Canonical B2B CRM Pipeline Stages (Seq 10..70)
        # ------------------------------------------------------------------
        canonical_stages_spec = [
            (1, 10, '01. Inbound & AI Concierge Capture (MQL)', False,
             'Thu nhận yêu cầu từ AI Concierge, ABM 4-Touch & Inbound Form; phân loại đặc thù kinh doanh.'),
            (2, 20, '02. BANT / MEDDICC Qualified (SQL)', False,
             'Đã thẩm định Ngân sách (Budget), Người quyết định (Economic Buyer), Nỗi đau & Tiến độ triển khai.'),
            (3, 30, '03. Fit-to-Standard & Value Case Discovery', False,
             'Khảo sát quy trình chuẩn Clean-Core (Class A/B/C) và định lượng mô hình TCO / ROI 3 năm.'),
            (None, 40, '04. Rapid CPQ Quotation & Battlecard (< 5m SLA)', False,
             'Khởi tạo Báo giá Nhanh CPQ trong 5 phút kèm Ma trận So sánh Cạnh tranh (Battlecard).'),
            (None, 50, '05. Deal Desk, MSA/SOW & Partner Onboarding (TMP -> PTN)', False,
             'Phê duyệt Deal Desk, cấp mã TMP-DGM và hoàn thiện 4 chứng từ KYC, NDA, MSA, Cổng Thanh toán.'),
            (4, 60, '06. Won · Active Delivery, Timesheet & 1C26TAA Billing', True,
             'Triển khai dự án SAP Activate / Squad Man-Hour, chốt Timesheet trước ngày 05 & xuất HĐĐT 1C26TAA.'),
            (None, 70, '07. Maintain Sale · QBR, SLA Renewal & Cross-Sell Expansion', True,
             'Chăm sóc khách hàng hiện hữu, họp QBR hàng quý, cảnh báo gia hạn 45 ngày & mở rộng đa trụ cột.'),
        ]
        stage_by_seq = {}
        for preferred_id, seq, st_name, is_won, req_text in canonical_stages_spec:
            stage_rec = Stage.browse(preferred_id).exists() if preferred_id else Stage.browse()
            if not stage_rec:
                stage_rec = Stage.search(['|', ('sequence', '=', seq), ('name', '=', st_name)], limit=1)
            stage_vals = {
                'name': st_name,
                'sequence': seq,
                'is_won': is_won,
                'fold': False,
                'requirements': req_text,
                'team_ids': [(5, 0, 0)],
            }
            if stage_rec:
                stage_rec.write(stage_vals)
            else:
                stage_rec = Stage.create(stage_vals)
            stage_by_seq[seq] = stage_rec

        # ------------------------------------------------------------------
        # 3. Configure 8 Canonical CRM Tags & 6 Lost Reasons
        # ------------------------------------------------------------------
        canonical_tag_specs = [
            ('Man-Hour Squad (MTI/Global)', 2),
            ('KTT Finance & 1C26TAA', 4),
            ('Insilos Clean-Core ERP', 10),
            ('Vertical Resilience GRC (NĐ 13 / ISO 27701)', 3),
            ('Mojo AI & Sovereign RAG', 5),
            ('Export 0% VAT (NĐ 70/2025)', 6),
            ('Maintain Sale & Renewal', 7),
            ('Rapid CPQ < 5m', 1),
        ]
        tag_map = {}
        for t_name, t_color in canonical_tag_specs:
            t_rec = Tag.search([('name', '=', t_name)], limit=1)
            if not t_rec:
                t_rec = Tag.create({'name': t_name, 'color': t_color})
            else:
                t_rec.write({'color': t_color})
            tag_map[t_name] = t_rec

        canonical_lost_reasons = [
            'Chưa phê duyệt ngân sách năm (Chuyển luồng ABM Nurture)',
            'Yêu cầu tùy biến phá vỡ Clean-Core (Class D Exception Rejected)',
            'Khách hàng dời lịch triển khai sang Quý tiếp theo',
            'Đối thủ chào giá thấp (Thiếu chuẩn ISO 27701 / GRC)',
            'Chưa hoàn tất KYC / Cổng Kiểm soát Thanh toán (SOP-DGM-06)',
            'Thay đổi nhân sự Quyết định (Economic Buyer)',
        ]
        for lr_name in canonical_lost_reasons:
            lr_rec = LostReason.with_context(active_test=False).search([('name', '=', lr_name)], limit=1)
            if not lr_rec:
                LostReason.create({'name': lr_name, 'active': True})
            elif not lr_rec.active:
                lr_rec.write({'active': True})

        # ------------------------------------------------------------------
        # 4. Calibrate 12 B2B CRM Opportunities Across All 7 Stages & 5 Pillars
        # ------------------------------------------------------------------
        lead_specs = [
            {
                'match_id': 305,
                'match_kw': 'MTI Technology',
                'name': '[DGM-B2B] MTI Technology — Gia hạn & Mở rộng Hợp đồng Kỹ sư Onsite 2026 (HĐ DIGIMATE2401-001)',
                'partner_name': 'CÔNG TY TNHH MTI TECHNOLOGY',
                'contact_name': 'Ban Giám đốc R&D & PMO MTI',
                'email_from': 'pmo-billing@mti-tech.vn',
                'phone': '+842839108888',
                'expected_revenue': 660_000_000.0,
                'probability': 100.0,
                'stage_seq': 70,
                'team_id': team_farmer.id,
                'customer_business_archetype': 'outsourcing_partner',
                'service_pillar': 'sw_squad',
                'deal_motion': 'account_maintenance_renewal',
                'billing_governance_mode': 'monthly_timesheet_1c26taa',
                'account_health_score': 96,
                'next_qbr_or_renewal_date': '2026-12-15',
                'tags': ['Man-Hour Squad (MTI/Global)', 'Maintain Sale & Renewal'],
                'authority_name': 'Giám đốc Khối Kỹ thuật & PMO (MTI Technology)',
                'need': 'Duy trì & mở rộng đội ngũ Kỹ sư Dedicated Squad Onsite/Offshore, đối soát MTI - TIMESHEET tự động trước ngày 05 hàng tháng (OT 100%/150%) và xuất HĐĐT 1C26TAA.',
                'metrics': 'Tiết kiệm 38% chi phí tuyển dụng & vận hành kỹ sư; 100% kỳ đối soát Timesheet đúng hạn trước ngày 05.',
                'criteria': 'Đội ngũ kỹ sư đạt chuẩn chứng chỉ SOP-DGM-11, đối soát Timesheet minh bạch 2 bậc OT và tuân thủ thuế GTGT.',
            },
            {
                'match_id': 306,
                'match_kw': 'Canva Pty Ltd',
                'name': '[DGM-EXP] Canva Pty Ltd — Mở rộng Hệ sinh thái Canvassador & Mojo AI Apps (Export 0% VAT)',
                'partner_name': 'Canva Pty Ltd',
                'contact_name': 'Global Ecosystem & Partnerships Team',
                'email_from': 'pub@digimate.vn',
                'phone': '+61280009999',
                'expected_revenue': 480_000_000.0,
                'probability': 100.0,
                'stage_seq': 60,
                'team_id': team_farmer.id,
                'customer_business_archetype': 'mojo_ai_automation',
                'service_pillar': 'sw_turnkey',
                'deal_motion': 'account_expansion_upsell',
                'billing_governance_mode': 'swift_24h_export_sla',
                'account_health_score': 94,
                'next_qbr_or_renewal_date': '2026-11-30',
                'tags': ['Mojo AI & Sovereign RAG', 'Export 0% VAT (NĐ 70/2025)', 'Maintain Sale & Renewal'],
                'authority_name': 'Head of Developer Ecosystem & App Partnerships',
                'need': 'Phát triển mở rộng chuỗi ứng dụng AI trên hệ sinh thái thiết kế quốc tế, đối soát doanh thu USD/AUD và xuất hóa đơn xuất khẩu 0% GTGT trong 24h nhận SWIFT.',
                'metrics': 'Tăng trưởng 2.8x sản lượng người dùng quốc tế, đảm bảo 100% hồ sơ hoàn thuế & xuất khẩu phần mềm 0% GTGT theo Nghị định 70/2025/NĐ-CP.',
                'criteria': 'Bảo mật API quốc tế, tốc độ phản hồi suy luận AI < 1.5s và quy trình chứng từ SWIFT chuẩn mực.',
            },
            {
                'match_id': 307,
                'match_kw': 'MobiFone',
                'name': '[DGM-CSP] Trung tâm Dịch vụ số MobiFone (MDS) — Tích hợp Cổng AI & Nội dung số MobiAI (HĐ 191/MOBIFONE)',
                'partner_name': 'Trung tâm Dịch vụ số MobiFone - Chi nhánh Tổng Công ty Viễn thông MobiFone',
                'contact_name': 'Ban Dự án Dịch vụ Số MDS',
                'email_from': 'mds-partner@mobifone.vn',
                'phone': '+842437831800',
                'expected_revenue': 350_000_000.0,
                'probability': 85.0,
                'stage_seq': 50,
                'team_id': team_farmer.id,
                'customer_business_archetype': 'mojo_ai_automation',
                'service_pillar': 'ai',
                'deal_motion': 'account_expansion_upsell',
                'billing_governance_mode': 'sap_activate_5gate',
                'account_health_score': 91,
                'next_qbr_or_renewal_date': '2026-11-20',
                'tags': ['Mojo AI & Sovereign RAG', 'Maintain Sale & Renewal'],
                'authority_name': 'Ban Giám đốc Trung tâm Dịch vụ Số (MDS)',
                'need': 'Mở rộng cổng dịch vụ AI & nội dung số, hoàn tất bộ 4 chứng từ On-boarding (KYC, NDA, MSA, Payment Gate) và nghiệm thu theo 5 cột mốc.',
                'metrics': 'Rút ngắn 60% thời gian tích hợp dịch vụ VAS/AI mới, đối soát doanh thu tự động hàng tháng.',
                'criteria': 'Đáp ứng tiêu chuẩn an toàn thông tin viễn thông, SLA 99.95% và đầy đủ hồ sơ pháp lý hợp đồng.',
            },
            {
                'match_id': 308,
                'match_kw': 'Temecula Valley',
                'name': '[DGM-EDU] Temecula Valley USD — Cung cấp Nền tảng Mojo AI Credits & Giải pháp Giáo dục Số (USA Export)',
                'partner_name': 'Temecula Valley Unified School District',
                'contact_name': 'Director of Educational Technology',
                'email_from': 'edtech-procurement@tvusd.us',
                'phone': '+19516762661',
                'expected_revenue': 250_000_000.0,
                'probability': 100.0,
                'stage_seq': 70,
                'team_id': team_farmer.id,
                'customer_business_archetype': 'mojo_ai_automation',
                'service_pillar': 'zencode',
                'deal_motion': 'account_maintenance_renewal',
                'billing_governance_mode': 'swift_24h_export_sla',
                'account_health_score': 95,
                'next_qbr_or_renewal_date': '2026-12-20',
                'tags': ['Mojo AI & Sovereign RAG', 'Export 0% VAT (NĐ 70/2025)', 'Maintain Sale & Renewal'],
                'authority_name': 'Chief Technology Officer — District Board',
                'need': 'Gia hạn gói thuê bao Mojo AI Credits thường niên cho hệ thống giáo dục Hoa Kỳ, thanh toán Wire USD và xuất hóa đơn điện tử 0% GTGT trong 24h.',
                'metrics': 'Phục vụ >15,000 học sinh & giáo viên với tỷ lệ hài lòng 96%, tiết kiệm 55% ngân sách công cụ AI học tập.',
                'criteria': 'Tuân thủ bảo mật dữ liệu giáo dục, kiểm soát định mức Token minh bạch qua sổ cái Mojo Usage Ledger.',
            },
            {
                'match_id': 309,
                'match_kw': 'Tập Đoàn Công Nghiệp Toàn Cầu',
                'name': 'Yêu cầu Tư vấn 3D Showcase — Tập Đoàn Công Nghiệp Toàn Cầu (Insilos Clean-Core ERP)',
                'partner_name': 'Tổ hợp Sản xuất Cơ khí & Công nghệ Cao Toàn Cầu',
                'contact_name': 'Nguyễn Hoàng An — Giám đốc Chuyển đổi Số (CIO)',
                'email_from': 'an.nguyen@enterprise-partner.vn',
                'phone': '+84903112233',
                'expected_revenue': 378_900_000.0,
                'probability': 60.0,
                'stage_seq': 30,
                'team_id': team_hunter.id,
                'customer_business_archetype': 'erp_insilos_enterprise',
                'service_pillar': 'erp',
                'deal_motion': 'new_logo_hunt',
                'billing_governance_mode': 'sap_activate_5gate',
                'account_health_score': 86,
                'next_qbr_or_renewal_date': '2026-11-15',
                'tags': ['Insilos Clean-Core ERP', 'Rapid CPQ < 5m'],
                'authority_name': 'Nguyễn Hoàng An — CIO & Phó Tổng Giám đốc Vận hành',
                'need': 'Thay thế 6 phần mềm rời rạc bằng hệ thống đóng gói Insilos Clean-Core ERP tích hợp MRP, Kho đa vị trí, Hóa đơn 1C26TAA và bảng lương VCB DigiBiz 11 cột.',
                'metrics': 'Giảm 42% TCO vận hành CNTT trong 3 năm, rút ngắn chu kỳ chốt giá thành sản xuất từ 10 ngày xuống 1.5 ngày.',
                'criteria': '100% kiến trúc Clean-Core (Zero Class D Core Hack), triển khai gói gọn trong 6 tuần theo chuẩn SAP Activate.',
            },
            {
                'match_id': 310,
                'match_kw': 'Tổ Hợp Cơ Khí Động Lực',
                'name': 'Yêu cầu Tư vấn 3D Showcase — Tổ Hợp Cơ Khí Động Lực (Insilos ERP & Quản trị Sản xuất)',
                'partner_name': 'Khu Phức hợp Cơ khí & Chế tạo Máy Công nghiệp Động Lực',
                'contact_name': 'Phạm Quốc Bình — Giám đốc Tài chính (CFO)',
                'email_from': 'binh.pham@enterprise-mfg.vn',
                'phone': '+84908223344',
                'expected_revenue': 330_700_000.0,
                'probability': 45.0,
                'stage_seq': 20,
                'team_id': team_hunter.id,
                'customer_business_archetype': 'erp_insilos_enterprise',
                'service_pillar': 'erp',
                'deal_motion': 'new_logo_hunt',
                'billing_governance_mode': 'sap_activate_5gate',
                'account_health_score': 84,
                'next_qbr_or_renewal_date': '2026-11-25',
                'tags': ['Insilos Clean-Core ERP'],
                'authority_name': 'Phạm Quốc Bình — Giám đốc Tài chính (CFO)',
                'need': 'Chuẩn hóa quy trình mua hàng - sản xuất - kế toán thuế GTGT theo Nghị định 70/2025/NĐ-CP và kiểm soát định mức nguyên vật liệu BOM.',
                'metrics': 'Tiết kiệm 350 triệu VND/năm chi phí tồn kho dư thừa và giảm 80% thời gian lập báo cáo quản trị dòng tiền.',
                'criteria': 'Tích hợp trực tiếp hóa đơn điện tử 1C26TAA, đối soát công nợ tự động và giao diện song ngữ Việt - Anh.',
            },
            {
                'match_id': None,
                'match_kw': '[DGM-KTT]',
                'name': '[DGM-KTT] Khối Kế toán Trưởng Tập đoàn Phân phối Đông Nam Á — Tự động hóa Đối soát 3,000 HĐĐT 1C26TAA, VCB DigiBiz 11 Cột & Lương BHXH TZ0857G',
                'partner_name': 'Tập đoàn Phân phối & Bán lẻ Đông Nam Á (SEA Distribution Group)',
                'contact_name': 'Lê Thị Minh Tâm — Kế toán Trưởng (Chief Accountant)',
                'email_from': 'tam.le.ktt@seadist-group.vn',
                'phone': '+84912345678',
                'expected_revenue': 185_000_000.0,
                'probability': 75.0,
                'stage_seq': 40,
                'team_id': team_hunter.id,
                'customer_business_archetype': 'ktt_finance_ops',
                'service_pillar': 'sw_turnkey',
                'deal_motion': 'new_logo_hunt',
                'billing_governance_mode': 'sap_activate_5gate',
                'account_health_score': 90,
                'next_qbr_or_renewal_date': '2026-11-10',
                'tags': ['KTT Finance & 1C26TAA', 'Rapid CPQ < 5m'],
                'authority_name': 'Lê Thị Minh Tâm — Kế toán Trưởng & Ủy viên Tài chính',
                'need': 'Tự động hóa đối soát 3,000 hóa đơn điện tử 1C26TAA mỗi tháng, tính lương PIT 5 bậc 2026, BHXH mã đơn vị TZ0857G (8%/1.5%/1%) và xuất file VCB DigiBiz 11 cột.',
                'metrics': 'Giảm 85% thời gian khóa sổ kế toán tháng, triệt tiêu 100% rủi ro phạt hành chính thuế & BHXH, hoàn vốn sau 2.4 tháng.',
                'criteria': 'Đúng chuẩn định dạng `@` giữ số 0 đầu trên VCB DigiBiz 11 cột và khóa xuất hóa đơn khi chưa có biên bản nghiệm thu.',
            },
            {
                'match_id': None,
                'match_kw': '[DGM-GRC]',
                'name': '[DGM-GRC] Khối Ngân hàng Số & Fintech Việt Nam — Triển khai Vertical Resilience GRC, Bảo vệ Dữ liệu NĐ 13/2023 & ISO/IEC 27701',
                'partner_name': 'Khối Ngân hàng Số & Dịch vụ Tài chính Việt Nam (VN Digital FinServ)',
                'contact_name': 'Trần Đức Huy — Giám đốc Quản trị Rủi ro & Tuân thủ (CRO / DPO)',
                'email_from': 'huy.tran.dpo@vndigitalfin.vn',
                'phone': '+84988776655',
                'expected_revenue': 550_000_000.0,
                'probability': 78.0,
                'stage_seq': 40,
                'team_id': team_hunter.id,
                'customer_business_archetype': 'grc_vertical_resilience',
                'service_pillar': 'grc',
                'deal_motion': 'new_logo_hunt',
                'billing_governance_mode': 'sap_activate_5gate',
                'account_health_score': 92,
                'next_qbr_or_renewal_date': '2026-11-18',
                'tags': ['Vertical Resilience GRC (NĐ 13 / ISO 27701)', 'Rapid CPQ < 5m'],
                'authority_name': 'Trần Đức Huy — Chief Risk & Privacy Officer (CRO)',
                'need': 'Triển khai giải pháp đóng gói Vertical Resilience GRC quản lý Sổ đăng ký Rủi ro, che dấu PII tự động (Partial Masking 30s) và hồ sơ đánh giá tác động Nghị định 13/2023/NĐ-CP.',
                'metrics': 'Phòng ngừa rủi ro phạt vi phạm dữ liệu cá nhân (tới 5% doanh thu), rút ngắn 70% thời gian chuẩn bị bằng chứng kiểm toán ISO 27001/27701.',
                'criteria': 'Nhật ký kiểm toán bất biến SHA-256, quy trình Maker-Checker 2 bước và phân tách dữ liệu đa thuê bao.',
            },
            {
                'match_id': None,
                'match_kw': '[DGM-ERP]',
                'name': '[DGM-ERP] Tổng Công ty Sản xuất & Chuỗi Cung ứng Miền Nam — Triển khai Insilos Clean-Core ERP Growth (SAP Activate 5-Gate)',
                'partner_name': 'Tổng Công ty Sản xuất & Chuỗi Cung ứng Công nghiệp Miền Nam',
                'contact_name': 'Võ Văn Kiệt — Tổng Giám đốc Điều hành (CEO)',
                'email_from': 'kiet.vo@southern-supplychain.vn',
                'phone': '+84909556677',
                'expected_revenue': 495_000_000.0,
                'probability': 88.0,
                'stage_seq': 50,
                'team_id': team_hunter.id,
                'customer_business_archetype': 'erp_insilos_enterprise',
                'service_pillar': 'erp',
                'deal_motion': 'new_logo_hunt',
                'billing_governance_mode': 'sap_activate_5gate',
                'account_health_score': 89,
                'next_qbr_or_renewal_date': '2026-11-12',
                'tags': ['Insilos Clean-Core ERP', 'Rapid CPQ < 5m'],
                'authority_name': 'Võ Văn Kiệt — Tổng Giám đốc (CEO)',
                'need': 'Triển khai toàn trình Insilos Clean-Core ERP Growth cho 180 nhân sự: CRM, Mua hàng, Kho, Sản xuất, Dự án và Kế toán Trưởng KTT theo 5 cổng SAP Activate.',
                'metrics': 'Lợi ích ròng 3 năm đạt >3.8 tỷ VND, tỷ lệ Benefit-to-Quote đạt 4.6x, thời gian hoàn vốn 4.1 tháng.',
                'criteria': 'Cam kết tiến độ Go-Live 6 tuần, bảo toàn 100% khả năng nâng cấp phiên bản và đào tạo chuyển giao SOP đầy đủ.',
            },
            {
                'match_id': None,
                'match_kw': '[DGM-MOJO]',
                'name': '[DGM-MOJO] Khối Logistics & Cảng Biển Quốc tế — Triển khai Mojo AI Sovereign SOP-RAG & IDP OCR Chứng từ Vận tải',
                'partner_name': 'Tập đoàn Vận tải & Cảng Biển Quốc tế Thái Bình Dương',
                'contact_name': 'Đặng Thu Hà — Giám đốc Vận hành Khai thác (COO)',
                'email_from': 'ha.dang.coo@pacific-portlogistics.vn',
                'phone': '+84938990011',
                'expected_revenue': 415_000_000.0,
                'probability': 65.0,
                'stage_seq': 30,
                'team_id': team_hunter.id,
                'customer_business_archetype': 'mojo_ai_automation',
                'service_pillar': 'ai',
                'deal_motion': 'new_logo_hunt',
                'billing_governance_mode': 'sap_activate_5gate',
                'account_health_score': 87,
                'next_qbr_or_renewal_date': '2026-11-28',
                'tags': ['Mojo AI & Sovereign RAG', 'Rapid CPQ < 5m'],
                'authority_name': 'Đặng Thu Hà — Giám đốc Vận hành (COO)',
                'need': 'Ứng dụng Mojo AI IDP bóc tách tự động vận đơn B/L, tờ khai hải quan và trợ lý tri thức nội bộ Sovereign SOP-RAG (RRF k=60, Entailment >= 0.85).',
                'metrics': 'Tăng 3.5x tốc độ xử lý bộ chứng từ xuất nhập khẩu, tiết kiệm 1,800 giờ nhân sự đối chiếu thủ công mỗi năm.',
                'criteria': 'Độ chính xác trích xuất chứng từ >= 98.5%, kiểm soát phân quyền RBAC nghiêm ngặt và không rò rỉ dữ liệu ra mô hình công cộng.',
            },
            {
                'match_id': None,
                'match_kw': '[DGM-MH]',
                'name': '[DGM-MH] Đối tác Công nghệ APAC — Mở rộng Dedicated Agile Squad 8 Kỹ sư Senior (Man-Hour Staff Augmentation 0% VAT)',
                'partner_name': 'APAC Enterprise Cloud Solutions Pte Ltd',
                'contact_name': 'Kelvin Tan — VP of Engineering',
                'email_from': 'kelvin.tan@apac-cloudsolutions.sg',
                'phone': '+6567891234',
                'expected_revenue': 840_000_000.0,
                'probability': 55.0,
                'stage_seq': 20,
                'team_id': team_farmer.id,
                'customer_business_archetype': 'outsourcing_partner',
                'service_pillar': 'sw_squad',
                'deal_motion': 'account_expansion_upsell',
                'billing_governance_mode': 'monthly_timesheet_1c26taa',
                'account_health_score': 93,
                'next_qbr_or_renewal_date': '2026-12-05',
                'tags': ['Man-Hour Squad (MTI/Global)', 'Export 0% VAT (NĐ 70/2025)'],
                'authority_name': 'Kelvin Tan — Vice President of Engineering',
                'need': 'Mở rộng thêm 8 Kỹ sư Senior (Python, OWL, Cloud DevSecOps) theo mô hình Dedicated Agile Squad, đối soát Timesheet hàng tháng và thanh toán xuất khẩu 0% GTGT.',
                'metrics': 'Rút ngắn 50% thời gian ra mắt sản phẩm Quý 4, tiết kiệm 40% chi phí R&D so với tuyển dụng tại Singapore.',
                'criteria': 'Kỹ sư đạt chứng chỉ năng lực Hạng A/B (SOP-DGM-11), báo cáo velocity hàng tuần và cam kết bảo mật mã nguồn NDA.',
            },
            {
                'match_id': None,
                'match_kw': '[DGM-INB]',
                'name': '[DGM-INB] Yêu cầu Báo giá Nhanh từ AI Concierge — Tổ hợp GRC Vertical Resilience & Phần mềm KTT',
                'partner_name': 'Công ty Cổ phần Đầu tư Công nghệ & Dược phẩm Á Châu',
                'contact_name': 'Hoàng Minh Tuấn — Trưởng Ban Pháp chế & Kiểm soát Nội bộ',
                'email_from': 'tuan.hoang@asiapharma-tech.vn',
                'phone': '+84977665544',
                'expected_revenue': 290_000_000.0,
                'probability': 25.0,
                'stage_seq': 10,
                'team_id': team_sdr.id,
                'customer_business_archetype': 'hybrid_full_stack',
                'service_pillar': 'grc',
                'deal_motion': 'inbound_ai_concierge',
                'billing_governance_mode': 'sap_activate_5gate',
                'account_health_score': 82,
                'next_qbr_or_renewal_date': '2026-11-08',
                'tags': ['Vertical Resilience GRC (NĐ 13 / ISO 27701)', 'KTT Finance & 1C26TAA', 'Rapid CPQ < 5m'],
                'authority_name': 'Hoàng Minh Tuấn — Trưởng Ban Pháp chế & Kiểm soát Nội bộ',
                'need': 'Khách hàng tương tác qua AI Concierge yêu cầu báo giá nhanh tổ hợp Tuân thủ Nghị định 13/2023/NĐ-CP và Phân hệ Kế toán Trưởng tự động.',
                'metrics': 'Dự kiến giảm 75% rủi ro tuân thủ dữ liệu y tế & dược phẩm, tự động hóa 100% bảng kê thuế & lương.',
                'criteria': 'Báo giá minh bạch trong 5 phút kèm lộ trình triển khai phân kỳ rõ ràng.',
            },
        ]

        calibrated_leads = Lead.browse()
        for spec in lead_specs:
            lead_rec = Lead.browse(spec['match_id']).exists() if spec['match_id'] else Lead.browse()
            if not lead_rec:
                lead_rec = Lead.with_context(active_test=False).search([
                    ('name', 'ilike', spec['match_kw'])
                ], limit=1)

            partner = lead_rec.partner_id if lead_rec and lead_rec.partner_id else Partner.search([
                ('name', '=', spec['partner_name'])
            ], limit=1)
            if not partner:
                partner = Partner.create({
                    'name': spec['partner_name'],
                    'email': spec['email_from'],
                    'phone': spec['phone'],
                    'is_company': True,
                    'company_id': company.id if company else False,
                })

            is_qualified = spec['stage_seq'] >= 20
            tag_ids = [tag_map[t].id for t in spec['tags'] if t in tag_map]
            stage_rec = stage_by_seq[spec['stage_seq']]

            vals = {
                'name': spec['name'],
                'type': 'opportunity',
                'active': True,
                'partner_id': partner.id,
                'partner_name': spec['partner_name'],
                'contact_name': spec['contact_name'],
                'email_from': spec['email_from'],
                'phone': spec['phone'],
                'expected_revenue': spec['expected_revenue'],
                'probability': spec['probability'],
                'stage_id': stage_rec.id,
                'team_id': spec['team_id'],
                'customer_business_archetype': spec['customer_business_archetype'],
                'service_pillar': spec['service_pillar'],
                'deal_motion': spec['deal_motion'],
                'billing_governance_mode': spec['billing_governance_mode'],
                'account_health_score': spec['account_health_score'],
                'next_qbr_or_renewal_date': spec['next_qbr_or_renewal_date'],
                'tag_ids': [(6, 0, tag_ids)],
                'al2c_bant_budget': True,
                'al2c_bant_budget_amount': spec['expected_revenue'],
                'al2c_bant_authority': is_qualified,
                'al2c_bant_authority_name': spec['authority_name'],
                'al2c_bant_need': spec['need'],
                'al2c_bant_timeline': '1_3_months',
                'al2c_meddicc_metrics': spec['metrics'],
                'al2c_meddicc_economic_buyer': spec['authority_name'] if is_qualified else False,
                'al2c_meddicc_decision_criteria': spec['criteria'],
                'al2c_meddicc_decision_process': (
                    'Thẩm định Fit-to-Standard -> Báo giá Nhanh CPQ (< 5 phút) -> Deal Desk & Ký MSA/SOW (SOP-DGM-06 / SOP-DGM-15).'
                ),
                'al2c_meddicc_identify_pain': spec['need'],
                'al2c_meddicc_champion': spec['contact_name'],
                'al2c_sentiment': 'positive',
                'al2c_touch_count': 3 if is_qualified else 1,
                'al2c_qualification_state': 'qualified' if is_qualified else 'in_progress',
            }
            if lead_rec:
                lead_rec.write(vals)
            else:
                lead_rec = Lead.create(vals)

            lead_rec._compute_al2c_qualification_score()

            if spec['stage_seq'] >= 30:
                lead_rec.with_context(preserve_lead_stage=True).action_generate_rapid_quote_from_lead()
                if lead_rec.expected_revenue != spec['expected_revenue'] or lead_rec.stage_id != stage_rec:
                    lead_rec.write({
                        'expected_revenue': spec['expected_revenue'],
                        'stage_id': stage_rec.id,
                    })
                if lead_rec.value_case_id and lead_rec.value_case_id.quotation_price_vnd != spec['expected_revenue']:
                    lead_rec.value_case_id.action_calibrate_archetype_roi(
                        quotation_price_override=spec['expected_revenue']
                    )

            calibrated_leads |= lead_rec

        legacy_demo_leads = Lead.search([
            ('id', 'not in', calibrated_leads.ids),
            '|',
            ('expected_revenue', '<=', 0),
            '|', '|', '|', '|', '|',
            ('name', 'ilike', 'VinFast'),
            ('name', 'ilike', 'Tân Cảng'),
            ('name', 'ilike', 'Sun Group'),
            ('name', 'ilike', 'Gemadept'),
            ('name', 'ilike', 'Đình Vũ'),
            ('name', 'ilike', 'Cát Lái'),
        ])
        if legacy_demo_leads:
            legacy_demo_leads.write({'active': False})

        # ------------------------------------------------------------------
        # 5. Configure 6 Segmented Email Marketing Lists & 18 B2B Contacts
        # ------------------------------------------------------------------
        mailing_list_specs = [
            (
                1,
                '[DGM-LIST-01] Khách hàng Hiện hữu — Maintain Sale, QBR, Timesheet & Đối soát Thanh toán 1C26TAA',
                [
                    ('Ban PMO & Đối soát Timesheet — MTI Technology', 'CÔNG TY TNHH MTI TECHNOLOGY', 'pmo-billing@mti-tech.vn'),
                    ('Global Ecosystem Billing — Canva Pty Ltd', 'Canva Pty Ltd', 'finance-ap@canva-partner.au'),
                    ('Ban Quản lý Hợp đồng Dịch vụ Số — MobiFone MDS', 'Trung tâm Dịch vụ số MobiFone', 'mds-contract@mobifone.vn'),
                ],
            ),
            (
                None,
                '[DGM-LIST-02] Đối tác Outsourcing & Global R&D — Cung ứng Man-Hour & Dedicated Squad',
                [
                    ('Kelvin Tan — VP Engineering', 'APAC Enterprise Cloud Solutions Pte Ltd', 'kelvin.tan@apac-cloudsolutions.sg'),
                    ('Kenji Takahashi — Director of Offshore R&D', 'Tokyo FinTech Innovation Corp', 'k.takahashi@tokyofintech.jp'),
                    ('Sarah Jenkins — Head of EdTech Platform', 'Temecula Valley Unified School District', 'edtech-procurement@tvusd.us'),
                ],
            ),
            (
                None,
                '[DGM-LIST-03] Câu lạc bộ Kế toán Trưởng (KTT) & CFO — Tự động hóa HĐĐT 1C26TAA, Lương BHXH TZ0857G & VCB DigiBiz',
                [
                    ('Lê Thị Minh Tâm — Kế toán Trưởng Tập đoàn', 'Tập đoàn Phân phối & Bán lẻ Đông Nam Á', 'tam.le.ktt@seadist-group.vn'),
                    ('Phạm Quốc Bình — Giám đốc Tài chính (CFO)', 'Khu Phức hợp Cơ khí Động Lực', 'binh.pham@enterprise-mfg.vn'),
                    ('Nguyễn Thị Thu Trang — Trưởng Ban Kế toán Thuế', 'Tổng Công ty Thương mại & Dịch vụ Sài Gòn', 'trang.nguyen.tax@saigoncommerce.vn'),
                ],
            ),
            (
                None,
                '[DGM-LIST-04] Doanh nghiệp Chuyển đổi Số — Insilos Clean-Core ERP (SAP Activate)',
                [
                    ('Nguyễn Hoàng An — Giám đốc Chuyển đổi Số (CIO)', 'Tập Đoàn Công Nghiệp Toàn Cầu', 'an.nguyen@enterprise-partner.vn'),
                    ('Võ Văn Kiệt — Tổng Giám đốc Điều hành (CEO)', 'Tổng Công ty Sản xuất & Chuỗi Cung ứng Miền Nam', 'kiet.vo@southern-supplychain.vn'),
                    ('Trương Minh Quân — Giám đốc Nhà máy Thông minh', 'Công ty Cổ phần Công nghiệp Phụ trợ Việt Nhật', 'quan.truong@vj-industrial.vn'),
                ],
            ),
            (
                None,
                '[DGM-LIST-05] Khối Tài chính, Sản xuất & Y tế — Vertical Resilience GRC (ISO 27001/27701 & Nghị định 13/2023)',
                [
                    ('Trần Đức Huy — Giám đốc Quản trị Rủi ro & DPO', 'Khối Ngân hàng Số & Dịch vụ Tài chính Việt Nam', 'huy.tran.dpo@vndigitalfin.vn'),
                    ('Hoàng Minh Tuấn — Trưởng Ban Pháp chế & Kiểm soát', 'Công ty Cổ phần Công nghệ & Dược phẩm Á Châu', 'tuan.hoang@asiapharma-tech.vn'),
                    ('Đỗ Thanh Tùng — CISO & Trưởng Ban An toàn Thông tin', 'Tập đoàn Bảo hiểm & Đầu tư Quốc gia', 'tung.do.ciso@nationalinsure.vn'),
                ],
            ),
            (
                None,
                '[DGM-LIST-06] Khối Tự động hóa Tri thức — Mojo AI Tools, Sovereign SOP-RAG & IDP OCR',
                [
                    ('Đặng Thu Hà — Giám đốc Vận hành Cảng Biển (COO)', 'Tập đoàn Vận tải & Cảng Biển Thái Bình Dương', 'ha.dang.coo@pacific-portlogistics.vn'),
                    ('Lâm Bảo Ngọc — Giám đốc Trung tâm Chăm sóc Khách hàng Số', 'Hệ thống Thương mại Đa kênh OmniRetail', 'ngoc.lam.cx@omniretail.vn'),
                    ('Vũ Hoàng Nam — Giám đốc Chiến lược AI & Dữ liệu', 'Tập đoàn Hàng tiêu dùng Nhanh Đông Dương', 'nam.vu.ai@indochinafmcg.vn'),
                ],
            ),
        ]

        mailing_lists = []
        for preferred_list_id, list_name, contacts_data in mailing_list_specs:
            mlist = MailingList.browse(preferred_list_id).exists() if preferred_list_id else MailingList.browse()
            if not mlist:
                mlist = MailingList.with_context(active_test=False).search([
                    '|', ('name', '=', list_name), ('name', 'ilike', list_name[:14])
                ], limit=1)
            if mlist:
                mlist.write({'name': list_name, 'is_public': True, 'active': True})
            else:
                mlist = MailingList.create({'name': list_name, 'is_public': True, 'active': True})
            mailing_lists.append(mlist)

            for c_name, c_company, c_email in contacts_data:
                contact = MailingContact.search([('email', '=', c_email)], limit=1)
                if not contact:
                    contact = MailingContact.create({
                        'name': c_name,
                        'company_name': c_company,
                        'email': c_email,
                    })
                else:
                    contact.write({
                        'name': c_name,
                        'company_name': c_company,
                    })
                sub = MailingSubscription.search([
                    ('contact_id', '=', contact.id),
                    ('list_id', '=', mlist.id),
                ], limit=1)
                if not sub:
                    MailingSubscription.create({
                        'contact_id': contact.id,
                        'list_id': mlist.id,
                        'opt_out': False,
                    })
                elif sub.opt_out:
                    sub.write({'opt_out': False})

        # Archive or assign the generic 'Administrator' contact if it has no email
        admin_contact = MailingContact.search([('name', '=', 'Administrator'), ('email', '=', False)], limit=1)
        if admin_contact:
            admin_contact.write({
                'name': 'Ban Điều hành Chuyển đổi Số — Innoria & Digimate JSC',
                'company_name': 'INNORIA GROUP',
                'email': 'info@inno.ai.vn',
                'list_ids': [(4, mailing_lists[0].id)],
            })

        # ------------------------------------------------------------------
        # 6. Configure 8 Executive HTML `mailing.mailing` Broadcasts
        # ------------------------------------------------------------------
        mailing_list_model = IrModel.search([('model', '=', 'mailing.list')], limit=1)
        default_utm_campaign = UtmCampaign.search([], order='id asc', limit=1)

        broadcast_specs = [
            {
                'match_id': 1,
                'subject': '[Insilos Enterprise] Hồ Sơ Thiết Kế KCN & Trọn Bộ Video 4K Khảo Sát Nghiệp Vụ Clean-Core ERP',
                'preview': 'Khung kiến trúc Insilos Clean-Core ERP cho Khu Công nghiệp, Sản xuất MRP và Chuỗi cung ứng.',
                'list_indexes': [3],
                'eyebrow': 'INSILOS CLEAN-CORE ERP · SAP ACTIVATE 5-GATE',
                'headline': 'Hồ sơ Thiết kế Kiến trúc Khu Công nghiệp & Chuỗi Cung ứng trên Nền tảng Insilos ERP',
                'lead_copy': (
                    'Giải pháp đóng gói Insilos Clean-Core ERP giúp doanh nghiệp sản xuất và khu công nghiệp chuẩn hóa '
                    '100% quy trình từ Báo giá CPQ, Kế hoạch Sản xuất MRP, Quản trị Kho đa vị trí đến Kế toán Thuế 1C26TAA chỉ trong 6 tuần.'
                ),
                'kpis': [
                    ('Thời gian Go-Live', '6 Tuần (Activate)'),
                    ('Tiết kiệm TCO 3 Năm', '42% - 60%'),
                    ('Sửa đổi Lõi (Class D)', '0% (Clean-Core)'),
                ],
                'bullets': [
                    'Áp dụng quy chuẩn Fit-to-Standard 4 lớp (Class A, Class B, Class C, cấm Class D) bảo toàn nâng cấp.',
                    'Tích hợp đồng bộ Hóa đơn Điện tử 1C26TAA (Nghị định 70/2025/NĐ-CP) và Ủy nhiệm chi VCB DigiBiz 11 cột.',
                    'Báo giá nhanh CPQ dưới 5 phút đi kèm Hồ sơ Định lượng Giá trị (Value Case ROI 3 năm).',
                ],
                'cta_label': 'Yêu cầu Báo giá Nhanh CPQ & Demo Kiến trúc',
                'cta_url': '/contactus',
            },
            {
                'match_id': 2,
                'subject': '[Case Study Insilos] Tối Ưu Lệnh Sản Xuất MRP & Điều Phối Đội Xe Cảng Biển Quốc Tế',
                'preview': 'Case Study thực chiến: Giảm 42% TCO vận hành và tự động hóa 100% đối soát chứng từ cảng biển.',
                'list_indexes': [3, 5],
                'eyebrow': 'CASE STUDY THỰC CHIẾN · SẢN XUẤT & LOGISTICS QUỐC TẾ',
                'headline': 'Tối ưu Lệnh Sản xuất MRP & Điều phối Chuỗi Cung ứng Cảng Biển cùng Insilos & Mojo AI',
                'lead_copy': (
                    'Khám phá cách các tổ hợp sản xuất cơ khí và logistics cảng biển kết hợp Insilos Clean-Core ERP '
                    'cùng Mojo AI IDP OCR để rút ngắn 65% chu kỳ xử lý đơn hàng và khóa sổ giá thành cuối tháng.'
                ),
                'kpis': [
                    ('Tốc độ Xử lý Chứng từ', 'Tăng 3.5x'),
                    ('Độ chính xác IDP OCR', '>= 98.5%'),
                    ('Hoàn vốn Đầu tư (Payback)', '3.8 Tháng'),
                ],
                'bullets': [
                    'Bóc tách tự động vận đơn B/L, Packing List và Hóa đơn thương mại gắn trực tiếp vào lệnh nhập xuất kho.',
                    'Theo dõi định mức nguyên vật liệu (BOM) và cảnh báo lệch chuẩn chi phí sản xuất theo thời gian thực.',
                    'Đối soát công nợ tự động và kiểm soát hạn mức tín dụng tại cổng Deal Desk.',
                ],
                'cta_label': 'Xem Hồ sơ Định lượng ROI & Battlecard',
                'cta_url': '/solutions',
            },
            {
                'match_id': 3,
                'subject': '[Innoria Enterprise] Hồ Sơ Kiến Trúc Dịch Vụ Phần Mềm Dedicated Squad & Bảng Dự Toán TCO/ROI',
                'preview': 'Cung ứng Kỹ sư Senior Dedicated Squad (Man-Hour) & Giải pháp Phần mềm Chìa khóa trao tay.',
                'list_indexes': [1],
                'eyebrow': 'DEDICATED AGILE SQUAD · MAN-HOUR STAFF AUGMENTATION',
                'headline': 'Hồ sơ Kiến trúc Dịch vụ Phần mềm Chuyên trách & Minh bạch Đối soát Man-Hour',
                'lead_copy': (
                    'Innoria & Digimate JSC cung ứng đội ngũ Kỹ sư Phần mềm Hạng A/B đạt chuẩn chứng chỉ năng lực SOP-DGM-11 '
                    'cho các trung tâm R&D quốc tế (Nhật Bản, Úc, Mỹ, APAC) và tập đoàn tài chính - viễn thông.'
                ),
                'kpis': [
                    ('Tiết kiệm Chi phí R&D', '38% - 45%'),
                    ('SLA Chốt Timesheet', 'Trước Ngày 05'),
                    ('Thuế GTGT Xuất khẩu', '0% (NĐ 70/2025)'),
                ],
                'bullets': [
                    'Đồng bộ tự động bảng chấm công đa kênh vào al2c.timesheet.staging với quy tắc OT 2 bậc (100% và 150%).',
                    'Xuất hóa đơn điện tử 1C26TAA ngay sau biên bản nghiệm thu hoặc trong 24h nhận điện SWIFT ngoại tệ.',
                    'Cam kết bảo mật mã nguồn NDA và tuân thủ tiêu chuẩn an toàn thông tin ISO/IEC 27001.',
                ],
                'cta_label': 'Đặt lịch Phỏng vấn Kỹ sư & Nhận Dự toán Squad',
                'cta_url': '/platform',
            },
            {
                'match_id': 4,
                'subject': '[Bảo Chứng Kỹ Nghệ Innoria] Tối Ưu 50% TCO Phần Mềm & Tuân Thủ ISO 27001 / Nghị Định 13/2023',
                'preview': 'Khung bảo chứng kỹ nghệ Clean-Core, bảo vệ dữ liệu cá nhân Nghị định 13 và kiểm toán SHA-256.',
                'list_indexes': [3, 4],
                'eyebrow': 'CLEAN-CORE GOVERNANCE · ISO/IEC 27001 & 27701',
                'headline': 'Bảo chứng Kỹ nghệ Innoria: Tối ưu 50% TCO Phần mềm & Tuân thủ Pháp lý Toàn diện',
                'lead_copy': (
                    'Mọi giải pháp do Innoria & Digimate JSC triển khai đều được kiểm chứng qua Cổng Kiến trúc Clean-Core, '
                    'bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP và định lượng lợi ích kinh tế rõ ràng trước khi ký kết.'
                ),
                'kpis': [
                    ('Tối ưu TCO Phần mềm', '50% - 65%'),
                    ('Grounding Claim Atom', '100% SHA-256'),
                    ('SLA Báo giá Nhanh CPQ', '< 5 Phút'),
                ],
                'bullets': [
                    'Loại bỏ hoàn toàn chi phí ẩn từ các bản vá lỗi phá vỡ lõi hệ thống (Zero Technical Debt).',
                    'Che dấu tự động trường thông tin nhạy cảm (CCCD, SĐT, Tài khoản ngân hàng) kèm nhật ký kiểm toán bất biến.',
                    'Hỗ trợ quy trình On-boarding đối tác linh hoạt (TMP-DGM -> PTN-DGM) không làm chậm tiến độ bán hàng.',
                ],
                'cta_label': 'Khám phá Nền tảng Kỹ nghệ Innoria',
                'cta_url': '/about',
            },
            {
                'match_id': 5,
                'subject': '[Maintain Sale & QBR] Thông báo Lịch Đối soát Timesheet Trước Ngày 05, Xuất HĐĐT 1C26TAA & Ưu đãi Mở rộng Gói GRC/Mojo AI',
                'preview': 'Quy trình chăm sóc khách hàng hiện hữu: Chốt Timesheet trước ngày 05, xuất HĐĐT 1C26TAA và họp QBR Quý.',
                'list_indexes': [0, 1],
                'eyebrow': 'CUSTOMER SUCCESS & MAINTAIN SALE · SOP-DGM-08 / SOP-DGM-15',
                'headline': 'Lịch Đối soát Timesheet Hàng tháng, Thanh toán HĐĐT 1C26TAA & Chương trình Mở rộng Đa Trụ cột',
                'lead_copy': (
                    'Kính gửi Quý Đối tác & Khách hàng Hiện hữu của Innoria / Digimate JSC, nhằm đảm bảo tiến độ quyết toán '
                    'và vận hành liên tục 99.9%, Phòng Quản lý Tài khoản (Farmer Team) trân trọng cập nhật lịch đối soát định kỳ.'
                ),
                'kpis': [
                    ('Chốt Bảng công Timesheet', 'Ngày làm việc 01-05'),
                    ('Ký hiệu Hóa đơn NĐ 70', '1C26TAA'),
                    ('Ưu đãi Cross-Sell Quý', '15% Gói GRC / AI'),
                ],
                'bullets': [
                    'Bước 1 (Ngày 01 - 03): Đồng bộ bảng chấm công kỹ sư (MTI - TIMESHEET) lên cổng đối soát tự động, tách bạch giờ chuẩn và OT 2 bậc (<=20h: 100%, >20h: 150%).',
                    'Bước 2 (Trước ngày 05): Hai bên xác nhận Biên bản Nghiệm thu Khối lượng Công việc điện tử.',
                    'Bước 3 (Thanh toán & HĐĐT): Hệ thống tự động phát hành Hóa đơn Điện tử 1C26TAA (Nghị định 70/2025/NĐ-CP) và đối soát thanh toán qua VCB DigiBiz / SWIFT 24h.',
                ],
                'cta_label': 'Xác nhận Lịch Họp QBR & Nhận Báo giá Mở rộng',
                'cta_url': '/contactus',
            },
            {
                'match_id': 6,
                'subject': '[Giải pháp KTT 4.0] Tự động hóa 100% Đối soát HĐĐT 1C26TAA, Ủy nhiệm chi VCB DigiBiz 11 Cột & BHXH TZ0857G — Hoàn vốn sau 1.5 Tháng',
                'preview': 'Giải pháp chuyên biệt cho Kế toán Trưởng (KTT) & CFO: Thuế GTGT Luật 48/2024, Lương PIT 5 bậc 2026 & VCB DigiBiz.',
                'list_indexes': [2],
                'eyebrow': 'CHIEF ACCOUNTANT (KTT) AUTOMATION · SOP-DGM-05 / SOP-DGM-06',
                'headline': 'Tự động hóa Toàn trình Nghiệp vụ Kế toán Trưởng: Hóa đơn 1C26TAA, Lương BHXH TZ0857G & VCB DigiBiz 11 Cột',
                'lead_copy': (
                    'Được thiết kế chuyên sâu cho Kế toán Trưởng (KTT) và Giám đốc Tài chính (CFO) tại Việt Nam, '
                    'phân hệ KTT của Insilos loại bỏ hoàn toàn thao tác đối chiếu Excel thủ công và rủi ro phạt chậm nộp thuế/BHXH.'
                ),
                'kpis': [
                    ('Thời gian Khóa sổ Tháng', 'Giảm 85%'),
                    ('Chuẩn Ủy nhiệm chi VCB', '11 Cột (@ Text)'),
                    ('Thời gian Hoàn vốn', '1.5 - 2.4 Tháng'),
                ],
                'bullets': [
                    'Tự động phân loại thuế suất GTGT (KCT phần mềm theo Luật 48/2024/QH15, 0% xuất khẩu NĐ 70/2025, 8% dịch vụ CNTT NĐ 174/2025, 10% hạ tầng).',
                    'Tính lương tự động theo biểu thuế TNCN 5 bậc mới nhất 2026 và trích nộp BHXH bắt buộc (8% BHXH, 1.5% BHYT, 1% BHTN — Mã đơn vị TZ0857G).',
                    'Kết xuất 1 chạm bảng kê thanh toán lương & nhà cung cấp chuẩn VCB DigiBiz 11 cột bảo toàn số 0 đầu tài khoản.',
                ],
                'cta_label': 'Nhận Báo giá Gói KTT 4.0 trong 5 Phút',
                'cta_url': '/pricing',
            },
            {
                'match_id': 7,
                'subject': '[Vertical Resilience GRC] Khung Quản trị Rủi ro & Bảo vệ Dữ liệu Cá nhân Nghị định 13/2023 & ISO/IEC 27701 — Báo giá Nhanh trong 5 Phút',
                'preview': 'Giải pháp đóng gói Vertical Resilience GRC: Sổ đăng ký rủi ro, che dấu PII tự động 30s và bằng chứng kiểm toán.',
                'list_indexes': [4],
                'eyebrow': 'VERTICAL RESILIENCE GRC · ISO 27001/27701 & NGHỊ ĐỊNH 13/2023/NĐ-CP',
                'headline': 'Giải pháp Đóng gói Vertical Resilience GRC: Lá chắn Tuân thủ Pháp lý & Bảo vệ Dữ liệu Cá nhân',
                'lead_copy': (
                    'Trước yêu cầu kiểm tra nghiêm ngặt về Bảo vệ Dữ liệu Cá nhân (Nghị định 13/2023/NĐ-CP) và tiêu chuẩn '
                    'quốc tế ISO/IEC 27001 & 27701, Vertical Resilience GRC cung cấp bộ khung kiểm soát tự động hóa sẵn sàng vận hành ngay.'
                ),
                'kpis': [
                    ('Che dấu Dữ liệu Nhạy cảm', 'Mặc định 100%'),
                    ('Thời gian Chuẩn bị Audit', 'Giảm 70%'),
                    ('Nhật ký Kiểm toán', 'Bất biến SHA-256'),
                ],
                'bullets': [
                    'Mặc định che dấu một phần (Partial Masking) CCCD, SĐT, Tài khoản ngân hàng; tự động khóa lại sau 30 giây mở xem và ghi vết dgm.hr.privacy_audit_log.',
                    'Quy trình phê duyệt 2 bước (Maker -> Checker) đối với mọi yêu cầu cập nhật hồ sơ pháp lý hoặc quyền truy cập.',
                    'Cung cấp trọn bộ Sổ đăng ký Rủi ro (Risk Register) và Hồ sơ Đánh giá Tác động Xử lý Dữ liệu Cá nhân (DPIA).',
                ],
                'cta_label': 'Đánh giá Mức độ Tuân thủ & Nhận Báo giá GRC',
                'cta_url': '/solutions',
            },
            {
                'match_id': 8,
                'subject': '[Mojo AI & Sovereign RAG] Trợ lý AI Nội bộ Chuẩn Xác thực Entailment >= 0.85 & Tự động hóa Báo giá CPQ cho Doanh nghiệp',
                'preview': 'Triển khai Mojo AI Tools, Sovereign SOP-RAG Copilot chống ảo giác và tự động hóa quy trình chứng từ IDP.',
                'list_indexes': [5, 0],
                'eyebrow': 'MOJO AI TOOLS · SOVEREIGN SOP-RAG COPILOT (SOP-DGM-12 / SOP-DGM-15)',
                'headline': 'Đưa Trí tuệ Nhân tạo Có Kiểm chứng (Grounded SOP-RAG) vào Vận hành Doanh nghiệp',
                'lead_copy': (
                    'Khác biệt hoàn toàn với các chatbot tự do dễ sinh ảo giác, Mojo AI Sovereign SOP-RAG sử dụng thuật toán '
                    'Hybrid Retrieval (RRF k=60) kết hợp cổng kiểm chứng Entailment >= 0.85 bám sát 100% quy trình SOP nội bộ của doanh nghiệp.'
                ),
                'kpis': [
                    ('Ngưỡng Xác thực Entailment', '>= 0.85 (Zero Hallucination)'),
                    ('Tốc độ Tra cứu & Báo giá', 'Nhanh gấp 3.2x'),
                    ('Phân quyền Truy cập Tri thức', 'RBAC 4 Cấp độ'),
                ],
                'bullets': [
                    'Trích dẫn chính xác mã quy trình [SOP_CODE | Section | #chunk_id | hash8] trên từng câu trả lời tư vấn.',
                    'Tự động phân tích đặc thù kinh doanh khách hàng để gợi ý cấu hình Báo giá Nhanh CPQ và tính toán ROI 3 năm.',
                    'Kiểm soát ngân sách suy luận AI minh bạch qua sổ cái Mojo Usage Ledger và cổng tự hành 2 chiều.',
                ],
                'cta_label': 'Trải nghiệm Mojo AI Copilot & Nhận Báo giá',
                'cta_url': '/platform',
            },
        ]

        mailings_by_idx = {}
        for idx, bspec in enumerate(broadcast_specs, start=1):
            mailing_rec = Mailing.browse(bspec['match_id']).exists() if bspec.get('match_id') else Mailing.browse()
            if not mailing_rec:
                mailing_rec = Mailing.search([('subject', '=', bspec['subject'])], limit=1)
            if not mailing_rec:
                mailing_rec = Mailing.search([('subject', 'ilike', bspec['subject'][:28])], limit=1)

            target_lists = [mailing_lists[i].id for i in bspec['list_indexes'] if i < len(mailing_lists)]
            html_content = _render_carbon_email_html(
                eyebrow=bspec['eyebrow'],
                headline=bspec['headline'],
                lead_copy=bspec['lead_copy'],
                kpi_items=bspec['kpis'],
                bullet_points=bspec['bullets'],
                cta_label=bspec['cta_label'],
                cta_url=bspec['cta_url'],
            )
            mailing_vals = {
                'subject': bspec['subject'],
                'preview': bspec['preview'],
                'email_from': 'Innoria & Digimate B2B Advisory <info@inno.ai.vn>',
                'reply_to': 'info@inno.ai.vn',
                'mailing_type': 'mail',
                'mailing_model_id': mailing_list_model.id,
                'contact_list_ids': [(6, 0, target_lists)],
                'campaign_id': default_utm_campaign.id if default_utm_campaign else False,
                'use_in_marketing_automation': False,
                'body_arch': html_content,
                'body_html': html_content,
                'state': 'draft',
                'active': True,
            }
            if mailing_rec:
                mailing_rec.write(mailing_vals)
            else:
                mailing_rec = Mailing.create(mailing_vals)
            mailings_by_idx[idx] = mailing_rec

        # ------------------------------------------------------------------
        # 7. Ensure Complete 4-Touch `marketing.activity` Chains on ALL
        #    `marketing.campaign` Records (#1..#8, including AUT-CMP-01..06)
        # ------------------------------------------------------------------
        lead_model = IrModel.search([('model', '=', 'crm.lead')], limit=1)
        server_action = ServerAction.search([
            ('model_id', '=', lead_model.id),
            ('state', '=', 'code'),
        ], limit=1)
        if not server_action and lead_model:
            server_action = ServerAction.create({
                'name': 'AL2C Touch 4: Khởi tạo Báo giá Nhanh CPQ & Lịch Họp Solution Architect',
                'model_id': lead_model.id,
                'state': 'code',
                'code': "records.action_generate_rapid_quote_from_lead()",
            })

        campaign_touch_mailing_map = {
            'AUT-CMP-01': (mailings_by_idx[3], mailings_by_idx[5], mailings_by_idx[4], mailings_by_idx[5]),
            'AUT-CMP-02': (mailings_by_idx[6], mailings_by_idx[4], mailings_by_idx[2], mailings_by_idx[5]),
            'AUT-CMP-03': (mailings_by_idx[1], mailings_by_idx[6], mailings_by_idx[2], mailings_by_idx[5]),
            'AUT-CMP-04': (mailings_by_idx[7], mailings_by_idx[4], mailings_by_idx[1], mailings_by_idx[5]),
            'AUT-CMP-05': (mailings_by_idx[8], mailings_by_idx[2], mailings_by_idx[4], mailings_by_idx[5]),
            'AUT-CMP-06': (mailings_by_idx[3], mailings_by_idx[8], mailings_by_idx[4], mailings_by_idx[5]),
        }

        all_mkt_campaigns = MarketingCampaign.search([('active', '=', True)], order='id asc')
        for mcamp in all_mkt_campaigns:
            if lead_model and mcamp.model_id != lead_model:
                mcamp.write({'model_id': lead_model.id})
            if mcamp.state != 'running':
                mcamp.write({'state': 'running'})

            matched_code = None
            for code_key in campaign_touch_mailing_map:
                if code_key in (mcamp.name or ''):
                    matched_code = code_key
                    break

            if matched_code:
                m1, m2, m3, m4 = campaign_touch_mailing_map[matched_code]
            elif mcamp.id == 1:
                m1, m2, m3, m4 = mailings_by_idx[1], mailings_by_idx[2], mailings_by_idx[6], mailings_by_idx[5]
            else:
                m1, m2, m3, m4 = mailings_by_idx[3], mailings_by_idx[4], mailings_by_idx[8], mailings_by_idx[5]

            existing_acts = MarketingActivity.search([('campaign_id', '=', mcamp.id)], order='interval_standardized asc, id asc')
            touch_specs = [
                ('Touch 1 (Ngày 1): Nhận diện Nỗi đau Vận hành & Gửi Hồ sơ Kiến trúc Chuẩn', 'email', 0, 'hours', 'begin', m1),
                ('Touch 2 (Ngày 4): Khung Kiến trúc Clean-Core & Tuân thủ Pháp lý NĐ 70 / NĐ 13', 'email', 4, 'days', 'activity', m2),
                ('Touch 3 (Ngày 8): Case Study Thực chiến & Bảng So sánh Cạnh tranh Battlecard ROI', 'email', 8, 'days', 'activity', m3),
                ('Touch 4 (Ngày 14): Báo giá Nhanh CPQ (< 5 Phút), Họp Solution Architect & Lịch QBR', 'email', 14, 'days', 'activity', m4),
            ]

            prev_act = False
            for idx_t, (t_name, t_type, iv_num, iv_type, trig_type, mailing_target) in enumerate(touch_specs):
                act_rec = existing_acts[idx_t] if idx_t < len(existing_acts) else MarketingActivity.browse()
                act_vals = {
                    'name': t_name,
                    'campaign_id': mcamp.id,
                    'activity_type': t_type,
                    'mass_mailing_id': mailing_target.id if t_type == 'email' else False,
                    'server_action_id': server_action.id if t_type == 'action' and server_action else False,
                    'interval_number': iv_num,
                    'interval_type': iv_type,
                    'trigger_type': trig_type,
                    'parent_id': prev_act.id if (prev_act and trig_type != 'begin') else False,
                    'activity_domain': '[]',
                    'require_sync': False,
                }
                if act_rec:
                    act_rec.write(act_vals)
                else:
                    act_rec = MarketingActivity.create(act_vals)
                prev_act = act_rec

        # ------------------------------------------------------------------
        # 8. Run Autonomous Marketing & Market Research Attribution Loop
        # ------------------------------------------------------------------
        cron_summary = self.env['dgm.marketing.automation.campaign'].sudo().cron_dgm_autonomous_marketing_and_research()

        return {
            'status': 'configured',
            'teams_count': len(b2b_team_ids),
            'stages_count': len(stage_by_seq),
            'tags_count': len(tag_map),
            'lost_reasons_count': len(canonical_lost_reasons),
            'opportunities_calibrated': len(calibrated_leads),
            'mailing_lists_count': len(mailing_lists),
            'mailings_count': len(mailings_by_idx),
            'marketing_campaigns_count': len(all_mkt_campaigns),
            'autonomous_cron': cron_summary,
        }
