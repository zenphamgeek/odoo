import re

BASE_DIR = "/home/zen/O20/enterprise/insilos_website/views"
path = f"{BASE_DIR}/snippets.xml"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

import sys
sys.path.append("/home/zen/O20/enterprise/insilos_website/tools")
from upgrade_3d_cockpit_heroes import make_cockpit_markup, CONFIGS

cockpit_html = make_cockpit_markup(CONFIGS['platform'])
# We need to wrap it in our snippet structure
snippet_html = f"""    <!-- Snippet 12: C3.ai 3D Cockpit Stack -->
    <template id="s_c3ai_3d_cockpit" name="C3.ai 3D Cockpit Stack">
        <section class="s_cover o_colored_level o_cc o_cc5 pt80 pb80 position-relative" data-snippet="s_cover" data-name="C3.ai 3D Cockpit Stack" data-bs-theme="dark">
            <div class="container py-lg-4 position-relative ins-hero-content-layer">
                <div class="row align-items-center g-5">
                    <div class="col-lg-6">
                        <div class="ins-pill-badge mb-3">
                            <span class="ins-live-ping ins-live-ping--emerald"/>
                            <span>SOVEREIGN ARCHITECTURE</span>
                        </div>
                        <h2 class="display-4 fw-bold text-white mb-3">Trụ Cột Vận Hành Tự Chủ</h2>
                        <p class="lead text-secondary mb-4 col-lg-11 p-0">Mô hình kiến trúc 4 lớp của nền tảng Insilos.</p>
                    </div>
{cockpit_html}
                </div>
            </div>
        </section>
    </template>

    <!-- Snippet 12 Options -->
    <template id="s_c3ai_3d_cockpit_options" inherit_id="website.snippet_options">
        <xpath expr="." position="inside">
            <div data-selector=".ins-3d-cockpit-viewport">
                <we-row string="Layer 1">
                    <we-input string="Title" data-select-data-attribute="l1-title" data-attribute-default-value="Ingestion &amp; IDP Streaming"/>
                    <we-input string="Icon" data-select-data-attribute="l1-icon" data-attribute-default-value="plugs-connected"/>
                    <we-input string="Badge" data-select-data-attribute="l1-badge" data-attribute-default-value="100+ Connectors"/>
                    <we-input string="Desc" data-select-data-attribute="l1-desc" data-attribute-default-value="SAP, Oracle, Kafka Stream, IoT OPC-UA &amp; Scanned PDFs"/>
                    <we-input string="Metric" data-select-data-attribute="l1-metric" data-attribute-default-value="50.02 Hz · 12.4k pts/s"/>
                </we-row>
                <we-row string="Layer 2">
                    <we-input string="Title" data-select-data-attribute="l2-title" data-attribute-default-value="Knowledge Graph &amp; Digital Twin"/>
                    <we-input string="Icon" data-select-data-attribute="l2-icon" data-attribute-default-value="graph"/>
                    <we-input string="Badge" data-select-data-attribute="l2-badge" data-attribute-default-value="&lt; 15ms Query"/>
                    <we-input string="Desc" data-select-data-attribute="l2-desc" data-attribute-default-value="Entity Resolution, W3C OWL/RDF &amp; 1.4M Enterprise Triples"/>
                    <we-input string="Metric" data-select-data-attribute="l2-metric" data-attribute-default-value="1.4M Triples · Real-Time"/>
                </we-row>
                <we-row string="Layer 3">
                    <we-input string="Title" data-select-data-attribute="l3-title" data-attribute-default-value="Autonomous Operational Agents"/>
                    <we-input string="Icon" data-select-data-attribute="l3-icon" data-attribute-default-value="robot"/>
                    <we-input string="Badge" data-select-data-attribute="l3-badge" data-attribute-default-value="97.4% STP"/>
                    <we-input string="Desc" data-select-data-attribute="l3-desc" data-attribute-default-value="HS Classifier, FTA Matrix, 3D Packing &amp; Predictive FSM"/>
                    <we-input string="Metric" data-select-data-attribute="l3-metric" data-attribute-default-value="Sub-45s SLA Execution"/>
                </we-row>
                <we-row string="Layer 4">
                    <we-input string="Title" data-select-data-attribute="l4-title" data-attribute-default-value="Closed-Loop Execution &amp; Write-Back"/>
                    <we-input string="Icon" data-select-data-attribute="l4-icon" data-attribute-default-value="check-circle"/>
                    <we-input string="Badge" data-select-data-attribute="l4-badge" data-attribute-default-value="AUDIT VERIFIED"/>
                    <we-input string="Desc" data-select-data-attribute="l4-desc" data-attribute-default-value="ERP Write-Back, Cryptographic Dossier &amp; Human Gatekeeper"/>
                    <we-input string="Metric" data-select-data-attribute="l4-metric" data-attribute-default-value="Zero Drift Protection"/>
                </we-row>
            </div>
        </xpath>
    </template>
"""

# Now we need to modify the .ins-3d-cockpit-viewport div to include the data attributes
attrs = '''data-l1-title="Ingestion &amp; IDP Streaming" data-l1-icon="plugs-connected" data-l1-badge="100+ Connectors" data-l1-desc="SAP, Oracle, Kafka Stream, IoT OPC-UA &amp; Scanned PDFs" data-l1-metric="50.02 Hz · 12.4k pts/s" data-l2-title="Knowledge Graph &amp; Digital Twin" data-l2-icon="graph" data-l2-badge="&lt; 15ms Query" data-l2-desc="Entity Resolution, W3C OWL/RDF &amp; 1.4M Enterprise Triples" data-l2-metric="1.4M Triples · Real-Time" data-l3-title="Autonomous Operational Agents" data-l3-icon="robot" data-l3-badge="97.4% STP" data-l3-desc="HS Classifier, FTA Matrix, 3D Packing &amp; Predictive FSM" data-l3-metric="Sub-45s SLA Execution" data-l4-title="Closed-Loop Execution &amp; Write-Back" data-l4-icon="check-circle" data-l4-badge="AUDIT VERIFIED" data-l4-desc="ERP Write-Back, Cryptographic Dossier &amp; Human Gatekeeper" data-l4-metric="Zero Drift Protection"'''

snippet_html = snippet_html.replace('<div class="ins-3d-cockpit-viewport">', f'<div class="ins-3d-cockpit-viewport" {attrs}>')

# Inject before the 2. INHERIT WEBSITE SNIPPETS PALETTE
content = content.replace('<!-- ================================================================= -->\n    <!-- 2. INHERIT', snippet_html + '\n    <!-- ================================================================= -->\n    <!-- 2. INHERIT')

# Append to xpath
content = content.replace('</xpath>', '    <t t-snippet="insilos_website.s_c3ai_3d_cockpit" string="C3.ai 3D Cockpit Stack" group="content"/>\n        </xpath>')

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
