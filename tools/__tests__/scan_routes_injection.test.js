#!/usr/bin/env node
/**
 * Regression test for CWE-78 command injection mitigation in tools/scan_all_innokafe_routes.js.
 */
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const assert = require('assert');

console.log('Running CWE-78 Command Injection Regression Test...');

const canary = path.join(os.tmpdir(), `canary_${Date.now()}_${Math.random().toString(36).substring(7)}`);
const payload = `http://127.0.0.1:1/ ; touch ${canary} ; #`;

try {
  execFileSync('node', ['tools/scan_all_innokafe_routes.js', payload], {
    encoding: 'utf-8',
    timeout: 15000,
    stdio: 'pipe'
  });
} catch (e) {
  // It should reject invalid URL and exit with code 2, without spawning shell
}

assert.strictEqual(
  fs.existsSync(canary),
  false,
  'SECURITY REGRESSION: Canary file was created! Command injection succeeded.'
);

if (fs.existsSync(canary)) {
  fs.unlinkSync(canary);
}

console.log('✅ CWE-78 Command Injection Test PASSED: Canary was NOT created, shell execution blocked.');
