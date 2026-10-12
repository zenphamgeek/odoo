import logging
from odoo import api, models
from odoo.exceptions import MissingError

_logger = logging.getLogger(__name__)


class IrUiView(models.Model):
    _name = 'ir.ui.view'
    _inherit = ['ir.ui.view', 'pos.load.mixin']

    @api.model
    def _load_pos_data_domain(self, data, *args, **kwargs):
        return [('id', '=', False)]

    @api.model
    def _load_pos_data_fields(self, config):
        return ['key']

    @api.model
    def _load_pos_data_read(self, records, config):
        read_records = super()._load_pos_data_read(records, config)

        for key in self._get_xml_ids_to_load():
            view_id = False
            template = False
            try:
                _tree, template, ref = self.env['ir.qweb']._get_template(key)
                if isinstance(ref, int):
                    view_id = ref
                else:
                    view_id = self.env['ir.model.data']._xmlid_to_res_id(key, raise_if_not_found=False) or False
            except (ValueError, KeyError, MissingError) as err:
                view_id = self.env['ir.model.data']._xmlid_to_res_id(key, raise_if_not_found=False) or False
                template = False
                _logger.warning("POS: QWeb template missing or failed to compile for xmlid %r: %s", key, err)

            read_records.append({
                'id': view_id or False,
                'key': key,
                '_template': template,
            })

        return read_records

    @api.model
    def _get_xml_ids_to_load(self):
        return [
            'point_of_sale.pos_order_receipt_header',
            'point_of_sale.pos_order_receipt_style',
            'point_of_sale.company_info_receipt',
            'point_of_sale.pos_orderline_receipt_information',
            'point_of_sale.pos_orderline_receipt',
            'point_of_sale.pos_order_receipt_footer',
            'point_of_sale.pos_order_receipt',
            'point_of_sale.pos_order_change_receipt',
            'point_of_sale.pos_order_change_receipt_zpl',
            'point_of_sale.pos_order_change_receipt_line',
            'point_of_sale.pos_cash_move_receipt',
            'point_of_sale.pos_tip_receipt',
            'point_of_sale.pos_sale_details_receipt',
            'point_of_sale.pos_sale_details_receipt_product_line',
        ]
