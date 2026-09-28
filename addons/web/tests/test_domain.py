# -*- coding: utf-8 -*-
# Part of Insilos. See LICENSE file for full copyright and licensing details.

import json

from insilos.addons.base.tests.common import HttpCaseWithUserDemo
from insilos.tests import tagged
from insilos.tools import mute_logger


@tagged('post_install', '-at_install')
class DomainTest(HttpCaseWithUserDemo):

    def test_domain_validate(self):
        self.authenticate("demo", "demo")

        with mute_logger('insilos.http'):
            resp = self.url_open(
                '/web/domain/validate',
                headers={'Content-Type': 'application/json'},
                data=json.dumps({'params': {'model':'i', 'domain':[]}}),
            )
        self.assertEqual(resp.json()['error']['data']['message'], "Invalid model: i")

        resp = self.url_open(
            '/web/domain/validate',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'params': {'model':'res.users', 'domain':[]}}),
        )
        self.assertEqual(resp.json()['result'], True)

        resp = self.url_open(
            '/web/domain/validate',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'params': {'model':'res.users', 'domain':[('name', 'ilike', 'ad')]}}),
        )
        self.assertEqual(resp.json()['result'], True)

        resp = self.url_open(
            '/web/domain/validate',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'params': {'model':'res.users', 'domain':[('hop')]}}),
        )
        self.assertEqual(resp.json()['result'], False)

        resp = self.url_open(
            '/web/domain/validate',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'params': {'model': 'res.users', 'domain': [('', '=', 1)]}}),
        )
        self.assertEqual(resp.json()['result'], False)

        resp = self.url_open(
            '/web/domain/validate',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'params': {'model': 'res.users', 'domain': [('accesses_count', '>', 10)]}}),
        )
        self.assertEqual(resp.json()['result'], False)

        resp = self.url_open(
            '/web/domain/validate',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'params': {'model': 'res.currency', 'domain': [('iso_numeric', '=', 10)]}}),
        )
        self.assertEqual(resp.json()['result'], True)

        resp = self.url_open(
            '/web/domain/validate',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'params': {'model': 'res.currency', 'domain': [('iso_numeric', '=', 'dfd')]}}),
        )
        self.assertEqual(resp.json()['result'], False)
