# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_delivery_bpost = fields.Boolean(string="bpost Connector")
    module_delivery_dhl = fields.Boolean(string="DHL Connector")
    module_delivery_dhl_rest = fields.Boolean(string="DHL REST Connector")
    module_delivery_easypost = fields.Boolean(string="Easypost Connector")
    module_delivery_envia = fields.Boolean(string="Envia Connector")
    module_delivery_fedex = fields.Boolean(string="Fedex Connector")
    module_delivery_fedex_rest = fields.Boolean(string="Fedex REST Connector")
    module_delivery_sendcloud = fields.Boolean(string="Sendcloud Connector")
    module_delivery_shiprocket = fields.Boolean(string="Shiprocket Connector")
    module_delivery_starshipit = fields.Boolean(string="Starshipit Connector")
    module_delivery_ups = fields.Boolean(string="UPS Connector")
    module_delivery_ups_rest = fields.Boolean(string="UPS REST Connector")
    module_delivery_usps = fields.Boolean(string="USPS Connector")
    module_delivery_usps_rest = fields.Boolean(string="USPS REST Connector")

    def action_install_more_provider(self):
        return self.env["delivery.carrier"].install_more_provider()
