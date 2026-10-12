# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools.sql import SQL


class AnalyticMixin(models.AbstractModel):
    _inherit = 'analytic.mixin'

    def _get_count_id(self, query):
        alias = query.table._alias
        if alias in ('account_move_line', 'finance_journal_line'):
            return SQL('move_id')
        if alias in ('purchase_order_line', 'procurement_order_line'):
            return SQL('order_id')
        return super()._get_count_id(query)
