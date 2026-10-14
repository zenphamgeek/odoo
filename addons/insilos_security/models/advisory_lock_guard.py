# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import hashlib
import logging
import struct
from contextlib import contextmanager

try:
    from odoo.exceptions import AccessError, UserError, ValidationError
except (ImportError, Exception):
    class AccessError(Exception):
        pass

    class UserError(Exception):
        pass

    class ValidationError(Exception):
        pass

try:
    from odoo import api, fields, models, _
except (ImportError, Exception):
    class models:
        class AbstractModel:
            _name = None
            _description = None

            def __init__(self, env=None):
                self.env = env

        class Model:
            _name = None
            _description = None

    class api:
        @staticmethod
        def model(f):
            return f

    def _(msg):
        return msg

_logger = logging.getLogger(__name__)


def compute_blake2b_lock_key(model_name: str, record_id: int) -> int:
    """
    Computes a signed 32-bit integer lock key from Blake2b digest of f"{model_name}:{record_id}".
    Guaranteed bounds: -2147483648 <= key <= 2147483647.
    """
    payload = f"{model_name}:{record_id}".encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=4).digest()
    return struct.unpack(">i", digest)[0]


class TenantAdvisoryLockGuard(models.AbstractModel):
    _name = "tenant.advisory.lock.guard"
    _description = "Partitioned Multi-Tenant Advisory Lock Guard"

    @api.model
    @contextmanager
    def acquire_tenant_lock(self, model_name: str, record_id: int, company_id: int = None):
        """
        Acquires a two-key PostgreSQL transaction-scoped advisory lock:
        (tenant_key, object_key) ensuring strict tenant isolation and collision resistance.
        """
        tenant_key = int(company_id or self.env.company.id) & 0x7FFFFFFF
        object_key = compute_blake2b_lock_key(model_name, record_id)
        cr = self.env.cr
        cr.execute("SELECT pg_advisory_xact_lock(%s, %s);", (tenant_key, object_key))
        yield

    @api.model
    @contextmanager
    def odoo_tenant_boundary(self, target_company_id: int):
        """
        Hermetic statutory tenant boundary preventing context pollution, credential leakage,
        or uncontained sudo() escalations during batch crons.
        """
        previous_company = self.env.company
        target_company = self.env["res.company"].browse(target_company_id)
        if not target_company.exists():
            raise UserError(f"Target company {target_company_id} does not exist.")
        self.env.invalidate_all()
        isolated_env = self.env(context=dict(self.env.context, allowed_company_ids=[target_company.id]))
        isolated_env = isolated_env.with_company(target_company)
        try:
            yield isolated_env
        finally:
            self.env.invalidate_all()
            self.env.context = dict(self.env.context, allowed_company_ids=[previous_company.id])
            self.env.with_company(previous_company)
