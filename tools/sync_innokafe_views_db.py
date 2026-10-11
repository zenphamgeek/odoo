#!/usr/bin/env python3
"""
Sync InnoKafe views, pages, menus, header brand, hotline, and footer isolation into PostgreSQL innokafe_prod database.
Converts <template id="xyz"> to Odoo's native QWeb <t t-name="module.key"> format.
Supports local (127.0.0.1:5434) and production pod (pgbouncer-service:6432) environments.
"""

import sys
import os
import re
import json
import psycopg2

def extract_template_arch(xml_path, template_id, full_key):
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Search for <template id="template_id" ...> ... </template>
    pattern = rf'(<template\s+[^>]*id=["\']{template_id}["\'][^>]*>)(.*?)(</template>)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"Template '{template_id}' not found in {xml_path}")
    
    open_tag = match.group(1)
    body = match.group(2)
    
    name_match = re.search(r'name=["\']([^"\']+)["\']', open_tag)
    view_name = name_match.group(1) if name_match else template_id
    
    # If the template inherits another view (extension view), Odoo QWeb requires <data> root, not <t t-name>
    if 'inherit_id=' in open_tag or '<xpath' in body:
        return f'<data>{body}</data>', view_name

    name_attr = f' name="{view_name}"' if name_match else ''
    
    # Convert primary <template> to standard Odoo QWeb root <t t-name="...">
    return f'<t t-name="{full_key}"{name_attr}>{body}</t>', view_name

def sync_database(host, port, user, password, dbname):
    print(f"[*] Connecting to {dbname} on {host}:{port} as {user}...")
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname
    )
    cur = conn.cursor()

    if os.path.exists("/app/insilos/enterprise/innokafe_website"):
        base_dir = "/app/insilos"
    elif os.path.exists("/home/zen/O20/enterprise/innokafe_website"):
        base_dir = "/home/zen/O20"
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    innokafe_dir = os.path.join(base_dir, "enterprise", "innokafe_website")
    views_dir = os.path.join(innokafe_dir, "views")

    xml_home = os.path.join(views_dir, "home.xml")
    xml_story = os.path.join(views_dir, "story.xml")
    xml_products = os.path.join(views_dir, "products.xml")
    xml_profiler = os.path.join(views_dir, "taste_profiler.xml")
    xml_b2b = os.path.join(views_dir, "solutions_b2b.xml")
    xml_contactus = os.path.join(views_dir, "contactus.xml")
    xml_templates = os.path.join(views_dir, "website_templates.xml")
    xml_snippets = os.path.join(views_dir, "snippets.xml")

    targets = [
        # Full Pages
        ("homepage", "innokafe_website.homepage", xml_home),
        ("story_page", "innokafe_website.story_page", xml_story),
        ("products_page", "innokafe_website.products_page", xml_products),
        ("taste_profiler_page", "innokafe_website.taste_profiler_page", xml_profiler),
        ("solutions_b2b_page", "innokafe_website.solutions_b2b_page", xml_b2b),
        ("contactus_page", "innokafe_website.contactus_page", xml_contactus),

        # Layout, Brand & Helpers
        ("innokafe_head_metadata", "innokafe_website.innokafe_head_metadata", xml_templates),
        ("innokafe_global_cta", "innokafe_website.innokafe_global_cta", xml_templates),
        ("innokafe_pledge_ribbon", "innokafe_website.innokafe_pledge_ribbon", xml_templates),
        ("innokafe_footer_custom", "innokafe_website.innokafe_footer_custom", xml_templates),

        # Custom Snippets
        ("s_innokafe_hero_story", "innokafe_website.s_innokafe_hero_story", xml_snippets),
        ("s_innokafe_farm_heritage", "innokafe_website.s_innokafe_farm_heritage", xml_snippets),
        ("s_innokafe_four_zero_promise", "innokafe_website.s_innokafe_four_zero_promise", xml_snippets),
        ("s_innokafe_processing_methods", "innokafe_website.s_innokafe_processing_methods", xml_snippets),
        ("s_innokafe_bean_showcase", "innokafe_website.s_innokafe_bean_showcase", xml_snippets),
        ("s_innokafe_roast_profiles", "innokafe_website.s_innokafe_roast_profiles", xml_snippets),
        ("s_innokafe_sensory_wheel", "innokafe_website.s_innokafe_sensory_wheel", xml_snippets),
        ("s_innokafe_taste_profiler", "innokafe_website.s_innokafe_taste_profiler", xml_snippets),
        ("s_innokafe_b2b_solutions", "innokafe_website.s_innokafe_b2b_solutions", xml_snippets),
        ("s_innokafe_testimonials", "innokafe_website.s_innokafe_testimonials", xml_snippets),
        ("s_innokafe_faq", "innokafe_website.s_innokafe_faq", xml_snippets),
        ("s_innokafe_roastery_bar", "innokafe_website.s_innokafe_roastery_bar", xml_snippets),
        ("s_innokafe_cta_sample_box", "innokafe_website.s_innokafe_cta_sample_box", xml_snippets),
        ("s_innokafe_grind_guide", "innokafe_website.s_innokafe_grind_guide", xml_snippets),
        ("s_innokafe_brew_lab", "innokafe_website.s_innokafe_brew_lab", xml_snippets),
        ("s_innokafe_terroir_deepdive", "innokafe_website.s_innokafe_terroir_deepdive", xml_snippets),
        ("s_innokafe_roast_mastery", "innokafe_website.s_innokafe_roast_mastery", xml_snippets),
        ("s_innokafe_subscription_club", "innokafe_website.s_innokafe_subscription_club", xml_snippets),
        ("innokafe_custom_snippets", "innokafe_website.innokafe_custom_snippets", xml_snippets),
    ]

    for tmpl_id, key, xml_path in targets:
        arch_xml, view_name = extract_template_arch(xml_path, tmpl_id, key)
        arch_dict = {"vi_VN": arch_xml, "en_US": arch_xml}
        
        # Check if view exists
        cur.execute("SELECT id, name FROM ir_ui_view WHERE key = %s", (key,))
        rows = cur.fetchall()
        if rows:
            for view_id, name in rows:
                cur.execute("""
                    UPDATE ir_ui_view
                    SET arch_db = %s::jsonb, name = %s, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
                    WHERE id = %s
                """, (json.dumps(arch_dict), view_name, view_id))
                print(f"[✓] Updated view {view_id} ({key}: '{view_name}') - {len(arch_xml)} bytes")
        else:
            cur.execute("""
                INSERT INTO ir_ui_view (name, key, type, mode, priority, active, arch_updated, arch_db, arch_fs, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, 'qweb', 'primary', 16, true, true, %s::jsonb, NULL, 1, 1, NOW(), NOW())
                RETURNING id
            """, (view_name, key, json.dumps(arch_dict)))
            new_view_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
                VALUES (%s, 'innokafe_website', 'ir.ui.view', %s, false)
                ON CONFLICT (module, name) DO UPDATE SET res_id = EXCLUDED.res_id
            """, (tmpl_id, new_view_id))
            print(f"[✓] Inserted view {new_view_id} ({key}: '{view_name}') - {len(arch_xml)} bytes")

    # 1. Sync InnoKafe homepage arch directly to website.homepage (views 980 and 1688)
    homepage_arch_xml, hp_name = extract_template_arch(xml_home, "homepage", "website.homepage")
    homepage_arch_dict = {"vi_VN": homepage_arch_xml, "en_US": homepage_arch_xml}
    cur.execute("SELECT id FROM ir_ui_view WHERE key = 'website.homepage'")
    for row in cur.fetchall():
        v_id = row[0]
        cur.execute("""
            UPDATE ir_ui_view
            SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
            WHERE id = %s
        """, (json.dumps(homepage_arch_dict), v_id))
        print(f"[✓] Synced InnoKafe homepage arch to website.homepage view {v_id} ({len(homepage_arch_xml)} bytes)")

    # 2. Also sync to insilos_website.insilos_homepage in case controller falls back to it
    cur.execute("SELECT id FROM ir_ui_view WHERE key = 'insilos_website.insilos_homepage'")
    for row in cur.fetchall():
        v_id = row[0]
        cur.execute("""
            UPDATE ir_ui_view
            SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
            WHERE id = %s
        """, (json.dumps(homepage_arch_dict), v_id))
        print(f"[✓] Synced InnoKafe homepage arch to insilos_website.insilos_homepage view {v_id}")

    # 2b. Also sync to website.innokafe-homepage (view 15754)
    cur.execute("SELECT id FROM ir_ui_view WHERE key = 'website.innokafe-homepage'")
    for row in cur.fetchall():
        v_id = row[0]
        cur.execute("""
            UPDATE ir_ui_view
            SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
            WHERE id = %s
        """, (json.dumps(homepage_arch_dict), v_id))
        print(f"[✓] Synced InnoKafe homepage arch to website.innokafe-homepage view {v_id}")

    # 2c. Also sync to website.contactus (view 981) so default contactus route renders InnoKafe design
    contactus_arch_xml, cu_name = extract_template_arch(xml_contactus, "contactus_page", "website.contactus")
    contactus_arch_dict = {"vi_VN": contactus_arch_xml, "en_US": contactus_arch_xml}
    cur.execute("SELECT id FROM ir_ui_view WHERE key = 'website.contactus'")
    for row in cur.fetchall():
        v_id = row[0]
        cur.execute("""
            UPDATE ir_ui_view
            SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
            WHERE id = %s
        """, (json.dumps(contactus_arch_dict), v_id))
        print(f"[✓] Synced InnoKafe contactus arch to website.contactus view {v_id} ({len(contactus_arch_xml)} bytes)")

    # 2d. Permanently deactivate legacy insilos_website.insilos_vietnamese_fonts on innokafe_prod
    cur.execute("UPDATE ir_ui_view SET active = false WHERE key = 'insilos_website.insilos_vietnamese_fonts'")
    if cur.rowcount > 0:
        print(f"[✓] Deactivated legacy insilos_website.insilos_vietnamese_fonts ({cur.rowcount} views) on {dbname}")

    # 3. Synchronize InnoKafe Brand Logo to Header Brand views (view 1046 and 1693)
    inno_brand_logo_arch = """<data name="Header Brand Logo">
    <xpath expr="//*[@id='o_fake_navbar_brand']" position="replace">
        <a data-name="Navbar Logo" href="/" t-attf-class="navbar-brand logo inno-logo-interactive d-inline-flex align-items-center py-1 me-xl-4 me-3 #{_link_class}">
            <img class="inno-brand-logo img-fluid" src="/innokafe_website/static/src/img/branding/innokafe_logo_master.svg" alt="InnoKafe - Inspire the Techno" height="38" style="height: 38px; width: auto; max-height: 44px;"/>
        </a>
    </xpath>
</data>"""
    cur.execute("""
        UPDATE ir_ui_view
        SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
        WHERE id = 1046 OR key = 'website.option_header_brand_logo'
    """, (json.dumps({"vi_VN": inno_brand_logo_arch, "en_US": inno_brand_logo_arch}),))
    print("[✓] Updated website.option_header_brand_logo (view 1046) with InnoKafe vector SVG brand logo")

    # Also update website.template_header_default (views 1005 and 1693) to include glass style and direct InnoKafe brand
    inno_header_default_arch = """<data name="Template Header Default">
    <xpath expr="//header//nav" position="replace">
        <t t-set="_navbar_classes" t-valuef="d-none d-lg-block"/>
        <t t-call="website.navbar" _navbar_classes="_navbar_classes">

            <div id="o_main_nav" class="o_main_nav inno-header-glass border-bottom border-dark">
                <!-- Brand -->
                <t t-call="website.placeholder_header_brand" _link_class.f="me-4"/>
                <!-- Navbar -->
                <t t-call="website.navbar_nav" _nav_class.f="me-auto">
                    <!-- Menu -->
                    <t t-foreach="website.menu_id.child_id" t-as="submenu">
                        <t t-call="website.submenu" item_class.f="nav-item" link_class.f="nav-link"/>
                    </t>
                </t>
                <!-- Extra elements -->
                <ul class="navbar-nav align-items-center gap-2 flex-shrink-0 justify-content-end ps-3">
                    <!-- Search Bar -->
                    <t t-call="website.placeholder_header_search_box" _simple_button_layout="True" _simple_button_classes.f="o_navlink_background rounded-circle p-1 lh-1 text-reset"/>
                    <!-- Text element -->
                    <t t-call="website.placeholder_header_text_element"/>
                    <!-- Social -->
                    <t t-call="website.placeholder_header_social_links"/>
                    <!-- Language Selector -->
                    <t t-call="website.placeholder_header_language_selector" _btn_class="_additional_btn_color or 'nav-link'" _dropdown_menu_class.f="dropdown-menu-end"/>
                    <!-- Sign In -->
                    <t t-call="portal.placeholder_user_sign_in" _link_class="_additional_btn_color or 'o_nav_link_btn nav-link border px-3'"/>
                    <!-- User Dropdown -->
                    <t t-call="portal.user_dropdown" _user_name="True" _item_class.f="dropdown" _link_class.f="{{_additional_btn_color or 'nav-link'}} border-0" _dropdown_menu_class.f="dropdown-menu-end"/>
                    <!-- Call To Action -->
                    <t t-call="website.placeholder_header_call_to_action"/>
                </ul>
            </div>
        </t>
        <t t-call="website.template_header_mobile"/>
    </xpath>
</data>"""
    cur.execute("""
        UPDATE ir_ui_view
        SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
        WHERE key = 'website.template_header_default'
    """, (json.dumps({"vi_VN": inno_header_default_arch, "en_US": inno_header_default_arch}),))
    print("[✓] Updated website.template_header_default (views 1005, 1693) with InnoKafe header brand & glass nav")

    # 4. Synchronize Header Hotline (website.header_text_element views 1133 and 2495)
    inno_hotline_arch = """<data inherit_id="website.placeholder_header_text_element" name="Header Text element" active="True">
    <xpath expr="." position="inside">
        <li t-attf-class="#{_item_class}">
            <div t-attf-class="s_text_block #{_div_class}" data-name="Text">
                <a href="tel:+842873006688" class="nav-link o_nav-link_secondary p-2 inno-amber-text d-flex align-items-center gap-1">
                    <i class="oi oi-1x oi-fw oi-filled" data-icon="phone"/>
                    <span class="o_force_ltr"><small class="fw-bold">+84 28 7300 6688</small></span>
                </a>
            </div>
        </li>
    </xpath>
</data>"""
    cur.execute("""
        UPDATE ir_ui_view
        SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
        WHERE key = 'website.header_text_element'
    """, (json.dumps({"vi_VN": inno_hotline_arch, "en_US": inno_hotline_arch}),))
    print("[✓] Updated website.header_text_element with InnoKafe Tasting Bar Hotline (+84 28 7300 6688)")

    # 5. Synchronize InnoKafe Luxury Footer (website.footer_custom views 1059 and 1696)
    inno_footer_arch = """<data inherit_id="website.layout" name="Default" active="True">
    <xpath expr="//div[@id='footer']" position="replace">
        <div id="footer" class="oe_structure oe_structure_solo inno-espresso-bg text-white" t-ignore="true" t-if="not no_footer">
            <section class="s_text_block o_colored_level o_cc o_cc5 pt80 pb40 inno-espresso-bg" data-snippet="s_text_block" data-name="InnoKafe Footer Master" style="background-color: #1E120B;">
                <div class="container">
                    <div class="row g-5 mb-5">
                        <!-- Col 1: Brand & Origin Mission -->
                        <div class="col-lg-4 col-md-6">
                            <div class="mb-3">
                                <a href="/" class="d-inline-flex align-items-center text-decoration-none">
                                    <img src="/innokafe_website/static/src/img/branding/innokafe_logo_white.svg" alt="InnoKafe - Inspire the Techno" height="38" style="height: 38px; width: auto; max-height: 44px;"/>
                                </a>
                            </div>
                            <p class="text-secondary small lh-lg mb-4">
                                Hành trình tôn vinh hạt cà phê Việt Nam nguyên bản từ thủ phủ Robusta Đắk Lắk (Cư M'gar) và Arabica Cầu Đất (1.650m). Chúng tôi kiên định với triết lý Farm-to-Cup, rang mộc Hot-Air chuẩn quốc tế và cam kết 4 Không tuyệt đối vì sức khỏe người thưởng thức.
                            </p>
                            <div class="d-flex align-items-center gap-3">
                                <span class="badge rounded-pill bg-warning text-dark px-3 py-2 fw-bold font-monospace">SCA 84+</span>
                                <span class="badge rounded-pill bg-secondary text-white px-3 py-2 fw-bold font-monospace">HOT-AIR ROAST</span>
                                <span class="badge rounded-pill bg-secondary text-warning px-3 py-2 fw-bold font-monospace">4 KHÔNG</span>
                            </div>
                        </div>

                        <!-- Col 2: Di Sản Nông Trại -->
                        <div class="col-lg-2 col-md-6 col-6">
                            <h6 class="text-white text-uppercase fw-bold mb-3 tracking-wider" style="font-size: 0.85rem; letter-spacing: 0.08em;">
                                Di Sản Nông Trại
                            </h6>
                            <ul class="list-unstyled text-secondary small d-flex flex-column gap-2">
                                <li><a href="/story#daklak" class="text-secondary text-decoration-none hover-white">Robusta Đắk Lắk (Cư M'gar)</a></li>
                                <li><a href="/story#caudat" class="text-secondary text-decoration-none hover-white">Arabica Cầu Đất (1.650m)</a></li>
                                <li><a href="/story#natural" class="text-secondary text-decoration-none hover-white">Phương Pháp Natural</a></li>
                                <li><a href="/story#honey" class="text-secondary text-decoration-none hover-white">Phương Pháp Honey</a></li>
                                <li><a href="/story#washed" class="text-secondary text-decoration-none hover-white">Phương Pháp Washed</a></li>
                                <li><a href="/story#roasting" class="text-secondary text-decoration-none hover-white">Nghệ Thuật Rang Hot-Air</a></li>
                            </ul>
                        </div>

                        <!-- Col 3: Dòng Sản Phẩm & Trải Nghiệm -->
                        <div class="col-lg-2 col-md-6 col-6">
                            <h6 class="text-white text-uppercase fw-bold mb-3 tracking-wider" style="font-size: 0.85rem; letter-spacing: 0.08em;">
                                Sản Phẩm &amp; Gu
                            </h6>
                            <ul class="list-unstyled text-secondary small d-flex flex-column gap-2">
                                <li><a href="/products" class="text-secondary text-decoration-none hover-white">Hạt Cà Phê Đặc Sản</a></li>
                                <li><a href="/products#dripbag" class="text-secondary text-decoration-none hover-white">Phin Giấy Drip Bag</a></li>
                                <li><a href="/products#coldbrew" class="text-secondary text-decoration-none hover-white">Cà Phê Ủ Lạnh Cold Brew</a></li>
                                <li><a href="/taste-profiler" class="text-warning text-decoration-none fw-semibold">Trắc Nghiệm Tìm Gu (Quiz)</a></li>
                                <li><a href="/solutions-b2b" class="text-secondary text-decoration-none hover-white">Giải Pháp B2B Horeca</a></li>
                                <li><a href="/solutions-b2b#equipment" class="text-secondary text-decoration-none hover-white">Tài Trợ Máy Pha 0đ</a></li>
                            </ul>
                        </div>

                        <!-- Col 4: Liên Hệ & Showroom Trải Nghiệm -->
                        <div class="col-lg-4 col-md-6">
                            <h6 class="text-white text-uppercase fw-bold mb-3 tracking-wider" style="font-size: 0.85rem; letter-spacing: 0.08em;">
                                Showroom &amp; Xưởng Rang
                            </h6>
                            <ul class="list-unstyled text-secondary small d-flex flex-column gap-3 mb-4">
                                <li class="d-flex align-items-start gap-2">
                                    <i class="fa fa-map-marker text-warning mt-1"/>
                                    <span><strong>Flagship Tasting Bar:</strong> 128 Nguyễn Đình Chiểu, Phường Võ Thị Sáu, Quận 3, TP. Hồ Chí Minh</span>
                                </li>
                                <li class="d-flex align-items-start gap-2">
                                    <i class="fa fa-fire text-warning mt-1"/>
                                    <span><strong>Xưởng Rang Thủ Công:</strong> Km 7, Quốc Lộ 14, Xã Cư M'gar, Huyện Cư M'gar, Tỉnh Đắk Lắk</span>
                                </li>
                                <li class="d-flex align-items-center gap-2">
                                    <i class="fa fa-phone text-warning"/>
                                    <span><strong>Hotline Thử Mẫu &amp; B2B:</strong> <a href="tel:+842873006688" class="text-white text-decoration-none">+84 28 7300 6688</a></span>
                                </li>
                                <li class="d-flex align-items-center gap-2">
                                    <i class="fa fa-envelope text-warning"/>
                                    <span><strong>Email:</strong> <a href="mailto:hello@innokafe.com" class="text-white text-decoration-none">hello@innokafe.com</a></span>
                                </li>
                            </ul>
                            <div class="d-flex align-items-center gap-3">
                                <span class="badge bg-secondary bg-opacity-25 text-warning border border-warning border-opacity-25 p-2 small">SCA STANDARD 84+</span>
                                <span class="badge bg-secondary bg-opacity-25 text-white border border-secondary border-opacity-25 p-2 small">100% MỘC NGUYÊN CHẤT</span>
                            </div>
                        </div>
                    </div>

                    <!-- Bottom Copyright & Compliance -->
                    <div class="pt-4 border-top border-secondary border-opacity-25 d-flex flex-column flex-md-row justify-content-between align-items-center gap-3 small text-secondary">
                        <div>
                            © 2026 InnoKafe Specialty Coffee &amp; Roastery. Bản quyền thuộc về InnoKafe.
                        </div>
                        <div class="d-flex gap-3">
                            <a href="/story" class="text-secondary text-decoration-none">Câu Chuyện Nông Trại</a>
                            <span>·</span>
                            <a href="/taste-profiler" class="text-secondary text-decoration-none">Tìm Gu Cà Phê</a>
                            <span>·</span>
                            <a href="/solutions-b2b" class="text-secondary text-decoration-none">Hợp Tác Doanh Nghiệp</a>
                            <span>·</span>
                            <a href="/contactus" class="text-secondary text-decoration-none">Liên Hệ</a>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </xpath>
</data>"""
    cur.execute("""
        UPDATE ir_ui_view
        SET arch_db = %s::jsonb, arch_fs = NULL, arch_updated = true, active = true, write_date = NOW()
        WHERE key = 'website.footer_custom'
    """, (json.dumps({"vi_VN": inno_footer_arch, "en_US": inno_footer_arch}),))
    print("[✓] Updated website.footer_custom (views 1059, 1696) with InnoKafe Luxury Footer")

    # 6. Deactivate competing Insilos Enterprise headers, megamenus, footers and corporate snippets
    cur.execute("""
        UPDATE ir_ui_view
        SET active = false, write_date = NOW()
        WHERE (
            key LIKE 'insilos_website.insilos_header%'
            OR key LIKE 'insilos_website.insilos_megamenu%'
            OR key LIKE 'insilos_website.insilos_footer%'
            OR key LIKE 'insilos_website.s_c3ai%'
            OR key LIKE 'insilos_website.s_insilos_%'
            OR key LIKE 'insilos_website.insilos_option_header%'
            OR key LIKE 'insilos_website.s_ins_%'
            OR key LIKE 'insilos_website.s_production_line_topology'
            OR key LIKE 'insilos_website.s_industrial_metrics_kpi'
            OR key LIKE 'insilos_website.s_high_density_comparison'
            OR key LIKE 'website.s_mega_menu_insilos_menu'
        ) AND active = true
    """)
    deactivated_count = cur.rowcount
    print(f"[✓] Deactivated {deactivated_count} competing Insilos UI views in {dbname}")

    # 7. Activate all innokafe_website views
    cur.execute("""
        UPDATE ir_ui_view
        SET active = true, write_date = NOW()
        WHERE key LIKE '%innokafe%' AND (active IS NULL OR active = false)
    """)
    activated_innokafe = cur.rowcount
    print(f"[✓] Activated {activated_innokafe} innokafe views")

    # 8. Configure website domain, clean SEO metadata, and primary Vietnamese language
    # Ensure vi_VN language is active
    cur.execute("UPDATE res_lang SET active = true WHERE code = 'vi_VN'")
    cur.execute("SELECT id FROM res_lang WHERE code = 'vi_VN'")
    vi_lang_row = cur.fetchone()
    vi_lang_id = vi_lang_row[0] if vi_lang_row else 91

    cur.execute("""
        UPDATE website
        SET homepage_url = '/',
            domain = 'https://innokafe.com',
            name = 'InnoKafe Specialty Coffee',
            default_lang_id = %s,
            custom_code_head = NULL
        WHERE id = 1
    """, (vi_lang_id,))

    cur.execute("""
        UPDATE res_company
        SET name = 'InnoKafe Specialty Coffee & Roastery',
            email = 'hello@innokafe.com',
            phone = '+84 28 7300 6688'
        WHERE id = 1
    """)

    # Enforce single language vi_VN for Website 1 (eliminates /en/en and disables multilingual router)
    cur.execute("DELETE FROM website_lang_rel WHERE website_id = 1")
    cur.execute("INSERT INTO website_lang_rel (website_id, lang_id) VALUES (1, %s)", (vi_lang_id,))
    print(f"[✓] Configured website 1 (https://innokafe.com, default_lang vi_VN={vi_lang_id}) and cleaned custom_code_head")

    # 8b. Add 301 Permanent Redirects for legacy /en and /en/en routes to root routes
    legacy_redirects = [
        ('/en', '/'),
        ('/en/', '/'),
        ('/en/en', '/'),
        ('/en/story', '/story'),
        ('/en/products', '/products'),
        ('/en/taste-profiler', '/taste-profiler'),
        ('/en/solutions-b2b', '/solutions-b2b'),
        ('/en/contactus', '/contactus'),
    ]
    for url_from, url_to in legacy_redirects:
        cur.execute("SELECT id FROM website_rewrite WHERE website_id = 1 AND url_from = %s", (url_from,))
        rw_row = cur.fetchone()
        if rw_row:
            cur.execute("""
                UPDATE website_rewrite
                SET url_to = %s, redirect_type = '301', active = true, write_date = NOW()
                WHERE id = %s
            """, (url_to, rw_row[0]))
        else:
            cur.execute("""
                INSERT INTO website_rewrite (name, website_id, url_from, url_to, redirect_type, active, sequence, create_uid, write_uid, create_date, write_date)
                VALUES (%s, 1, %s, %s, '301', true, 10, 1, 1, NOW(), NOW())
            """, (f"Redirect {url_from} to {url_to}", url_from, url_to))
    print(f"[✓] Synced {len(legacy_redirects)} legacy /en routes 301 redirects in website_rewrite")

    # 9. Synchronize website.page records
    pages_to_sync = [
        ("/", "homepage", "InnoKafe — Cà Phê Việt Nam Nguyên Bản"),
        ("/story", "story_page", "Di Sản Nông Trại & Farm to Cup"),
        ("/products", "products_page", "Sản Phẩm Cà Phê Đặc Sản"),
        ("/taste-profiler", "taste_profiler_page", "Tìm Gu Cà Phê Của Bạn"),
        ("/solutions-b2b", "solutions_b2b_page", "Giải Pháp Cà Phê B2B Horeca"),
        ("/contactus", "contactus_page", "Liên Hệ InnoKafe"),
    ]

    for p_url, v_key_suffix, p_title in pages_to_sync:
        cur.execute("SELECT id FROM ir_ui_view WHERE key = %s LIMIT 1", (f"innokafe_website.{v_key_suffix}",))
        v_row = cur.fetchone()
        if not v_row:
            continue
        v_id = v_row[0]
        title_dict = {"vi_VN": p_title, "en_US": p_title}
        url_dict = {"vi_VN": p_url, "en_US": p_url}
        cur.execute("""
            UPDATE website_page
            SET view_id = %s, name = %s::jsonb, is_published = true, write_date = NOW()
            WHERE url::text LIKE %s
        """, (v_id, json.dumps(title_dict), f'%"{p_url}"%'))
        if cur.rowcount == 0:
            cur.execute("""
                INSERT INTO website_page (name, url, view_id, website_id, is_published, website_indexed, create_uid, write_uid, create_date, write_date)
                VALUES (%s::jsonb, %s::jsonb, %s, 1, true, true, 1, 1, NOW(), NOW())
            """, (json.dumps(title_dict), json.dumps(url_dict), v_id))
        print(f"[✓] Page {p_url} mapped to view {v_id} ({p_title}) - updated {cur.rowcount} website_page records")

    # 10. Clean up and deduplicate navigation menu items
    # Purge any rogue Insilos or orphaned menus
    cur.execute("""
        DELETE FROM website_menu
        WHERE manual_url IN (
            '/platform', '/solutions', '/industries', '/resources', '/pricing', '/about', '/request-demo', '/showcase-3d'
        )
    """)

    # Purge ALL children of parent 1 and 3 to eliminate duplicate entries completely
    cur.execute("DELETE FROM website_menu WHERE parent_id IN (1, 3)")
    print("[✓] Cleared duplicate children under menu root (parent_id 1, 3)")

    # Ensure parent menu for Website 1 exists
    cur.execute("SELECT id FROM website_menu WHERE parent_id IS NULL AND website_id = 1 LIMIT 1")
    parent_row = cur.fetchone()
    if parent_row:
        top_menu_id = parent_row[0]
    else:
        top_menu_id = 3

    inno_menus = [
        ("Trang chủ", "/", 10),
        ("Câu chuyện Nông trại", "/story", 20),
        ("Sản phẩm Đặc sản", "/products", 30),
        ("Tìm Gu Cà Phê", "/taste-profiler", 40),
        ("Giải pháp B2B", "/solutions-b2b", 50),
        ("Liên hệ", "/contactus", 60),
    ]

    for name_vn, url_path, seq in inno_menus:
        name_dict = {"en_US": name_vn, "vi_VN": name_vn}
        cur.execute("""
            INSERT INTO website_menu (name, manual_url, sequence, parent_id, website_id, create_uid, write_uid, create_date, write_date)
            VALUES (%s::jsonb, %s, %s, %s, 1, 1, 1, NOW(), NOW())
            RETURNING id
        """, (json.dumps(name_dict), url_path, seq, top_menu_id))
        new_m_id = cur.fetchone()[0]
        print(f"[✓] Created clean menu {new_m_id}: {name_vn} ({url_path}, seq {seq}) under parent {top_menu_id}")

    # 11. Synchronize ir_asset records and bust frontend bundle cache
    assets_to_sync = [
        ("InnoKafe Liquid Spatial SCSS", "web.assets_frontend", "append", "innokafe_website/static/src/scss/innokafe_liquid_spatial.scss", 100),
        ("InnoKafe Theme SCSS", "web.assets_frontend", "append", "innokafe_website/static/src/scss/innokafe_theme.scss", 101),
        ("InnoKafe Taste Profiler JS", "web.assets_frontend", "append", "innokafe_website/static/src/js/taste_profiler.js", 102),
        ("InnoKafe B2B Solutions JS", "web.assets_frontend", "append", "innokafe_website/static/src/js/b2b_solutions.js", 103),
    ]

    for a_name, a_bundle, a_directive, a_path, a_seq in assets_to_sync:
        cur.execute("SELECT id FROM ir_asset WHERE path = %s AND bundle = %s", (a_path, a_bundle))
        existing_asset = cur.fetchone()
        if existing_asset:
            cur.execute("""
                UPDATE ir_asset
                SET name = %s, directive = %s, sequence = %s, active = true, write_date = NOW()
                WHERE id = %s
            """, (a_name, a_directive, a_seq, existing_asset[0]))
        else:
            cur.execute("""
                INSERT INTO ir_asset (name, bundle, directive, path, sequence, active, create_uid, write_uid, create_date, write_date)
                VALUES (%s, %s, %s, %s, %s, true, 1, 1, NOW(), NOW())
            """, (a_name, a_bundle, a_directive, a_path, a_seq))
        print(f"[✓] Synced asset: {a_name} ({a_path})")

    # Invalidate cached bundle attachments strictly scoped to website 1 and ir.ui.view (FAIL-2 remediation)
    cur.execute("""
        DELETE FROM ir_attachment
        WHERE res_model = 'ir.ui.view'
          AND public = true
          AND url ~ '^/web/assets/.*assets_frontend'
          AND (website_id = 1 OR website_id IS NULL)
    """)
    print(f"[✓] Invalidated {cur.rowcount} cached frontend asset attachments for clean bundle recompilation (website_id=1)")

    conn.commit()
    conn.close()
    print(f"\n[✓] InnoKafe total synchronization for {dbname} committed successfully.")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'local'
    if target == 'local':
        db_pass = os.environ.get('INNOKAFE_DB_PASS') or os.environ.get('PGPASSWORD')
        if not db_pass:
            sys.exit("FATAL: INNOKAFE_DB_PASS or PGPASSWORD environment variable is not set; refusing to connect with an empty password.")
        sync_database('127.0.0.1', 5434, 'odoo', db_pass, 'innokafe_prod')
    elif target == 'prod_pod':
        db_pass = os.environ.get('PGPASSWORD') or os.environ.get('INNOKAFE_DB_PASS')
        if not db_pass:
            sys.exit("FATAL: PGPASSWORD or INNOKAFE_DB_PASS environment variable is not set; refusing to connect with an empty password.")
        sync_database(
            os.environ.get('DB_HOST', 'pgbouncer-service'),
            int(os.environ.get('DB_PORT', 6432)),
            os.environ.get('DB_USER', 'insilos'),
            db_pass,
            'innokafe_prod'
        )
