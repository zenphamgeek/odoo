# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'insilos_al2c')
class TestAl2cCatalogManifest(HttpCase):
    """
    Tests for AL2C-MKT-401: Machine-Readable Catalog Manifest (/llms.txt & /llms-full.txt).
    Verifies GEO (Generative Engine Optimization) markdown endpoints.
    """

    def test_llms_txt_endpoint(self):
        res = self.url_open('/llms.txt')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/markdown', res.headers.get('Content-Type', ''))
        content = res.text
        self.assertIn('# Insilos Enterprise Solutions Manifest', content)
        self.assertIn('ERP-STARTER', content)
        self.assertIn('ERP-GROWTH', content)
        self.assertIn('AI-POC', content)
        self.assertIn('/llms-full.txt', content)

    def test_llms_full_txt_endpoint(self):
        res = self.url_open('/llms-full.txt')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/markdown', res.headers.get('Content-Type', ''))
        content = res.text
        self.assertIn('# Insilos Enterprise Solutions — Complete Technical Catalog', content)
        self.assertIn('## SKU: ERP-GROWTH', content)
        self.assertIn('VAT Statutory Classification', content)
        self.assertIn('Delivery Milestones (Activate):', content)
        self.assertIn('Prepare -> Explore -> Realize -> Deploy -> Run', content)
