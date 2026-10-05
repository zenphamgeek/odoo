#!/usr/bin/env python3
import re
import xml.etree.ElementTree as ET

path = 'enterprise/insilos_website/views/innoria_pages.xml'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix accidental quote in class
text = text.replace(
    'class="btn btn-outline-primary" style="border-color:#0284C7;color:#0284C7;background:#FFFFFF; inn-btn-outline-glass px-4 py-3 fw-bold rounded-3 d-inline-flex align-items-center gap-2"',
    'class="btn btn-outline-primary inn-btn-outline-glass px-4 py-3 fw-bold rounded-3 d-inline-flex align-items-center gap-2" style="border-color:#0284C7;color:#0284C7;background:#FFFFFF;"'
)
text = text.replace(
    'class="btn btn-outline-primary" style="border-color:#0284C7;color:#0284C7;background:#FFFFFF; btn-sm px-3 py-2 rounded-3 d-inline-flex align-items-center gap-2"',
    'class="btn btn-outline-primary btn-sm px-3 py-2 rounded-3 d-inline-flex align-items-center gap-2" style="border-color:#0284C7;color:#0284C7;background:#FFFFFF;"'
)

# Line 1901
text = text.replace(
    'style="background:linear-gradient(145deg,#1F2937,#172033);border:1px solid rgba(139,92,246,.45);"',
    'style="background:linear-gradient(145deg,#FFFFFF,#F8FAFC);border:1px solid #E2E8F0;box-shadow:0 10px 30px rgba(139,92,246,.08);"'
)

# Lines 2069 & 2460
text = text.replace(
    'style="background:linear-gradient(120deg,#063947,#111827);"',
    'style="background:linear-gradient(135deg,#F0F9FF 0%,#E0F2FE 100%);"'
)
text = text.replace(
    'style="background:linear-gradient(120deg,#063645,#111827);"',
    'style="background:linear-gradient(135deg,#F0F9FF 0%,#E0F2FE 100%);"'
)

# Line 2875
text = text.replace(
    'style="background: linear-gradient(180deg, #111827 0%, #16202E 100%);"',
    'style="background: linear-gradient(180deg, #FFFFFF 0%, #F0F9FF 100%);"'
)

# Line 3048
text = text.replace(
    'style="border: 1px solid rgba(10, 187, 219, 0.45); background: linear-gradient(145deg, #1F2937, #192330);"',
    'style="border: 1px solid #BAE6FD; background: linear-gradient(145deg, #FFFFFF, #F8FAFC); box-shadow: 0 10px 30px rgba(2, 132, 199, 0.08);"'
)

# Line 3061
text = text.replace(
    'style="background: rgba(0, 0, 0, 0.25); border: 1px solid #E2E8F0;"',
    'style="background: #F8FAFC; border: 1px solid #E2E8F0;"'
)

# Clean remaining button colors with #07151A or #111827
text = text.replace('color: #07151A;', 'color: #FFFFFF;')
text = text.replace('color:#07151A;', 'color:#FFFFFF;')
text = text.replace('background: var(--inn-cyan); color: #07151A;', 'background: #0284C7; color: #FFFFFF;')

ET.fromstring(text)
print("XML validation passed successfully!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("enterprise/insilos_website/views/innoria_pages.xml finalized successfully!")
