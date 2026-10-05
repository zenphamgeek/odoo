#!/usr/bin/env python3
import re
import xml.etree.ElementTree as ET

path = 'enterprise/insilos_website/views/innoria_pages.xml'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace o_cc5
text = text.replace('o_colored_level o_cc o_cc5', 'o_colored_level')

# Replace remaining 111827
text = text.replace('style="background-color: #111827;"', 'style="background-color: #F8FAFC;"')
text = text.replace('style="background-color:#111827;"', 'style="background-color:#F8FAFC;"')
text = text.replace('background: #111827;', 'background: #FFFFFF;')
text = text.replace('background:#111827;', 'background:#FFFFFF;')
text = text.replace('color:#111827;', 'color:#FFFFFF;')
text = text.replace('color: #111827;', 'color: #FFFFFF;')

# Replace remaining 1F2937
text = text.replace('background-color: #1F2937 !important;', 'background-color: #FFFFFF !important; border: 1px solid #E2E8F0 !important;')
text = text.replace('background:#1F2937;', 'background:#FFFFFF; border: 1px solid #E2E8F0;')
text = text.replace('background: #1F2937;', 'background: #FFFFFF; border: 1px solid #E2E8F0;')

# Replace white borders
text = re.sub(r'border-color:\s*rgba\(255,\s*255,\s*255,[^\)]+\)\s*!important;', 'border-color: #E2E8F0 !important;', text)
text = re.sub(r'border:\s*1px\s*solid\s*rgba\(255,\s*255,\s*255,[^\)]+\);', 'border: 1px solid #E2E8F0;', text)
text = re.sub(r'border-top:\s*1px\s*solid\s*rgba\(255,\s*255,\s*255,[^\)]+\);', 'border-top: 1px solid #E2E8F0;', text)
text = re.sub(r'border-bottom:\s*1px\s*solid\s*rgba\(255,\s*255,\s*255,[^\)]+\);', 'border-bottom: 1px solid #E2E8F0;', text)

# Gradient in contactus hero
text = text.replace(
    'background: linear-gradient(90deg, #0ABBDB 0%, #B2FFDA 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;',
    'background: linear-gradient(135deg, #0284C7 0%, #0ABBDB 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'
)

# Badges with light blue
text = text.replace(
    'style="background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.15); color: #B2FFDA;"',
    'style="background: #E0F2FE; border: 1px solid #BAE6FD; color: #0369A1;"'
)
text = text.replace(
    'style="background: rgba(178, 255, 218, 0.15); color: #B2FFDA;"',
    'style="background: #E0F2FE; color: #0284C7;"'
)

# Verify XML
ET.fromstring(text)
print("XML validation succeeded!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Cleaned up remaining dark tokens in innoria_pages.xml successfully!")
