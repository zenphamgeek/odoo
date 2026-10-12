# -*- coding: utf-8 -*-
import json
import time
import hmac
import hashlib
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install', 'insilos_al2c', 'runtime_report')
class TestRuntimeReportGateway(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.incident_model = cls.env['al2c.runtime.incident']
        cls.asset_model = cls.env['al2c.tech.asset']

        # Ensure core assets exist
        cls.asset_o20 = cls.asset_model.search([('code', '=', 'O20')], limit=1)
        if not cls.asset_o20:
            cls.asset_o20 = cls.asset_model.create({
                'name': 'O20 Platform Core',
                'code': 'O20',
                'repo_path': '/home/zen/O20',
                'category': 'platform_core',
            })

        cls.asset_mobo = cls.asset_model.search([('code', '=', 'INSILOS_MOBILE')], limit=1)
        if not cls.asset_mobo:
            cls.asset_mobo = cls.asset_model.create({
                'name': 'Insilos Mobile',
                'code': 'INSILOS_MOBILE',
                'repo_path': '/home/zen/insilos_mobile',
                'category': 'mobile_client',
            })

    def test_01_compute_fingerprint_determinism(self):
        """Verify fingerprint is deterministic and normalizes memory addresses and line numbers."""
        tb1 = "Traceback:\n  File '/home/zen/O20/addons/web/models.py', line 123, in execute\n    raise ValueError('Sample 0x7fa123')"
        tb2 = "Traceback:\n  File '/home/zen/O20/addons/web/models.py', line 456, in execute\n    raise ValueError('Sample 0x7fb888')"

        fp1 = self.incident_model.compute_fingerprint("ValueError", tb1, "O20")
        fp2 = self.incident_model.compute_fingerprint("ValueError", tb2, "O20")

        self.assertEqual(fp1, fp2, "Fingerprints must be identical despite line number or memory address drift.")

    def test_02_ingress_valid_report_and_deduplication(self):
        """Test public /api/v1/runtime-report endpoint ingestion and subsequent deduplication."""
        instance_id = "test-instance-saas-01"
        secret = "insilos-enterprise-runtime-sovereign-2026"
        timestamp = str(int(time.time()))
        error_name = "TypeError"

        hash_body = f"{instance_id}:{timestamp}:{error_name}".encode('utf-8')
        signature = hmac.new(secret.encode('utf-8'), hash_body, hashlib.sha256).hexdigest()

        headers = {
            'Content-Type': 'application/json',
            'X-Insilos-Instance-Id': instance_id,
            'X-Insilos-Timestamp': timestamp,
            'X-Insilos-Signature': signature,
        }

        payload = {
            'name': error_name,
            'message': 'Cannot read properties of undefined (reading dataset)',
            'traceback': "TypeError: Cannot read properties of undefined\n  at ListRenderer.js (enterprise/insilos_theme_genesis)",
            'url': 'https://saas.insilos.com/odoo/action-crm',
            'user_agent': 'Mozilla/5.0 Playwright Chrome Headless',
        }

        # 1. First Ingestion -> Created (201)
        response1 = self.url_open('/api/v1/runtime-report', data=json.dumps(payload), headers=headers)
        self.assertEqual(response1.status_code, 201)
        data1 = response1.json()
        self.assertEqual(data1['status'], 'created')
        self.assertEqual(data1['asset'], 'O20')
        incident_code = data1['incident_code']

        # 2. Second Ingestion with identical error -> Deduplicated (200)
        response2 = self.url_open('/api/v1/runtime-report', data=json.dumps(payload), headers=headers)
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(data2['status'], 'deduplicated')
        self.assertEqual(data2['incident_code'], incident_code)
        self.assertGreaterEqual(data2['occurrences'], 2)

    def test_03_antidos_payload_size_limit(self):
        """Verify payloads exceeding 256KB are blocked with HTTP 413 (Payload Too Large)."""
        huge_payload = {
            'name': 'HugeSpamError',
            'traceback': 'A' * (300 * 1024),  # 300 KB
        }
        headers = {'Content-Type': 'application/json'}
        response = self.url_open('/api/v1/runtime-report', data=json.dumps(huge_payload), headers=headers)
        self.assertEqual(response.status_code, 413, "Payload exceeding 256KB must return 413 Payload Too Large.")

    def test_04_asset_classification(self):
        """Verify automatic repository classification based on traceback patterns."""
        from odoo.addons.insilos_al2c.controllers.runtime_report_gateway import RuntimeReportGateway
        gateway = RuntimeReportGateway()

        mobo_tb = "flutter: Exception in peek_polycondensation_engine.dart line 42"
        self.assertEqual(gateway._classify_tech_asset(mobo_tb, {}), 'INSILOS_MOBILE')

        grc_tb = "Error in /home/zen/VerticalRisk/eramba/workflow.ts"
        self.assertEqual(gateway._classify_tech_asset(grc_tb, {}), 'VERTICAL_RISK')

        zen_tb = "Exception in /home/zen/zencode-ent/router/fleet_manager.py: QuotaExhausted"
        self.assertEqual(gateway._classify_tech_asset(zen_tb, {}), 'ZENCODE_ENT')

        o20_tb = "TypeError in enterprise/insilos_theme_genesis/list_controller.js"
        self.assertEqual(gateway._classify_tech_asset(o20_tb, {}), 'O20')

    def test_05_convert_incident_to_backlog_improvement(self):
        """Verify converting runtime incident to Backlog v2 item."""
        incident = self.incident_model.create({
            'name': 'Crash: Uncaught RPC Error on Lead Confirmation',
            'incident_code': 'INC-2026-TEST01',
            'fingerprint': 'test_hash_fingerprint_01',
            'asset_id': self.asset_o20.id,
            'error_name': 'RPCError',
            'error_message': 'Database connection timeout',
            'traceback': 'odoo.exceptions.UserError: connection timeout',
            'severity': 'critical',
        })

        incident.action_create_backlog_improvement()
        self.assertTrue(incident.improvement_id)
        self.assertEqual(incident.improvement_id.priority, 'P0')
        self.assertEqual(incident.state, 'in_backlog')
        self.assertTrue(incident.improvement_id.backlog_v2_line.startswith('- [ ] [AL2C-O20-BUG'))
