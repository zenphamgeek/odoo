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

let scannerRan = false;
let canaryExitCode = null;
let canaryStderr = '';

try {
  execFileSync('node', ['tools/scan_all_innokafe_routes.js', payload], {
    encoding: 'utf-8',
    timeout: 15000,
    stdio: ['pipe', 'pipe', 'pipe']
  });
  canaryExitCode = 0;
  scannerRan = true;
} catch (err) {
  if (err.code === 'ENOENT' || err.status === null || err.status === undefined) {
    throw new Error(`Scanner failed to execute (not a security pass): ${err.message}`);
  }
  canaryExitCode = err.status;
  canaryStderr = err.stderr ? err.stderr.toString() : '';
  scannerRan = true;
}

assert.ok(scannerRan, 'SECURITY TEST INVALID: scanner never executed; canary result is meaningless.');
assert.strictEqual(
  canaryExitCode,
  2,
  `Expected scanner to reject injected URL with exit 2, got ${canaryExitCode}`
);
assert.ok(
  canaryStderr.includes('Invalid base URL argument'),
  `Expected stderr to contain rejection message, got: ${canaryStderr}`
);
assert.strictEqual(
  fs.existsSync(canary),
  false,
  'SECURITY REGRESSION: Canary file was created! Command injection succeeded via shell metacharacters.'
);
if (fs.existsSync(canary)) {
  fs.unlinkSync(canary);
}
console.log('  [✓] PASS: Scanner executed, rejected metacharacters with exit code 2, and canary was NOT created.');

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
    stderr.includes('Invalid base URL'),
    `Expected stderr to contain rejection message for '${badUrl}', got: ${stderr}`
  );
  console.log(`  [✓] PASS: '${badUrl}' rejected cleanly with exit code 2.`);
}

// Test 3: Malformed Non-URL String & Empty Argument Rejection
console.log('\n[Test 3] Verifying malformed non-URL and empty argument rejection (exit code 2)...');
const malformedUrls = ['not_a_valid_url', '://missing-scheme', '   ', ''];
for (const malformed of malformedUrls) {
  let exitCode = null;
  let stderr = '';
  try {
    execFileSync('node', ['tools/scan_all_innokafe_routes.js', malformed], {
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
    `SECURITY REGRESSION: Malformed URL '${malformed}' was not rejected with exit code 2 (got ${exitCode})`
  );
  assert.ok(
    stderr.includes('Invalid base URL'),
    `Expected stderr to contain rejection message for '${malformed}', got: ${stderr}`
  );
  console.log(`  [✓] PASS: '${malformed}' rejected cleanly with exit code 2.`);
}

// Test 4: Default Safe Invocation & Flag Validation
console.log('\n[Test 4] Verifying default invocation and safe argument parsing (--validate-only)...');
try {
  const stdout = execFileSync('node', ['tools/scan_all_innokafe_routes.js', '--validate-only'], {
    encoding: 'utf-8',
    timeout: 5000,
    stdio: ['pipe', 'pipe', 'pipe']
  });
  assert.ok(stdout.includes('Validated base URL: http://127.0.0.1:28071'), `Expected default URL validation, got: ${stdout}`);
  console.log('  [✓] PASS: Default URL validated successfully with exit code 0.');
} catch (err) {
  throw new Error(`Failed to validate default URL: ${err.message}`);
}

console.log('\n' + '='.repeat(70));
console.log('🎉 ALL SECURITY INVARIANTS VERIFIED: 0 VULNERABILITIES DETECTED');
console.log('='.repeat(70));
