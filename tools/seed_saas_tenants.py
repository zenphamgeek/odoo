#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/seed_saas_tenants.py
==========================
Provisions and tailors the 2 SaaS Cloud Tenants:
  1. innoria.insilos.com  (Database: innoria_prod)  - IT Services & Enterprise Consulting
  2. innokafe.insilos.com (Database: innokafe_prod) - Specialty Coffee & F&B POS
Also registers both tenants in the Master Control Plane (insilos20_dev).
"""

import sys
import os
import hashlib
from datetime import datetime, timedelta

REPO_ROOT = '/home/zen/O20'
sys.path.insert(0, REPO_ROOT)

import odoo
from odoo import api, SUPERUSER_ID, fields
from odoo.modules.registry import Registry

def setup_control_plane():
    print("\n" + "=" * 70)
    print("▶ STEP 1: REGISTERING TENANTS ON MASTER CONTROL PLANE (insilos20_dev)")
    print("=" * 70)
    
    odoo.tools.config.parse_config(['-c', f'{REPO_ROOT}/insilos.conf', '-d', 'insilos20_dev'])
    registry = Registry('insilos20_dev')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # 1. Templates
        tmpl_it = env['insilos.industry.template'].search([('name', 'ilike', 'IT Services')], limit=1)
        if not tmpl_it:
            tmpl_it = env['insilos.industry.template'].search([], limit=1)
            
        tmpl_cafe = env['insilos.industry.template'].search([('name', 'ilike', 'Café')], limit=1)
        if not tmpl_cafe:
            tmpl_cafe = env['insilos.industry.template'].search([('name', 'ilike', 'Restaurant')], limit=1) or tmpl_it

        # 2. Template Releases
        def get_or_create_release(template, tag):
            rel = env['insilos.template.release'].search([('template_id', '=', template.id)], limit=1)
            if not rel:
                sha = hashlib.sha256(f"{template.id}_{tag}_2026".encode()).hexdigest()
                rel = env['insilos.template.release'].create({
                    'name': f"20.0-LTS-{tag}",
                    'template_id': template.id,
                    'artifact_uri': f's3://insilos-releases/{sha}.sql.gz',
                    'artifact_sha256': sha,
                    'catalog_sha256': hashlib.sha256(b'catalog_manifest').hexdigest(),
                    'schema_sha256': hashlib.sha256(b'schema_manifest').hexdigest(),
                    'image_ref': 'docker.io/innoriahub/insilos@sha256:' + hashlib.sha256(b'docker_img').hexdigest(),
                    'postgres_version': '16',
                    'module_manifest': '["base", "web", "insilos_tenant_control"]',
                    'app_version': '19.0',
                    'filestore_manifest_uri': 's3://insilos-filestore/' + hashlib.sha256(b'filestore').hexdigest() + '.json',
                    'test_evidence_uri': 's3://insilos-evidence/' + hashlib.sha256(b'evidence').hexdigest() + '.json',
                    'state': 'published',
                })
            return rel

        rel_it = get_or_create_release(tmpl_it, "IT")
        rel_cafe = get_or_create_release(tmpl_cafe, "CAFE")

        # 3. Innoria Tenant Registration
        t_innoria = env['insilos.tenant'].search([('slug', '=', 'innoria')], limit=1)
        if not t_innoria:
            t_innoria = env['insilos.tenant'].create({
                'name': 'Innoria Solutions JSC',
                'slug': 'innoria',
                'db_name': 'innoria_prod',
                'primary_domain': 'innoria.insilos.com',
                'db_uuid': '11111111-2222-4333-8444-555555555555',
                'environment': 'production',
                'template_id': tmpl_it.id,
                'release_id': rel_it.id,
                'tenant_type': 'paid',
                'billing_state': 'paid_active',
                'paid_until': fields.Datetime.now() + timedelta(days=365),
                'plan_tier': 'enterprise',
                'monthly_price': 4900000.0,
                'owner_name': 'Zen Pham (CTO)',
                'owner_email': 'zen@innoria.com',
                'owner_phone': '+84 908 123 456',
                'company_size': '51-200',
                'desired_state': 'provisioned',
                'observed_state': 'healthy',
            })
            print(f"  ✓ Registered Tenant: {t_innoria.name} [{t_innoria.primary_domain}] -> DB: {t_innoria.db_name}")
        else:
            print(f"  ✓ Tenant already registered: {t_innoria.name}")

        # 4. InnoKafe Tenant Registration
        t_kafe = env['insilos.tenant'].search([('slug', '=', 'innokafe')], limit=1)
        if not t_kafe:
            t_kafe = env['insilos.tenant'].create({
                'name': 'InnoKafe Specialty Coffee',
                'slug': 'innokafe',
                'db_name': 'innokafe_prod',
                'primary_domain': 'innokafe.insilos.com',
                'db_uuid': '66666666-7777-4888-9999-000000000000',
                'environment': 'production',
                'template_id': tmpl_cafe.id,
                'release_id': rel_cafe.id,
                'tenant_type': 'trial',
                'billing_state': 'trial_active',
                'trial_started_at': fields.Datetime.now(),
                'trial_ends_at': fields.Datetime.now() + timedelta(days=30),
                'plan_tier': 'standard',
                'monthly_price': 1490000.0,
                'owner_name': 'InnoKafe Barista Team',
                'owner_email': 'contact@innokafe.insilos.com',
                'owner_phone': '+84 909 654 321',
                'company_size': '11-50',
                'desired_state': 'provisioned',
                'observed_state': 'healthy',
            })
            print(f"  ✓ Registered Tenant: {t_kafe.name} [{t_kafe.primary_domain}] -> DB: {t_kafe.db_name}")
        else:
            print(f"  ✓ Tenant already registered: {t_kafe.name}")

        cr.commit()


def customize_innoria():
    print("\n" + "=" * 70)
    print("▶ STEP 2: TAILORING INNORIA TENANT (innoria_prod - IT Consulting & PM)")
    print("=" * 70)
    
    odoo.tools.config.parse_config(['-c', f'{REPO_ROOT}/innoria.conf', '-d', 'innoria_prod'])
    registry = Registry('innoria_prod')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Company
        company = env['res.company'].search([], limit=1)
        if company:
            company.write({
                'name': 'Innoria Solutions JSC',
                'street': 'Tòa nhà Innovation Hub, 180 Đường Nguyễn Cơ Thạch, TP. Thủ Đức',
                'city': 'Hồ Chí Minh',
                'email': 'contact@innoria.insilos.com',
                'website': 'https://innoria.insilos.com',
                'phone': '+84 28 7300 8899',
            })
            print(f"  ✓ Updated Company Master: {company.name} ({company.email})")

        # IT Services Project
        project = env['project.project'].search([('name', 'ilike', 'Insilos ERP 20')], limit=1)
        if not project:
            project = env['project.project'].create({
                'name': 'Dự Án Triển Khai Insilos Enterprise ERP 20 - Tân Cảng SNP',
                'company_id': company.id,
                'privacy_visibility': 'employees',
            })
            print(f"  ✓ Created Enterprise Project: {project.name} (ID: {project.id})")

            # Project Tasks (WBS)
            task_names = [
                '1. Khảo sát kiến trúc nghiệp vụ Master Data & SAP Lexicon',
                '2. Thiết lập cụm Multi-Tenant Cloud Sovereign Enclave',
                '3. Tích hợp Barcode Logistics Drayage Cát Lái - Cái Mép',
                '4. Đào tạo vận hành và bàn giao nghiệm thu',
            ]
            for tname in task_names:
                env['project.task'].create({
                    'name': tname,
                    'project_id': project.id,
                    'company_id': company.id,
                })
            print(f"  ✓ Created {len(task_names)} WBS Tasks in project.")

        # Consulting Services Products
        prod_consulting = env['product.template'].search([('name', 'ilike', 'Tư Vấn Kiến Trúc')], limit=1)
        if not prod_consulting:
            env['product.template'].create({
                'name': 'Dịch Vụ Tư Vấn Kiến Trúc Enterprise Cloud (Man-Day)',
                'list_price': 12000000.0,
                'type': 'service',
                'service_type': 'manual',
            })
            print("  ✓ Created Service Product: Dịch Vụ Tư Vấn Kiến Trúc Enterprise Cloud")

        cr.commit()


def customize_innokafe():
    print("\n" + "=" * 70)
    print("▶ STEP 3: TAILORING INNOKAFE TENANT (innokafe_prod - Coffee & F&B POS)")
    print("=" * 70)
    
    odoo.tools.config.parse_config(['-c', f'{REPO_ROOT}/innokafe.conf', '-d', 'innokafe_prod'])
    registry = Registry('innokafe_prod')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Company
        company = env['res.company'].search([], limit=1)
        if company:
            company.write({
                'name': 'InnoKafe Specialty Coffee & Roastery',
                'street': '24 Thảo Điền, Phường Thảo Điền, TP. Thủ Đức',
                'city': 'Hồ Chí Minh',
                'email': 'hello@innokafe.insilos.com',
                'website': 'https://innokafe.insilos.com',
                'phone': '+84 28 7300 6688',
            })
            print(f"  ✓ Updated Company Master: {company.name} ({company.email})")

        # F&B Menu Items
        menu_items = [
            ('Cà Phê Muối Insilos Signature (Ly)', 45000.0),
            ('Pour-over Arabica Cầu Đất Đặc Sản (Bình)', 65000.0),
            ('Cold Brew Cam Vàng Thanh Mát (Ly)', 55000.0),
            ('Matcha Latte Sữa Yến Mạch (Ly)', 50000.0),
            ('Bánh Croissant Bơ Pháp Nướng Nóng (Cái)', 35000.0),
        ]
        created_menu = 0
        for name, price in menu_items:
            existing = env['product.template'].search([('name', '=', name)], limit=1)
            if not existing:
                env['product.template'].create({
                    'name': name,
                    'list_price': price,
                    'type': 'consu',
                    'available_in_pos': True if hasattr(env['product.template'], 'available_in_pos') else False,
                })
                created_menu += 1
        print(f"  ✓ Added {created_menu} Specialty Coffee Menu Items to InnoKafe Catalog.")

        # Raw Materials for Recipe / BOM
        raw_items = [
            ('Hạt Cà Phê Arabica Cầu Đất (kg)', 320000.0),
            ('Hạt Cà Phê Robusta Fine Honey (kg)', 180000.0),
            ('Sữa Tươi Thanh Trùng Dalat Milk 1L', 38000.0),
        ]
        created_raw = 0
        for name, cost in raw_items:
            existing = env['product.template'].search([('name', '=', name)], limit=1)
            if not existing:
                env['product.template'].create({
                    'name': name,
                    'standard_price': cost,
                    'type': 'consu',
                })
                created_raw += 1
        print(f"  ✓ Added {created_raw} Roastery Ingredients to InnoKafe Inventory.")

        cr.commit()

if __name__ == '__main__':
    setup_control_plane()
    customize_innoria()
    customize_innokafe()
    print("\n" + "=" * 70)
    print("🎉 ALL TENANT DATA CUSTOMIZED & PROVISIONED SUCCESSFULLY!")
    print("========================================================================")
