#!/usr/bin/env python3
import xml.etree.ElementTree as ET

path = 'enterprise/insilos_website/views/innoria_homepage.xml'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Update navbar template
old_nav = '''    <template id="innoria_navbar" name="INNORIA Navbar">
        <nav class="navbar navbar-expand-lg innoria-navbar" id="innoria_main_nav">'''

new_nav = '''    <template id="innoria_navbar" name="INNORIA Navbar">
        <nav class="navbar navbar-expand-lg innoria-navbar" id="innoria_main_nav" style="background-color: rgba(255, 255, 255, 0.98) !important; border-bottom: 1px solid #E2E8F0 !important; box-shadow: 0 4px 20px -2px rgba(2, 132, 199, 0.08) !important;">
            <style>
                #wrapwrap { background-color: #FFFFFF !important; }
                .innoria-navbar { background-color: rgba(255, 255, 255, 0.98) !important; border-bottom: 1px solid #E2E8F0 !important; }
                .innoria-navbar .nav-link { color: #0F172A !important; font-weight: 600 !important; font-size: 0.9rem !important; }
                .innoria-navbar .nav-link:hover { color: #0284C7 !important; }
                .innoria-navbar .dropdown-menu { background-color: #FFFFFF !important; border: 1px solid #E2E8F0 !important; }
                .innoria-navbar .dropdown-item { color: #0F172A !important; }
                .innoria-navbar .dropdown-item:hover { background-color: #F0F9FF !important; color: #0284C7 !important; }
                .btn-innoria-nav { background: linear-gradient(135deg, #0ABBDB 0%, #0284C7 100%) !important; color: #FFFFFF !important; border: none !important; border-radius: 9999px !important; font-weight: 700 !important; padding: 0.5rem 1.25rem !important; box-shadow: 0 4px 14px rgba(10, 187, 219, 0.35) !important; }
                .btn-innoria-nav:hover { background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important; color: #FFFFFF !important; transform: translateY(-1px) !important; }
            </style>'''

text = text.replace(old_nav, new_nav)

# Improve contrast of lead texts
text = text.replace(
    '<p class="lead text-secondary fs-5 col-lg-10 mx-auto mb-4">',
    '<p class="lead fs-5 col-lg-10 mx-auto mb-4" style="color: #334155 !important;">'
)
text = text.replace(
    '<p class="lead text-secondary fs-5 col-lg-10 mx-auto">',
    '<p class="lead fs-5 col-lg-10 mx-auto" style="color: #334155 !important;">'
)
text = text.replace(
    '<p class="lead text-secondary fs-5 mb-4">',
    '<p class="lead fs-5 mb-4" style="color: #334155 !important;">'
)

# Text secondary in list items to slate 700
text = text.replace('class="text-secondary small mb-3"', 'class="small mb-3" style="color: #475569 !important;"')
text = text.replace('class="text-secondary small mb-0"', 'class="small mb-0" style="color: #475569 !important;"')
text = text.replace('class="text-secondary small"', 'class="small" style="color: #475569 !important;"')

ET.fromstring(text)
print("XML validation passed!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("enterprise/insilos_website/views/innoria_homepage.xml updated!")
