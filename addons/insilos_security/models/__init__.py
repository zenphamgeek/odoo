# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

try:
    from . import advisory_lock_guard
except Exception:
    advisory_lock_guard = None
