# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools.sql import SQL


class AnalyticMixin(models.AbstractModel):
    _inherit = 'analytic.mixin'

    def _get_count_id(self, query):
        alias = getattr(query.table, '_alias', None) or (query.table if isinstance(query.table, str) else self._table)
        if alias in ('account_move_line', 'finance_journal_line'):
            return SQL("%s.%s", SQL.identifier(alias), SQL.identifier('move_id'))
        if alias in ('purchase_order_line', 'procurement_order_line'):
            return SQL("%s.%s", SQL.identifier(alias), SQL.identifier('order_id'))
        return super()._get_count_id(query)
