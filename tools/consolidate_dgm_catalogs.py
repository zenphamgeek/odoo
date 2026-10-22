#!/usr/bin/env python3
"""Consolidate all ERP catalogs and purge legacy demo data on insilos20_dev.

Target Entity: CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ (DIGIMATE JSC — MST: 0317958465)
Database: insilos20_dev (127.0.0.1:5434)
"""
import sys

import odoo
from odoo import api, SUPERUSER_ID

CANONICAL_SKUS = {
    'ERP-STARTER', 'ERP-GROWTH', 'ERP-ENT',
    'SAAS-USER-M', 'SAAS-HOSTING-PRO', 'SAAS-SLA-PLUS',
    'GRC-ESSENTIALS', 'GRC-RISK-REGISTER', 'GRC-AUDIT-PACK',
    'AI-DISCOVERY', 'AI-POC', 'AI-PILOT', 'AI-PROD',
    'MOJO-APP-SUB', 'MOJO-TOKENS', 'MOJO-ONPREM',
    'AMS-BRONZE', 'AMS-SILVER', 'AMS-GOLD',
    'TRAINING-DAY', 'CONSULT-HOUR',
    'DGM-ONSITE-STD', 'DGM-ONSITE-OT100', 'DGM-ONSITE-OT150',
    'DGM-CANVA-AWARD', 'DGM-MOJO-CREDITS', 'DGM-ADMOB-REV',
    'DGM-MOBIAI-CSP', 'DGM-PREPAID-VNPT', 'DGM-PREPAID-VIETTELCA',
}


def run_consolidation(env):
    report = {}

    # 1. Consolidate res.company (ID 1)
    company = env.company
    company.write({
        'name': 'CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ',
        'vat': '0317958465',
        'street': 'Số 11, Đường số 3, KDC CityLand, Phường Tân Mỹ, TP. Hồ Chí Minh',
        'city': 'TP. Hồ Chí Minh',
        'email': 'info@inno.ai.vn',
        'phone': '+84 28 7300 8899',
        'website': 'https://innoria.com',
    })
    if company.partner_id:
        company.partner_id.write({
            'name': 'CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ',
            'vat': '0317958465',
            'street': 'Số 11, Đường số 3, KDC CityLand, Phường Tân Mỹ, TP. Hồ Chí Minh',
            'city': 'TP. Hồ Chí Minh',
            'email': 'info@inno.ai.vn',
            'website': 'https://innoria.com',
        })
    report['company'] = f"{company.name} (MST: {company.vat})"

    # 2. Align all 30 Canonical Products & Pricelists
    ProductTmpl = env['product.template'].with_context(active_test=False)
    ProductTmpl._al2c_align_catalog_prices()

    # Keep only the first/canonical record for each of the 30 SKUs, archive everything else
    all_tmpls = ProductTmpl.search([], order='id asc')
    seen_skus = {}
    non_canonical_ids = []
    for tmpl in all_tmpls:
        code = (tmpl.default_code or '').strip()
        if code in CANONICAL_SKUS and code not in seen_skus:
            seen_skus[code] = tmpl
            if not tmpl.active:
                env.cr.execute("UPDATE product_template SET active = TRUE WHERE id = %s", (tmpl.id,))
                env.cr.execute("UPDATE product_product SET active = TRUE WHERE product_tmpl_id = %s", (tmpl.id,))
        else:
            if tmpl.active:
                non_canonical_ids.append(tmpl.id)

    if non_canonical_ids:
        env.cr.execute("UPDATE product_template SET active = FALSE WHERE id = ANY(%s)", (non_canonical_ids,))
        env.cr.execute("UPDATE product_product SET active = FALSE WHERE product_tmpl_id = ANY(%s)", (non_canonical_ids,))
    env.invalidate_all()

    # Re-run price/account alignment on active canonical templates
    env['product.template']._al2c_align_catalog_prices()
    report['active_skus'] = env['product.template'].search_count([])
    report['archived_demo_products'] = len(non_canonical_ids)

    # 3. Clean up l10n_vn_demo product categories (IDs 28..32)
    Categ = env['product.category']
    fallback_categ = env.ref('product.product_category_all', raise_if_not_found=False) or Categ.browse(1)
    demo_categs = Categ.search([('id', 'in', [28, 29, 30, 31, 32])], order='parent_path desc')
    if demo_categs:
        prods_in_demo_categ = ProductTmpl.search([('categ_id', 'in', demo_categs.ids)])
        if prods_in_demo_categ:
            prods_in_demo_categ.write({'categ_id': fallback_categ.id})
        demo_categs.unlink()
    report['active_categories'] = Categ.search_count([])

    # 4. Consolidate hr.employee
    Employee = env['hr.employee'].with_context(active_test=False)
    # Map duplicate employees 579..583 -> canonical 787..791
    emp_dup_map = {
        579: 787,  # Mai Thị Hồng Thắm
        580: 788,  # Bùi Hữu Tài
        581: 789,  # Huỳnh Trần Quang Khánh
        582: 790,  # Ngô Thanh Lộc
        583: 791,  # Lê Cao Bảo Phúc
    }
    for old_id, new_id in emp_dup_map.items():
        old_emp = Employee.browse(old_id).exists()
        new_emp = Employee.browse(new_id).exists()
        if old_emp and new_emp:
            env.cr.execute(
                "UPDATE account_analytic_line SET employee_id = %s WHERE employee_id = %s",
                (new_id, old_id),
            )
            env.cr.execute(
                "UPDATE al2c_timesheet_staging SET employee_id = %s WHERE employee_id = %s",
                (new_id, old_id),
            )
            env.cr.execute("UPDATE hr_employee SET active = FALSE WHERE id = %s", (old_id,))

    # Tag ID 578 (Phạm Chiến Thắng) as canonical Onsite Engineer DGM-EXT-001
    emp_thang = Employee.browse(578).exists()
    if emp_thang:
        emp_thang.write({
            'job_title': 'Kỹ sư Phần mềm Onsite (Dự án MTI Technology)',
            'work_email': 'thang.pham@inno.ai.vn',
        })
    emp_admin = Employee.browse(1).exists()
    if emp_admin:
        emp_admin.write({
            'job_title': 'System Administrator',
        })
    env.cr.execute("UPDATE hr_employee SET active = TRUE, barcode = 'DGM-EXT-001' WHERE id = 578")
    env.cr.execute("UPDATE hr_employee SET active = TRUE, barcode = 'DGM-ADMIN' WHERE id = 1")
    for idx, emp_id in enumerate([785, 786, 787, 788, 789, 790, 791, 792], start=1):
        env.cr.execute("UPDATE hr_employee SET active = TRUE, barcode = %s WHERE id = %s", (f"DGM-{idx:03d}", emp_id))

    canonical_emp_ids = [1, 578, 785, 786, 787, 788, 789, 790, 791, 792]
    env.cr.execute(
        "UPDATE hr_employee SET active = FALSE WHERE active = TRUE AND NOT (id = ANY(%s))",
        (canonical_emp_ids,),
    )
    archived_emps = env.cr.rowcount
    env.invalidate_all()
    report['active_employees'] = env['hr.employee'].search_count([])
    report['archived_demo_employees'] = archived_emps

    # 5. Consolidate res.partner & Merge duplicate MTI Technology (2859 -> partner_dgm_mti)
    mti_partner = env.ref('insilos_al2c.partner_dgm_mti', raise_if_not_found=False)
    dup_mti = env['res.partner'].with_context(active_test=False).browse(2859).exists()
    dgm_onsite_std = seen_skus.get('DGM-ONSITE-STD')
    dgm_onsite_variant = dgm_onsite_std.product_variant_id if dgm_onsite_std else False

    if mti_partner and dup_mti and dup_mti.id != mti_partner.id:
        env.cr.execute(
            "UPDATE order_header SET partner_id = %s, partner_invoice_id = %s, partner_shipping_id = %s WHERE partner_id = %s",
            (mti_partner.id, mti_partner.id, mti_partner.id, dup_mti.id),
        )
        env.cr.execute(
            "UPDATE account_move SET partner_id = %s, commercial_partner_id = %s WHERE partner_id = %s",
            (mti_partner.id, mti_partner.id, dup_mti.id),
        )
        env.cr.execute(
            "UPDATE account_move_line SET partner_id = %s WHERE partner_id = %s",
            (mti_partner.id, dup_mti.id),
        )
        env.cr.execute(
            "UPDATE project_project SET partner_id = %s WHERE partner_id = %s",
            (mti_partner.id, dup_mti.id),
        )
        dup_mti.write({'active': False, 'name': 'MTI Technology (Merged Duplicate)'})

    # Link SO S01504 (1551) and INV/2026/00005 (1073) lines to DGM-ONSITE-STD
    if dgm_onsite_variant:
        so_mti = env['sale.order'].browse(1551).exists()
        if so_mti and so_mti.order_line:
            env.cr.execute(
                "UPDATE order_line SET product_id = %s WHERE order_id = %s",
                (dgm_onsite_variant.id, so_mti.id),
            )
        inv_mti = env['account.move'].browse(1073).exists()
        if inv_mti:
            env.cr.execute(
                "UPDATE account_move_line SET product_id = %s WHERE move_id = %s AND display_type = 'product'",
                (dgm_onsite_variant.id, inv_mti.id),
            )

    # Archive all non-canonical res.partner records
    env.cr.execute(
        """
        UPDATE party_master
           SET active = FALSE
         WHERE active = TRUE
           AND id NOT IN (1, 2, 3, 3338, 3339, 3340, 3341, 3342, 3343, 3344, 3345, 3346, 3347, 3348, 3349, 3350, 3351)
           AND id NOT IN (SELECT partner_id FROM res_users WHERE active = TRUE AND partner_id IS NOT NULL)
           AND id NOT IN (SELECT work_contact_id FROM hr_employee WHERE active = TRUE AND work_contact_id IS NOT NULL)
        """
    )
    archived_partner_count = env.cr.rowcount
    env.invalidate_all()
    report['active_partners'] = env['res.partner'].search_count([])
    report['archived_demo_partners'] = archived_partner_count

    # 6. Consolidate Sale Orders & Account Moves (remove l10n_vn_demo orders 1,2,597 and test moves)
    demo_so_ids = [1, 2, 597]
    env.cr.execute("DELETE FROM order_line WHERE order_id = ANY(%s)", (demo_so_ids,))
    env.cr.execute("DELETE FROM order_header WHERE id = ANY(%s)", (demo_so_ids,))

    demo_move_ids = [12, 13, 14, 15, 16, 17, 320, 345, 347, 776, 777] + list(range(61, 73))
    env.cr.execute("DELETE FROM account_partial_reconcile WHERE debit_move_id IN (SELECT id FROM account_move_line WHERE move_id = ANY(%s)) OR credit_move_id IN (SELECT id FROM account_move_line WHERE move_id = ANY(%s))", (demo_move_ids, demo_move_ids))
    env.cr.execute("DELETE FROM account_move_line WHERE move_id = ANY(%s)", (demo_move_ids,))
    env.cr.execute("DELETE FROM account_move WHERE id = ANY(%s)", (demo_move_ids,))
    env.invalidate_all()
    report['active_sale_orders'] = env['sale.order'].search_count([])
    report['active_account_moves'] = env['account.move'].search_count([])

    # 7. Consolidate CRM Leads (purge l10n_vn_demo forklift/steel leads & seed 4 canonical DGM B2B opportunities)
    Lead = env['crm.lead']
    demo_leads = Lead.with_context(active_test=False).search([
        '|',
        ('id', 'in', list(range(1, 45))),
        ('name', 'ilike', 'Xe nâng'),
    ])
    if demo_leads:
        demo_leads.unlink()

    canva_partner = env.ref('insilos_al2c.partner_dgm_canva', raise_if_not_found=False)
    mobifone_partner = env.ref('insilos_al2c.partner_dgm_mobifone_mds', raise_if_not_found=False)
    temecula_partner = env.ref('insilos_al2c.partner_dgm_temecula', raise_if_not_found=False)

    dgm_opportunities = [
        {
            'name': '[DGM-B2B] MTI Technology — Gia hạn & Mở rộng Hợp đồng Kỹ sư Onsite 2026 (HĐ DIGIMATE2401-001)',
            'partner_id': mti_partner.id if mti_partner else False,
            'expected_revenue': 660000000.0,
            'probability': 95.0,
            'type': 'opportunity',
            'description': 'Cung cấp dịch vụ kỹ sư phần mềm Onsite theo chuẩn Man-Month (DGM-ONSITE-STD, DGM-ONSITE-OT100, DGM-ONSITE-OT150). Thuế GTGT 8% theo NĐ 174/2025/NĐ-CP.',
        },
        {
            'name': '[DGM-EXP] Canva Pty Ltd — Mở rộng Hệ sinh thái Canvassador & Mojo AI Apps (Export 0% VAT)',
            'partner_id': canva_partner.id if canva_partner else False,
            'expected_revenue': 480000000.0,
            'probability': 90.0,
            'type': 'opportunity',
            'description': 'Hợp đồng xuất khẩu dịch vụ phần mềm và nội dung số với Canva Pty Ltd (Australia). Áp dụng thuế suất GTGT 0% (DGM-CANVA-AWARD) và SLA xuất hóa đơn điện tử trong 24h khi nhận điện báo Có USD Vietcombank.',
        },
        {
            'name': '[DGM-CSP] Trung tâm Dịch vụ số MobiFone (MDS) — Tích hợp Cổng AI & Nội dung số MobiAI (HĐ 191/MOBIFONE)',
            'partner_id': mobifone_partner.id if mobifone_partner else False,
            'expected_revenue': 350000000.0,
            'probability': 80.0,
            'type': 'opportunity',
            'description': 'Hợp tác phân phối dịch vụ nội dung số và AI trên hạ tầng MobiFone MDS (DGM-MOBIAI-CSP). Đối soát doanh thu định kỳ hàng tháng, thuế GTGT 10%.',
        },
        {
            'name': '[DGM-EDU] Temecula Valley USD — Cung cấp Nền tảng Mojo AI Credits & Giải pháp Giáo dục Số (USA Export)',
            'partner_id': temecula_partner.id if temecula_partner else False,
            'expected_revenue': 250000000.0,
            'probability': 85.0,
            'type': 'opportunity',
            'description': 'Cung cấp gói thuê bao Mojo AI Credits (DGM-MOJO-CREDITS) cho đối tác giáo dục Hoa Kỳ Temecula Valley Unified School District (PO P0074540). Thuế suất xuất khẩu 0%.',
        },
    ]
    for opp_vals in dgm_opportunities:
        existing_opp = Lead.search([('name', '=', opp_vals['name'])], limit=1)
        if existing_opp:
            existing_opp.write(opp_vals)
        else:
            Lead.create(opp_vals)
    report['active_crm_leads'] = Lead.search_count([])

    # 8. Consolidate Project Templates & Operational Projects
    Project = env['project.project'].with_context(active_test=False)
    canonical_proj_xmlids = [
        'project_consulting_pool', 'tpl_erp_starter', 'tpl_erp_growth', 'tpl_erp_ent',
        'tpl_grc_essentials', 'tpl_grc_risk', 'tpl_grc_audit',
        'tpl_ai_discovery', 'tpl_ai_poc', 'tpl_ai_pilot', 'tpl_ai_prod',
        'tpl_mojo_onprem', 'tpl_dgm_onsite_mti',
    ]
    canonical_proj_ids = set()
    for xid in canonical_proj_xmlids:
        p = env.ref(f'insilos_al2c.{xid}', raise_if_not_found=False)
        if p:
            canonical_proj_ids.add(p.id)
            if not p.active:
                p.active = True
    mti_proj = Project.browse(487).exists()
    if mti_proj:
        mti_proj.write({
            'active': True,
            'name': 'MTI Technology — B2B Onsite Software Engineering (HĐ DIGIMATE2401-001)',
            'partner_id': mti_partner.id if mti_partner else False,
        })
        canonical_proj_ids.add(mti_proj.id)

    extra_projects = Project.search([('id', 'not in', list(canonical_proj_ids)), ('active', '=', True)])
    if extra_projects:
        extra_projects.write({'active': False})
    report['active_projects'] = env['project.project'].search_count([])

    # 9. Consolidate Knowledge Articles (keep only insilos_al2c articles + 5 Tech Asset Living Architecture articles)
    env.cr.execute(
        """
        UPDATE knowledge_article
           SET active = FALSE
         WHERE active = TRUE
           AND id NOT IN (SELECT res_id FROM ir_model_data WHERE module = 'insilos_al2c' AND model = 'knowledge.article')
           AND id NOT IN (681, 682, 683, 684, 685)
        """
    )
    env.invalidate_all()
    report['active_knowledge_articles'] = env['knowledge.article'].search_count([])

    # 10. Consolidate Documents Root Folders (archive Fleet ID 15 and top-level duplicates 259..263)
    env.cr.execute(
        "UPDATE documents_document SET active = FALSE WHERE id = ANY(%s)",
        ([15, 259, 260, 261, 262, 263],),
    )
    env.invalidate_all()
    report['active_root_folders'] = env['documents.document'].search_count([('type', '=', 'folder'), ('folder_id', '=', False)])

    env.cr.commit()
    return report


def main():
    odoo.tools.config.parse_config(['-c', 'insilos.conf', '-d', 'insilos20_dev'])
    registry = odoo.modules.registry.Registry.new('insilos20_dev')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        report = run_consolidation(env)
        print("=== DGM & AL2C MULTI-CATALOG CONSOLIDATION REPORT ===")
        for k, v in report.items():
            print(f"  {k}: {v}")


if __name__ == '__main__':
    main()
