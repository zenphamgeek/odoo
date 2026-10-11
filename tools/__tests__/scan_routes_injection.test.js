#!/usr/bin/env node
/**
 * Comprehensive security regression test suite for tools/scan_all_innokafe_routes.js.
 * Validates:
 * 1. CWE-78: Shell metacharacters are NOT evaluated by any shell (canary test).
 * 2. URL Protocol Allowlist: Rejection of file://, javascript:, gopher:// with exit code 2.
 * 3. Malformed URL Rejection: Rejection of non-URL strings with exit code 2.
 */
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const assert = require('assert');

console.log('='.repeat(70));
console.log('SECURITY REGRESSION SUITE: tools/scan_all_innokafe_routes.js');
console.log('='.repeat(70));

// Test 1: Shell Metacharacters (Canary Test)
console.log('\n[Test 1] Verifying shell metacharacters do not execute injected commands...');
const canary = path.join(os.tmpdir(), `canary_${Date.now()}_${Math.random().toString(36).substring(7)}`);
const payload = `http://127.0.0.1:1/ ; touch ${canary} ; #`;

try {
  execFileSync('node', ['tools/scan_all_innokafe_routes.js', payload], {
    encoding: 'utf-8',
    timeout: 15000,
    stdio: 'pipe'
  });
} catch (_) {
  // Connection error to 127.0.0.1:1 or scanner exit is expected; canary creation is the failure condition.
}

assert.strictEqual(
  fs.existsSync(canary),
  false,
  'SECURITY REGRESSION: Canary file was created! Command injection succeeded via shell metacharacters.'
);
if (fs.existsSync(canary)) {
  fs.unlinkSync(canary);
}
console.log('  [✓] PASS: No shell spawned, canary file was NOT created.');

// Test 2: Protocol Allowlist Enforcement (file://, javascript:, gopher://)
const invalidProtocols = [
  'file:///etc/passwd',
  'javascript:alert(1)',
  'gopher://127.0.0.1:70',
  'ftp://ftp.example.com/pub'
];

console.log('\n[Test 2] Verifying protocol allowlist rejection (exit code 2)...');
for (const badUrl of invalidProtocols) {
  let exitCode = null;
  let stderr = '';
  try {
    execFileSync('node', ['tools/scan_all_innokafe_routes.js', badUrl], {
      encoding: 'utf-8',
      timeout: 5000,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    exitCode = 0;
  } catch (err) {
    exitCode = err.status;
    stderr = err.stderr ? err.stderr.toString() : '';
  }

  assert.strictEqual(
    exitCode,
    2,
    `SECURITY REGRESSION: Protocol '${badUrl}' was not rejected with exit code 2 (got ${exitCode})`
  );
  assert.ok(
    stderr.includes('[✗] Invalid base URL argument'),
    `Expected stderr to contain rejection message for '${badUrl}', got: ${stderr}`
  );
  console.log(`  [✓] PASS: '${badUrl}' rejected cleanly with exit code 2.`);
}

// Test 3: Malformed Non-URL String Rejection
console.log('\n[Test 3] Verifying malformed non-URL string rejection (exit code 2)...');
const malformedUrls = ['not_a_valid_url', '://missing-scheme', '   '];
for (const malformed of malformedUrls) {
  let exitCode = null;
  try {
    execFileSync('node', ['tools/scan_all_innokafe_routes.js', malformed], {
      encoding: 'utf-8',
      timeout: 5000,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    exitCode = 0;
  } catch (err) {
    exitCode = err.status;
  }

  assert.strictEqual(
    exitCode,
    2,
    `SECURITY REGRESSION: Malformed URL '${malformed}' was not rejected with exit code 2 (got ${exitCode})`
  );
  console.log(`  [✓] PASS: '${malformed}' rejected cleanly with exit code 2.`);
}

console.log('\n' + '='.repeat(70));
console.log('🎉 ALL SECURITY INVARIANTS VERIFIED: 0 VULNERABILITIES DETECTED');
console.log('='.repeat(70));
