#!/usr/bin/env node
/**
 * Comprehensive security regression test suite for tools/scan_all_innokafe_routes.js.
 * Validates:
 * 1. CWE-78: Metacharacter class sweep (;, $(), `, \n, &&, |) with unconditional canary cleanup.
 * 2. URL Protocol Allowlist: Rejection of file://, javascript:, gopher://, ftp:// with exit code 2.
 * 3. Malformed URL Rejection: Rejection of non-URL strings and empty/whitespace inputs with exit code 2.
 * 4. Safe Short-Circuit Validation (--validate-only): Validates both happy path and rejection with exit code 2 without scanning.
 */
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const assert = require('assert');

console.log('='.repeat(70));
console.log('SECURITY REGRESSION SUITE: tools/scan_all_innokafe_routes.js');
console.log('='.repeat(70));

// Test 1: Adversarial Metacharacter Class Sweep (CWE-78 + Defense-in-Depth)
console.log('\n[Test 1] Sweeping metacharacter injection vectors with unconditional canary cleanup...');
const canaryBase = path.join(os.tmpdir(), `canary_${Date.now()}_${Math.random().toString(36).substring(7)}`);

const injectionPayloads = [
  `http://127.0.0.1:1/ ; touch ${canaryBase}_semi ; #`,
  `http://127.0.0.1:1/$(touch ${canaryBase}_subshell)`,
  `http://127.0.0.1:1/\`touch ${canaryBase}_backtick\``,
  `http://127.0.0.1:1/\n touch ${canaryBase}_newline`,
  `http://127.0.0.1:1/ && touch ${canaryBase}_and`,
  `http://127.0.0.1:1/ | touch ${canaryBase}_pipe`,
];

for (const payload of injectionPayloads) {
  let scannerRan = false;
  let exitCode = null;
  let stderr = '';

  try {
    execFileSync('node', ['tools/scan_all_innokafe_routes.js', payload], {
      encoding: 'utf-8',
      timeout: 15000,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    exitCode = 0;
    scannerRan = true;
  } catch (err) {
    if (err.code === 'ENOENT' || err.status === null || err.status === undefined) {
      throw new Error(`Scanner failed to execute (not a security pass): ${err.message}`);
    }
    exitCode = err.status;
    stderr = err.stderr ? err.stderr.toString() : '';
    scannerRan = true;
  }

  assert.ok(scannerRan, 'SECURITY TEST INVALID: scanner never executed; canary result is meaningless.');
  assert.notStrictEqual(exitCode, 0, `Security failure: process must not exit 0 for payload: ${payload}`);
  assert.strictEqual(
    exitCode,
    2,
    `Expected scanner to reject injected URL with exit 2, got ${exitCode} for payload: ${payload}`
  );
  assert.ok(
    /^\[✗\] Invalid base URL/m.test(stderr),
    `Expected stderr to begin a line with the rejection marker, got: ${stderr}`
  );

  // Scoped check for canary files matching this run in tmpdir
  const base = path.basename(canaryBase);
  const leakedCanaries = fs.readdirSync(os.tmpdir()).filter(f => f.startsWith(base) && f.length > base.length);
  const canaryCreated = leakedCanaries.length > 0;

  // Unconditional cleanup before assertion to prevent artifact leaks
  for (const leaked of leakedCanaries) {
    try {
      fs.unlinkSync(path.join(os.tmpdir(), leaked));
    } catch (_) {}
  }

  assert.strictEqual(
    canaryCreated,
    false,
    `CRITICAL: shell was spawned — injected canary file was created for payload: ${payload}`
  );
  console.log(`  [✓] PASS: Rejected payload cleanly (exit 2, canary absent): ${payload.substring(0, 38)}...`);
}

// Test 2: Protocol Allowlist Enforcement (file://, javascript:, gopher://, ftp://)
const invalidProtocols = [
  'file:///etc/passwd',
  'javascript:alert(1)',
  'gopher://127.0.0.1:70',
  'ftp://ftp.example.com/pub'
];

console.log('\n[Test 2] Verifying protocol allowlist rejection (exit code 2 + anchored stderr)...');
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
    /^\[✗\] Invalid base URL/m.test(stderr),
    `Expected stderr to begin a line with the rejection marker for '${badUrl}', got: ${stderr}`
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
    /^\[✗\] Invalid base URL/m.test(stderr),
    `Expected stderr to begin a line with the rejection marker for '${malformed}', got: ${stderr}`
  );
  console.log(`  [✓] PASS: '${malformed}' rejected cleanly with exit code 2.`);
}

// Test 4: Default Safe Invocation & Flag Validation (--validate-only)
console.log('\n[Test 4] Verifying safe short-circuit validation (--validate-only)...');
// 4a. Default URL
try {
  const stdout = execFileSync('node', ['tools/scan_all_innokafe_routes.js', '--validate-only'], {
    encoding: 'utf-8',
    timeout: 5000,
    stdio: ['pipe', 'pipe', 'pipe']
  });
  assert.ok(stdout.includes('Validated base URL: http://127.0.0.1:28071'), `Expected default URL validation, got: ${stdout}`);
  console.log('  [✓] PASS: Default URL validated successfully (exit 0) without triggering scan.');
} catch (err) {
  throw new Error(`Failed to validate default URL: ${err.message}`);
}

// 4b. Custom valid URL
try {
  const stdout = execFileSync('node', ['tools/scan_all_innokafe_routes.js', 'https://innokafe.insilos.com', '--validate-only'], {
    encoding: 'utf-8',
    timeout: 5000,
    stdio: ['pipe', 'pipe', 'pipe']
  });
  assert.ok(stdout.includes('Validated base URL: https://innokafe.insilos.com'), `Expected custom URL validation, got: ${stdout}`);
  console.log('  [✓] PASS: Custom URL validated successfully (exit 0) without triggering scan.');
} catch (err) {
  throw new Error(`Failed to validate custom URL: ${err.message}`);
}

// 4c. Invalid URL with --validate-only must still reject with exit code 2
{
  let exitCode = null;
  let stderr = '';
  try {
    execFileSync('node', ['tools/scan_all_innokafe_routes.js', 'file:///etc/shadow', '--validate-only'], {
      encoding: 'utf-8',
      timeout: 5000,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    exitCode = 0;
  } catch (err) {
    exitCode = err.status;
    stderr = err.stderr ? err.stderr.toString() : '';
  }
  assert.strictEqual(exitCode, 2, `Expected invalid URL with --validate-only to reject with exit code 2 (got ${exitCode})`);
  assert.ok(/^\[✗\] Invalid base URL/m.test(stderr), `Expected anchored rejection message, got: ${stderr}`);
  console.log('  [✓] PASS: Invalid URL with --validate-only rejected cleanly with exit code 2.');
}

console.log('\n' + '='.repeat(70));
console.log('🎉 ALL SECURITY INVARIANTS VERIFIED: 0 VULNERABILITIES DETECTED');
console.log('='.repeat(70));
