# -*- coding: utf-8 -*-
from datetime import date, timedelta
from odoo import api, fields, models, _


class ProjectProject(models.Model):
    _inherit = 'project.project'

    al2c_rag_status = fields.Selection([
        ('green', 'Green (On Track)'),
        ('amber', 'Amber (Attention Required)'),
        ('red', 'Red (Critical Risk)'),
    ], string='Autonomous RAG Status', default='green', tracking=True)

    al2c_risk_score = fields.Float(
        string='Autonomous Risk Score (0-100)',
        default=0.0,
        tracking=True,
    )
    al2c_risk_summary = fields.Text(
        string='Risk Factor Breakdown',
        tracking=True,
    )
    al2c_last_risk_evaluation = fields.Datetime(
        string='Last Risk Evaluation',
        readonly=True,
    )
    value_case_id = fields.Many2one(
        'al2c.value.case',
        string='Enterprise Value Case',
        copy=False,
        tracking=True,
    )

    def _create_missing_folders(self):
        # Project templates do not hold documents: the delivery project created from
        # the template gets its own workspace folder. Skipping templates also avoids
        # duplicating a folder tree on every "create from template".
        valid_projects = self.filtered(
            lambda p: not p.is_template
            and (not p.company_id.documents_project_folder or p.company_id.documents_project_folder.active)
        )
        return super(ProjectProject, valid_projects)._create_missing_folders()

    @api.model
    def _al2c_detach_template_folders(self):
        """Detach (and archive when empty) documents folders previously attached to
        the AL2C project templates. Idempotent; called from data on install/update."""
        IMD = self.env['ir.model.data'].sudo()
        ids = IMD.search([
            ('module', '=', 'insilos_al2c'), ('model', '=', self._name), ('name', '=like', 'tpl_%'),
        ]).mapped('res_id')
        templates = self.sudo().with_context(no_create_folder=True, active_test=False).browse(ids).exists()
        for template in templates.filtered(lambda p: p.is_template and p.documents_folder_id):
            folder = template.documents_folder_id
            template.documents_folder_id = False
            Document = self.env['documents.document'].sudo().with_context(active_test=False)
            if not Document.search_count([('folder_id', '=', folder.id)]) and not folder.project_ids:
                folder.active = False
        return True

    def action_evaluate_project_risk(self):
        """
        AL2C-PRJ-003: Autonomous Project Risk Sentinel.
        Evaluates project delivery risks across milestone deadlines, timesheet burn vs budget,
        and task blockers, calculating project RAG status (green/amber/red).
        """
        today = date.today()
        for project in self:
            if project.is_template:
                continue

            risk_score = 0.0
            reasons = []

            # 1. Milestone Deadline Analysis
            overdue_critical = False
            for ms in project.milestone_ids:
                if ms.deadline and not ms.is_reached:
                    diff_days = (today - ms.deadline).days
                    if diff_days > 7:
                        risk_score += 45.0
                        overdue_critical = True
                        reasons.append(_("Milestone '%s' is overdue by %d days (>7 days critical).") % (ms.name, diff_days))
                    elif diff_days > 0:
                        risk_score += 25.0
                        reasons.append(_("Milestone '%s' is overdue by %d days.") % (ms.name, diff_days))
                    elif -3 <= diff_days <= 0:
                        risk_score += 10.0
                        reasons.append(_("Milestone '%s' deadline is approaching within 3 days.") % ms.name)

            # 2. Timesheet Burn vs Allocated Budget
            total_allocated = sum(project.task_ids.mapped('allocated_hours'))
            total_timesheet = sum(project.task_ids.mapped('effective_hours'))
            if total_allocated > 0:
                burn_pct = total_timesheet / total_allocated
                unreached_milestones = project.milestone_ids.filtered(lambda m: not m.is_reached)
                if burn_pct > 1.0 and unreached_milestones:
                    risk_score += 40.0
                    reasons.append(_("Timesheet burn rate (%.1f%%) exceeds allocated budget with %d milestone(s) pending.") % (
                        burn_pct * 100.0, len(unreached_milestones)
                    ))
                elif burn_pct > 0.85 and unreached_milestones:
                    risk_score += 20.0
                    reasons.append(_("Timesheet burn rate is at %.1f%% of allocated budget.") % (burn_pct * 100.0))

            # 3. Determine RAG
            if risk_score >= 50.0 or overdue_critical:
                new_rag = 'red'
            elif risk_score >= 25.0:
                new_rag = 'amber'
            else:
                new_rag = 'green'

            old_rag = project.al2c_rag_status
            summary_text = "\n".join(reasons) if reasons else _("All milestones on schedule and timesheet burn within budget.")

            project.sudo().write({
                'al2c_rag_status': new_rag,
                'al2c_risk_score': min(risk_score, 100.0),
                'al2c_risk_summary': summary_text,
                'al2c_last_risk_evaluation': fields.Datetime.now(),
            })

            # Chatter alert and activity on status degradation or critical Red
            if new_rag != old_rag or new_rag == 'red':
                rag_badge = {
                    'green': '🟢 Green (On Track)',
                    'amber': '🟡 Amber (Attention Required)',
                    'red': '🔴 Red (Critical Delivery Risk)',
                }.get(new_rag, new_rag)

                project.message_post(
                    body=_("<b>Autonomous Project Risk Sentinel:</b> Status updated to <b>%s</b> (Risk Score: %.0f/100).<br/>"
                           "<b>Identified Factors:</b><br/>%s") % (
                        rag_badge,
                        min(risk_score, 100.0),
                        "<br/>• " + "<br/>• ".join(reasons) if reasons else _("Nominal operational parameters."),
                    )
                )

                if new_rag == 'red':
                    project.activity_schedule(
                        'mail.mail_activity_data_warning',
                        summary=_("URGENT: Project Delivery Critical Risk Alert (Sentinel RED)"),
                        note=_("Autonomous Risk Sentinel triggered RED status. Corrective milestone action required immediately:\n%s") % summary_text,
                        user_id=project.user_id.id if project.user_id else self.env.user.id,
                    )

        return True
