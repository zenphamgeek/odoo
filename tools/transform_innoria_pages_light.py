#!/usr/bin/env python3
"""
Transform all 7 templates in enterprise/insilos_website/views/innoria_pages.xml
from dark theme to pristine Innoria White & Blue theme.
"""
import re
import sys
import xml.etree.ElementTree as ET

path = 'enterprise/insilos_website/views/innoria_pages.xml'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ==============================================================================
# 1. TEMPLATE 1: insilos_about_page
# ==============================================================================
print("Transforming 1. insilos_about_page...")

# Main wrap
content = content.replace(
    '<main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="--innoria-dark-canvas:#111827;--innoria-card:#1F2937;--innoria-cyan:#0ABBDB;--innoria-orange:#FF8000;--innoria-mint:#B2FFDA;background-color:var(--innoria-dark-canvas);color:#F9FAFB;overflow:hidden;">',
    '<main id="wrap" class="oe_structure o_colored_level" style="--innoria-canvas:#FFFFFF;--innoria-card:#FFFFFF;--innoria-cyan:#0ABBDB;--innoria-orange:#FF8000;--innoria-blue:#0284C7;background-color:#FFFFFF;color:#0F172A;overflow:hidden;">'
)

# Style
old_about_style = """                    .inn-about{font-family:Inter,system-ui,sans-serif}.inn-about .eyebrow{color:#0ABBDB;letter-spacing:.16em;font-size:.75rem;font-weight:700;text-transform:uppercase}.inn-about .display{font-size:clamp(2.7rem,6vw,5.8rem);font-weight:800;letter-spacing:-.06em;line-height:.94}.inn-about .section-title{font-size:clamp(2rem,4vw,3.8rem);font-weight:800;letter-spacing:-.05em;line-height:1}.inn-about .glass{background:rgba(31,41,55,.78);border:1px solid rgba(255,255,255,.08);border-radius:1.25rem}.inn-about .accent-line{height:3px;width:64px;background:linear-gradient(90deg,#0ABBDB,#B2FFDA)}.inn-about .hover-card{transition:transform .25s ease,border-color .25s ease,background .25s ease}.inn-about .hover-card:hover{transform:translateY(-8px);border-color:rgba(10,187,219,.65);background:#253247}.inn-about .timeline-line{position:absolute;left:15px;top:1rem;bottom:1rem;width:1px;background:rgba(255,255,255,.14)}.inn-about .timeline-dot{width:31px;height:31px;border-radius:50%;background:#111827;border:2px solid #0ABBDB;position:relative;z-index:1}.inn-about .number{color:#B2FFDA;font-size:3rem;font-weight:800;line-height:1}.inn-about .quote{border-left:3px solid #FF8000}.inn-about .logo-cell{height:96px;display:flex;align-items:center;justify-content:center;border:1px solid rgba(255,255,255,.08);border-radius:.75rem;background:rgba(255,255,255,.025)}.inn-about .logo-cell img{max-height:42px;max-width:130px;filter:grayscale(1);opacity:.72}.inn-about .matrix-head{color:#B2FFDA;font-weight:700}.inn-about .btn-innoria{background:#0ABBDB;border-color:#0ABBDB;color:#07151A;font-weight:800}.inn-about .btn-innoria:hover{background:#B2FFDA;border-color:#B2FFDA;color:#07151A}"""

new_about_style = """                    .inn-about{font-family:Inter,system-ui,sans-serif}.inn-about .eyebrow{color:#0284C7;letter-spacing:.16em;font-size:.75rem;font-weight:700;text-transform:uppercase}.inn-about .display{font-size:clamp(2.7rem,6vw,5.8rem);font-weight:800;letter-spacing:-.06em;line-height:.94;color:#0F172A}.inn-about .section-title{font-size:clamp(2rem,4vw,3.8rem);font-weight:800;letter-spacing:-.05em;line-height:1;color:#0F172A}.inn-about .glass{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:1.25rem;box-shadow:0 4px 20px rgba(15,23,42,0.04)}.inn-about .accent-line{height:3px;width:64px;background:linear-gradient(90deg,#0284C7,#0ABBDB)}.inn-about .hover-card{transition:transform .25s ease,border-color .25s ease,background .25s ease,box-shadow .25s ease}.inn-about .hover-card:hover{transform:translateY(-8px);border-color:#0ABBDB;background:#F0F9FF;box-shadow:0 12px 28px rgba(10,187,219,.15)}.inn-about .timeline-line{position:absolute;left:15px;top:1rem;bottom:1rem;width:1px;background:#E2E8F0}.inn-about .timeline-dot{width:31px;height:31px;border-radius:50%;background:#FFFFFF;border:2px solid #0284C7;position:relative;z-index:1}.inn-about .number{color:#0284C7;font-size:3rem;font-weight:800;line-height:1}.inn-about .quote{border-left:3px solid #FF8000;color:#334155}.inn-about .logo-cell{height:96px;display:flex;align-items:center;justify-content:center;border:1px solid #E2E8F0;border-radius:.75rem;background:#FFFFFF}.inn-about .logo-cell img{max-height:42px;max-width:130px;filter:grayscale(1);opacity:.72}.inn-about .matrix-head{color:#0284C7;font-weight:700}.inn-about .btn-innoria{background:#0284C7;border-color:#0284C7;color:#FFFFFF;font-weight:800}.inn-about .btn-innoria:hover{background:#0ABBDB;border-color:#0ABBDB;color:#07151A}"""

content = content.replace(old_about_style, new_about_style)

# Sections in about page
content = content.replace(
    '<section class="inn-about position-relative py-5" style="min-height:760px;background:radial-gradient(circle at 78% 25%,rgba(10,187,219,.20),transparent 29%),radial-gradient(circle at 15% 85%,rgba(255,128,0,.14),transparent 30%),#111827;">',
    '<section class="inn-about position-relative py-5" style="min-height:760px;background:radial-gradient(circle at 78% 25%,rgba(10,187,219,.15),transparent 35%),radial-gradient(circle at 15% 85%,rgba(255,128,0,.08),transparent 30%),#FFFFFF;">'
)
content = content.replace(
    '<a href="#story" class="btn btn-outline-light btn-lg px-4 py-3">Our heritage</a>',
    '<a href="#story" class="btn btn-outline-primary btn-lg px-4 py-3" style="border-color:#0284C7;color:#0284C7;background:#FFFFFF;">Our heritage</a>'
)
content = content.replace(
    '<section class="inn-about py-5" style="background:#0D1523;">\n                    <div class="container py-lg-5">\n                        <div class="text-center mx-auto mb-5" style="max-width:780px;">\n                            <div class="eyebrow mb-3">Culture cannot be borrowed</div>',
    '<section class="inn-about py-5" style="background:#F8FAFC;">\n                    <div class="container py-lg-5">\n                        <div class="text-center mx-auto mb-5" style="max-width:780px;">\n                            <div class="eyebrow mb-3">Culture cannot be borrowed</div>'
)
content = content.replace(
    '<section class="inn-about py-5" style="background:linear-gradient(135deg,#102F38,#111827 58%);">',
    '<section class="inn-about py-5" style="background:#F0F9FF;">'
)
content = content.replace(
    '<section class="inn-about py-5" style="background:#0D1523;">\n                    <div class="container py-lg-5">\n                        <div class="text-center mx-auto mb-5" style="max-width:760px;">\n                            <div class="eyebrow mb-3">Trusted delivery</div>',
    '<section class="inn-about py-5" style="background:#F8FAFC;">\n                    <div class="container py-lg-5">\n                        <div class="text-center mx-auto mb-5" style="max-width:760px;">\n                            <div class="eyebrow mb-3">Trusted delivery</div>'
)
content = content.replace(
    '<section id="consultation" class="inn-about py-5" style="background:radial-gradient(circle at 80% 15%,rgba(255,128,0,.25),transparent 30%),linear-gradient(120deg,#073641,#111827);">',
    '<section id="consultation" class="inn-about py-5" style="background:linear-gradient(135deg,#F0F9FF 0%,#E0F2FE 100%);">'
)

# Replace text-white-50 in about page
# We target the about page block specifically
about_end = content.find('</template>\n\n    <template id="insilos_platform_page"')
about_block = content[:about_end]
about_block_clean = about_block.replace('text-white-50', 'text-muted')
about_block_clean = about_block_clean.replace('<hr class="border-secondary my-4"/>', '<hr class="border-slate-200 my-4" style="border-color:#E2E8F0;"/>')
about_block_clean = about_block_clean.replace('border-bottom border-secondary', 'border-bottom border-slate-200')
content = about_block_clean + content[about_end:]

# ==============================================================================
# 2. TEMPLATE 2: insilos_platform_page (MOJO AI)
# ==============================================================================
print("Transforming 2. insilos_platform_page...")

# Main wrap
content = content.replace(
    '<main id="wrap" class="oe_structure o_colored_level o_cc o_cc5 mojo-platform-root" style="background-color: var(--innoria-dark-canvas, #111827); color: #F3F4F6; overflow-x: hidden;">',
    '<main id="wrap" class="oe_structure o_colored_level mojo-platform-root" style="background-color: #FFFFFF; color: #0F172A; overflow-x: hidden;">'
)

# Root styles in CDATA
old_mojo_cdata_vars = """                :root {
                    --innoria-dark-canvas: #111827;
                    --mojo-bg: #111827;
                    --mojo-card: #1F2937;
                    --mojo-card-alt: #16202E;
                    --mojo-card-hover: #263345;
                    --mojo-cyan: #0ABBDB;
                    --mojo-cyan-glow: rgba(10, 187, 219, 0.25);
                    --mojo-orange: #FF8000;
                    --mojo-orange-glow: rgba(255, 128, 0, 0.25);
                    --mojo-mint: #B2FFDA;
                    --mojo-mint-glow: rgba(178, 255, 218, 0.25);
                    --mojo-border: rgba(10, 187, 219, 0.2);
                    --mojo-text-muted: #9CA3AF;
                }

                .mojo-platform-root {
                    font-family: inherit;
                    background-color: #111827 !important;
                }"""

new_mojo_cdata_vars = """                :root {
                    --innoria-dark-canvas: #FFFFFF;
                    --mojo-bg: #FFFFFF;
                    --mojo-card: #FFFFFF;
                    --mojo-card-alt: #F8FAFC;
                    --mojo-card-hover: #F0F9FF;
                    --mojo-cyan: #0ABBDB;
                    --mojo-cyan-glow: rgba(10, 187, 219, 0.15);
                    --mojo-orange: #FF8000;
                    --mojo-orange-glow: rgba(255, 128, 0, 0.15);
                    --mojo-mint: #0284C7;
                    --mojo-mint-glow: rgba(2, 132, 199, 0.15);
                    --mojo-border: #E2E8F0;
                    --mojo-text-muted: #64748B;
                }

                .mojo-platform-root {
                    font-family: inherit;
                    background-color: #FFFFFF !important;
                    color: #0F172A !important;
                }"""

content = content.replace(old_mojo_cdata_vars, new_mojo_cdata_vars)

# Mojo gradient and badges
content = content.replace(
    'background: linear-gradient(135deg, #FFFFFF 20%, #B2FFDA 55%, #0ABBDB 90%);',
    'background: linear-gradient(135deg, #0F172A 20%, #0284C7 60%, #0ABBDB 95%);'
)
content = content.replace(
    'background: rgba(31, 41, 55, 0.82);\n                    backdrop-filter: blur(16px);\n                    -webkit-backdrop-filter: blur(16px);\n                    border: 1px solid var(--mojo-border);',
    'background: #FFFFFF;\n                    border: 1px solid #E2E8F0;\n                    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);'
)
content = content.replace(
    '.mojo-card-luxury:hover {\n                    transform: translateY(-5px);\n                    border-color: rgba(10, 187, 219, 0.5);\n                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), 0 0 30px var(--mojo-cyan-glow);\n                }',
    '.mojo-card-luxury:hover {\n                    transform: translateY(-5px);\n                    border-color: #0ABBDB;\n                    box-shadow: 0 16px 36px rgba(10, 187, 219, 0.15);\n                }'
)
content = content.replace(
    'background: rgba(10, 187, 219, 0.1);\n                    border: 1px solid rgba(10, 187, 219, 0.35);\n                    color: var(--mojo-mint);',
    'background: #E0F2FE;\n                    border: 1px solid #BAE6FD;\n                    color: #0369A1;'
)

# Scope changes in platform page
p_start = content.find('<template id="insilos_platform_page"')
p_end = content.find('</template>\n\n    <template id="innoria_digiforce_page"')
p_block = content[p_start:p_end]
p_block = p_block.replace('text-white-50', 'text-muted')
p_block = p_block.replace('text-white', 'text-dark')
p_block = p_block.replace('btn-outline-light', 'btn-outline-primary" style="border-color:#0284C7;color:#0284C7;background:#FFFFFF;')
p_block = p_block.replace('bg-dark', 'bg-white')
content = content[:p_start] + p_block + content[p_end:]

# ==============================================================================
# 3. TEMPLATE 3: innoria_digiforce_page (DIGIFORCE)
# ==============================================================================
print("Transforming 3. innoria_digiforce_page...")

# Main wrap
content = content.replace(
    '<template id="innoria_digiforce_page" name="DIGIFORCE No-Code Platform | INNORIA">\n        <t t-call="website.layout" no_header="True" no_footer="True">\n            <t t-call="insilos_website.innoria_navbar"/>\n            <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="background-color: var(--innoria-dark-canvas, #111827); color: #F9FAFB;">',
    '<template id="innoria_digiforce_page" name="DIGIFORCE No-Code Platform | INNORIA">\n        <t t-call="website.layout" no_header="True" no_footer="True">\n            <t t-call="insilos_website.innoria_navbar"/>\n            <main id="wrap" class="oe_structure o_colored_level" style="background-color: #FFFFFF; color: #0F172A;">'
)

# Style
old_df_style = """.df-page{--df-dark:#111827;--df-card:#1F2937;--df-cyan:#0ABBDB;--df-orange:#FF8000;--df-green:#10B981;--df-muted:#9CA3AF;font-family:inherit;overflow:hidden}
                    .df-page .df-section{padding:96px 0}.df-page .df-eyebrow{color:var(--df-cyan);font-size:.78rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase}.df-page .df-title{font-size:clamp(2rem,4vw,4rem);font-weight:800;line-height:1.06}.df-page .df-subtitle{color:#D1D5DB;font-size:1.1rem;line-height:1.7}.df-page .df-card{background:var(--df-card);border:1px solid rgba(10,187,219,.2);border-radius:20px}.df-page .df-glow{box-shadow:0 0 60px rgba(10,187,219,.14)}
                    .df-hero{position:relative;padding:100px 0 90px;background:radial-gradient(circle at 80% 20%,rgba(10,187,219,.22),transparent 30%),radial-gradient(circle at 12% 72%,rgba(255,128,0,.14),transparent 27%),#111827}.df-hero:before{content:"";position:absolute;inset:0;opacity:.2;background-image:linear-gradient(rgba(10,187,219,.15) 1px,transparent 1px),linear-gradient(90deg,rgba(10,187,219,.15) 1px,transparent 1px);background-size:48px 48px;mask-image:linear-gradient(to bottom,#000,transparent)}
                    .df-quote{border-left:3px solid var(--df-orange);background:rgba(31,41,55,.85);border-radius:0 12px 12px 0;padding:16px 20px;color:#E5E7EB}.df-quote small{color:var(--df-orange);font-weight:700}
                    .df-canvas{background:#0B1220;border:1px solid rgba(10,187,219,.45);border-radius:22px;overflow:hidden;position:relative;min-height:450px;box-shadow:0 25px 70px rgba(0,0,0,.42)}.df-canvas-top{height:44px;background:#172033;border-bottom:1px solid #293548;padding:13px 16px}.df-dot{display:inline-block;width:9px;height:9px;margin-right:6px;border-radius:50%}.df-nav{width:82px;background:#151E2E;border-right:1px solid #293548;padding:18px 12px}.df-nav i{display:block;height:28px;margin:0 0 12px;border-radius:7px;background:#243147}.df-nav i:first-child{background:rgba(10,187,219,.35);border-left:2px solid var(--df-cyan)}.df-workspace{padding:26px;background:radial-gradient(#2B3A50 1px,transparent 1px);background-size:18px 18px}.df-panel{background:#1D293B;border:1px solid #34445A;border-radius:10px;padding:14px;color:#E5E7EB;box-shadow:0 10px 24px rgba(0,0,0,.28)}.df-canvas-card{position:absolute}.df-node{font-size:.72rem;font-weight:700;padding:11px 13px;border-radius:8px;background:#1F2937;border:1px solid #42536A;color:#E5E7EB}.df-node.cyan{border-color:var(--df-cyan);box-shadow:0 0 20px rgba(10,187,219,.18)}.df-node.orange{border-color:var(--df-orange)}.df-node.green{border-color:var(--df-green)}
                    .df-kpi{height:100%;padding:30px}.df-kpi-value{font-size:3rem;font-weight:850;line-height:1;color:var(--df-cyan)}.df-kpi:nth-child(2) .df-kpi-value{color:var(--df-orange)}.df-kpi:nth-child(3) .df-kpi-value{color:var(--df-green)}.df-kpi p{margin:12px 0 0;color:#D1D5DB}
                    .df-compare{overflow:hidden}.df-compare table{margin:0;color:#E5E7EB}.df-compare th{padding:20px;background:#192436;border:0}.df-compare td{padding:18px;border-color:#374151}.df-compare .old{color:#FDA4AF}.df-compare .new{color:#6EE7B7}.df-check{color:var(--df-green);font-weight:800}.df-cross{color:#FB7185;font-weight:800}
                    .df-suite{height:100%;padding:32px;position:relative;overflow:hidden}.df-suite:after{content:"";position:absolute;width:160px;height:160px;border-radius:50%;right:-70px;bottom:-75px;background:rgba(10,187,219,.1)}.df-suite h3{font-weight:800}.df-suite ul{position:relative;z-index:1;padding:0;list-style:none}.df-suite li{padding:11px 0;border-bottom:1px solid rgba(255,255,255,.08);color:#D1D5DB}.df-suite li:before{content:"◆";color:var(--df-cyan);font-size:.6rem;margin-right:10px}.df-suite.grc li:before{color:var(--df-orange)}
                    .df-engine{position:relative;padding:48px 18px;min-height:420px;background:linear-gradient(135deg,#162337,#101827);border-radius:24px;border:1px solid rgba(10,187,219,.25)}.df-engine-core{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:205px;height:205px;border-radius:50%;background:linear-gradient(145deg,#0ABBDB,#087B97);display:flex;align-items:center;justify-content:center;text-align:center;font-weight:850;font-size:1.25rem;box-shadow:0 0 0 15px rgba(10,187,219,.08),0 0 50px rgba(10,187,219,.4)}.df-orbit{position:absolute;border:1px dashed rgba(10,187,219,.42);border-radius:50%;top:50%;left:50%;transform:translate(-50%,-50%);width:430px;height:300px}.df-tech{position:absolute;background:#1F2937;border:1px solid #41526A;border-radius:13px;padding:12px 16px;font-weight:700;box-shadow:0 10px 24px rgba(0,0,0,.25)}.df-tech.ai{top:18%;left:8%;border-color:var(--df-cyan)}.df-tech.rpa{top:18%;right:8%;border-color:var(--df-orange)}.df-tech.chain{bottom:14%;left:10%;border-color:var(--df-green)}.df-tech.api{bottom:14%;right:10%;border-color:#A78BFA}
                    .df-workflow{padding:35px;background:#0D1524;border:1px solid #263A55;border-radius:24px;overflow:auto}.df-flow{min-width:790px;min-height:300px;position:relative;background-image:radial-gradient(#34445A 1px,transparent 1px);background-size:20px 20px}.df-flow-line{position:absolute;height:2px;background:linear-gradient(90deg,var(--df-cyan),var(--df-green));top:145px;left:145px;width:505px}.df-flow-node{position:absolute;top:100px;width:140px;min-height:90px;padding:15px;border-radius:12px;background:#1F2937;border:1px solid #41526A;text-align:center;font-size:.8rem;font-weight:700}.df-flow-node small{display:block;margin-top:6px;color:#9CA3AF;font-weight:400}.df-flow-node:nth-child(2){left:10px;border-color:var(--df-cyan)}.df-flow-node:nth-child(3){left:185px;border-color:var(--df-orange)}.df-flow-node:nth-child(4){left:360px;border-color:#A78BFA}.df-flow-node:nth-child(5){left:535px;border-color:var(--df-green)}.df-flow-node:nth-child(6){left:710px;border-color:var(--df-cyan)}
                    .df-cta{background:linear-gradient(120deg,#087C94,#0ABBDB 54%,#0A9E7C);padding:72px 0}.df-button{display:inline-block;padding:15px 25px;border-radius:9px;background:var(--df-orange);color:#fff!important;font-weight:800;text-decoration:none;box-shadow:0 10px 24px rgba(111,55,0,.32)}.df-button:hover{background:#FF9126}.df-chip{display:inline-block;padding:7px 11px;border:1px solid rgba(10,187,219,.4);border-radius:99px;color:#A5F3FC;font-size:.77rem;margin:4px}
                    @media(max-width:767px){.df-section{padding:64px 0}.df-canvas{min-height:390px}.df-orbit{width:290px;height:280px}.df-tech{font-size:.72rem;padding:9px}.df-engine-core{width:145px;height:145px;font-size:1rem}}"""

new_df_style = """.df-page{--df-dark:#FFFFFF;--df-card:#FFFFFF;--df-cyan:#0ABBDB;--df-orange:#FF8000;--df-green:#0284C7;--df-muted:#64748B;font-family:inherit;overflow:hidden}
                    .df-page .df-section{padding:96px 0;background:#FFFFFF}.df-page .df-section:nth-of-type(even){background:#F8FAFC}.df-page .df-eyebrow{color:var(--df-green);font-size:.78rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase}.df-page .df-title{font-size:clamp(2rem,4vw,4rem);font-weight:800;line-height:1.06;color:#0F172A}.df-page .df-subtitle{color:#475569;font-size:1.1rem;line-height:1.7}.df-page .df-card{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:20px;box-shadow:0 4px 20px rgba(15,23,42,0.04)}.df-page .df-glow{box-shadow:0 10px 35px rgba(2,132,199,.08)}
                    .df-hero{position:relative;padding:100px 0 90px;background:radial-gradient(circle at 80% 20%,rgba(10,187,219,.15),transparent 35%),radial-gradient(circle at 12% 72%,rgba(255,128,0,.08),transparent 30%),#FFFFFF}
                    .df-quote{border-left:3px solid var(--df-orange);background:#F8FAFC;border:1px solid #E2E8F0;border-left-width:3px;border-radius:0 12px 12px 0;padding:16px 20px;color:#334155}.df-quote small{color:var(--df-orange);font-weight:700}
                    .df-canvas{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:22px;overflow:hidden;position:relative;min-height:450px;box-shadow:0 20px 50px rgba(2,132,199,.08)}.df-canvas-top{height:44px;background:#F8FAFC;border-bottom:1px solid #E2E8F0;padding:13px 16px}.df-dot{display:inline-block;width:9px;height:9px;margin-right:6px;border-radius:50%}.df-nav{width:82px;background:#F8FAFC;border-right:1px solid #E2E8F0;padding:18px 12px}.df-nav i{display:block;height:28px;margin:0 0 12px;border-radius:7px;background:#E2E8F0}.df-nav i:first-child{background:#E0F2FE;border-left:2px solid var(--df-cyan)}.df-workspace{padding:26px;background:radial-gradient(#E2E8F0 1px,transparent 1px);background-size:18px 18px}.df-panel{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;padding:14px;color:#0F172A;box-shadow:0 4px 12px rgba(15,23,42,.05)}.df-canvas-card{position:absolute}.df-node{font-size:.72rem;font-weight:700;padding:11px 13px;border-radius:8px;background:#FFFFFF;border:1px solid #E2E8F0;color:#0F172A;box-shadow:0 2px 8px rgba(15,23,42,.04)}.df-node.cyan{border-color:var(--df-cyan)}.df-node.orange{border-color:var(--df-orange)}.df-node.green{border-color:var(--df-green)}
                    .df-kpi{height:100%;padding:30px;background:#FFFFFF}.df-kpi-value{font-size:3rem;font-weight:850;line-height:1;color:#0284C7}.df-kpi:nth-child(2) .df-kpi-value{color:var(--df-orange)}.df-kpi:nth-child(3) .df-kpi-value{color:#0ABBDB}.df-kpi p{margin:12px 0 0;color:#475569}
                    .df-compare{overflow:hidden}.df-compare table{margin:0;color:#0F172A}.df-compare th{padding:20px;background:#F8FAFC;color:#0F172A;border-bottom:2px solid #E2E8F0}.df-compare td{padding:18px;border-color:#E2E8F0}.df-compare .old{color:#E11D48}.df-compare .new{color:#0284C7}.df-check{color:#0284C7;font-weight:800}.df-cross{color:#E11D48;font-weight:800}
                    .df-suite{height:100%;padding:32px;position:relative;overflow:hidden;background:#FFFFFF}.df-suite:after{content:"";position:absolute;width:160px;height:160px;border-radius:50%;right:-70px;bottom:-75px;background:rgba(10,187,219,.06)}.df-suite h3{font-weight:800;color:#0F172A}.df-suite ul{position:relative;z-index:1;padding:0;list-style:none}.df-suite li{padding:11px 0;border-bottom:1px solid #E2E8F0;color:#475569}.df-suite li:before{content:"◆";color:var(--df-cyan);font-size:.6rem;margin-right:10px}.df-suite.grc li:before{color:var(--df-orange)}
                    .df-engine{position:relative;padding:48px 18px;min-height:420px;background:#F8FAFC;border-radius:24px;border:1px solid #E2E8F0}.df-engine-core{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:205px;height:205px;border-radius:50%;background:linear-gradient(145deg,#0284C7,#0ABBDB);display:flex;align-items:center;justify-content:center;text-align:center;font-weight:850;font-size:1.25rem;color:#FFFFFF;box-shadow:0 0 0 15px rgba(2,132,199,.08),0 0 50px rgba(2,132,199,.3)}.df-orbit{position:absolute;border:1px dashed rgba(2,132,199,.35);border-radius:50%;top:50%;left:50%;transform:translate(-50%,-50%);width:430px;height:300px}.df-tech{position:absolute;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:13px;padding:12px 16px;font-weight:700;color:#0F172A;box-shadow:0 4px 12px rgba(15,23,42,.05)}.df-tech.ai{top:18%;left:8%;border-color:var(--df-cyan)}.df-tech.rpa{top:18%;right:8%;border-color:var(--df-orange)}.df-tech.chain{bottom:14%;left:10%;border-color:var(--df-green)}.df-tech.api{bottom:14%;right:10%;border-color:#0284C7}
                    .df-workflow{padding:35px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:24px;overflow:auto}.df-flow{min-width:790px;min-height:300px;position:relative;background-image:radial-gradient(#CBD5E1 1px,transparent 1px);background-size:20px 20px}.df-flow-line{position:absolute;height:2px;background:linear-gradient(90deg,var(--df-cyan),var(--df-green));top:145px;left:145px;width:505px}.df-flow-node{position:absolute;top:100px;width:140px;min-height:90px;padding:15px;border-radius:12px;background:#FFFFFF;border:1px solid #E2E8F0;text-align:center;font-size:.8rem;font-weight:700;color:#0F172A;box-shadow:0 2px 8px rgba(15,23,42,.04)}.df-flow-node small{display:block;margin-top:6px;color:#64748B;font-weight:400}.df-flow-node:nth-child(2){left:10px;border-color:var(--df-cyan)}.df-flow-node:nth-child(3){left:185px;border-color:var(--df-orange)}.df-flow-node:nth-child(4){left:360px;border-color:#0284C7}.df-flow-node:nth-child(5){left:535px;border-color:var(--df-green)}.df-flow-node:nth-child(6){left:710px;border-color:var(--df-cyan)}
                    .df-cta{background:linear-gradient(120deg,#0284C7,#0ABBDB 54%,#0D9488);padding:72px 0}.df-button{display:inline-block;padding:15px 25px;border-radius:9px;background:var(--df-orange);color:#fff!important;font-weight:800;text-decoration:none;box-shadow:0 10px 24px rgba(111,55,0,.32)}.df-button:hover{background:#FF9126}.df-chip{display:inline-block;padding:7px 11px;border:1px solid #BAE6FD;border-radius:99px;background:#E0F2FE;color:#0369A1;font-size:.77rem;margin:4px}
                    @media(max-width:767px){.df-section{padding:64px 0}.df-canvas{min-height:390px}.df-orbit{width:290px;height:280px}.df-tech{font-size:.72rem;padding:9px}.df-engine-core{width:145px;height:145px;font-size:1rem}}"""

content = content.replace(old_df_style, new_df_style)

# Scope changes in digiforce
df_start = content.find('<template id="innoria_digiforce_page"')
df_end = content.find('</template>\n\n    <template id="innoria_blockchain_page"')
df_block = content[df_start:df_end]
df_block = df_block.replace('text-white-50', 'text-muted')
df_block = df_block.replace('text-white', 'text-dark')
df_block = df_block.replace('background:#172033;border:1px solid #34445A;', 'background:#F8FAFC;border:1px solid #E2E8F0;')
content = content[:df_start] + df_block + content[df_end:]

# ==============================================================================
# 4. TEMPLATE 4: innoria_blockchain_page (MOJOVERSE)
# ==============================================================================
print("Transforming 4. innoria_blockchain_page...")

# Main wrap
content = content.replace(
    '<template id="innoria_blockchain_page" name="MOJOVERSE Blockchain Platform | INNORIA">\n        <t t-call="website.layout" no_header="True" no_footer="True">\n            <t t-call="insilos_website.innoria_navbar"/>\n            <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="--innoria-dark-canvas:#111827;--innoria-card:#1F2937;--innoria-cyan:#0ABBDB;--innoria-orange:#FF8000;--innoria-violet:#8B5CF6;background-color:var(--innoria-dark-canvas);color:#F9FAFB;overflow:hidden;">',
    '<template id="innoria_blockchain_page" name="MOJOVERSE Blockchain Platform | INNORIA">\n        <t t-call="website.layout" no_header="True" no_footer="True">\n            <t t-call="insilos_website.innoria_navbar"/>\n            <main id="wrap" class="oe_structure o_colored_level" style="--innoria-canvas:#FFFFFF;--innoria-card:#FFFFFF;--innoria-cyan:#0ABBDB;--innoria-orange:#FF8000;--innoria-blue:#0284C7;background-color:#FFFFFF;color:#0F172A;overflow:hidden;">'
)

# Hero section & quotes in blockchain
bc_start = content.find('<template id="innoria_blockchain_page"')
bc_end = content.find('</template>\n\n    <template id="insilos_solutions_page"')
bc_block = content[bc_start:bc_end]

bc_block = bc_block.replace(
    'style="background:radial-gradient(circle at 15% 20%,rgba(10,187,219,.20),transparent 30%),radial-gradient(circle at 85% 10%,rgba(139,92,246,.18),transparent 32%),#111827;"',
    'style="background:radial-gradient(circle at 15% 20%,rgba(10,187,219,.15),transparent 35%),radial-gradient(circle at 85% 10%,rgba(2,132,199,.10),transparent 32%),#FFFFFF;"'
)
bc_block = bc_block.replace('border:1px solid rgba(10,187,219,.45);background:rgba(10,187,219,.08);color:#0ABBDB;', 'border:1px solid #BAE6FD;background:#E0F2FE;color:#0369A1;')
bc_block = bc_block.replace('color:#CBD5E1;', 'color:#475569;')
bc_block = bc_block.replace('background:rgba(31,41,55,.82);border-left:3px solid #0ABBDB;box-shadow:0 16px 45px rgba(0,0,0,.25);', 'background:#FFFFFF;border:1px solid #E2E8F0;border-left:4px solid #0ABBDB;box-shadow:0 10px 30px rgba(10,187,219,.08);color:#334155;')
bc_block = bc_block.replace('border:1px solid #8B5CF6;color:#E9D5FF;', 'border:1px solid #0284C7;color:#0284C7;background:#FFFFFF;')
bc_block = bc_block.replace('background:linear-gradient(135deg,rgba(10,187,219,.2),rgba(139,92,246,.2));border:1px solid rgba(10,187,219,.45);box-shadow:0 0 75px rgba(10,187,219,.2);', 'background:linear-gradient(135deg,#F0F9FF,#E0F2FE);border:1px solid #BAE6FD;box-shadow:0 10px 35px rgba(2,132,199,.1);')
bc_block = bc_block.replace('background:#1F2937;border:1px solid rgba(10,187,219,.2);', 'background:#FFFFFF;border:1px solid #E2E8F0;box-shadow:0 2px 8px rgba(15,23,42,.04);')
bc_block = bc_block.replace('background:#1F2937;border:1px solid rgba(255,128,0,.2);', 'background:#FFFFFF;border:1px solid #E2E8F0;box-shadow:0 2px 8px rgba(15,23,42,.04);')
bc_block = bc_block.replace('background:#1F2937;border:1px solid rgba(139,92,246,.2);', 'background:#FFFFFF;border:1px solid #E2E8F0;box-shadow:0 2px 8px rgba(15,23,42,.04);')
bc_block = bc_block.replace('background:#1F2937;', 'background:#FFFFFF;border:1px solid #E2E8F0;')
bc_block = bc_block.replace('background:#111827;', 'background:#F8FAFC;')
bc_block = bc_block.replace('background:#16202E;', 'background:#FFFFFF;border:1px solid #E2E8F0;')
bc_block = bc_block.replace('text-white-50', 'text-muted')
bc_block = bc_block.replace('text-white', 'text-dark')

content = content[:bc_start] + bc_block + content[bc_end:]

# ==============================================================================
# 5. TEMPLATE 5: insilos_solutions_page (AI-Enhanced ERP)
# ==============================================================================
print("Transforming 5. insilos_solutions_page...")

# Main wrap
content = content.replace(
    '<template id="insilos_solutions_page" name="AI-Enhanced ERP | INNORIA">\n        <t t-call="website.layout" no_header="True" no_footer="True">\n            <t t-call="insilos_website.innoria_navbar"/>\n            <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="--innoria-dark-canvas:#111827;--innoria-card:#1F2937;--innoria-cyan:#0ABBDB;--innoria-orange:#FF8000;--innoria-yellow:#F59E0B;background-color:var(--innoria-dark-canvas);color:#F9FAFB;">',
    '<template id="insilos_solutions_page" name="AI-Enhanced ERP | INNORIA">\n        <t t-call="website.layout" no_header="True" no_footer="True">\n            <t t-call="insilos_website.innoria_navbar"/>\n            <main id="wrap" class="oe_structure o_colored_level" style="--innoria-canvas:#FFFFFF;--innoria-card:#FFFFFF;--innoria-cyan:#0ABBDB;--innoria-orange:#FF8000;background-color:#FFFFFF;color:#0F172A;">'
)

sol_start = content.find('<template id="insilos_solutions_page"')
sol_end = content.find('</template>\n\n    <template id="insilos_industries_page"')
sol_block = content[sol_start:sol_end]

sol_block = sol_block.replace(
    'style="background:radial-gradient(circle at 85% 10%,rgba(10,187,219,.22),transparent 30%),radial-gradient(circle at 10% 60%,rgba(255,128,0,.12),transparent 30%),#111827;"',
    'style="background:radial-gradient(circle at 85% 10%,rgba(10,187,219,.15),transparent 35%),radial-gradient(circle at 10% 60%,rgba(255,128,0,.08),transparent 30%),#FFFFFF;"'
)
sol_block = sol_block.replace('background:rgba(10,187,219,.16);color:#0ABBDB;border:1px solid #0ABBDB;', 'background:#E0F2FE;color:#0369A1;border:1px solid #BAE6FD;')
sol_block = sol_block.replace('background:#1F2937;border-left:4px solid #FF8000;', 'background:#FFFFFF;border:1px solid #E2E8F0;border-left:4px solid #FF8000;box-shadow:0 10px 30px rgba(255,128,0,.08);color:#334155;')
sol_block = sol_block.replace('btn-outline-light', 'btn-outline-primary" style="border-color:#0284C7;color:#0284C7;background:#FFFFFF;')
# Copilot simulator
sol_block = sol_block.replace('background:#1F2937;border:1px solid rgba(10,187,219,.45);', 'background:#FFFFFF;border:1px solid #E2E8F0;box-shadow:0 20px 40px rgba(2,132,199,.08);')
sol_block = sol_block.replace('border-bottom:1px solid #374151;', 'border-bottom:1px solid #E2E8F0;')
sol_block = sol_block.replace('background:#374151;', 'background:#F1F5F9;color:#0F172A;')
sol_block = sol_block.replace('background:rgba(10,187,219,.12);border:1px solid rgba(10,187,219,.3);', 'background:#F0F9FF;border:1px solid #BAE6FD;color:#0F172A;')
sol_block = sol_block.replace('background:#111827;border:1px solid #4B5563;color:#9CA3AF;', 'background:#FFFFFF;border:1px solid #CBD5E1;color:#64748B;')
# Dark cards in solutions
sol_block = sol_block.replace('background:#1F2937;', 'background:#FFFFFF;border:1px solid #E2E8F0;')
sol_block = sol_block.replace('background:#111827;', 'background:#F8FAFC;')
sol_block = sol_block.replace('text-white-50', 'text-muted')
sol_block = sol_block.replace('text-white', 'text-dark')

content = content[:sol_start] + sol_block + content[sol_end:]

# ==============================================================================
# 6. TEMPLATE 6: insilos_industries_page (Ultra AI Vision)
# ==============================================================================
print("Transforming 6. insilos_industries_page...")

# Main wrap
content = content.replace(
    '<template id="insilos_industries_page" name="Ultra AI Vision &amp; Industries | INNORIA">\n        <t t-call="website.layout" no_header="True" no_footer="True">\n            <t t-call="insilos_website.innoria_navbar"/>\n            <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="background-color: var(--innoria-dark-canvas, #111827); color: #f9fafb;">',
    '<template id="insilos_industries_page" name="Ultra AI Vision &amp; Industries | INNORIA">\n        <t t-call="website.layout" no_header="True" no_footer="True">\n            <t t-call="insilos_website.innoria_navbar"/>\n            <main id="wrap" class="oe_structure o_colored_level" style="background-color: #FFFFFF; color: #0F172A;">'
)

ind_start = content.find('<template id="insilos_industries_page"')
ind_end = content.find('</template>\n\n    <template id="innoria_contactus"')
ind_block = content[ind_start:ind_end]

ind_block = ind_block.replace(
    'style="background: radial-gradient(circle at 80% 15%, rgba(10,187,219,.22), transparent 30%), radial-gradient(circle at 10% 85%, rgba(255,128,0,.13), transparent 28%), #111827;"',
    'style="background: radial-gradient(circle at 80% 15%, rgba(10,187,219,.15), transparent 35%), radial-gradient(circle at 10% 85%, rgba(255,128,0,.08), transparent 30%), #FFFFFF;"'
)
ind_block = ind_block.replace('border: 1px solid rgba(0,240,255,.5); background: rgba(0,240,255,.08); color: #00F0FF;', 'border: 1px solid #BAE6FD; background: #E0F2FE; color: #0369A1;')
ind_block = ind_block.replace('background:#1F2937;border-left:4px solid #FF8000;', 'background:#FFFFFF;border:1px solid #E2E8F0;border-left:4px solid #FF8000;box-shadow:0 10px 30px rgba(255,128,0,.08);color:#334155;')
ind_block = ind_block.replace('background:#1F2937;border:1px solid rgba(0,240,255,.45);box-shadow:0 0 45px rgba(10,187,219,.18);', 'background:#FFFFFF;border:1px solid #E2E8F0;box-shadow:0 20px 40px rgba(10,187,219,.1);')
ind_block = ind_block.replace('background:rgba(17,24,39,.9);border:1px solid #00F0FF;color:#00F0FF;', 'background:rgba(255,255,255,.95);border:1px solid #0284C7;color:#0284C7;')
ind_block = ind_block.replace('background:rgba(17,24,39,.92);border:1px solid rgba(255,255,255,.15);', 'background:rgba(255,255,255,.95);border:1px solid #E2E8F0;color:#0F172A;')
ind_block = ind_block.replace('background:#1F2937;', 'background:#FFFFFF;border:1px solid #E2E8F0;')
ind_block = ind_block.replace('background:#111827;', 'background:#F8FAFC;')
ind_block = ind_block.replace('text-white-50', 'text-muted')
ind_block = ind_block.replace('text-white', 'text-dark')

content = content[:ind_start] + ind_block + content[ind_end:]

# ==============================================================================
# 7. TEMPLATE 7: innoria_contactus (Contact Us)
# ==============================================================================
print("Transforming 7. innoria_contactus...")

# Main wrap
content = content.replace(
    '<template id="innoria_contactus" name="Contact Us | INNORIA">\n    <t t-call="website.layout" no_header="True" no_footer="True">\n        <t t-call="insilos_website.innoria_navbar"/>\n\n        <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="--innoria-dark-canvas: #111827; --innoria-card: #1F2937; --innoria-cyan: #0ABBDB; --innoria-orange: #FF8000; --innoria-mint: #B2FFDA; background-color: var(--innoria-dark-canvas); color: #F9FAFB; font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; overflow-x: hidden;">',
    '<template id="innoria_contactus" name="Contact Us | INNORIA">\n    <t t-call="website.layout" no_header="True" no_footer="True">\n        <t t-call="insilos_website.innoria_navbar"/>\n\n        <main id="wrap" class="oe_structure o_colored_level" style="--innoria-canvas: #FFFFFF; --innoria-card: #FFFFFF; --innoria-cyan: #0ABBDB; --innoria-orange: #FF8000; background-color: #FFFFFF; color: #0F172A; font-family: \'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; overflow-x: hidden;">'
)

# Style
old_contact_style = """                :root {
                    --inn-canvas: #111827;
                    --inn-card: #1F2937;
                    --inn-card-hover: #263345;
                    --inn-cyan: #0ABBDB;
                    --inn-cyan-glow: rgba(10, 187, 219, 0.25);
                    --inn-orange: #FF8000;
                    --inn-orange-glow: rgba(255, 128, 0, 0.25);
                    --inn-mint: #B2FFDA;
                    --inn-mint-glow: rgba(178, 255, 218, 0.25);
                    --inn-border: rgba(255, 255, 255, 0.09);
                    --inn-text-muted: #9CA3AF;
                    --inn-text-light: #D1D5DB;
                }
                .inn-hero-gradient {
                    background: radial-gradient(circle at 82% 12%, rgba(10, 187, 219, 0.22), transparent 38%),
                                radial-gradient(circle at 14% 78%, rgba(255, 128, 0, 0.15), transparent 35%),
                                radial-gradient(circle at 50% 50%, rgba(17, 24, 39, 0.8), #111827);
                }
                .inn-glass-card {
                    background: rgba(31, 41, 55, 0.82);
                    backdrop-filter: blur(16px);
                    -webkit-backdrop-filter: blur(16px);
                    border: 1px solid var(--inn-border);
                    border-radius: 1.25rem;
                    transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
                }
                .inn-glass-card:hover {
                    border-color: rgba(10, 187, 219, 0.45);
                    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4);
                }
                .inn-blueprint-card {
                    background: #1F2937;
                    border: 1px solid var(--inn-border);
                    border-radius: 1.25rem;
                    transition: transform 0.25s ease, border-color 0.25s ease;
                    position: relative;
                    overflow: hidden;
                }
                .inn-blueprint-card:hover {
                    transform: translateY(-6px);
                    border-color: rgba(10, 187, 219, 0.6);
                }
                .inn-blueprint-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                }
                .inn-border-cyan::before { background: linear-gradient(90deg, #0ABBDB, transparent); }
                .inn-border-orange::before { background: linear-gradient(90deg, #FF8000, transparent); }
                .inn-border-mint::before { background: linear-gradient(90deg, #B2FFDA, transparent); }
                
                .inn-input-dark {
                    background-color: #16202E !important;
                    border: 1px solid rgba(255, 255, 255, 0.14) !important;
                    color: #FFFFFF !important;
                    border-radius: 0.75rem !important;
                    padding: 0.85rem 1.15rem !important;
                    font-size: 0.975rem !important;
                    transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease !important;
                }
                .inn-input-dark:focus {
                    background-color: #1A2638 !important;
                    border-color: var(--inn-cyan) !important;
                    box-shadow: 0 0 0 4px rgba(10, 187, 219, 0.2) !important;
                    outline: none !important;
                }
                .inn-input-dark::placeholder {
                    color: #6B7280 !important;
                }
                .inn-badge-pulse {
                    position: relative;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    padding: 0.45rem 1.1rem;
                    border-radius: 9999px;
                    font-size: 0.825rem;
                    font-weight: 700;
                    letter-spacing: 0.04em;
                    text-transform: uppercase;
                    background: rgba(178, 255, 218, 0.12);
                    border: 1px solid rgba(178, 255, 218, 0.35);
                    color: #B2FFDA;
                }"""

new_contact_style = """                :root {
                    --inn-canvas: #FFFFFF;
                    --inn-card: #FFFFFF;
                    --inn-card-hover: #F0F9FF;
                    --inn-cyan: #0ABBDB;
                    --inn-cyan-glow: rgba(10, 187, 219, 0.15);
                    --inn-orange: #FF8000;
                    --inn-orange-glow: rgba(255, 128, 0, 0.15);
                    --inn-mint: #0284C7;
                    --inn-mint-glow: rgba(2, 132, 199, 0.15);
                    --inn-border: #E2E8F0;
                    --inn-text-muted: #64748B;
                    --inn-text-light: #334155;
                }
                .inn-hero-gradient {
                    background: radial-gradient(circle at 82% 12%, rgba(10, 187, 219, 0.15), transparent 45%),
                                radial-gradient(circle at 14% 78%, rgba(255, 128, 0, 0.08), transparent 40%),
                                linear-gradient(180deg, #FFFFFF 0%, #F0F9FF 50%, #F8FAFC 100%);
                }
                .inn-glass-card {
                    background: #FFFFFF;
                    border: 1px solid var(--inn-border);
                    border-radius: 1.25rem;
                    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
                    transition: transform 0.28s ease, border-color 0.28s ease, box-shadow 0.28s ease;
                }
                .inn-glass-card:hover {
                    border-color: #0ABBDB;
                    box-shadow: 0 16px 40px rgba(10, 187, 219, 0.15);
                }
                .inn-blueprint-card {
                    background: #FFFFFF;
                    border: 1px solid var(--inn-border);
                    border-radius: 1.25rem;
                    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
                    transition: transform 0.25s ease, border-color 0.25s ease;
                    position: relative;
                    overflow: hidden;
                }
                .inn-blueprint-card:hover {
                    transform: translateY(-6px);
                    border-color: #0ABBDB;
                    box-shadow: 0 16px 40px rgba(10, 187, 219, 0.15);
                }
                .inn-blueprint-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                }
                .inn-border-cyan::before { background: linear-gradient(90deg, #0ABBDB, transparent); }
                .inn-border-orange::before { background: linear-gradient(90deg, #FF8000, transparent); }
                .inn-border-mint::before { background: linear-gradient(90deg, #0284C7, transparent); }
                
                .inn-input-dark {
                    background-color: #FFFFFF !important;
                    border: 1px solid #CBD5E1 !important;
                    color: #0F172A !important;
                    border-radius: 0.75rem !important;
                    padding: 0.85rem 1.15rem !important;
                    font-size: 0.975rem !important;
                    transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease !important;
                }
                .inn-input-dark:focus {
                    background-color: #FFFFFF !important;
                    border-color: #0284C7 !important;
                    box-shadow: 0 0 0 4px rgba(2, 132, 199, 0.15) !important;
                    outline: none !important;
                }
                .inn-input-dark::placeholder {
                    color: #94A3B8 !important;
                }
                .inn-badge-pulse {
                    position: relative;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    padding: 0.45rem 1.1rem;
                    border-radius: 9999px;
                    font-size: 0.825rem;
                    font-weight: 700;
                    letter-spacing: 0.04em;
                    text-transform: uppercase;
                    background: #E0F2FE;
                    border: 1px solid #BAE6FD;
                    color: #0369A1;
                }"""

content = content.replace(old_contact_style, new_contact_style)

# Scope changes in contactus
cnt_start = content.find('<template id="innoria_contactus"')
cnt_block = content[cnt_start:]
cnt_block = cnt_block.replace('text-white-50', 'text-muted')
cnt_block = cnt_block.replace('text-white', 'text-dark')
cnt_block = cnt_block.replace('background: #111827;', 'background: #FFFFFF;')
cnt_block = cnt_block.replace('background:#111827;', 'background:#FFFFFF;')
cnt_block = cnt_block.replace('background: #1F2937;', 'background: #FFFFFF; border: 1px solid #E2E8F0;')
cnt_block = cnt_block.replace('background:#1F2937;', 'background:#FFFFFF; border: 1px solid #E2E8F0;')
content = content[:cnt_start] + cnt_block

# XML Validation
ET.fromstring(content)
print("XML validation passed for all 7 templates in innoria_pages.xml!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("enterprise/insilos_website/views/innoria_pages.xml updated successfully!")
