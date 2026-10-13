# -*- coding: utf-8 -*-
# Part of Insilos AL2C Enterprise Architecture (SOP-RAG-003 & SOP-AI-004)

import hashlib
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'insilos_al2c', 'rag_grounding')
class TestAl2cRagGrounding(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = cls.env['al2c.rag.service']
        cls.company_a = cls.env.company
        # Clone company_a to create a secondary tenant without triggering payment.provider copy hook
        cls.env.cr.execute("CREATE TEMPORARY TABLE temp_comp AS SELECT * FROM organization_unit WHERE id = %s;", (cls.company_a.id,))
        cls.env.cr.execute("UPDATE temp_comp SET id = (SELECT COALESCE(MAX(id), 0) + 1 FROM organization_unit), name = 'Tenant Subsidiary B Corp';")
        cls.env.cr.execute("INSERT INTO organization_unit SELECT * FROM temp_comp RETURNING id;")
        company_b_id = cls.env.cr.fetchone()[0]
        cls.env.cr.execute("DROP TABLE temp_comp;")
        cls.company_b = cls.env['res.company'].browse(company_b_id)

    def test_01_hierarchical_chunking_and_table_preservation(self):
        """Verify markdown chunking preserves tables intact and computes SHA-256 hashes."""
        sample_doc = (
            "# Enterprise Quad-Core Architecture\n"
            "This document describes the 4 pillars of Innoria Enterprise platform.\n\n"
            "## ERP and GRC Integration\n"
            "Here is the feature and SKU matrix:\n\n"
            "| SKU Code | Service Line | SLA Tier |\n"
            "| :--- | :--- | :--- |\n"
            "| ERP-STARTER | Implementation | Bronze |\n"
            "| GRC-ESSENTIALS | Risk Register | Gold |\n"
            "| MOJO-APP-SUB | AI Copilot | Platinum |\n\n"
            "Follow-up paragraph detailing the deployment methodology according to SAP Activate."
        )

        chunks = self.service.chunk_document(
            text=sample_doc,
            source_ref="test_doc",
            doc_title="Architecture Doc",
            max_tokens=256,
        )

        self.assertTrue(len(chunks) >= 1, "Should generate at least one chunk")

        # Verify properties on chunks
        table_found = False
        for c in chunks:
            self.assertTrue(c['hash'], "Chunk must have a non-empty SHA-256 hash")
            self.assertEqual(len(c['hash']), 64, "SHA-256 hash must be 64 hexadecimal characters")
            computed_hash = hashlib.sha256(c['content'].encode('utf-8')).hexdigest()
            self.assertEqual(c['hash'], computed_hash, "Hash must match SHA-256 of content")
            self.assertTrue(c['citation'].startswith("[Architecture Doc |"), "Citation must follow standard contract")
            if c['has_table']:
                table_found = True
                self.assertIn("| SKU Code | Service Line | SLA Tier |", c['content'])
                self.assertIn("| ERP-STARTER | Implementation | Bronze |", c['content'])

        self.assertTrue(table_found, "Must detect and preserve markdown table")

    def test_02_large_table_splitting_preserves_headers(self):
        """Verify that large tables split across chunks retain header and delimiter rows."""
        table_rows = [
            "| SKU Code | Item Description | Price VND |",
            "| :--- | :--- | :--- |",
        ]
        for i in range(1, 26):
            table_rows.append(f"| SKU-{i:03d} | Enterprise Software Feature Number {i} | {i * 10000000} |")

        table_doc = (
            "# Large SKU Catalog\n\n" + "\n".join(table_rows)
        )

        # Force small max_tokens so table must split across multiple chunks
        chunks = self.service.chunk_document(
            text=table_doc,
            source_ref="large_catalog",
            doc_title="SKU Catalog",
            max_tokens=40,
        )

        self.assertTrue(len(chunks) > 1, f"Large table must split into multiple chunks, got {len(chunks)}")

        # Every chunk containing table rows must contain the header and delimiter
        header_row = "| SKU Code | Item Description | Price VND |"
        delim_row = "| :--- | :--- | :--- |"

        for idx, c in enumerate(chunks):
            if c['has_table']:
                self.assertIn(header_row, c['content'], f"Chunk {idx} must retain table header row")
                self.assertIn(delim_row, c['content'], f"Chunk {idx} must retain table delimiter row")

    def test_03_reciprocal_rank_fusion(self):
        """Verify Reciprocal Rank Fusion combines rankings correctly with k=60."""
        dense_results = ['docA', 'docB', 'docC']
        sparse_results = ['docB', 'docA', 'docD']

        fused = self.service.reciprocal_rank_fusion(dense_results, sparse_results, k=60)
        fused_dict = dict(fused)

        # Theoretical scores:
        # docA: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.01639344 + 0.01612903 = 0.03252247
        # docB: 1/(60+2) + 1/(60+1) = 0.03252247
        # docC: 1/(60+3) = 1/63 = 0.01587301
        # docD: 1/(60+3) = 1/63 = 0.01587301

        self.assertAlmostEqual(fused_dict['docA'], (1/61 + 1/62), places=5)
        self.assertAlmostEqual(fused_dict['docB'], (1/62 + 1/61), places=5)
        self.assertAlmostEqual(fused_dict['docC'], 1/63, places=5)
        self.assertAlmostEqual(fused_dict['docD'], 1/63, places=5)

        # Top 2 should be docA and docB
        top_2 = [item[0] for item in fused[:2]]
        self.assertIn('docA', top_2)
        self.assertIn('docB', top_2)

    def test_04_grounding_entailment_gate_pass_and_fail(self):
        """Verify Entailment Gate enforces threshold >= 0.85 and detects hallucinations."""
        context_chunks = [
            {
                'content': (
                    "Gói dịch vụ ERP-STARTER của Innoria Enterprise có chi phí triển khai là "
                    "500.000.000 VND, tuân thủ Nghị định 13/2023/NĐ-CP và Nghị định 70/2025/NĐ-CP. "
                    "Thời gian triển khai chuẩn theo phương pháp luận SAP Activate là 8 tuần."
                )
            }
        ]

        # Case 1: Grounded response
        grounded_resp = (
            "Gói ERP-STARTER của Innoria có mức giá 500.000.000 VND và tuân thủ Nghị định 13/2023/NĐ-CP."
        )
        is_grounded, score, reason = self.service.verify_grounding_entailment(
            query="Giá gói ERP Starter?",
            response_text=grounded_resp,
            retrieved_chunks=context_chunks,
            threshold=0.85,
        )
        self.assertTrue(is_grounded, f"Grounded response must pass entailment gate, got score={score}, reason={reason}")
        self.assertGreaterEqual(score, 0.85)

        # Case 2: Hallucinated response with invented numbers and SKU
        hallucinated_resp = (
            "Gói ERP-ENTERPRISE-ULTRA giá 9.999.000.000 USD đi kèm bảo hành vô thời hạn 2099."
        )
        is_grounded_hal, score_hal, reason_hal = self.service.verify_grounding_entailment(
            query="Giá gói ERP Starter?",
            response_text=hallucinated_resp,
            retrieved_chunks=context_chunks,
            threshold=0.85,
        )
        self.assertFalse(is_grounded_hal, f"Hallucinated response must fail entailment gate, got score={score_hal}")
        self.assertLess(score_hal, 0.85)
        self.assertIn("Insufficient grounding", reason_hal)

        # Case 3: Zero context
        is_grounded_zero, score_zero, reason_zero = self.service.verify_grounding_entailment(
            query="Bất kỳ câu hỏi nào",
            response_text="Câu trả lời không có ngữ cảnh",
            retrieved_chunks=[],
            threshold=0.85,
        )
        self.assertFalse(is_grounded_zero)
        self.assertEqual(score_zero, 0.0)

    def test_05_multi_tenant_isolation(self):
        """Verify knowledge chunks are strictly isolated by company_id."""
        text_a = 'Dự án bí mật tối mật của Tenant A'
        chunk_a = self.env['al2c.rag.chunk'].create({
            'name': 'Company A Proprietary SOW',
            'source_model': 'documents.document',
            'source_id': 101,
            'content': text_a,
            'chunk_hash': hashlib.sha256(text_a.encode('utf-8')).hexdigest(),
            'company_id': self.company_a.id,
        })

        text_b = 'Tài liệu độc quyền của Tenant B'
        chunk_b = self.env['al2c.rag.chunk'].create({
            'name': 'Company B Public Blueprint',
            'source_model': 'documents.document',
            'source_id': 102,
            'content': text_b,
            'chunk_hash': hashlib.sha256(text_b.encode('utf-8')).hexdigest(),
            'company_id': self.company_b.id,
        })

        # Query from perspective of Company A
        results_a = self.service.retrieve_grounded_context(
            query="tối mật",
            company_id=self.company_a.id,
        )
        self.assertIn(chunk_a, results_a, "Company A must retrieve its own chunk")
        self.assertNotIn(chunk_b, results_a, "Company A must NEVER retrieve Company B chunk")

        # Query from perspective of Company B
        results_b = self.service.retrieve_grounded_context(
            query="độc quyền",
            company_id=self.company_b.id,
        )
        self.assertIn(chunk_b, results_b, "Company B must retrieve its own chunk")
        self.assertNotIn(chunk_a, results_b, "Company B must NEVER retrieve Company A chunk")

    def test_06_cache_invalidation_and_reindexing(self):
        """Verify article re-indexing invalidates previous chunks."""
        article = self.env['knowledge.article'].create({
            'name': 'SOP Sales Delivery Playbook',
            'body': '<p>Nội dung cẩm nang bán hàng và quy trình chuyển giao.</p>',
        })

        created_chunks = self.service.index_knowledge_article(article)
        self.assertTrue(len(created_chunks) >= 1)
        chunk_ids = created_chunks.ids

        # Verify chunks exist in DB
        existing = self.env['al2c.rag.chunk'].search([('id', 'in', chunk_ids)])
        self.assertEqual(len(existing), len(chunk_ids))

        # Re-index with new body
        article.write({'body': '<p>Nội dung cẩm nang phiên bản mới cập nhật.</p>'})
        new_chunks = self.service.index_knowledge_article(article)

        # Old chunks must be unlinked (invalidated)
        old_remaining = self.env['al2c.rag.chunk'].search([('id', 'in', chunk_ids)])
        self.assertEqual(len(old_remaining), 0, "Previous chunks must be unlinked on re-index")
        self.assertTrue(len(new_chunks) >= 1, "New chunks must be indexed")
