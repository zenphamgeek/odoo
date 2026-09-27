# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrWorkEntryRegenerationWizard(models.TransientModel):
    _name = 'hr.work.entry.regeneration.wizard'
    _description = 'Regenerate Work Entries'

    earliest_available_date = fields.Date('Earliest date', readonly=True)
    latest_available_date = fields.Date('Latest date', readonly=True)
    date_from = fields.Date('From', required=True, default=fields.Date.context_today)
    date_to = fields.Date('To', required=True, default=fields.Date.context_today)
    employee_id = fields.Many2one('hr.employee', 'Employee')

    def _work_entry_fields_to_nullify(self):
        return []

    @api.model
    def regenerate_work_entries(self, slots=None, record_ids=None):
        if record_ids:
            work_entries = self.env['hr.work.entry'].browse(record_ids).exists()
            nullify_fields = self._work_entry_fields_to_nullify()
            if nullify_fields:
                vals = {f: False for f in nullify_fields if f in work_entries._fields}
                if vals:
                    work_entries.write(vals)
        return True
