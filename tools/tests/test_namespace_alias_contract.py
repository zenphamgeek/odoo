#!/usr/bin/env python3
"""
Namespace-Aliasing Contract Canary
===================================
Asserts object identity and model contract parity across fork (`insilos.addons`)
and upstream (`odoo.addons`) namespaces. Catches silent fork drift before deployment.
"""
import sys


def test_pricelist_model_identity():
    """Assert fork ProductPricelistItem is identical to upstream ProductPricelistItem."""
    from insilos.addons.product.models import product_pricelist_item as fork
    try:
        from odoo.addons.product.models import product_pricelist_item as upstream
    except ModuleNotFoundError:
        print("[canary] Pure-fork environment: upstream odoo namespace absent; identity check skipped.")
        return

    assert fork.ProductPricelistItem is upstream.ProductPricelistItem, (
        "FATAL: fork namespace diverged from upstream without an explicit divergence manifest! "
        f"fork={fork.ProductPricelistItem!r}, upstream={upstream.ProductPricelistItem!r}"
    )
    print("  [✓] Model identity confirmed: insilos ProductPricelistItem is odoo ProductPricelistItem")


def test_fail_closed_resolver_contract():
    """Assert _resolve_pricelist_model fails closed if namespaces are unresolvable."""
    from tools.deploy_innokafe_production import _resolve_pricelist_model
    import unittest.mock as mock

    # Normal resolution returns the class
    cls = _resolve_pricelist_model()
    assert cls.__name__ == "ProductPricelistItem"

    # Simulated total namespace absence must raise SystemExit, never return None or fallback silently
    with mock.patch.dict(sys.modules, {"insilos.addons.product.models.product_pricelist_item": None, "odoo.addons.product.models.product_pricelist_item": None}):
        try:
            _resolve_pricelist_model()
            assert False, "_resolve_pricelist_model failed to fail closed on missing namespaces"
        except (SystemExit, ModuleNotFoundError, ImportError):
            pass
    print("  [✓] Fail-closed resolver contract verified under namespace absence.")


def main():
    print("=" * 80)
    print(" NAMESPACE ALIASING CONTRACT CANARY AUDIT")
    print("=" * 80)
    test_pricelist_model_identity()
    test_fail_closed_resolver_contract()
    print("=" * 80)
    print("ALL NAMESPACE CONTRACT CANARIES PASSED (EXIT 0)")
    print("=" * 80)


if __name__ == '__main__':
    main()
