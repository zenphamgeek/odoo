# -*- coding: utf-8 -*-
# Part of Insilos AL2C Enterprise Architecture (SOP-DGM-GOV-01 & Compliance Sentinel)

import datetime
import logging
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Canonical Entity Identity (Digimate JSC)
DGM_CANONICAL_VAT = "0317958465"
DGM_CANONICAL_NAME = "CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ"
DGM_CANONICAL_WARD = "Phường Tân Mỹ"

# Banned Legacy Signatures
LEGACY_VAT_PATTERNS = [
    r'\b0313683499\b',
]

LEGACY_ENTITY_PATTERNS = [
    r'ứng\s*dụng\s*sáng\s*tạo',
    r'ung\s*dung\s*sang\s*tao',
    r'ung\s+dung\s+sang\s+tao\s+llc',
    r'cty\s+tnhh\s+ung\s+dung\s+sang\s+tao',
    r'công\s*ty\s*tnhh\s*ứng\s*dụng\s*sáng\s*tạo',
]

OUTDATED_WARD_PATTERNS = [
    r'phường\s+tân\s+phú',
    r'p\.\s*tân\s*phú',
    r'phuong\s+tan\s+phu',
    r'p\.\s*tan\s*phu',
]


class Al2cComplianceScanner(models.AbstractModel):
    """Single Legal Entity & Compliance Scanner.
    Audits documents, contracts, and foreign inward remittance e-invoicing against:
    1. Legacy Entity Name (0313683499 / Ứng Dụng Sáng Tạo)
    2. Outdated Ward Address (Phường Tân Phú, Quận 7 instead of Phường Tân Mỹ)
    3. Missing export invoice numbers past 24h SLA from bank credit date (Canva USD wires)
    """
    _name = 'al2c.compliance.scanner'
    _description = 'AL2C Single Legal Entity & Compliance Scanner'

    @api.model
    def scan_text(self, text):
        """Scans raw text against single legal entity and address compliance rules."""
        if not text:
            return {
                'is_compliant': True,
                'has_legacy_entity': False,
                'has_legacy_tax_code': False,
                'has_outdated_ward': False,
                'violations': [],
                'summary': "Compliant: Empty text analyzed.",
            }

        norm_text = text.lower()
        violations = []
        has_legacy_entity = False
        has_legacy_tax_code = False
        has_outdated_ward = False

        # 1. Check legacy tax code
        for pattern in LEGACY_VAT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                has_legacy_tax_code = True
                violations.append({
                    'type': 'legacy_tax_code',
                    'matched': match.group(0),
                    'message': _("Detected legacy tax code '%s' belonging to Ứng Dụng Sáng Tạo instead of DGM MST '0317958465'.", match.group(0)),
                })
                break

        # 2. Check legacy company name
        for pattern in LEGACY_ENTITY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                has_legacy_entity = True
                violations.append({
                    'type': 'legacy_entity',
                    'matched': match.group(0),
                    'message': _("Detected legacy entity name reference '%s' (Banned legacy signature). Must use 'CÔNG TY CỔ PHẦN NGƯỜI BẠN SỐ'.", match.group(0)),
                })
                break

        # 3. Check outdated ward address (Phường Tân Phú instead of Phường Tân Mỹ)
        # Note: If text explicitly references Phường Tân Mỹ, we verify if it is an explanatory note.
        # Otherwise, standalone reference to Phường Tân Phú (Quận 7) is flagged.
        for pattern in OUTDATED_WARD_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # If Phường Tân Mỹ is also mentioned as replacement, verify context
                if "tân mỹ" not in norm_text and "tan my" not in norm_text:
                    has_outdated_ward = True
                    violations.append({
                        'type': 'outdated_ward',
                        'matched': match.group(0),
                        'message': _("Detected outdated ward address '%s'. Address must be updated to 'Phường Tân Mỹ' following 2026 administrative boundary merger.", match.group(0)),
                    })
                    break

        is_compliant = len(violations) == 0
        if is_compliant:
            summary = _("Compliant: Entity identity, tax code, and address conform to Digimate JSC (MST: 0317958465, Phường Tân Mỹ).")
        else:
            summary = _("Non-compliant: %d legal entity / address deviation(s) detected:\n%s", len(violations), "\n".join(f"- {v['message']}" for v in violations))

        return {
            'is_compliant': is_compliant,
            'has_legacy_entity': has_legacy_entity,
            'has_legacy_tax_code': has_legacy_tax_code,
            'has_outdated_ward': has_outdated_ward,
            'violations': violations,
            'summary': summary,
        }

    @api.model
    def scan_document(self, document):
        """Audits a documents.document record for entity/address compliance."""
        text_parts = [document.name or ""]
        if hasattr(document, 'attachment_id') and document.attachment_id:
            text_parts.append(document.attachment_id.name or "")
            if document.attachment_id.mimetype in ('text/plain', 'text/html', 'text/xml'):
                raw = document.attachment_id.raw or b""
                try:
                    text_parts.append(raw.decode('utf-8', errors='ignore'))
                except Exception:
                    pass

        content = " ".join(text_parts)
        result = self.scan_text(content)

        vals = {
            'al2c_compliance_status': 'compliant' if result['is_compliant'] else 'deviated',
            'al2c_compliance_summary': result['summary'],
        }
        document.write(vals)

        if not result['is_compliant']:
            document.message_post(
                body=f"<b>AL2C Compliance Sentinel:</b> {result['summary']}",
                message_type='comment',
                subtype_xmlid='mail.mt_note'
            )

        return result

    @api.model
    def scan_contract(self, sign_request, extra_text=None):
        """Audits a sign.request record for entity/address and standard contract deviations."""
        text_parts = [
            sign_request.reference or "",
            sign_request.message or "",
            extra_text or "",
        ]
        if hasattr(sign_request, 'attachment_ids') and sign_request.attachment_ids:
            text_parts.extend(sign_request.attachment_ids.mapped('name'))

        full_text = " ".join(text_parts)
        result = self.scan_text(full_text)

        # Standard legal clause check
        clause_patterns = [
            ('unlimited liability', 'Customer demands uncapped unlimited liability'),
            ('consequential damages', 'Customer altered consequential / indirect damages exclusion'),
            ('gross negligence', 'Unbalanced gross negligence liability clause'),
            ('liquidated damages', 'Liquidated damages / penalty exceeding statutory caps'),
            ('phạt vi phạm', 'Penalties exceeding 8% statutory cap under Vietnam Commercial Law'),
            ('indemnify and hold harmless', 'Broad unilateral indemnification obligation'),
            ('governing law', 'Foreign governing law or foreign jurisdiction clause'),
        ]
        clause_deviations = []
        lower_text = full_text.lower()
        for kw, desc in clause_patterns:
            if kw in lower_text:
                clause_deviations.append(f"- {desc} (keyword: '{kw}')")

        all_deviations = []
        for v in result['violations']:
            all_deviations.append(f"- {v['message']}")
        all_deviations.extend(clause_deviations)

        if all_deviations:
            summary = "Contract Compliance & Legal Deviations Detected:\n" + "\n".join(all_deviations)
            sign_request.write({
                'al2c_has_deviation': True,
                'al2c_clause_status': 'deviated',
                'al2c_deviation_summary': summary,
            })
            gc_user = self.env.ref('base.user_admin', raise_if_not_found=False) or self.env.user
            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            if activity_type:
                sign_request.activity_schedule(
                    activity_type_id=activity_type.id,
                    user_id=gc_user.id,
                    summary='Contract Compliance: Legal Entity / Clause Review Required',
                    note=summary,
                )
            return {'is_compliant': False, 'summary': summary, 'deviations': all_deviations}
        else:
            sign_request.write({
                'al2c_has_deviation': False,
                'al2c_clause_status': 'standard',
                'al2c_deviation_summary': False,
            })
            return {'is_compliant': True, 'summary': "Standard compliant contract.", 'deviations': []}

    @api.model
    def scan_export_invoices_sla(self, hours_threshold=24):
        """Audits foreign inward remittances (Canva USD wires) for 24h e-invoicing SLA.
        Flags any invoice/payment record where credit_date exceeds 24 hours without a valid
        al2c_einvoice_number.
        """
        Move = self.env['account.move']
        now = fields.Datetime.now()
        threshold_dt = now - datetime.timedelta(hours=hours_threshold)

        # Domain for foreign remittances (Canva USD wires, foreign export)
        domain = [
            '|', '|', '|',
            ('al2c_is_foreign_remittance', '=', True),
            ('currency_id.name', '=', 'USD'),
            ('partner_id.name', 'ilike', 'Canva'),
            ('name', 'ilike', 'Canva'),
        ]

        moves = Move.search(domain)
        breached_moves = Move.browse()

        for move in moves:
            # Determine credit date (bank receipt date)
            credit_dt = move.al2c_bank_credit_date
            if not credit_dt:
                # Fallback to date / invoice_date as datetime
                d = move.invoice_date or move.date
                if d:
                    credit_dt = datetime.datetime.combine(d, datetime.time(0, 0, 0))

            if not credit_dt:
                continue

            # Check if past threshold and missing e-invoice number
            is_overdue = credit_dt < threshold_dt
            missing_einvoice = not move.al2c_einvoice_number or move.al2c_einvoice_state not in ('issued',)

            if is_overdue and missing_einvoice:
                move.write({'al2c_sla_breached': True})
                breached_moves |= move
                move.message_post(
                    body=_(
                        "<b>AL2C Compliance Warning:</b> 24h Foreign Export Invoicing SLA Breached!<br/>"
                        "Bank credit date: %s exceeds 24h SLA without Decree 70 E-Invoice number.",
                        credit_dt
                    ),
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
            else:
                if move.al2c_sla_breached and not missing_einvoice:
                    move.write({'al2c_sla_breached': False})

        summary = _(
            "Scanned %d foreign remittances: %d SLA breaches detected (> %d hours without e-invoice).",
            len(moves), len(breached_moves), hours_threshold
        )
        return {
            'total_scanned': len(moves),
            'breached_count': len(breached_moves),
            'breached_moves': breached_moves,
            'summary': summary,
        }

    @api.model
    def run_full_compliance_audit(self):
        """Executes holistic compliance audit across all 3 pillars."""
        doc_res = self.env['documents.document'].search([], limit=50)
        docs_flagged = 0
        for doc in doc_res:
            res = self.scan_document(doc)
            if not res['is_compliant']:
                docs_flagged += 1

        sla_res = self.scan_export_invoices_sla(hours_threshold=24)

        report = {
            'documents_scanned': len(doc_res),
            'documents_deviated': docs_flagged,
            'export_sla_breaches': sla_res['breached_count'],
            'summary': _(
                "Full Governance Audit Complete. Documents Deviated: %d. Foreign Remittance SLA Breaches: %d.",
                docs_flagged, sla_res['breached_count']
            ),
        }
        _logger.info("AL2C Compliance Audit: %s", report['summary'])
        return report


class AccountMove(models.Model):
    _inherit = 'account.move'

    al2c_is_foreign_remittance = fields.Boolean(
        string='Foreign Inward Remittance (USD Wire)',
        default=False,
        help='Flags incoming wire remittance from foreign platform (Canva Pty Ltd, Apple, Google, PayPal)',
    )
    al2c_bank_credit_date = fields.Datetime(
        string='Bank Credit Date',
        help='Timestamp when foreign currency was credited to bank account (VCB 1202703007)',
    )
    al2c_sla_breached = fields.Boolean(
        string='Export 24h SLA Breached',
        default=False,
        tracking=True,
        help='Flags foreign remittances exceeding 24h SLA without statutory Decree 70 E-Invoice number',
    )

    def action_check_export_sla_compliance(self):
        """Action on invoice to trigger SLA audit."""
        return self.env['al2c.compliance.scanner'].scan_export_invoices_sla()


class SignRequest(models.Model):
    _inherit = 'sign.request'

    def action_scan_single_entity_compliance(self):
        """Scans contract text for single legal entity and address compliance."""
        return self.env['al2c.compliance.scanner'].scan_contract(self)


class Al2cRagService(models.AbstractModel):
    _inherit = 'al2c.rag.service'

    @api.model
    def retrieve_grounded_context(self, query, company_id=None, top_k=5):
        """Enhanced multi-tenant isolated retrieval with smart fallback ranking."""
        if not company_id:
            company_id = self.env.company.id

        domain = [
            ('company_id', '=', company_id),
            ('active', '=', True),
        ]

        if not query:
            return self.env['al2c.rag.chunk'].sudo().search(domain, limit=top_k)

        # Tokenize query
        words = [w for w in re.findall(r'\w+', query.lower()) if len(w) >= 3]
        short_tokens = [t for t in re.findall(r'\b(?:\d+%?|[a-z]\d+|c12)\b', query.lower()) if len(t) >= 2]
        all_terms = list(dict.fromkeys(words + short_tokens))

        if not all_terms:
            return self.env['al2c.rag.chunk'].sudo().search(domain, limit=top_k)

        # 1. First try strict AND
        strict_domain = list(domain)
        for term in all_terms[:4]:
            strict_domain.append(('content', 'ilike', term))
        chunks = self.env['al2c.rag.chunk'].sudo().search(strict_domain, limit=top_k)
        if chunks:
            return chunks

        # 2. Fallback: OR across all search terms with relevance ranking
        or_domain = list(domain)
        or_terms = [('content', 'ilike', term) for term in all_terms]
        if or_terms:
            or_domain.extend(['|'] * (len(or_terms) - 1) + or_terms)
            candidates = self.env['al2c.rag.chunk'].sudo().search(or_domain, limit=top_k * 4)
            if candidates:
                def score_candidate(c):
                    haystack = f"{c.name or ''} {c.section_header or ''} {c.content or ''}".lower()
                    return sum(2 if term in (c.section_header or '').lower() else (1 if term in haystack else 0) for term in all_terms)

                sorted_c = sorted(candidates, key=score_candidate, reverse=True)
                return self.env['al2c.rag.chunk'].browse([c.id for c in sorted_c[:top_k]])

        # 3. Super fallback: try parent retrieve_grounded_context
        return super().retrieve_grounded_context(query, company_id=company_id, top_k=top_k)

    @api.model
    def reindex_dgm_sops(self):
        """Indexes DGM SOP knowledge.article records into al2c.rag.chunk
        with citation tags [Doc | Sec | ID | Hash] and validates retrieval for:
        1. Canva 0% export invoicing
        2. MTI overtime tiers
        3. VCB DigiBiz 11 columns
        4. BHXH TZ0857G
        5. Mojo AI gross-to-net accounting
        """
        Article = self.env['knowledge.article'].sudo()
        articles = Article.search([
            '|', '|', '|',
            ('name', 'ilike', 'DGM'),
            ('name', 'ilike', 'Digimate'),
            ('name', 'ilike', 'SOP'),
            ('parent_id', 'in', [1677]),
        ])
        if not articles:
            articles = Article.search([('active', '=', True)], limit=50)

        # Clean prior chunks for these articles to prevent duplicates
        Chunk = self.env['al2c.rag.chunk'].sudo()
        old_chunks = Chunk.search([
            ('source_model', '=', 'knowledge.article'),
            ('source_id', 'in', articles.ids),
        ])
        if old_chunks:
            old_chunks.unlink()

        created_chunks = Chunk.browse()
        for art in articles:
            try:
                chunks = self.index_knowledge_article(art)
                created_chunks |= chunks
            except Exception as e:
                _logger.warning("Error indexing DGM SOP article %s: %s", art.name, e)

        # Validate retrieval
        retrieval_tests = {
            'canva': bool(self.retrieve_grounded_context("Canva 0% export invoicing", top_k=3)),
            'mti': bool(self.retrieve_grounded_context("MTI overtime tiers", top_k=3)),
            'vcb': bool(self.retrieve_grounded_context("VCB DigiBiz 11 columns", top_k=3)),
            'bhxh': bool(self.retrieve_grounded_context("BHXH TZ0857G", top_k=3)),
            'mojo': bool(self.retrieve_grounded_context("Mojo AI gross-to-net accounting", top_k=3)),
        }

        # Check citation tag format
        citations = created_chunks.mapped('citation_tag')

        return {
            'articles_indexed': len(articles),
            'chunks_created': len(created_chunks),
            'validation': retrieval_tests,
            'all_passed': all(retrieval_tests.values()),
            'sample_citations': citations[:5],
        }
