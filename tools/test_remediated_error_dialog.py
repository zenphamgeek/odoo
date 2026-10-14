#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adversarial Security Verification Suite for SEC-01, SEC-02, SEC-03:
Verifies `sanitizeErrorPayload` and `sanitizeUrl` in both:
  1. addons/web/static/src/core/errors/error_dialogs.js
  2. enterprise/insilos_theme_genesis/static/src/errors/runtime_error_dialog_patch.js
via Node.js execution, ReDoS benchmarking, and Python parity assertions.
"""
import json
import os
import subprocess
import sys

ROOT_DIR = "/home/zen/O20"
ERROR_DIALOGS_JS = os.path.join(ROOT_DIR, "addons/web/static/src/core/errors/error_dialogs.js")
PATCH_JS = os.path.join(ROOT_DIR, "enterprise/insilos_theme_genesis/static/src/errors/runtime_error_dialog_patch.js")


def extract_function_block(filepath, func_name):
    with open(filepath, "r", encoding="utf-8") as f:
        src = f.read()
    marker = f"export function {func_name}("
    idx = src.find(marker)
    if idx == -1:
        marker = f"function {func_name}("
        idx = src.find(marker)
    assert idx != -1, f"Function {func_name} not found in {filepath}"
    brace_depth = 0
    started = False
    for pos in range(idx, len(src)):
        ch = src[pos]
        if ch == "{":
            brace_depth += 1
            started = True
        elif ch == "}":
            brace_depth -= 1
            if started and brace_depth == 0:
                return src[idx : pos + 1].replace("export function ", "function ")
    raise RuntimeError(f"Unbalanced braces in {func_name} of {filepath}")


def run_node_tests(filepath):
    sanitize_payload_code = extract_function_block(filepath, "sanitizeErrorPayload")
    sanitize_url_code = extract_function_block(filepath, "sanitizeUrl")

    node_script = f"""
{sanitize_payload_code}
{sanitize_url_code}

const t0 = performance.now();
const redosPayload = "Digest " + 'realm="odoo", '.repeat(5000) + "MALFORMED_TAIL";
const redosOut = sanitizeErrorPayload(redosPayload);
const redosElapsedSec = (performance.now() - t0) / 1000.0;

const cases = {{
    spaced_double_quoted_pwd: sanitizeErrorPayload('Auth error: password="my super secret 123" failed'),
    spaced_single_quoted_pwd: sanitizeErrorPayload("Config: client_secret: 'top secret value 99'"),
    unquoted_pwd: sanitizeErrorPayload("login?password= plainSecret99&user=admin"),
    dsn_postgres: sanitizeErrorPayload("OperationalError: postgresql://odoo:sec_pass_99@db.internal:5432/prod"),
    dsn_redis: sanitizeErrorPayload("RedisError: redis://default:r3d1s_p4ss!@cache.local:6379/0"),
    dsn_mongodb: sanitizeErrorPayload("MongoError: mongodb+srv://admin:m0ng0_s3cr3t@cluster0.example.net/db"),
    auth_bearer: sanitizeErrorPayload("Header Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig"),
    auth_basic: sanitizeErrorPayload("Authorization: Basic dXNlcjpwYXNzd29yZDEyMw=="),
    auth_digest: sanitizeErrorPayload('Authorization: Digest username="admin", realm="insilos", nonce="xyz", response="9876543210abcdef"'),
    api_key_sk: sanitizeErrorPayload("OpenAI key sk-proj-AbCdEfGhIjKlMnOpQrStUvWxYz123456 leaked"),
    api_key_ant: sanitizeErrorPayload("Anthropic key sk-ant-api03-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789 leaked"),
    api_key_gemini: sanitizeErrorPayload("Gemini key AIzaSyDaGmWKa4JsXZ-HjGw7xH_1234567890ab leaked"),
    api_key_akia: sanitizeErrorPayload("AWS key AKIAIOSFODNN7EXAMPLE leaked"),
    api_key_ghp: sanitizeErrorPayload("GitHub token ghp_1234567890abcdefghijklmnopqrstuvwxyz leaked"),
    api_key_gh_pat: sanitizeErrorPayload("GitHub fine PAT github_pat_11AA22BB33CC44DD55EE66FF77GG88HH99II00JJ leaked"),
    vn_phone: sanitizeErrorPayload("Call customer at 0912345678 or 0387654321 immediately"),
    email_addr: sanitizeErrorPayload("Contact support@innoria.com or ceo.dgm@digimate.vn for help"),
    session_cookie: sanitizeErrorPayload("Cookie: session_id=abc123xyz987; sid=sec_sid_456"),
    url_strip: sanitizeUrl("https://innoria.com/web?token=abc&sid=123#debug=assets"),
    redos_elapsed_sec: redosElapsedSec,
}};
console.log(JSON.stringify(cases));
"""
    proc = subprocess.run(["node", "-e", node_script], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout.strip())


def verify_results(label, res):
    print(f"[*] Verifying {label}...")
    assert "my super secret 123" not in res["spaced_double_quoted_pwd"], f"Leak in {res['spaced_double_quoted_pwd']}"
    assert "password=[REDACTED]" in res["spaced_double_quoted_pwd"], res["spaced_double_quoted_pwd"]
    assert "top secret value 99" not in res["spaced_single_quoted_pwd"], f"Leak in {res['spaced_single_quoted_pwd']}"
    assert "client_secret=[REDACTED]" in res["spaced_single_quoted_pwd"], res["spaced_single_quoted_pwd"]
    assert "plainSecret99" not in res["unquoted_pwd"], f"Leak in {res['unquoted_pwd']}"

    assert "sec_pass_99" not in res["dsn_postgres"], f"Leak in {res['dsn_postgres']}"
    assert "postgresql://odoo:[REDACTED]@db.internal:5432/prod" in res["dsn_postgres"], res["dsn_postgres"]
    assert "r3d1s_p4ss!" not in res["dsn_redis"], f"Leak in {res['dsn_redis']}"
    assert "redis://default:[REDACTED]@cache.local:6379/0" in res["dsn_redis"], res["dsn_redis"]
    assert "m0ng0_s3cr3t" not in res["dsn_mongodb"], f"Leak in {res['dsn_mongodb']}"
    assert "mongodb+srv://admin:[REDACTED]@cluster0.example.net/db" in res["dsn_mongodb"], res["dsn_mongodb"]

    assert "eyJhbGciOi" not in res["auth_bearer"], f"Leak in {res['auth_bearer']}"
    assert "Bearer [REDACTED]" in res["auth_bearer"], res["auth_bearer"]
    assert "dXNlcjpwYXNzd29yZDEyMw" not in res["auth_basic"], f"Leak in {res['auth_basic']}"
    assert "Basic [REDACTED]" in res["auth_basic"], res["auth_basic"]
    assert "9876543210abcdef" not in res["auth_digest"], f"Leak in {res['auth_digest']}"
    assert "Digest [REDACTED]" in res["auth_digest"], res["auth_digest"]

    assert "sk-proj-" not in res["api_key_sk"], f"Leak in {res['api_key_sk']}"
    assert "[REDACTED_API_KEY]" in res["api_key_sk"], res["api_key_sk"]
    assert "sk-ant-api03-" not in res["api_key_ant"], f"Leak in {res['api_key_ant']}"
    assert "[REDACTED_API_KEY]" in res["api_key_ant"], res["api_key_ant"]
    assert "AIzaSyDaGmWKa4JsXZ" not in res["api_key_gemini"], f"Leak in {res['api_key_gemini']}"
    assert "[REDACTED_API_KEY]" in res["api_key_gemini"], res["api_key_gemini"]
    assert "AKIAIOSFODNN7EXAMPLE" not in res["api_key_akia"], f"Leak in {res['api_key_akia']}"
    assert "[REDACTED_API_KEY]" in res["api_key_akia"], res["api_key_akia"]
    assert "ghp_1234567890" not in res["api_key_ghp"], f"Leak in {res['api_key_ghp']}"
    assert "[REDACTED_API_KEY]" in res["api_key_ghp"], res["api_key_ghp"]
    assert "github_pat_11AA22BB" not in res["api_key_gh_pat"], f"Leak in {res['api_key_gh_pat']}"
    assert "[REDACTED_API_KEY]" in res["api_key_gh_pat"], res["api_key_gh_pat"]

    assert "0912345678" not in res["vn_phone"], f"Leak in {res['vn_phone']}"
    assert "0387654321" not in res["vn_phone"], f"Leak in {res['vn_phone']}"
    assert "091*****78" in res["vn_phone"], f"Expected 091*****78 in {res['vn_phone']}"
    assert "038*****21" in res["vn_phone"], f"Expected 038*****21 in {res['vn_phone']}"

    assert "support@innoria.com" not in res["email_addr"], f"Leak in {res['email_addr']}"
    assert "ceo.dgm@digimate.vn" not in res["email_addr"], f"Leak in {res['email_addr']}"
    assert res["email_addr"].count("[REDACTED_EMAIL]") == 2, res["email_addr"]

    assert "abc123xyz987" not in res["session_cookie"], f"Leak in {res['session_cookie']}"
    assert "sec_sid_456" not in res["session_cookie"], f"Leak in {res['session_cookie']}"

    assert res["url_strip"] == "https://innoria.com/web", f"Expected https://innoria.com/web, got {res['url_strip']}"
    assert res["redos_elapsed_sec"] < 0.05, f"ReDoS benchmark too slow: {res['redos_elapsed_sec']:.4f}s >= 0.05s"
    print(f"[✓] {label}: ALL 19 ADVERSARIAL VECTORS + ReDoS ({res['redos_elapsed_sec']*1000:.2f}ms) PASSED (0 LEAKS)")


def main():
    res_core = run_node_tests(ERROR_DIALOGS_JS)
    res_patch = run_node_tests(PATCH_JS)
    verify_results("addons/web/static/src/core/errors/error_dialogs.js", res_core)
    verify_results("enterprise/insilos_theme_genesis/static/src/errors/runtime_error_dialog_patch.js", res_patch)
    for k in res_core:
        if k != "redos_elapsed_sec":
            assert res_core[k] == res_patch[k], f"Parity mismatch on {k}: {res_core[k]} != {res_patch[k]}"
    print("[✓] 100% PARITY VERIFIED BETWEEN CORE ERROR_DIALOGS.JS AND RUNTIME_ERROR_DIALOG_PATCH.JS")


if __name__ == "__main__":
    main()
