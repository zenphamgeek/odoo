# Part of Odoo. See LICENSE file for full copyright and licensing details.
import inspect
import logging
from collections import defaultdict

from odoo import api, models
from math import floor

_logger = logging.getLogger(__name__)


class PosLoadMixin(models.AbstractModel):
    _name = 'pos.load.mixin'
    _description = "PoS data loading mixin"

    @api.model
    def _load_pos_data_domain(self, data, *args, **kwargs):
        """ Return the domain used to filter records """
        return []

    @api.model
    def _load_pos_data_fields(self, config):
        """ Return the list of fields to be loaded """
        return []

    @api.model
    def _load_pos_data_read(self, records, config):
        """ Read specific fields from the given records """
        if not config:
            raise ValueError("config must be provided to read PoS data.")

        fields = self._load_pos_data_fields(config)
        if fields and 'write_date' not in fields:
            fields.append('write_date')
        records = records._filtered_access("read").read(fields, load=False)
        return records or []

    @api.model
    def _load_pos_data_dependencies(self):
        return []

    @api.model
    def _load_data_relations(self, fields):
        model_fields = self._fields
        relations = {}

        for name, params in model_fields.items():
            if (len(fields) and name not in fields) or (not len(fields) and params.manual):
                continue

            if params.relational:
                relations[name] = {
                    'name': name,
                    'model': params.model_name,
                    'compute': bool(params.compute),
                    'related': bool(params.related),
                    'relation': params.comodel_name,
                    'type': params.type,
                }
                if params.type == 'many2one' and params.ondelete:
                    relations[name]['ondelete'] = params.ondelete
                if params.type == 'one2many' and params.inverse_name:
                    relations[name]['inverse_name'] = params.inverse_name
                if params.type == 'many2many':
                    relations[name]['relation_table'] = params.relation
            else:
                relations[name] = {
                    'name': name,
                    'type': params.type,
                    'compute': bool(params.compute),
                    'related': bool(params.related),
                }

        return relations

    @api.model
    def load_pos_data_force_loading(self):
        """ Override this method to force loading of all records of this model
        each time the POS starts (ignoring the local cache).
        """
        return False

    @api.model
    def _load_pos_data_domain_and_dependencies(self, data):
        adapted_data = {model: d['records'] for model, d in data.items()}
        config = data["pos.config"]["records"] if data.get("pos.config") else None
        fields = self._load_pos_data_fields(config)
        # Signature inspection prevents swallowing genuine TypeErrors inside custom domains (CWE-703)
        # and guarantees single-execution semantics.
        try:
            unwrapped = inspect.unwrap(self._load_pos_data_domain)
            sig = inspect.signature(unwrapped)
            accepts_config = len(sig.parameters) > 1 or any(
                p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
                for p in sig.parameters.values()
            )
        except (ValueError, TypeError):
            accepts_config = False
            _logger.warning(
                "POS: could not introspect %s._load_pos_data_domain; defaulting to single-arg dispatch",
                self._name,
            )

        domain = (
            self._load_pos_data_domain(adapted_data, config)
            if accepts_config
            else self._load_pos_data_domain(adapted_data)
        )
        return {
            'domain': domain,
            'dependencies': self._load_pos_data_dependencies(),
            'fields': fields,
            'relations': self._load_data_relations(fields),
        }

    @api.model
    def _load_pos_metadata(self, data, search_params={}):
        result = self._load_pos_data_domain_and_dependencies(data)
        model_data = {
            **result,
            'records': self.search(domain=search_params.get('domain', False) or result['domain'],
                                   limit=search_params.get('limit', False),
                                   offset=search_params.get('offset', 0))
        }
        data[self._name] = model_data
        reg = getattr(self.env, 'registry', None)
        if reg:
            if hasattr(reg, 'REVERSE_MODEL_ALIASES') and self._name in reg.REVERSE_MODEL_ALIASES:
                data[reg.REVERSE_MODEL_ALIASES[self._name]] = {**model_data}
            if hasattr(reg, 'SOVEREIGN_MODEL_ALIASES') and self._name in reg.SOVEREIGN_MODEL_ALIASES:
                data[reg.SOVEREIGN_MODEL_ALIASES[self._name]] = {**model_data}
        return data

    @api.model
    def _read_pos_data_from_metadata(self, server_data, local_data, config_id):
        model = self._name
        if model in local_data['models'] and model in local_data['records'] and len(local_data['records'][model]):
            ids = local_data['records'][model].keys()
            records = server_data['records'].filtered(lambda x: self.load_pos_data_force_loading() or not str(x.id) in ids or (x.write_date and floor(x.write_date.timestamp()) > local_data['records'][model][str(x.id)]))
        else:
            records = server_data['records']
        return {
            **server_data,
            'records': records._load_pos_data_read(records, config_id),
        }

    @api.model
    def _convert_pos_data_currency(self, records, config, price_field, currency_field):
        """ Convert ``price_field`` of each loaded record to the POS currency.

        ``records`` is the list of dicts returned by ``_load_pos_data_read`` and is
        updated in place. The source currency of each record is read from
        ``currency_field`` (an ``id``, as fields are read with ``load=False``); records
        already expressed in the ``config`` currency are left untouched.

        ``currency_field`` matters because a product stores its sale price and its cost
        in two potentially different currencies (``currency_id`` and
        ``cost_currency_id``): each price must be converted from its own currency.
        """
        records_by_currency = defaultdict(list)
        for record in records:
            currency_id = record[currency_field]
            if currency_id and currency_id != config.currency_id.id:
                records_by_currency[currency_id].append(record)

        for currency_id, currency_records in records_by_currency.items():
            currency = self.env['res.currency'].browse(currency_id)
            for record in currency_records:
                record[price_field] = currency._convert(
                    record[price_field], config.currency_id, self.env.company
                )
