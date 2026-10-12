#!/usr/bin/env python3
"""
Adversarial Verification Suite: OAuth Open Redirect Protection (CWE-601)
========================================================================
Asserts that malicious external URLs, protocol-relative links, control
characters, and bypass attempts are strictly sanitized and never escape
the local origin /insilos umbrella.
"""

import sys
import json
import werkzeug.urls


class MockHttpRequest:
    def __init__(self, url_root="http://localhost:28069/"):
        self.url_root = url_root


class MockRequest:
    def __init__(self, redirect_param, url_root="http://localhost:28069/"):
        self.params = {'redirect': redirect_param}
        self.session = type('Session', (), {'db': 'test_db'})()
        self.httprequest = MockHttpRequest(url_root)


def _is_safe_local_redirect(target_url):
    """Fail-closed validation verifying target_url is strictly local and cannot escape origin."""
    if not target_url or not isinstance(target_url, str):
        return False
    # Validate both raw form and unquoted form to prevent double-encoding bypasses (e.g. /%09evil.com)
    for s in (target_url, werkzeug.urls.url_unquote(target_url)):
        parsed = werkzeug.urls.url_parse(s)
        if parsed.scheme or parsed.netloc:
            return False
        if not s.startswith('/') or s.startswith('//'):
            return False
        if '\\' in s:
            return False
        if any(c in s for c in ('\r', '\n', '\t', '\0', ' ')):
            return False
    return True


def simulate_get_state(req, provider={'id': 1}):
    redirect = req.params.get('redirect') or '/insilos'
    if not _is_safe_local_redirect(redirect):
        redirect = '/insilos'
    parsed = werkzeug.urls.url_parse(redirect)
    clean_path = parsed.path
    if clean_path in ('', '/web', '/odoo', 'web', 'odoo') or clean_path.startswith(('/web/', '/odoo/', '/web?', '/odoo?')):
        redirect = '/insilos'
    else:
        query_part = ('?' + parsed.query) if parsed.query else ''
        redirect = clean_path + query_part

    redirect_url = '%s%s' % (req.httprequest.url_root, redirect[1:])
    return dict(
        d=req.session.db,
        p=provider['id'],
        r=werkzeug.urls.url_quote_plus(redirect_url),
    )


def simulate_signin_redirect_resolution(state_r, url_root="http://localhost:28069/"):
    req_root = MockHttpRequest(url_root)
    raw_redirect = werkzeug.urls.url_unquote_plus(state_r) if state_r else False
    url = '/insilos'
    if raw_redirect:
        parsed_r = werkzeug.urls.url_parse(raw_redirect)
        root_parsed = werkzeug.urls.url_parse(req_root.url_root)
        is_safe_local = _is_safe_local_redirect(raw_redirect)
        is_safe_same_origin = (
            parsed_r.scheme in ('http', 'https')
            and parsed_r.netloc == root_parsed.netloc
            and _is_safe_local_redirect(parsed_r.path)
        )
        if is_safe_local or is_safe_same_origin:
            clean_target_path = parsed_r.path
            if clean_target_path not in ('', '/web', '/odoo', 'web', 'odoo') and not clean_target_path.startswith(('/web/', '/odoo/', '/web?', '/odoo?')):
                query_part = ('?' + parsed_r.query) if parsed_r.query else ''
                url = clean_target_path + query_part
    return url


def run_tests():
    adversarial_payloads = [
        ('//evil.test', '/insilos'),
        ('https://evil.test', '/insilos'),
        ('http://attacker.com/malicious', '/insilos'),
        ('/\\evil.com', '/insilos'),
        ('/%09evil.com', '/insilos'),
        ('/\tevil', '/insilos'),
        ('\r\nhttps://evil.com', '/insilos'),
        ('javascript:alert(1)', '/insilos'),
        ('web', '/insilos'),
        ('/web', '/insilos'),
        ('/odoo', '/insilos'),
        ('/web?debug=assets', '/insilos'),
        ('/odoo?debug=1', '/insilos'),
        ('/web/login', '/insilos'),
        ('/odoo/action-123', '/insilos'),
        ('///evil.com', '/insilos'),
        ('\\\\evil.com', '/insilos'),
    ]

    legitimate_payloads = [
        ('/insilos/sales', '/insilos/sales'),
        ('/insilos/accounting?filter=posted', '/insilos/accounting?filter=posted'),
        ('/solutions-b2b', '/solutions-b2b'),
        ('/taste-profiler', '/taste-profiler'),
    ]

    print("=== RUNNING OAUTH OPEN REDIRECT ADVERSARIAL TEST SUITE ===")
    
    # 1. Test get_state adversarial inputs
    for payload, expected_target in adversarial_payloads:
        req = MockRequest(payload, "http://localhost:28069/")
        state = simulate_get_state(req)
        stored_r = werkzeug.urls.url_unquote_plus(state['r'])
        parsed_stored = werkzeug.urls.url_parse(stored_r)
        
        # Invariant 1: Must be strictly on localhost:28069
        assert parsed_stored.netloc == "localhost:28069", f"Bypass on get_state({payload!r})! Result netloc: {parsed_stored.netloc}"
        # Invariant 2: Path must resolve to /insilos for malicious payload
        assert parsed_stored.path == expected_target, f"Expected {expected_target} for {payload!r}, got {parsed_stored.path}"

        # Test downstream signin resolution
        resolved_url = simulate_signin_redirect_resolution(state['r'], "http://localhost:28069/")
        assert resolved_url == expected_target, f"Signin resolution failed for {payload!r}: {resolved_url} != {expected_target}"
        print(f"[✓] Adversarial payload {payload!r:<30} -> neutralized to: {resolved_url}")

    # 2. Test legitimate paths preserve deep routes and queries
    for payload, expected_target in legitimate_payloads:
        req = MockRequest(payload, "http://localhost:28069/")
        state = simulate_get_state(req)
        resolved_url = simulate_signin_redirect_resolution(state['r'], "http://localhost:28069/")
        assert resolved_url == expected_target, f"Legitimate payload {payload!r} distorted: got {resolved_url}"
        print(f"[✓] Legitimate route {payload!r:<30} -> preserved as:   {resolved_url}")

    # 3. Test tampered state['r'] (attacker directly tampers with state payload)
    tampered_states = [
        ("https://evil.com/pwn", '/insilos'),
        ("//evil.com", '/insilos'),
        ("http://attacker.com/steal-token", '/insilos'),
    ]
    for tampered_r, expected in tampered_states:
        resolved = simulate_signin_redirect_resolution(tampered_r, "http://localhost:28069/")
        assert resolved == expected, f"Tampered state bypass! Got {resolved}"
        print(f"[✓] Tampered state {tampered_r!r:<30} -> neutralized to: {resolved}")

    print("=" * 60)
    print("ALL ADVERSARIAL OAUTH OPEN REDIRECT TESTS PASSED (EXIT CODE: 0)")


if __name__ == '__main__':
    run_tests()
