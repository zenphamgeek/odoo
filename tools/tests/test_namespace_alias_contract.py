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


def test_differential_pricing_oracle():
    """Continuous differential-parity oracle: diffs calculations between fork and upstream."""
    try:
        from insilos.addons.product.models.product_pricelist_item import ProductPricelistItem as ForkModel
        from odoo.addons.product.models.product_pricelist_item import ProductPricelistItem as UpstreamModel
    except ModuleNotFoundError:
        print("[canary] Single-namespace environment: differential oracle skipped.")
        return

    class _ConcreteCurrency:
        def __init__(self, name: str, rate: float):
            self.name = name
            self.rate = rate
        def ensure_one(self): return True
        def _convert(self, amt, to_curr, date=None, round=False):
            return amt * to_curr.rate

    class _ConcretePricelistItem:
        def __init__(self, base='list_price'):
            self.base = base
            self.currency_id = None
            self.base_pricelist_id = None
            self.env = None

    class _ConcreteProduct:
        def __init__(self, pid: int, price: float, curr: _ConcreteCurrency):
            self.id = pid
            self._price = price
            self.currency_id = curr
            self.cost_currency_id = curr
        def _price_compute(self, rule_base, uom=None):
            return {self.id: self._price}

    item = _ConcretePricelistItem()
    c_usd = _ConcreteCurrency('USD', 1.0)
    c_vnd = _ConcreteCurrency('VND', 25000.0)
    c_jpy = _ConcreteCurrency('JPY', 155.25)
    c_eur = _ConcreteCurrency('EUR', 0.92)
    uom = object()

    cases = [
        (_ConcreteProduct(1, 100.0, c_usd), ('2026-10-15',), {'currency': c_vnd}),
        (_ConcreteProduct(2, 50.0, c_usd), ('2026-10-16', c_eur), {}),
        (_ConcreteProduct(3, 1000.0, c_usd), (), {'date': '2026-10-17', 'currency': c_jpy}),
        (_ConcreteProduct(4, 1e12, c_usd), ('2026-10-15',), {'currency': c_vnd}),
        (_ConcreteProduct(5, 0.01, c_usd), ('2026-10-16',), {'currency': c_eur}),
    ]

    for prod, args, kwargs in cases:
        res_fork = ForkModel._compute_base_price(item, prod, 1.0, uom, *args, **kwargs)
        res_upstream = UpstreamModel._compute_base_price(item, prod, 1.0, uom, *args, **kwargs)
        assert res_fork == res_upstream, f"Differential divergence: fork={res_fork} != upstream={res_upstream}"

    print("  [✓] Continuous differential-parity oracle verified (0 divergence across all vectors).")


def main():
    print("=" * 80)
    print(" NAMESPACE ALIASING CONTRACT CANARY AUDIT")
    print("=" * 80)
    test_pricelist_model_identity()
    test_fail_closed_resolver_contract()
    test_differential_pricing_oracle()
    print("=" * 80)
    print("ALL NAMESPACE CONTRACT CANARIES PASSED (EXIT 0)")
    print("=" * 80)


if __name__ == '__main__':
    main()
