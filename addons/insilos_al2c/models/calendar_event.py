# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    al2c_briefing_generated = fields.Boolean(
        string='Discovery Briefing Generated',
        default=False,
        tracking=True,
    )
    al2c_briefing_note = fields.Html(
        string='Executive Discovery Briefing',
        readonly=True,
    )

    def _message_log(self, *args, **kwargs):
        # appointment_crm passes tracking_value_ids to _message_log which triggers ValueError in mail_thread
        kwargs.pop('tracking_value_ids', None)
        return super()._message_log(*args, **kwargs)


    def action_generate_discovery_briefing(self):
        """
        AL2C-CRM-006: Automated Discovery Meeting Briefing Generator.
        Compiles past won deals, identified customer pain points, BANT/MEDDICC profile,
        and recommended discovery questions into an executive briefing pack posted to chatter.
        """
        for event in self:
            lead = event.opportunity_id
            customer = event.partner_ids.filtered(lambda p: p != self.env.user.partner_id)[:1]
            if not customer and lead and lead.partner_id:
                customer = lead.partner_id

            # 1. Gather Customer Context & Pain Points
            pain_point = lead.al2c_bant_need or lead.al2c_meddicc_identify_pain or _("Digital transformation and operational modernization.") if lead else _("General inquiry.")
            buyer = lead.al2c_bant_authority_name or lead.al2c_meddicc_economic_buyer or customer.name if lead and customer else _("Executive Stakeholder")
            metrics = lead.al2c_meddicc_metrics or _("Targeting 30%+ efficiency improvement.") if lead else _("Standard ROI.")

            # 2. Gather Similar Past Won Reference Deals
            won_leads = self.env['crm.lead'].search([
                ('stage_id.is_won', '=', True),
                ('id', '!=', lead.id if lead else False),
            ], limit=3, order='write_date desc')

            won_refs = []
            for wl in won_leads:
                won_refs.append(f"• <b>{wl.partner_id.name or wl.name}:</b> {wl.expected_revenue:,.0f} VND ({wl.name})")
            won_refs_html = "<br/>".join(won_refs) if won_refs else _("• Multiple enterprise references available in Insilos Knowledge base.")

            # 3. Compile Executive Briefing Pack
            briefing_html = _(
                "<div class='al2c-discovery-briefing' style='border-left: 4px solid #0052cc; padding-left: 12px;'>"
                "<h4>📋 <b>Executive Discovery Briefing Pack: %s</b></h4>"
                "<p><b>Scheduled Meeting:</b> %s | <b>Customer:</b> %s</p>"
                "<hr/>"
                "<h5>🎯 <b>Key Account Profile & Pain Points</b></h5>"
                "<ul>"
                "<li><b>Economic Decision Maker:</b> %s</li>"
                "<li><b>Identified Core Need / Pain:</b> %s</li>"
                "<li><b>Target Quantified Metrics:</b> %s</li>"
                "</ul>"
                "<h5>🏆 <b>Relevant Insilos Benchmark Reference Cases</b></h5>"
                "%s"
                "<h5 style='margin-top: 10px;'>💡 <b>Recommended Discovery Discussion Agenda</b></h5>"
                "<ol>"
                "<li>Validate current operational bottlenecks against Decree 70/2025 and ERP standards.</li>"
                "<li>Demonstrate targeted Insilos module live capability addressing key pain point.</li>"
                "<li>Establish joint success outcomes and agree on 2-week PoC or Activate scoping milestone.</li>"
                "</ol>"
                "</div>"
            ) % (
                event.name,
                event.start or fields.Datetime.now(),
                customer.name if customer else _("Prospect Account"),
                buyer,
                pain_point,
                metrics,
                won_refs_html,
            )

            event.write({
                'al2c_briefing_generated': True,
                'al2c_briefing_note': briefing_html,
            })

            event.message_post(body=briefing_html)
            if lead:
                lead.message_post(body=briefing_html)

        return True
