#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification Suite for Insilos API Perimeter Gateway
====================================================
Validates all perimeter gateway requirements:
1. Endpoints respond under /insilos/api/v1/... (ping, version, call, authenticate, catch-all).
2. 'Server: insilos/20.0' header is enforced on ALL responses (success and error).
3. Payload format is strictly standardized ({ "success": true/false, ... }).
4. Unexpected internal errors are completely masked (zero internal stack trace or file path leakage).
5. Secure session authentication and model execution work seamlessly over the perimeter gateway.
"""

import json
import sys
import unittest
import urllib.error
import urllib.request
import http.cookiejar

BASE_URL = "http://localhost:28069"


class TestInsilosPerimeterGateway(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up cookie jar for session management
        cls.cookie_jar = http.cookiejar.CookieJar()
        cls.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cls.cookie_jar))

    def _request(self, path, method="GET", data=None, headers=None, use_opener=True):
        url = f"{BASE_URL}{path}"
        req_headers = {"User-Agent": "Insilos-Perimeter-Test/1.0"}
        if headers:
            req_headers.update(headers)

        body_bytes = None
        if data is not None:
            if isinstance(data, (dict, list)):
                body_bytes = json.dumps(data).encode("utf-8")
                req_headers["Content-Type"] = "application/json"
            elif isinstance(data, str):
                body_bytes = data.encode("utf-8")
            else:
                body_bytes = data

        req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)
        opener = self.opener if use_opener else urllib.request.build_opener()

        try:
            with opener.open(req, timeout=10) as resp:
                status = resp.status
                resp_headers = dict(resp.headers)
                body = resp.read().decode("utf-8")
                return status, resp_headers, body
        except urllib.error.HTTPError as err:
            status = err.code
            resp_headers = dict(err.headers)
            body = err.read().decode("utf-8")
            return status, resp_headers, body

    def test_01_ping_get(self):
        """Verify GET /insilos/api/v1/ping returns 200, Server header, and pong payload."""
        status, headers, body = self._request("/insilos/api/v1/ping", method="GET")

        self.assertEqual(status, 200)
        self.assertEqual(headers.get("server"), "insilos/20.0")
        self.assertIn("application/json", headers.get("content-type", ""))

        data = json.loads(body)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("data", {}).get("status"), "pong")
        self.assertEqual(data.get("data", {}).get("server"), "insilos")
        self.assertEqual(data.get("data", {}).get("version"), "20.0")

    def test_02_ping_post(self):
        """Verify POST /insilos/api/v1/ping functions identically to GET."""
        status, headers, body = self._request("/insilos/api/v1/ping", method="POST", data={})

        self.assertEqual(status, 200)
        self.assertEqual(headers.get("server"), "insilos/20.0")
        data = json.loads(body)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("data", {}).get("status"), "pong")

    def test_03_ping_options_cors(self):
        """Verify OPTIONS CORS preflight returns 204/200 with Server and CORS headers."""
        status, headers, _ = self._request("/insilos/api/v1/ping", method="OPTIONS")

        self.assertIn(status, [200, 204])
        self.assertTrue(headers.get("server", "").startswith("insilos/20.0"))
        self.assertEqual(headers.get("access-control-allow-origin"), "*")

    def test_04_version_get(self):
        """Verify GET /insilos/api/v1/version returns Insilos platform version metadata."""
        status, headers, body = self._request("/insilos/api/v1/version", method="GET")

        self.assertEqual(status, 200)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        data = json.loads(body)
        self.assertTrue(data.get("success"))
        meta = data.get("data", {})
        self.assertEqual(meta.get("server_name"), "insilos")
        self.assertEqual(meta.get("server_version"), "20.0")
        self.assertEqual(meta.get("flavor"), "Insilos Enterprise Platform")
        self.assertEqual(meta.get("architecture"), "Ports & Adapters (Hexagonal)")

    def test_05_authenticate_invalid_credentials(self):
        """Verify POST /insilos/api/v1/authenticate rejects bad credentials with 401 and Server header."""
        status, headers, body = self._request(
            "/insilos/api/v1/authenticate",
            method="POST",
            data={"db": "odoo20_dev", "login": "admin", "password": "wrong_password_xyz"},
            use_opener=False,
        )

        self.assertEqual(status, 401)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        data = json.loads(body)
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error", {}).get("code"), 401)

    def test_06_authenticate_success(self):
        """Verify POST /insilos/api/v1/authenticate succeeds for valid credentials and sets session."""
        status, headers, body = self._request(
            "/insilos/api/v1/authenticate",
            method="POST",
            data={"db": "odoo20_dev", "login": "admin", "password": "admin"},
        )

        self.assertEqual(status, 200)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        data = json.loads(body)
        self.assertTrue(data.get("success"))
        auth_data = data.get("data", {})
        self.assertEqual(auth_data.get("uid"), 2)
        self.assertEqual(auth_data.get("db"), "odoo20_dev")
        self.assertTrue(bool(auth_data.get("session_id")))

    def test_07_call_unauthenticated(self):
        """Verify POST /insilos/api/v1/call without session returns 401 and Server header."""
        # Use a fresh, clean opener without cookies
        status, headers, body = self._request(
            "/insilos/api/v1/call",
            method="POST",
            data={"model": "res.users", "method": "search_read"},
            use_opener=False,
        )

        self.assertEqual(status, 401)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        data = json.loads(body)
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error", {}).get("code"), 401)

    def test_08_call_invalid_payload(self):
        """Verify POST /insilos/api/v1/call with invalid payload returns 400."""
        status, headers, body = self._request(
            "/insilos/api/v1/call",
            method="POST",
            data="not a valid json payload",
        )

        self.assertEqual(status, 400)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        data = json.loads(body)
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error", {}).get("code"), 400)

    def test_09_call_missing_parameters(self):
        """Verify POST /insilos/api/v1/call missing model or method returns 400."""
        status, headers, body = self._request(
            "/insilos/api/v1/call",
            method="POST",
            data={"model": "res.users"},  # missing method
        )

        self.assertEqual(status, 400)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        data = json.loads(body)
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error", {}).get("code"), 400)

    def test_10_call_private_method_rejection(self):
        """Verify POST /insilos/api/v1/call rejects private methods with 403."""
        status, headers, body = self._request(
            "/insilos/api/v1/call",
            method="POST",
            data={"model": "res.users", "method": "_compute_name"},
        )

        self.assertEqual(status, 403)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        data = json.loads(body)
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error", {}).get("code"), 403)

    def test_11_call_non_existent_model(self):
        """Verify POST /insilos/api/v1/call rejects unknown models with 404."""
        status, headers, body = self._request(
            "/insilos/api/v1/call",
            method="POST",
            data={"model": "totally.fake.model.xyz", "method": "search_read"},
        )

        self.assertEqual(status, 404)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        data = json.loads(body)
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error", {}).get("code"), 404)

    def test_12_call_authenticated_success(self):
        """Verify POST /insilos/api/v1/call executes model method with authenticated session."""
        status, headers, body = self._request(
            "/insilos/api/v1/call",
            method="POST",
            data={
                "model": "res.users",
                "method": "search_read",
                "args": [[["id", "=", 2]], ["id", "name", "login"]],
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        data = json.loads(body)
        self.assertTrue(data.get("success"))
        records = data.get("data")
        self.assertIsInstance(records, list)
        self.assertGreaterEqual(len(records), 1)
        self.assertEqual(records[0]["id"], 2)
        self.assertEqual(records[0]["login"], "admin")

    def test_13_mask_internal_stack_trace(self):
        """Verify internal exceptions are masked: no Traceback or internal paths in payload."""
        status, headers, body = self._request("/insilos/api/v1/test_error", method="GET")

        self.assertEqual(status, 500)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        # Crucial security invariants:
        self.assertNotIn("Traceback", body, "Response must not contain Python stack traces")
        self.assertNotIn("/home/zen/", body, "Response must not expose internal filesystem paths")
        self.assertNotIn(".py", body, "Response must not leak Python source file names")

        data = json.loads(body)
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error", {}).get("code"), 500)

    def test_14_catchall_fallback_404(self):
        """Verify undefined routes under /insilos/api/v1/ return 404 with Server header."""
        status, headers, body = self._request("/insilos/api/v1/non_existent_route_999", method="GET")

        self.assertEqual(status, 404)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        data = json.loads(body)
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error", {}).get("code"), 404)

    def test_15_call_datetime_serialization(self):
        """Verify model methods returning datetime/date fields serialize cleanly without 500 errors."""
        status, headers, body = self._request(
            "/insilos/api/v1/call",
            method="POST",
            data={
                "model": "res.users",
                "method": "search_read",
                "args": [[["id", "=", 2]], ["id", "login", "create_date", "write_date"]],
            },
        )

        self.assertEqual(status, 200)
        self.assertEqual(headers.get("server"), "insilos/20.0")

        data = json.loads(body)
        self.assertTrue(data.get("success"))
        records = data.get("data")
        self.assertIsInstance(records, list)
        self.assertGreaterEqual(len(records), 1)
        self.assertIn("create_date", records[0])
        self.assertIsInstance(records[0]["create_date"], str)

    def test_16_call_bearer_token_authentication(self):
        """Verify Authorization: Bearer <session_id> authenticates successfully without cookies."""
        # 1. Obtain a fresh session token
        status, _, body = self._request(
            "/insilos/api/v1/authenticate",
            method="POST",
            data={"db": "odoo20_dev", "login": "admin", "password": "admin"},
            use_opener=False,
        )
        self.assertEqual(status, 200)
        auth_data = json.loads(body)["data"]
        token = auth_data["session_id"]

        # 2. Call api using Bearer token without sending any cookies
        status, headers, body = self._request(
            "/insilos/api/v1/call",
            method="POST",
            data={
                "model": "res.users",
                "method": "search_read",
                "args": [[["id", "=", 2]], ["id", "login"]],
            },
            headers={"Authorization": f"Bearer {token}"},
            use_opener=False,
        )

        self.assertEqual(status, 200)
        self.assertEqual(headers.get("server"), "insilos/20.0")
        data = json.loads(body)
        self.assertTrue(data.get("success"))
        self.assertEqual(data["data"][0]["login"], "admin")

    def test_17_call_x_session_id_header_authentication(self):
        """Verify X-Session-Id header authenticates successfully without cookies."""
        status, _, body = self._request(
            "/insilos/api/v1/authenticate",
            method="POST",
            data={"db": "odoo20_dev", "login": "admin", "password": "admin"},
            use_opener=False,
        )
        token = json.loads(body)["data"]["session_id"]

        status, headers, body = self._request(
            "/insilos/api/v1/call",
            method="POST",
            data={
                "model": "res.users",
                "method": "search_read",
                "args": [[["id", "=", 2]], ["id", "login"]],
            },
            headers={"X-Session-Id": token},
            use_opener=False,
        )

        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data.get("success"))

    def test_18_call_invalid_parameter_types_returns_json_400(self):
        """Verify non-string method names or non-list args return clean 400 JSON, not raw 500 HTML."""
        # Non-string method (e.g. integer 123)
        status, headers, body = self._request(
            "/insilos/api/v1/call",
            method="POST",
            data={"model": "res.users", "method": 123},
        )
        self.assertEqual(status, 400)
        self.assertEqual(headers.get("server"), "insilos/20.0")
        data = json.loads(body)
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error", {}).get("code"), 400)

        # Non-list args (e.g. string "invalid")
        status, headers, body = self._request(
            "/insilos/api/v1/call",
            method="POST",
            data={"model": "res.users", "method": "search_read", "args": "invalid_args"},
        )
        self.assertEqual(status, 400)
        data = json.loads(body)
        self.assertFalse(data.get("success"))

    def test_19_gateway_base_url_index(self):
        """Verify GET /insilos/api/v1 and /insilos/api/v1/ return 200 JSON index without redirecting to login."""
        for path in ["/insilos/api/v1", "/insilos/api/v1/"]:
            status, headers, body = self._request(path, method="GET", use_opener=False)
            self.assertEqual(status, 200, f"Path {path} must return 200, not redirect")
            self.assertEqual(headers.get("server"), "insilos/20.0")
            data = json.loads(body)
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("data", {}).get("server"), "insilos")
            self.assertIn("/insilos/api/v1/ping", data.get("data", {}).get("endpoints", []))

    def test_20_cors_no_duplicate_headers(self):
        """Verify Access-Control-Allow-Origin header is not duplicated in raw HTTP response."""
        import urllib.request
        req = urllib.request.Request(f"{BASE_URL}/insilos/api/v1/ping")
        with urllib.request.urlopen(req) as resp:
            # get_all returns all occurrences of a header name
            cors_headers = resp.headers.get_all("Access-Control-Allow-Origin", [])
            self.assertLessEqual(len(cors_headers), 1, f"Expected at most 1 Access-Control-Allow-Origin, got: {cors_headers}")


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestInsilosPerimeterGateway)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
