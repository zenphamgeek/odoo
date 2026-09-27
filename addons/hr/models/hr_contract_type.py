# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrContractType(models.Model):
    _name = 'hr.contract.type'
    _description = 'Contract Type'
    _order = 'sequence, id'

    name = fields.Char(string='Contract Type', required=True, translate=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(default=10)
    country_id = fields.Many2one('res.country', string='Country')
