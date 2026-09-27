# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockReturnPicking(models.TransientModel):
    _name = 'stock.return.picking'
    _description = 'Return Picking'

    picking_id = fields.Many2one('stock.picking')
    product_return_moves = fields.One2many('stock.return.picking.line', 'wizard_id', 'Moves')
    move_dest_exists = fields.Boolean('Chained Move Exists')
    original_location_id = fields.Many2one('stock.location')
    parent_location_id = fields.Many2one('stock.location')
    location_id = fields.Many2one('stock.location', 'Return Location')
    company_id = fields.Many2one(related='picking_id.company_id')

    def _reset_carrier_id(self, picking):
        pass

    def _prepare_picking_default_values(self):
        return {}

    def _create_return(self):
        if self.picking_id:
            return self.picking_id._create_return()
        return self.env['stock.picking']

    def create_returns(self):
        return self._create_return()

    def action_create_returns(self):
        return self.create_returns()

    def action_create_exchanges(self):
        return self.create_returns()


class StockReturnPickingLine(models.TransientModel):
    _name = 'stock.return.picking.line'
    _description = 'Return Picking Line'

    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float("Quantity", digits='Product Unit of Measure')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    wizard_id = fields.Many2one('stock.return.picking', string="Wizard")
    move_id = fields.Many2one('stock.move', "Move")
    move_quantity = fields.Float("Move Quantity", compute='_compute_move_quantity', store=True, readonly=False)

    @api.depends('move_id.quantity')
    def _compute_move_quantity(self):
        for line in self:
            if line.move_id:
                line.move_quantity = line.move_id.quantity
            elif not line.move_quantity:
                line.move_quantity = 0.0
