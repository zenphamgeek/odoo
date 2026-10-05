# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.modules.db import FunctionStatus
from odoo.tools import SQL


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def init(self):
        from odoo.tools import sql
        if sql.table_kind(self.env.cr, self._table) in (sql.TableKind.View, sql.TableKind.Materialized):
            target_table = 'system_attachment' if sql.table_kind(self.env.cr, 'system_attachment') == sql.TableKind.Regular else None
            if not target_table:
                return
        else:
            target_table = self._table

        if self.env.registry.has_trigram:
            indexed_field = SQL('UNACCENT(index_content)') if self.env.registry.has_unaccent == FunctionStatus.INDEXABLE else SQL('index_content')

            self.env.cr.execute(SQL('''
                CREATE INDEX IF NOT EXISTS ir_attachment_index_content_applicant_trgm_idx
                    ON %(target_table)s USING gin (%(indexed_field)s gin_trgm_ops)
                 WHERE res_model = 'hr.applicant'
            ''', target_table=SQL.identifier(target_table), indexed_field=indexed_field))
