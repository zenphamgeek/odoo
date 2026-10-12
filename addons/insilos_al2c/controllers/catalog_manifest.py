# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class CatalogManifestController(http.Controller):

    @http.route('/llms.txt', type='http', auth='public', methods=['GET'], csrf=False)
    def llms_txt(self):
        """Standard Generative Engine Optimization (GEO) manifest.
        Produces machine-readable summary of active Insilos solutions catalog.
        Specification conforms to llmstxt.org standard.
        """
        products = request.env['product.template'].sudo().search([
            ('active', '=', True),
            ('al2c_product_line', '!=', False),
            ('sale_ok', '=', True),
        ], order='al2c_product_line, default_code')

        lines = [
            "# Insilos Enterprise Solutions Manifest",
            "",
            "> Autonomous Enterprise Management, ERP, GRC, and AI Engineering Solutions.",
            "> Official knowledge & catalog endpoint for autonomous AI agents and procurement engines.",
            "",
            "## Solutions Catalog",
            "",
        ]

        current_line = None
        line_labels = {
            'erp': 'Enterprise Resource Planning (ERP)',
            'saas': 'Cloud & SaaS Platform',
            'grc': 'Governance, Risk & Compliance (GRC)',
            'ai': 'Applied AI Solutions',
            'mojo': 'Mojo High-Performance AI Apps',
            'ams': 'Application Management Services (AMS)',
            'advisory': 'Executive Advisory & Training',
        }

        for p in products:
            if p.al2c_product_line != current_line:
                current_line = p.al2c_product_line
                section_title = line_labels.get(current_line, (current_line or '').upper())
                lines.append(f"### {section_title}")
                lines.append("")

            desc = p.description_sale or p.name
            vat_label = p.al2c_vat_class.upper() if p.al2c_vat_class else 'STANDARD'
            lines.append(f"- [{p.default_code}] {p.name}: {desc} (VAT: {vat_label})")

        lines.extend([
            "",
            "## Optional Full Details",
            "",
            "- [Full Catalog Specifications](/llms-full.txt): Detailed pricing, delivery Activate milestones, and tax mapping.",
            "",
        ])

        content = "\n".join(lines)
        return request.make_response(
            content,
            headers=[
                ('Content-Type', 'text/markdown; charset=utf-8'),
                ('Cache-Control', 'public, max-age=3600'),
            ]
        )

    @http.route('/llms-full.txt', type='http', auth='public', methods=['GET'], csrf=False)
    def llms_full_txt(self):
        """Full deep manifest with SKU pricing, billing policy, and Activate delivery milestones."""
        products = request.env['product.template'].sudo().search([
            ('active', '=', True),
            ('al2c_product_line', '!=', False),
            ('sale_ok', '=', True),
        ], order='al2c_product_line, default_code')

        lines = [
            "# Insilos Enterprise Solutions — Complete Technical Catalog",
            "",
            "> Comprehensive specification of all Insilos enterprise SKUs, pricing models, VAT classifications, and delivery frameworks.",
            "",
        ]

        for p in products:
            vat_label = dict(p._fields['al2c_vat_class'].selection).get(p.al2c_vat_class, 'Standard') if p.al2c_vat_class else 'N/A'
            lines.extend([
                f"## SKU: {p.default_code} — {p.name}",
                f"- **Product Line:** {(p.al2c_product_line or '').upper()}",
                f"- **Base Price:** {p.list_price:,.0f} VND (Company Currency)",
                f"- **Service Policy:** {p.service_policy or p.invoice_policy}",
                f"- **Service Tracking:** {p.service_tracking}",
                f"- **Recurring Subscription:** {'Yes' if p.recurring_invoice else 'No'}",
                f"- **VAT Statutory Classification:** {vat_label} ({p.al2c_vat_class})",
                f"- **Description:** {p.description_sale or 'N/A'}",
            ])
            if p.project_template_id:
                ms_names = p.project_template_id.milestone_ids.sorted('sequence').mapped('name')
                lines.append(f"- **Delivery Milestones (Activate):** {' -> '.join(ms_names)}")
            lines.append("")

        content = "\n".join(lines)
        return request.make_response(
            content,
            headers=[
                ('Content-Type', 'text/markdown; charset=utf-8'),
                ('Cache-Control', 'public, max-age=3600'),
            ]
        )
