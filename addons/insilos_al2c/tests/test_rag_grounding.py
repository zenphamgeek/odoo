# -*- coding: utf-8 -*-
# Part of Insilos AL2C Enterprise Architecture (SOP-RAG-003 & SOP-AI-004)

import hashlib
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'insilos_al2c', 'rag_grounding')
class TestRagGroundingCron(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = cls.env['al2c.rag.service']
        cls.company_a = cls.env.company

    def test_cron_reindex_knowledge_articles(self):
        """Verify cron_reindex_knowledge_articles runs cleanly, creates chunks, and prunes orphaned chunks."""
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
