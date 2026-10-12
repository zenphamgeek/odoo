#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POS React — Enterprise Demo Seeder.
===================================
Populates realistic POS Terminal configurations, Payment Methods, Product Categories,
Retail Product Catalog with Barcodes/Taxes, VIP/Corporate Customers, Active POS Sessions,
and Multi-Payment / Refund POS Orders for the React-based POS workspace.

Usage:
    python3 tools/seed_pos_react_demo.py [-d dbname] [-c config_file]
    or
    insilos/insilos-bin shell -d insilos_migration_digiforce_v2 < tools/seed_pos_react_demo.py
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add O20 root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import insilos
from insilos import fields
from insilos.tools import config
from insilos.modules.registry import Registry


def seed_pos_react_demo(env):
    print("=" * 85)
    print("🛒 [POS REACT SEEDER] Seeding Enterprise Retail & Cafe Demo Dataset for POS React")
    print("=" * 85)

    start_time = time.time()
    company = env.company
    stats = {}

    # -------------------------------------------------------------------------
    # 1. Journals & Payment Methods
    # -------------------------------------------------------------------------
    print("\n💳 [1/6] Configuring POS Payment Methods & Journals...")
    Journal = env["account.journal"]
    PaymentMethod = env["pos.payment.method"]

    cash_journal = Journal.search([
        ("company_id", "=", company.id),
        ("type", "=", "cash"),
    ], limit=1)
    if not cash_journal:
        cash_journal = Journal.create({
            "name": "POS Cash",
            "type": "cash",
            "code": "PCASH",
            "company_id": company.id,
        })

    bank_journal = Journal.search([
        ("company_id", "=", company.id),
        ("type", "=", "bank"),
    ], limit=1)
    if not bank_journal:
        bank_journal = Journal.create({
            "name": "POS Bank",
            "type": "bank",
            "code": "PBANK",
            "company_id": company.id,
        })

    # Cash Payment Method
    pm_cash = PaymentMethod.search([
        ("name", "=", "Cash (VND/USD)"),
        ("company_id", "=", company.id),
    ], limit=1)
    if not pm_cash:
        pm_cash = PaymentMethod.create({
            "name": "Cash (VND/USD)",
            "type": "cash",
            "journal_id": cash_journal.id,
            "company_id": company.id,
        })
        print(f"  • Created Payment Method: {pm_cash.name} (Cash)")
    else:
        print(f"  • Existing Payment Method: {pm_cash.name}")

    # Credit/Debit Card
    pm_card = PaymentMethod.search([
        ("name", "=", "Credit / Debit Card (Visa/Mastercard)"),
        ("company_id", "=", company.id),
    ], limit=1)
    if not pm_card:
        pm_card = PaymentMethod.create({
            "name": "Credit / Debit Card (Visa/Mastercard)",
            "type": "bank",
            "journal_id": bank_journal.id,
            "company_id": company.id,
        })
        print(f"  • Created Payment Method: {pm_card.name} (Card)")
    else:
        print(f"  • Existing Payment Method: {pm_card.name}")

    # VNPay QR / Mobile Wallet
    pm_qr = PaymentMethod.search([
        ("name", "=", "VNPay QR / Digital Wallet"),
        ("company_id", "=", company.id),
    ], limit=1)
    if not pm_qr:
        pm_qr = PaymentMethod.create({
            "name": "VNPay QR / Digital Wallet",
            "type": "bank",
            "journal_id": bank_journal.id,
            "company_id": company.id,
        })
        print(f"  • Created Payment Method: {pm_qr.name} (Digital Wallet)")
    else:
        print(f"  • Existing Payment Method: {pm_qr.name}")

    # Customer Account / Pay Later
    pm_account = PaymentMethod.search([
        ("name", "=", "Corporate Account (Pay Later)"),
        ("company_id", "=", company.id),
    ], limit=1)
    if not pm_account:
        pm_account = PaymentMethod.create({
            "name": "Corporate Account (Pay Later)",
            "type": "pay_later",
            "company_id": company.id,
        })
        print(f"  • Created Payment Method: {pm_account.name} (Account)")
    else:
        print(f"  • Existing Payment Method: {pm_account.name}")

    all_payment_methods = pm_cash | pm_card | pm_qr | pm_account
    stats["Payment Methods"] = len(all_payment_methods)

    # -------------------------------------------------------------------------
    # 2. Cash Rounding Configuration
    # -------------------------------------------------------------------------
    print("\n🪙 [2/6] Configuring POS Cash Rounding...")
    Rounding = env["account.cash.rounding"]
    Account = env["account.account"]

    rounding_acc = Account.search([
        ("company_ids", "in", company.id),
        ("account_type", "=", "expense"),
    ], limit=1) or Account.search([], limit=1)

    rounding_rule = Rounding.search([("name", "=", "POS Half-Up 0.01")], limit=1)
    if not rounding_rule and rounding_acc:
        rounding_rule = Rounding.create({
            "name": "POS Half-Up 0.01",
            "rounding": 0.01,
            "rounding_method": "HALF-UP",
            "strategy": "add_invoice_line",
            "profit_account_id": rounding_acc.id,
            "loss_account_id": rounding_acc.id,
        })
        print(f"  • Created Cash Rounding Rule: {rounding_rule.name}")

    # -------------------------------------------------------------------------
    # 3. POS Product Categories Hierarchy
    # -------------------------------------------------------------------------
    print("\n📂 [3/6] Seeding POS Product Categories Hierarchy...")
    Category = env["pos.category"]

    categories_spec = [
        {"name": "☕ Specialty Coffee & Beverages", "code": "BEV", "children": [
            "Espresso & Single Origin Brews",
            "Artisan Teas & Refreshers",
            "Signature Cold Brews",
        ]},
        {"name": "🥐 Artisan Bakery & Deli", "code": "BAKE", "children": [
            "Fresh French Pastries",
            "Sourdough & Bagels",
            "Gourmet Paninis & Salads",
        ]},
        {"name": "📱 Smart Office & Tech Gear", "code": "TECH", "children": [
            "Fast Chargers & Hubs",
            "Ergonomic Peripherals",
            "Audio & Wireless Headsets",
        ]},
        {"name": "🌿 Eco Lifestyle & Merchandise", "code": "ECO", "children": [
            "Reusable Tumblers & Bottles",
            "Organic Canvas Bags",
        ]},
        {"name": "🛡️ Industrial Safety Essentials", "code": "HSE", "children": [
            "PPE & Safety Eyewear",
            "Chemical Resistant Gloves",
        ]},
    ]

    category_map = {}
    total_categs = 0
    for cat_spec in categories_spec:
        parent = Category.search([("name", "=", cat_spec["name"])], limit=1)
        if not parent:
            parent = Category.create({"name": cat_spec["name"]})
            print(f"  • Created Parent Category: {parent.name}")
        category_map[cat_spec["name"]] = parent
        total_categs += 1

        for child_name in cat_spec.get("children", []):
            child = Category.search([("name", "=", child_name), ("parent_id", "=", parent.id)], limit=1)
            if not child:
                child = Category.create({"name": child_name, "parent_id": parent.id})
                print(f"    └─ Child Category: {child.name}")
            category_map[child_name] = child
            total_categs += 1

    stats["POS Categories"] = total_categs

    # -------------------------------------------------------------------------
    # 4. Product Catalog with POS Enablement, Barcodes, and Taxes
    # -------------------------------------------------------------------------
    print("\n🏷️ [4/6] Seeding Retail & Specialty Products Catalog...")
    Product = env["product.product"]
    Tax = env["account.tax"]

    tax_10 = Tax.search([("type_tax_use", "=", "sale"), ("amount", "=", 10.0)], limit=1)
    tax_8 = Tax.search([("type_tax_use", "=", "sale"), ("amount", "=", 8.0)], limit=1)
    default_tax = tax_10 or tax_8 or Tax.search([("type_tax_use", "=", "sale")], limit=1)

    products_spec = [
        # Coffee & Beverages
        {
            "name": "Single Origin Arabica Espresso (Double Shot)",
            "default_code": "BEV-ESP-01",
            "barcode": "8930001000011",
            "list_price": 3.50,
            "standard_price": 1.20,
            "category": "Espresso & Single Origin Brews",
        },
        {
            "name": "Vietnamese Traditional Iced Coffee (Cà Phê Sữa Đá)",
            "default_code": "BEV-VN-02",
            "barcode": "8930001000028",
            "list_price": 4.00,
            "standard_price": 1.10,
            "category": "Espresso & Single Origin Brews",
        },
        {
            "name": "Organic Uji Matcha Oat Latte",
            "default_code": "BEV-MAT-03",
            "barcode": "8930001000035",
            "list_price": 5.50,
            "standard_price": 2.00,
            "category": "Artisan Teas & Refreshers",
        },
        {
            "name": "Nitro Cold Brew Infused (12oz)",
            "default_code": "BEV-NCB-04",
            "barcode": "8930001000042",
            "list_price": 4.80,
            "standard_price": 1.60,
            "category": "Signature Cold Brews",
        },
        # Bakery & Deli
        {
            "name": "French Butter Croissant (AOP Isigny)",
            "default_code": "BAK-CRS-01",
            "barcode": "8930001000059",
            "list_price": 3.80,
            "standard_price": 1.40,
            "category": "Fresh French Pastries",
        },
        {
            "name": "Artisan Sourdough Loaf (Whole Wheat)",
            "default_code": "BAK-SRD-02",
            "barcode": "8930001000066",
            "list_price": 6.50,
            "standard_price": 2.20,
            "category": "Sourdough & Bagels",
        },
        {
            "name": "Smoked Salmon & Dill Cream Cheese Bagel",
            "default_code": "DELI-BGL-03",
            "barcode": "8930001000073",
            "list_price": 8.50,
            "standard_price": 3.80,
            "category": "Sourdough & Bagels",
        },
        {
            "name": "Truffle Prosciutto & Mozzarella Panini",
            "default_code": "DELI-PAN-04",
            "barcode": "8930001000080",
            "list_price": 9.80,
            "standard_price": 4.20,
            "category": "Gourmet Paninis & Salads",
        },
        # Tech Gear
        {
            "name": "USB-C GaN 65W Fast Charger (Triple Port)",
            "default_code": "TECH-GAN-01",
            "barcode": "8930001000097",
            "list_price": 35.00,
            "standard_price": 16.00,
            "category": "Fast Chargers & Hubs",
        },
        {
            "name": "Ergonomic Silent Wireless Mouse (Dual BT/2.4G)",
            "default_code": "TECH-MSE-02",
            "barcode": "8930001000103",
            "list_price": 28.00,
            "standard_price": 12.00,
            "category": "Ergonomic Peripherals",
        },
        {
            "name": "Active Noise-Cancelling Wireless Earbuds Pro",
            "default_code": "TECH-ANC-03",
            "barcode": "8930001000110",
            "list_price": 79.00,
            "standard_price": 38.00,
            "category": "Audio & Wireless Headsets",
        },
        {
            "name": "Hot-Swappable Mechanical Keyboard (RGB)",
            "default_code": "TECH-KBD-04",
            "barcode": "8930001000127",
            "list_price": 110.00,
            "standard_price": 55.00,
            "category": "Ergonomic Peripherals",
        },
        # Eco Merchandise
        {
            "name": "Insilos Insulated Stainless Steel Tumbler 500ml",
            "default_code": "ECO-TMB-01",
            "barcode": "8930001000134",
            "list_price": 22.00,
            "standard_price": 9.00,
            "category": "Reusable Tumblers & Bottles",
        },
        {
            "name": "Organic Heavyweight Canvas Tote Bag",
            "default_code": "ECO-TOT-02",
            "barcode": "8930001000141",
            "list_price": 15.00,
            "standard_price": 5.50,
            "category": "Organic Canvas Bags",
        },
        # HSE Safety
        {
            "name": "Anti-Fog Clear Safety Goggles (ANSI Z87.1)",
            "default_code": "HSE-GOG-01",
            "barcode": "8930001000158",
            "list_price": 12.50,
            "standard_price": 4.80,
            "category": "PPE & Safety Eyewear",
        },
        {
            "name": "Nitrile Chemical Resistant Work Gloves (Heavy Duty)",
            "default_code": "HSE-GLV-02",
            "barcode": "8930001000165",
            "list_price": 8.00,
            "standard_price": 3.00,
            "category": "Chemical Resistant Gloves",
        },
    ]

    product_records = {}
    for p_val in products_spec:
        prod = Product.search([("default_code", "=", p_val["default_code"])], limit=1)
        categ = category_map.get(p_val["category"])
        taxes = [default_tax.id] if default_tax else []

        vals = {
            "name": p_val["name"],
            "default_code": p_val["default_code"],
            "barcode": p_val["barcode"],
            "list_price": p_val["list_price"],
            "standard_price": p_val["standard_price"],
            "available_in_pos": True,
            "pos_categ_ids": [(6, 0, [categ.id])] if categ else False,
            "taxes_id": [(6, 0, taxes)],
        }

        if not prod:
            prod = Product.create(vals)
            print(f"  • Created POS Product: {prod.name} (${prod.list_price:.2f})")
        else:
            prod.write(vals)
            print(f"  • Updated POS Product: {prod.name} (${prod.list_price:.2f})")

        product_records[p_val["default_code"]] = prod

    stats["Products"] = len(product_records)

    # -------------------------------------------------------------------------
    # 5. VIP Retail & Corporate Customers
    # -------------------------------------------------------------------------
    print("\n👥 [5/6] Seeding VIP Retail & Corporate POS Customers...")
    Partner = env["res.partner"]

    customers_spec = [
        {
            "name": "Nguyen Van An (VIP Gold)",
            "email": "an.nguyen@example.com",
            "phone": "+84 903 123 456",
            "street": "72 Le Thanh Ton, District 1",
            "city": "Ho Chi Minh City",
            "customer_rank": 1,
        },
        {
            "name": "Tran Thi Mai (Platinum Member)",
            "email": "mai.tran@example.com",
            "phone": "+84 918 888 999",
            "street": "18 Hoan Kiem, Tran Hung Dao",
            "city": "Hanoi",
            "customer_rank": 1,
        },
        {
            "name": "TechNova Innovation Labs JSC",
            "email": "procurement@technova.vn",
            "phone": "+84 28 3910 0000",
            "street": "Saigon Hi-Tech Park, District 9",
            "city": "Ho Chi Minh City",
            "is_company": True,
            "customer_rank": 2,
        },
        {
            "name": "GreenLeaf Industrial Operations",
            "email": "admin@greenleaf-ops.com",
            "phone": "+84 225 388 7766",
            "street": "Dinh Vu Industrial Zone",
            "city": "Hai Phong",
            "is_company": True,
            "customer_rank": 2,
        },
    ]

    customer_records = []
    for c_val in customers_spec:
        partner = Partner.search([("name", "=", c_val["name"])], limit=1)
        if not partner:
            partner = Partner.create(c_val)
            print(f"  • Created Customer: {partner.name}")
        else:
            print(f"  • Existing Customer: {partner.name}")
        customer_records.append(partner)

    stats["Customers"] = len(customer_records)

    # -------------------------------------------------------------------------
    # 6. POS Terminal Configuration, Active Session & Orders
    # -------------------------------------------------------------------------
    print("\n🖥️ [6/6] Configuring POS React Terminal, Active Session & Demo Orders...")
    PosConfig = env["pos.config"]
    PosSession = env["pos.session"]
    PosOrder = env["pos.order"]

    config_name = "Insilos Flagship Retail & Cafe (React POS)"
    pos_conf = PosConfig.search([("name", "=", config_name)], limit=1)
    config_vals = {
        "name": config_name,
        "payment_method_ids": [(6, 0, all_payment_methods.ids)],
        "company_id": company.id,
        "cash_rounding": True if rounding_rule else False,
        "rounding_method": rounding_rule.id if rounding_rule else False,
        "only_round_cash_method": True,
        "active": True,
    }

    if not pos_conf:
        pos_conf = PosConfig.create(config_vals)
        print(f"  • Created POS Config: {pos_conf.name} (ID: {pos_conf.id})")
    else:
        # If active session exists, don't modify payment_method_ids to avoid UserError
        if pos_conf.has_active_session:
            safe_vals = {k: v for k, v in config_vals.items() if k != "payment_method_ids"}
            pos_conf.write(safe_vals)
        else:
            pos_conf.write(config_vals)
        print(f"  • Updated POS Config: {pos_conf.name} (ID: {pos_conf.id})")

    # Ensure an active session exists
    session = PosSession.search([
        ("config_id", "=", pos_conf.id),
        ("state", "in", ["opening_control", "opened"]),
    ], limit=1)

    if not session:
        session = PosSession.create({
            "name": f"POS-SESSION-{datetime.now().strftime('%Y%m%d')}-001",
            "config_id": pos_conf.id,
            "user_id": env.uid,
            "state": "opened",
            "start_at": fields.Datetime.now(),
        })
        print(f"  • Opened Active POS Session: {session.name} (ID: {session.id})")
    else:
        print(f"  • Existing Active POS Session: {session.name} (ID: {session.id}, State: {session.state})")

    stats["Active POS Config ID"] = pos_conf.id
    stats["Active Session ID"] = session.id

    # Seed Realistic Orders (Paid, Draft, Refund)
    p_esp = product_records["BEV-ESP-01"]
    p_crs = product_records["BAK-CRS-01"]
    p_bgl = product_records["DELI-BGL-03"]
    p_gan = product_records["TECH-GAN-01"]
    p_tmb = product_records["ECO-TMB-01"]
    p_gog = product_records["HSE-GOG-01"]

    cust1 = customer_records[0]
    cust2 = customer_records[1]
    cust3 = customer_records[2]

    # Order 1: Morning Coffee & Pastry (Paid with Cash)
    ord1_uuid = "pos-react-order-demo-001"
    ord1 = PosOrder.search([("uuid", "=", ord1_uuid)], limit=1)
    if not ord1:
        qty_esp = 2
        qty_crs = 2
        total_ord1 = (p_esp.list_price * qty_esp) + (p_crs.list_price * qty_crs)
        ord1 = PosOrder.create({
            "name": "POS-REACT/2026/0001",
            "pos_reference": "Order 00001-001-0001",
            "session_id": session.id,
            "company_id": company.id,
            "partner_id": cust1.id,
            "uuid": ord1_uuid,
            "access_token": ord1_uuid,
            "state": "paid",
            "amount_total": total_ord1,
            "amount_paid": total_ord1,
            "amount_tax": total_ord1 * 0.1,
            "amount_return": 0.0,
            "date_order": datetime.now() - timedelta(hours=3),
            "lines": [
                (0, 0, {
                    "uuid": f"{ord1_uuid}-line-1",
                    "product_id": p_esp.id,
                    "qty": qty_esp,
                    "price_unit": p_esp.list_price,
                    "price_subtotal": p_esp.list_price * qty_esp,
                    "price_subtotal_incl": p_esp.list_price * qty_esp * 1.1,
                }),
                (0, 0, {
                    "uuid": f"{ord1_uuid}-line-2",
                    "product_id": p_crs.id,
                    "qty": qty_crs,
                    "price_unit": p_crs.list_price,
                    "price_subtotal": p_crs.list_price * qty_crs,
                    "price_subtotal_incl": p_crs.list_price * qty_crs * 1.1,
                }),
            ],
            "payment_ids": [
                (0, 0, {
                    "uuid": str(uuid4()),
                    "payment_method_id": pm_cash.id,
                    "amount": total_ord1,
                    "payment_date": datetime.now() - timedelta(hours=3),
                }),
            ],
        })
        print(f"  • Created Paid Order 1: {ord1.pos_reference} (${total_ord1:.2f} via Cash)")

    # Order 2: Tech Gear & Tumbler (Paid with Card + VNPay QR split)
    ord2_uuid = "pos-react-order-demo-002"
    ord2 = PosOrder.search([("uuid", "=", ord2_uuid)], limit=1)
    if not ord2:
        qty_gan = 1
        qty_tmb = 1
        total_ord2 = (p_gan.list_price * qty_gan) + (p_tmb.list_price * qty_tmb)
        split_card = 40.00
        split_qr = total_ord2 - split_card
        ord2 = PosOrder.create({
            "name": "POS-REACT/2026/0002",
            "pos_reference": "Order 00001-001-0002",
            "session_id": session.id,
            "company_id": company.id,
            "partner_id": cust2.id,
            "uuid": ord2_uuid,
            "access_token": ord2_uuid,
            "state": "paid",
            "amount_total": total_ord2,
            "amount_paid": total_ord2,
            "amount_tax": total_ord2 * 0.1,
            "amount_return": 0.0,
            "date_order": datetime.now() - timedelta(hours=1, minutes=30),
            "lines": [
                (0, 0, {
                    "uuid": f"{ord2_uuid}-line-1",
                    "product_id": p_gan.id,
                    "qty": qty_gan,
                    "price_unit": p_gan.list_price,
                    "price_subtotal": p_gan.list_price * qty_gan,
                    "price_subtotal_incl": p_gan.list_price * qty_gan * 1.1,
                }),
                (0, 0, {
                    "uuid": f"{ord2_uuid}-line-2",
                    "product_id": p_tmb.id,
                    "qty": qty_tmb,
                    "price_unit": p_tmb.list_price,
                    "price_subtotal": p_tmb.list_price * qty_tmb,
                    "price_subtotal_incl": p_tmb.list_price * qty_tmb * 1.1,
                }),
            ],
            "payment_ids": [
                (0, 0, {
                    "uuid": str(uuid4()),
                    "payment_method_id": pm_card.id,
                    "amount": split_card,
                    "payment_date": datetime.now() - timedelta(hours=1, minutes=30),
                }),
                (0, 0, {
                    "uuid": str(uuid4()),
                    "payment_method_id": pm_qr.id,
                    "amount": split_qr,
                    "payment_date": datetime.now() - timedelta(hours=1, minutes=30),
                }),
            ],
        })
        print(f"  • Created Paid Order 2: {ord2.pos_reference} (${total_ord2:.2f} via Card + VNPay QR)")

    # Order 3: B2B Deli & Safety Supplies (Corporate Account)
    ord3_uuid = "pos-react-order-demo-003"
    ord3 = PosOrder.search([("uuid", "=", ord3_uuid)], limit=1)
    if not ord3:
        qty_bgl = 5
        qty_gog = 4
        total_ord3 = (p_bgl.list_price * qty_bgl) + (p_gog.list_price * qty_gog)
        ord3 = PosOrder.create({
            "name": "POS-REACT/2026/0003",
            "pos_reference": "Order 00001-001-0003",
            "session_id": session.id,
            "company_id": company.id,
            "partner_id": cust3.id,
            "uuid": ord3_uuid,
            "access_token": ord3_uuid,
            "state": "paid",
            "amount_total": total_ord3,
            "amount_paid": total_ord3,
            "amount_tax": total_ord3 * 0.1,
            "amount_return": 0.0,
            "date_order": datetime.now() - timedelta(minutes=45),
            "lines": [
                (0, 0, {
                    "uuid": f"{ord3_uuid}-line-1",
                    "product_id": p_bgl.id,
                    "qty": qty_bgl,
                    "price_unit": p_bgl.list_price,
                    "price_subtotal": p_bgl.list_price * qty_bgl,
                    "price_subtotal_incl": p_bgl.list_price * qty_bgl * 1.1,
                }),
                (0, 0, {
                    "uuid": f"{ord3_uuid}-line-2",
                    "product_id": p_gog.id,
                    "qty": qty_gog,
                    "price_unit": p_gog.list_price,
                    "price_subtotal": p_gog.list_price * qty_gog,
                    "price_subtotal_incl": p_gog.list_price * qty_gog * 1.1,
                }),
            ],
            "payment_ids": [
                (0, 0, {
                    "uuid": str(uuid4()),
                    "payment_method_id": pm_account.id,
                    "amount": total_ord3,
                    "payment_date": datetime.now() - timedelta(minutes=45),
                }),
            ],
        })
        print(f"  • Created Paid Order 3: {ord3.pos_reference} (${total_ord3:.2f} via Corporate Account)")

    # Order 4: Draft Order (Active Cart Sync Demo)
    ord4_uuid = "pos-react-order-demo-004-draft"
    ord4 = PosOrder.search([("uuid", "=", ord4_uuid)], limit=1)
    if not ord4:
        qty_draft = 1
        total_draft = p_esp.list_price * qty_draft
        ord4 = PosOrder.create({
            "name": "POS-REACT/2026/0004",
            "pos_reference": "Order 00001-001-0004",
            "session_id": session.id,
            "company_id": company.id,
            "partner_id": cust1.id,
            "uuid": ord4_uuid,
            "access_token": ord4_uuid,
            "state": "draft",
            "amount_total": total_draft,
            "amount_paid": 0.0,
            "amount_tax": total_draft * 0.1,
            "amount_return": 0.0,
            "date_order": datetime.now(),
            "lines": [
                (0, 0, {
                    "uuid": f"{ord4_uuid}-line-1",
                    "product_id": p_esp.id,
                    "qty": qty_draft,
                    "price_unit": p_esp.list_price,
                    "price_subtotal": total_draft,
                    "price_subtotal_incl": total_draft * 1.1,
                }),
            ],
        })
        print(f"  • Created Draft Synced Cart Order 4: {ord4.pos_reference} (${total_draft:.2f})")

    # Order 5: Refund Demo Order (Returns 1 Croissant from Order 1)
    ord5_uuid = "pos-react-order-demo-005-refund"
    ord5 = PosOrder.search([("uuid", "=", ord5_uuid)], limit=1)
    if not ord5 and ord1:
        ord1_crs_line = ord1.lines.filtered(lambda l: l.product_id.id == p_crs.id)[:1]
        if ord1_crs_line:
            refund_qty = -1
            refund_amount = p_crs.list_price * refund_qty
            ord5 = PosOrder.create({
                "name": "POS-REACT/2026/0005",
                "pos_reference": "Order 00001-001-0005 (Refund)",
                "session_id": session.id,
                "company_id": company.id,
                "partner_id": cust1.id,
                "uuid": ord5_uuid,
                "access_token": ord5_uuid,
                "state": "paid",
                "is_refund": True,
                "amount_total": refund_amount,
                "amount_paid": refund_amount,
                "amount_tax": refund_amount * 0.1,
                "amount_return": 0.0,
                "date_order": datetime.now() - timedelta(minutes=15),
                "lines": [
                    (0, 0, {
                        "uuid": f"{ord5_uuid}-line-1",
                        "product_id": p_crs.id,
                        "qty": refund_qty,
                        "price_unit": p_crs.list_price,
                        "price_subtotal": refund_amount,
                        "price_subtotal_incl": refund_amount * 1.1,
                        "refunded_orderline_id": ord1_crs_line.id,
                    }),
                ],
                "payment_ids": [
                    (0, 0, {
                        "uuid": str(uuid4()),
                        "payment_method_id": pm_cash.id,
                        "amount": refund_amount,
                        "payment_date": datetime.now() - timedelta(minutes=15),
                    }),
                ],
            })
            print(f"  • Created Refund Order 5: {ord5.pos_reference} (${refund_amount:.2f} via Cash Refund)")

    elapsed = time.time() - start_time
    print("\n" + "=" * 85)
    print(f"🎉 [POS REACT SEED SUCCESS] Demo Data Successfully Seeded in {elapsed:.2f}s!")
    print("=" * 85)
    for k, v in stats.items():
        print(f"  ✓ {k}: {v}")
    print(f"  ✓ Direct URL: http://localhost:28069/pos/react/{pos_conf.id}")
    print("=" * 85)
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed POS React enterprise demo dataset")
    parser.add_argument("-c", "--config", dest="config_file", default=str(ROOT / "insilos.conf"), help="Config file path")
    parser.add_argument("-d", "--database", dest="dbname", default="odoo20_dev", help="Database name")
    args, _ = parser.parse_known_args()

    config.parse_config(["-c", args.config_file, "-d", args.dbname, "--no-http"])
    registry = Registry(args.dbname)
    with registry.cursor() as cr:
        env = insilos.api.Environment(cr, insilos.SUPERUSER_ID, {})
        seed_pos_react_demo(env)
        cr.commit()


if __name__ == "__main__":
    if globals().get("env") is not None:
        seed_pos_react_demo(globals()["env"])
    else:
        main()
