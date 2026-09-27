# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrDepartureWizard(models.TransientModel):
    _name = 'hr.departure.wizard'
    _description = 'Departure Wizard'

    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.context.get('active_id'))
    employee_ids = fields.Many2many('hr.employee', string='Employees', compute='_compute_employee_ids', inverse='_inverse_employee_ids')
    departure_reason_id = fields.Many2one('hr.departure.reason', string='Departure Reason')
    departure_description = fields.Html(string='Additional Information')
    departure_date = fields.Date(string='Departure Date', default=fields.Date.today)
    archive_private_address = fields.Boolean(string='Archive Private Address', default=True)

    @api.depends('employee_id')
    def _compute_employee_ids(self):
        for rec in self:
            rec.employee_ids = rec.employee_id

    def _inverse_employee_ids(self):
        for rec in self:
            if rec.employee_ids:
                rec.employee_id = rec.employee_ids[0]

    def action_register_departure(self):
        employees = self.employee_ids or self.employee_id
        for employee in employees:
            departure = self.env['hr.employee.departure'].create({
                'employee_id': employee.id,
                'departure_reason_id': self.departure_reason_id.id or self.env['hr.departure.reason'].search([], limit=1).id,
                'departure_description': self.departure_description,
                'departure_date': self.departure_date,
            })
            departure.action_register()
        return {'type': 'ir.actions.act_window_close'}
