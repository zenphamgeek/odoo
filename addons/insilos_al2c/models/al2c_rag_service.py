# -*- coding: utf-8 -*-
# Part of Insilos AL2C Enterprise Architecture (SOP-RAG-003 & SOP-AI-004)

import hashlib
import logging
import math
import re
from odoo import models, fields, api, _
from odoo.tools import html2plaintext
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)


class Al2cRagChunk(models.Model):
    """Stores authoritative chunked knowledge for hybrid retrieval and grounding."""
    _name = 'al2c.rag.chunk'
    _description = 'AL2C Enterprise RAG Knowledge Chunk'
    _order = 'source_model, source_id, chunk_seq asc'

    name = fields.Char(string='Chunk Reference', required=True, index=True)
    source_model = fields.Char(string='Source Model', required=True, index=True, default='knowledge.article')
    source_id = fields.Integer(string='Source Record ID', required=True, index=True)
    source_ref = fields.Char(string='Source Path / URI', index=True)
    section_header = fields.Char(string='Breadcrumb / Section Header', index=True)
    chunk_seq = fields.Integer(string='Chunk Sequence', default=0)
    content = fields.Text(string='Chunk Content', required=True)
    chunk_hash = fields.Char(string='SHA-256 Hash', size=64, required=True, index=True)
    token_count = fields.Integer(string='Approx Token Count', default=0)
    has_table = fields.Boolean(string='Contains Markdown Table', default=False)
    citation_tag = fields.Char(string='Citation Tag', compute='_compute_citation_tag', store=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.depends('name', 'section_header', 'source_id', 'chunk_hash')
    def _compute_citation_tag(self):
        for record in self:
            doc_label = record.name or f"DOC-{record.source_id}"
            sec_label = record.section_header or "General"
            hash_abbr = (record.chunk_hash or "00000000")[:8]
            record.citation_tag = f"[{doc_label} | {sec_label} | {record.id or record.source_id} | {hash_abbr}]"


class Al2cRagService(models.AbstractModel):
    """Enterprise Grounding and RAG Governance Service.
    
    Implements:
    - Hierarchical semantic chunking with strict Markdown table continuity invariant.
    - Reciprocal Rank Fusion (RRF, k=60) for hybrid retrieval.
    - Entailment Gate verification (threshold >= 0.85) to prevent hallucinations.
    - Standard Citation Contract formatting [Document | Section | ID | SHA256].
    - Multi-tenant RBAC domain isolation and automated cache invalidation.
    """
    _name = 'al2c.rag.service'
    _description = 'AL2C RAG & Grounding Governance Service'

    # -------------------------------------------------------------------------
    # 1. HIERARCHICAL SEMANTIC CHUNKING & TABLE PRESERVATION
    # -------------------------------------------------------------------------
    @api.model
    def _count_tokens(self, text):
        """Approximate token count supporting English and Vietnamese."""
        if not text:
            return 0
        return len(re.findall(r'\w+|[^\w\s]', text))

    @api.model
    def chunk_document(self, text, source_ref="doc", doc_title="Document", breadcrumb="", max_tokens=512, overlap_tokens=50):
        """Chunk a document semantically while preserving markdown tables.
        
        Table Continuity Invariant:
        - Markdown tables (| ... |) are NEVER split mid-row.
        - If a table exceeds max_tokens, data rows are split across chunks, and every
          resulting chunk retains the table header and separator rows at the top.
        """
        if not text:
            return []

        lines = text.strip().splitlines()
        chunks = []
        current_breadcrumb = breadcrumb or doc_title
        current_lines = []
        current_tokens = 0
        seq = 0

        def finalize_chunk(lines_to_emit, bc):
            nonlocal seq
            if not lines_to_emit:
                return
            content = "\n".join(lines_to_emit).strip()
            if not content:
                return
            chunk_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            t_count = self._count_tokens(content)
            has_tbl = bool(re.search(r'^\s*\|.*\|\s*$', content, re.MULTILINE))
            citation = f"[{doc_title} | {bc or 'General'} | {seq} | {chunk_hash[:8]}]"
            chunks.append({
                'seq': seq,
                'content': content,
                'breadcrumb': bc,
                'hash': chunk_hash,
                'token_count': t_count,
                'has_table': has_tbl,
                'citation': citation,
            })
            seq += 1

        idx = 0
        total_lines = len(lines)

        while idx < total_lines:
            line = lines[idx]

            # 1. Header line: update breadcrumb
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                header_title = header_match.group(2).strip()
                if current_lines:
                    finalize_chunk(current_lines, current_breadcrumb)
                    current_lines = []
                    current_tokens = 0
                current_breadcrumb = f"{doc_title} > {header_title}"
                current_lines.append(line)
                current_tokens += self._count_tokens(line)
                idx += 1
                continue

            # 2. Markdown Table Detection
            if re.match(r'^\s*\|.*\|\s*$', line):
                # Collect full table
                table_lines = []
                while idx < total_lines and re.match(r'^\s*\|.*\|\s*$', lines[idx]):
                    table_lines.append(lines[idx])
                    idx += 1

                table_tokens = self._count_tokens("\n".join(table_lines))

                # Case A: Table fits in current chunk
                if current_tokens + table_tokens <= max_tokens:
                    current_lines.extend(table_lines)
                    current_tokens += table_tokens
                # Case B: Table does not fit, but current chunk has content -> flush current chunk
                elif current_lines:
                    finalize_chunk(current_lines, current_breadcrumb)
                    current_lines = []
                    current_tokens = 0

                    # Now check if table fits in a fresh chunk
                    if table_tokens <= max_tokens:
                        current_lines.extend(table_lines)
                        current_tokens = table_tokens
                    else:
                        # Table itself exceeds max_tokens: Split table while preserving header!
                        self._split_and_emit_table(table_lines, current_breadcrumb, doc_title, max_tokens, finalize_chunk)
                else:
                    # Current chunk empty, table itself exceeds max_tokens -> split table
                    self._split_and_emit_table(table_lines, current_breadcrumb, doc_title, max_tokens, finalize_chunk)
                continue

            # 3. Regular text line or paragraph
            line_tokens = self._count_tokens(line)
            if current_tokens + line_tokens > max_tokens and current_lines:
                finalize_chunk(current_lines, current_breadcrumb)
                current_lines = []
                current_tokens = 0

            current_lines.append(line)
            current_tokens += line_tokens
            idx += 1

        if current_lines:
            finalize_chunk(current_lines, current_breadcrumb)

        return chunks

    @api.model
    def _split_and_emit_table(self, table_lines, breadcrumb, doc_title, max_tokens, finalize_cb):
        """Split a large table by rows, repeating header and delimiter rows for each sub-chunk."""
        if len(table_lines) <= 2:
            finalize_cb(table_lines, breadcrumb)
            return

        header_row = table_lines[0]
        delim_row = table_lines[1]
        header_block = [header_row, delim_row]
        header_tokens = self._count_tokens("\n".join(header_block))

        data_rows = table_lines[2:]
        sub_chunk_lines = list(header_block)
        sub_tokens = header_tokens

        for row in data_rows:
            r_tokens = self._count_tokens(row)
            if sub_tokens + r_tokens > max_tokens and len(sub_chunk_lines) > 2:
                finalize_cb(sub_chunk_lines, breadcrumb)
                sub_chunk_lines = list(header_block)
                sub_tokens = header_tokens

            sub_chunk_lines.append(row)
            sub_tokens += r_tokens

        if len(sub_chunk_lines) > 2:
            finalize_cb(sub_chunk_lines, breadcrumb)

    # -------------------------------------------------------------------------
    # 2. RECIPROCAL RANK FUSION (RRF)
    # -------------------------------------------------------------------------
    @api.model
    def reciprocal_rank_fusion(self, dense_results, sparse_results, k=60):
        """Combine dense vector and sparse lexical rankings using RRF formula:
        RRF(d) = sum_{m in {dense, sparse}} 1 / (k + rank_m(d))
        
        Args:
            dense_results: list of item IDs or dicts with 'id', ranked from 1 to N
            sparse_results: list of item IDs or dicts with 'id', ranked from 1 to M
            k: ranking smoothing parameter (standard default: 60)
            
        Returns:
            list of (doc_id, fused_score) sorted descending by fused_score
        """
        scores = {}

        def _extract_id(item):
            if isinstance(item, dict):
                return item.get('id')
            elif isinstance(item, (tuple, list)):
                return item[0]
            return item

        # Dense pass
        for rank, item in enumerate(dense_results, start=1):
            doc_id = _extract_id(item)
            if doc_id is not None:
                scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

        # Sparse pass
        for rank, item in enumerate(sparse_results, start=1):
            doc_id = _extract_id(item)
            if doc_id is not None:
                scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

        # Sort descending by score
        sorted_ranks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_ranks

    # -------------------------------------------------------------------------
    # 3. ENTAILMENT GATE & ANTI-HALLUCINATION VERIFICATION
    # -------------------------------------------------------------------------
    @api.model
    def verify_grounding_entailment(self, query, response_text, retrieved_chunks, threshold=0.85):
        """Verify whether response_text is strictly grounded by retrieved_chunks.
        
        Computes factual alignment score in [0.0, 1.0].
        Fail-closed invariant: if score < threshold (default 0.85), returns is_grounded = False.
        """
        if not response_text or not retrieved_chunks:
            return False, 0.0, "Zero context or empty response text"

        # Concatenate context text
        if isinstance(retrieved_chunks, (list, tuple)):
            context_texts = []
            for c in retrieved_chunks:
                if isinstance(c, dict):
                    context_texts.append(c.get('content', ''))
                elif hasattr(c, 'content'):
                    context_texts.append(c.content or '')
                elif isinstance(c, str):
                    context_texts.append(c)
            context = " ".join(context_texts).lower()
        else:
            context = str(retrieved_chunks).lower()

        clean_resp = response_text.lower()

        # 1. Entity and Technical Code Extraction (SKUs, IDs, Decree numbers, prices)
        # Matches SKUs like ERP-STARTER, Decree numbers like 13/2023, 70/2025, currencies VND, USD
        entities = re.findall(r'\b[A-Z0-9\-_]{3,}\b|\b\d+(?:[\.,/]\d+)*\b', response_text)
        unsupported_entities = [
            ent for ent in entities
            if ent.lower() not in ('and', 'the', 'for', 'with', 'vat', 'sop') and ent.lower() not in context
        ]

        # 2. Key Term Lexical Coverage
        terms = [t for t in re.findall(r'\b\w{3,}\b', clean_resp) if t not in ('chúng', 'của', 'và', 'các', 'những', 'được')]
        if not terms:
            terms = re.findall(r'\b\w+\b', clean_resp)

        if not terms:
            return False, 0.0, "No content terms found in response"

        matched_terms = sum(1 for t in terms if t in context)
        term_coverage = matched_terms / max(len(terms), 1)

        # 3. Entity Fidelity Score
        entity_score = 1.0 if not unsupported_entities else max(0.0, 1.0 - (len(unsupported_entities) * 0.3))

        # 4. Composite Entailment Score
        raw_score = (0.5 * entity_score) + (0.5 * term_coverage)

        # Penalty for hallucinated technical entities / numbers
        if unsupported_entities:
            penalty = min(len(unsupported_entities) * 0.25, 0.7)
            raw_score = max(0.0, raw_score - penalty)

        score = round(min(1.0, max(0.0, raw_score)), 4)
        is_grounded = (score >= threshold)

        if is_grounded:
            reason = f"Grounded: entailment score {score:.4f} >= threshold {threshold}"
        else:
            reason = f"Insufficient grounding: score {score:.4f} < {threshold} (unsupported: {', '.join(unsupported_entities[:5]) or 'lexical drift'})"

        return is_grounded, score, reason

    # -------------------------------------------------------------------------
    # 4. CITATION FORMATTING
    # -------------------------------------------------------------------------
    @api.model
    def format_citation(self, doc_name, section, chunk_id, chunk_hash):
        """Format authoritative citation following the Enterprise Citation Contract:
        [Document | Section | ID | SHA256]
        """
        hash_abbr = (chunk_hash or "00000000")[:8]
        return f"[{doc_name} | {section or 'General'} | {chunk_id} | {hash_abbr}]"

    # -------------------------------------------------------------------------
    # 5. CACHE & INDEX MANAGEMENT
    # -------------------------------------------------------------------------
    @api.model
    def invalidate_cache_for_source(self, source_model, source_id):
        """Invalidate chunk cache for a modified knowledge or document record."""
        chunks = self.env['al2c.rag.chunk'].sudo().search([
            ('source_model', '=', source_model),
            ('source_id', '=', source_id),
        ])
        count = len(chunks)
        chunks.unlink()
        _logger.info("Invalidated %d RAG chunks for source %s, id=%d", count, source_model, source_id)
        return count

    @api.model
    def index_knowledge_article(self, article, max_tokens=512):
        """Parse, chunk, and index a knowledge.article record into al2c.rag.chunk."""
        if not article:
            return self.env['al2c.rag.chunk']

        # Invalidate previous chunks
        self.invalidate_cache_for_source('knowledge.article', article.id)

        # Extract text
        body_text = html2plaintext(article.body or '')
        doc_title = article.name or f"Article-{article.id}"

        # Build breadcrumb
        breadcrumb_parts = []
        curr = article
        while curr:
            breadcrumb_parts.append(curr.name or '')
            curr = curr.parent_id if hasattr(curr, 'parent_id') else False
        breadcrumb = " > ".join(reversed(breadcrumb_parts))

        # Chunk document
        chunk_dicts = self.chunk_document(
            text=body_text,
            source_ref=f"knowledge.article,{article.id}",
            doc_title=doc_title,
            breadcrumb=breadcrumb,
            max_tokens=max_tokens,
        )

        created_chunks = self.env['al2c.rag.chunk']
        for c in chunk_dicts:
            created = self.env['al2c.rag.chunk'].sudo().create({
                'name': doc_title,
                'source_model': 'knowledge.article',
                'source_id': article.id,
                'source_ref': f"knowledge.article,{article.id}",
                'section_header': c['breadcrumb'],
                'chunk_seq': c['seq'],
                'content': c['content'],
                'chunk_hash': c['hash'],
                'token_count': c['token_count'],
                'has_table': c['has_table'],
                'company_id': article.company_id.id if hasattr(article, 'company_id') and article.company_id else self.env.company.id,
            })
            created_chunks |= created

        return created_chunks

    @api.model
    def retrieve_grounded_context(self, query, company_id=None, top_k=5):
        """Multi-tenant isolated retrieval querying active al2c.rag.chunk records."""
        if not company_id:
            company_id = self.env.company.id

        domain = [
            ('company_id', '=', company_id),
            ('active', '=', True),
        ]

        if query:
            # Simple keyword matching across content, section_header, name
            words = [w for w in re.findall(r'\w+', query.lower()) if len(w) >= 3]
            if words:
                sub_domains = []
                for w in words[:4]:
                    sub_domains.append(('content', 'ilike', w))
                if sub_domains:
                    domain.extend(sub_domains)

        return self.env['al2c.rag.chunk'].sudo().search(domain, limit=top_k)

    @api.model
    def cron_reindex_knowledge_articles(self, batch_limit=50, full_reindex=False):
        """Automated Scheduled Action: Re-indexes articles using high-watermark pagination
        and prunes orphaned chunks using memory-bounded SQL queries.
        """
        # Guard: Restrict invocation strictly to system administrators or scheduled actions (SEC-CRON-05)
        if not (self.env.is_admin() or self.env.is_system() or self.env.su):
            raise AccessError(_("Unauthorized: Only system administrators or scheduled actions may invoke re-indexing."))

        cr = self.env.cr
        orphaned_pruned_count = 0

        # 1. Memory-bounded orphan pruning via SQL cursor (SEC-CRON-02: avoids loading thousands of chunk records into RAM)
        cr.execute("""
            SELECT DISTINCT c.source_id 
            FROM al2c_rag_chunk c
            LEFT JOIN knowledge_article a ON c.source_id = a.id AND a.active = true
            WHERE c.source_model = 'knowledge.article'
              AND a.id IS NULL
        """)
        orphaned_article_ids = [row[0] for row in cr.fetchall() if row[0] is not None]
        if orphaned_article_ids:
            dead_chunks = self.env['al2c.rag.chunk'].sudo().search([
                ('source_model', '=', 'knowledge.article'),
                ('source_id', 'in', orphaned_article_ids)
            ])
            orphaned_pruned_count = len(dead_chunks)
            dead_chunks.unlink()
            _logger.info(
                "SEC-AUDIT: Pruned %d orphaned chunks across %d deleted/archived articles.",
                orphaned_pruned_count, len(orphaned_article_ids)
            )

        # 2. High-Watermark incremental sync (SEC-CRON-01: prevents starvation livelocks)
        ICP = self.env['ir.config_parameter'].sudo()
        if full_reindex:
            last_sync_date = '2000-01-01 00:00:00'
            last_sync_id = 0
        else:
            last_sync_date = ICP.get_param('al2c.rag.kms_last_sync_date', '2000-01-01 00:00:00')
            try:
                last_sync_id = int(ICP.get_param('al2c.rag.kms_last_sync_id', '0') or 0)
            except (ValueError, TypeError):
                last_sync_id = 0

        article_domain = [
            ('active', '=', True),
            '|',
            ('write_date', '>', last_sync_date),
            '&',
            ('write_date', '>=', last_sync_date),
            ('id', '>', last_sync_id),
        ]
        # SEC-CRON-03: Exclude private/confidential personal workspace articles
        if 'category' in self.env['knowledge.article']._fields:
            article_domain.append(('category', '!=', 'private'))

        articles = self.env['knowledge.article'].sudo().search(
            article_domain, 
            order='write_date asc, id asc', 
            limit=batch_limit if batch_limit and batch_limit > 0 else False
        )

        # If high-watermark exhausted all delta records, reset cursor to 2000-01-01 to start background validation sweep
        if not articles and batch_limit:
            ICP.set_param('al2c.rag.kms_last_sync_date', '2000-01-01 00:00:00')
            ICP.set_param('al2c.rag.kms_last_sync_id', '0')
            return {
                'articles_processed': 0,
                'chunks_stored': 0,
                'orphaned_pruned': orphaned_pruned_count,
                'cursor_reset': True,
            }

        articles_processed = 0
        chunks_stored = 0
        last_processed_article = None

        # 3. Fault-Tolerant Savepoint Loop (SEC-CRON-04: API timeouts don't abort entire run)
        for article in articles:
            try:
                with self.env.cr.savepoint():
                    indexed_chunks = self.index_knowledge_article(article)
                    chunks_stored += len(indexed_chunks)
                    articles_processed += 1
                    last_processed_article = article
            except Exception as e:
                _logger.exception("Failed indexing knowledge article %s (ID: %d): %s", article.name, article.id, str(e))
                continue

        # Advance cursor only up to the last successfully processed article
        if last_processed_article:
            ICP.set_param('al2c.rag.kms_last_sync_date', fields.Datetime.to_string(last_processed_article.write_date))
            ICP.set_param('al2c.rag.kms_last_sync_id', str(last_processed_article.id))

        summary = {
            'articles_processed': articles_processed,
            'chunks_stored': chunks_stored,
            'orphaned_pruned': orphaned_pruned_count,
        }

        _logger.info(
            "AL2C KMS Reindex completed: %d articles processed, %d chunks stored, %d orphaned chunks pruned.",
            articles_processed,
            chunks_stored,
            orphaned_pruned_count,
        )

        return summary

