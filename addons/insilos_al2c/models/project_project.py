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
        if self.env.context.get('no_create_folder'):
            return
        env_folder = getattr(self.env.company, 'documents_project_folder_id', False)
        if env_folder and not env_folder.active:
            return
        valid_projects = self.filtered(
            lambda p: not getattr(p, 'is_template', False)
            and (
                not getattr(p.company_id, 'documents_project_folder_id', False)
                or getattr(p.company_id, 'documents_project_folder_id').active
            )
            and (
                not getattr(p.company_id, 'documents_project_folder', False)
                or getattr(p.company_id, 'documents_project_folder').active
            )
        )
        if not valid_projects:
            return
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

    @api.model
    def link_inno_customer_folders_to_projects(self):
        """Scans the customer folders under 'INNORIA / INNO - HỢP ĐỒNG, DỰ ÁN, KH' in
        documents.document (ADOBE, AIFIN, KTT, MBF, MOJO, SWAROVSKI, etc.), ensures every
        customer folder has dgm_rbac_profile = 'project_delivery', and links matching active
        project.project records (documents_folder_id) to their canonical customer folder
        without creating duplicate empty folders.
        """
        Doc = self.env['documents.document'].sudo()
        cr = self.env.cr

        parent_folder = Doc.search([
            ('type', '=', 'folder'),
            ('active', '=', True),
            ('name', 'ilike', 'HỢP ĐỒNG, DỰ ÁN, KH'),
        ], limit=1)

        if not parent_folder:
            return {
                'status': 'skipped',
                'reason': 'inno_customer_parent_folder_not_found',
                'customer_folders_verified': 0,
                'projects_linked': 0,
            }

        customer_folders = Doc.search([
            ('type', '=', 'folder'),
            ('active', '=', True),
            ('folder_id', '=', parent_folder.id),
        ])

        needs_rbac_reconcile = any(
            f.dgm_rbac_profile != 'project_delivery'
            or not f.dgm_rbac_generation_id
            or f.owner_id
            or f.access_internal != 'edit'
            for f in customer_folders
        )
        if customer_folders:
            cr.execute("""
                UPDATE documents_document
                SET dgm_rbac_profile = 'project_delivery',
                    dgm_confidentiality_level = 'confidential',
                    access_internal = 'edit',
                    owner_id = NULL
                WHERE id = ANY(%s)
                  AND (dgm_rbac_profile IS DISTINCT FROM 'project_delivery'
                       OR owner_id IS NOT NULL
                       OR access_internal IS DISTINCT FROM 'edit')
            """, (customer_folders.ids,))
            if needs_rbac_reconcile:
                Doc.apply_dgm_inno_rbac_matrix()

        folder_by_key = {}
        for cf in customer_folders:
            cname = (cf.name or '').strip().upper()
            if cname:
                folder_by_key[cname] = cf

        mti_folder = Doc.search([
            ('type', '=', 'folder'),
            ('active', '=', True),
            '|',
            ('name', 'ilike', 'PTN-DGM-2026-0001'),
            ('name', 'ilike', 'MTI - TIMESHEET'),
        ], order='id asc', limit=1)

        active_projects = self.sudo().with_context(no_create_folder=True).search([
            ('active', '=', True),
            ('is_template', '=', False),
        ])

        linked_project_ids = []
        for proj in active_projects:
            proj_upper = f"{proj.name or ''} {proj.partner_id.name if proj.partner_id else ''}".upper()
            target_folder = False

            for key, cf in folder_by_key.items():
                if len(key) >= 2 and key not in ('SS', 'LP', 'CƠ HỘI', 'BẢNG GIÁ THEO YÊU CẦU') and key in proj_upper:
                    target_folder = cf
                    break

            if not target_folder and 'MTI' in proj_upper and mti_folder:
                target_folder = mti_folder

            if not target_folder and (not proj.documents_folder_id or not proj.documents_folder_id.active):
                target_folder = folder_by_key.get('MOJO') or parent_folder

            if target_folder and (not proj.documents_folder_id or not proj.documents_folder_id.active or proj.documents_folder_id.id != target_folder.id):
                # Keep existing valid active non-empty partner onboarding folder if already bound (e.g. PTN-DGM-2026-0007),
                # unless it's inactive or unlinked or we're linking to INNO customer folder
                old_folder = proj.documents_folder_id
                if not old_folder or not old_folder.active or 'PTN-DGM-2026-' not in (old_folder.name or ''):
                    proj.with_context(no_create_folder=True).write({'documents_folder_id': target_folder.id})
                    if old_folder and old_folder.exists() and old_folder.active and old_folder.id != target_folder.id:
                        has_children = Doc.search_count([('active', '=', True), ('folder_id', '=', old_folder.id)])
                        has_projects = self.sudo().search_count([('active', '=', True), ('documents_folder_id', '=', old_folder.id)])
                        if not has_children and not has_projects:
                            old_folder.write({'active': False})
                linked_project_ids.append(proj.id)
            elif proj.documents_folder_id and proj.documents_folder_id.active:
                linked_project_ids.append(proj.id)

        # Enforce Zero Empty Folders Invariant (AGENTS.md §6)
        cr.execute("""
            UPDATE documents_document f
            SET active = FALSE
            WHERE f.active = TRUE AND f.type = 'folder'
              AND NOT EXISTS (
                  SELECT 1 FROM documents_document c
                  WHERE c.active = TRUE AND c.folder_id = f.id
              )
        """)
        self.env.invalidate_all()

        return {
            'status': 'success',
            'parent_folder_id': parent_folder.id,
            'customer_folders_verified': len(customer_folders),
            'projects_linked': len(linked_project_ids),
            'linked_project_ids': linked_project_ids,
        }

