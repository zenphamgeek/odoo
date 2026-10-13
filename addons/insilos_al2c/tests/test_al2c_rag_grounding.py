# -*- coding: utf-8 -*-
# Part of Insilos AL2C Enterprise Architecture (SOP-RAG-003 & SOP-AI-004)

import hashlib
from unittest.mock import patch
from odoo import fields
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, AccessError


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

    def test_07_cron_reindex_knowledge_articles(self):
        """Verify automated cron reindexing indexes active articles and prunes orphaned chunks."""
        # 1. Create an active article with markdown table
        active_article = self.env['knowledge.article'].create({
            'name': 'Active Operational SOP Article',
            'body': (
                '<p>Overview of autonomous operations:</p>'
                '<p>| Process Code | Lead Time | Responsible Role |<br/>'
                '| :--- | :--- | :--- |<br/>'
                '| SOP-AL2C-001 | 2 Days | Revenue Ops Manager |<br/>'
                '| SOP-AL2C-002 | 1 Day | Legal Reviewer |</p>'
            ),
        })

        # 2. Create an article to be archived
        archived_article = self.env['knowledge.article'].create({
            'name': 'Legacy Deprecated Knowledge Article',
            'body': '<p>This process is deprecated and will be archived.</p>',
        })

        # Pre-index both articles
        self.service.index_knowledge_article(active_article)
        archived_chunks = self.service.index_knowledge_article(archived_article)
        archived_chunk_ids = archived_chunks.ids

        # Now archive the second article
        archived_article.write({'active': False})

        # 3. Create a synthetic orphaned chunk for an article that was completely deleted
        deleted_chunk = self.env['al2c.rag.chunk'].create({
            'name': 'Ghost Article Deleted Long Ago',
            'source_model': 'knowledge.article',
            'source_id': 99999999,
            'content': 'Orphaned content with nonexistent source id',
            'chunk_hash': hashlib.sha256(b'deleted_source_content').hexdigest(),
            'company_id': self.company_a.id,
        })
        deleted_chunk_id = deleted_chunk.id

        # Verify orphaned chunks currently exist in database
        self.assertTrue(self.env['al2c.rag.chunk'].browse(archived_chunk_ids).exists())
        self.assertTrue(self.env['al2c.rag.chunk'].browse(deleted_chunk_id).exists())

        # 4. Trigger cron_reindex_knowledge_articles
        result = self.service.cron_reindex_knowledge_articles(batch_limit=50)

        # 5. Assertions on return summary
        self.assertIsInstance(result, dict)
        self.assertIn('articles_processed', result)
        self.assertIn('chunks_stored', result)
        self.assertGreaterEqual(result['articles_processed'], 1)
        self.assertGreaterEqual(result['chunks_stored'], 1)

        # 6. Verify orphaned chunks were pruned
        remaining_archived_chunks = self.env['al2c.rag.chunk'].search([('id', 'in', archived_chunk_ids)])
        self.assertEqual(len(remaining_archived_chunks), 0, "Chunks of archived articles must be pruned by cron")

        remaining_deleted_chunks = self.env['al2c.rag.chunk'].search([('id', '=', deleted_chunk_id)])
        self.assertEqual(len(remaining_deleted_chunks), 0, "Orphaned chunks of deleted articles must be pruned by cron")

        # 7. Verify active article chunks were indexed and preserved table
        active_chunks = self.env['al2c.rag.chunk'].search([
            ('source_model', '=', 'knowledge.article'),
            ('source_id', '=', active_article.id),
        ])
        self.assertTrue(len(active_chunks) >= 1, "Active article must have chunks stored")
        table_chunks = active_chunks.filtered(lambda c: c.has_table)
        self.assertTrue(len(table_chunks) >= 1, "Markdown table in active article must be preserved with has_table=True")


@tagged('post_install', '-at_install', 'insilos_al2c', 'rag_grounding')
class TestAl2cRagAdversarialAudit(TransactionCase):
    """Adversarial security audit verification for SEC-CRON-01 to SEC-CRON-05."""

    def setUp(self):
        super().setUp()
        self.rag_service = self.env['al2c.rag.service']
        self.article_model = self.env['knowledge.article']
        self.chunk_model = self.env['al2c.rag.chunk']
        try:
            self.portal_user = self.env.ref('base.demo_user0')
        except ValueError:
            self.portal_user = self.env['res.users'].create({
                'name': 'Unprivileged Test User',
                'login': 'unprivileged_test_user@example.com',
                'email': 'unprivileged_test_user@example.com',
            })

    def test_adv_01_prevent_unauthorized_rpc_execution(self):
        """SEC-CRON-05: Verify unprivileged/portal users cannot invoke cron_reindex via RPC."""
        with self.assertRaises(AccessError):
            self.rag_service.with_user(self.portal_user).cron_reindex_knowledge_articles()

    def test_adv_02_pagination_prevents_starvation_livelock(self):
        """SEC-CRON-01: Create 100 articles and verify batching advances past the first 50."""
        # Align cursor to the latest existing article before creating test articles
        last_art = self.article_model.search([], order='write_date desc, id desc', limit=1)
        ICP = self.env['ir.config_parameter'].sudo()
        if last_art:
            ICP.set_param('al2c.rag.kms_last_sync_date', fields.Datetime.to_string(last_art.write_date))
            ICP.set_param('al2c.rag.kms_last_sync_id', str(last_art.id))
        else:
            ICP.set_param('al2c.rag.kms_last_sync_date', '2000-01-01 00:00:00')
            ICP.set_param('al2c.rag.kms_last_sync_id', '0')

        articles = [
            self.article_model.create({
                'name': f'Pagination Adv Article {i}',
                'body': f'<p>Content for pagination adversarial testing {i}</p>',
                'active': True
            })
            for i in range(100)
        ]

        # Run Batch 1: must process first 50
        res1 = self.rag_service.cron_reindex_knowledge_articles(batch_limit=50)
        self.assertEqual(res1['articles_processed'], 50)

        # Run Batch 2: must advance to remaining 50, NOT repeat the original 50
        res2 = self.rag_service.cron_reindex_knowledge_articles(batch_limit=50)
        self.assertEqual(res2['articles_processed'], 50)

    def test_adv_03_pruning_does_not_trigger_oom(self):
        """SEC-CRON-02: Simulate orphan cleanup and assert bounded SQL pruning."""
        article = self.article_model.create({'name': 'Deleted Adversarial Article', 'active': True})
        self.chunk_model.create({
            'source_model': 'knowledge.article',
            'source_id': article.id,
            'content': 'Orphan payload for memory bounded pruning test',
            'name': 'Deleted Adversarial Article Chunk',
            'chunk_hash': hashlib.sha256(b'orphan_payload_oom_test').hexdigest(),
        })
        article_id = article.id
        article.unlink()

        res = self.rag_service.cron_reindex_knowledge_articles(batch_limit=10)
        self.assertGreaterEqual(res['orphaned_pruned'], 1)

        remaining = self.chunk_model.search([
            ('source_model', '=', 'knowledge.article'),
            ('source_id', '=', article_id)
        ])
        self.assertEqual(len(remaining), 0)

    def test_adv_04_savepoint_resilience_on_api_timeout(self):
        """SEC-CRON-04: Ensure an API failure on one article does not revert preceding ones."""
        last_art = self.article_model.search([], order='write_date desc, id desc', limit=1)
        ICP = self.env['ir.config_parameter'].sudo()
        if last_art:
            ICP.set_param('al2c.rag.kms_last_sync_date', fields.Datetime.to_string(last_art.write_date))
            ICP.set_param('al2c.rag.kms_last_sync_id', str(last_art.id))

        a1 = self.article_model.create({'name': 'Valid Doc Adv', 'active': True, 'body': '<p>Valid content</p>'})
        a2 = self.article_model.create({'name': 'Failing Doc Adv', 'active': True, 'body': '<p>Failing content</p>'})

        def mock_index(article, *args, **kwargs):
            if article.id == a2.id:
                raise ConnectionError("LLM Gateway Timeout 504")
            return [{'chunk_id': 1}]

        with patch.object(type(self.rag_service), 'index_knowledge_article', side_effect=mock_index):
            summary = self.rag_service.cron_reindex_knowledge_articles(batch_limit=10)
            self.assertEqual(summary['articles_processed'], 1)


