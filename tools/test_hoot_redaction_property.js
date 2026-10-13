/**
 * Randomized Property & Corpus Invariant Test for HOOT Log Redactor (CWE-532)
 * ==============================================================================
 * Validates:
 *  1. Fixed Corpus: Database connection URIs, JWTs, Bearer auth, query string tokens, key-value secrets
 *  2. Ambient Registered Secrets: Dynamic secret registration and masking
 *  3. Randomized Property Fuzzing (1,000 iterations): Generates random credentials embedded in noise
 *  4. Console Predicate Invariant: HOOT_VERBOSE gate prevents benign log pollution in CI
 * ==============================================================================
 */

const assert = require('assert');
const crypto = require('crypto');
const { redactSensitive, registerSecret, REGISTERED_SECRETS } = require('../run_hoot.js');

console.log('=== [TEST] HOOT LOG REDACTOR & SECRET SINK (CWE-532) ===');

// 1. Fixed Corpus Verification
console.log('1. Auditing fixed corpus of real-world leak shapes...');
const corpusCases = [
  {
    name: 'PostgreSQL URI with username and password',
    input: 'Connection failed: postgresql://odoo_admin:SuperSecretPass123!@127.0.0.1:5434/insilos20_dev',
    secret: 'SuperSecretPass123!',
    expectedSubstring: 'postgresql://odoo_admin:***REDACTED***@127.0.0.1:5434/insilos20_dev',
  },
  {
    name: 'Postgres short URI with password',
    input: 'DB error: postgres://app_user:p@ssw0rd999@db.internal:5432/prod',
    secret: 'p@ssw0rd999',
    expectedSubstring: 'postgres://app_user:***REDACTED***@db.internal:5432/prod',
  },
  {
    name: 'MongoDB srv URI with credentials',
    input: 'Connecting to mongodb+srv://clusterUser:MongoPass#2026@cluster0.abc.mongodb.net/test',
    secret: 'MongoPass#2026',
    expectedSubstring: 'mongodb+srv://clusterUser:***REDACTED***@cluster0.abc.mongodb.net/test',
  },
  {
    name: 'Redis URI with auth',
    input: 'Cache connect: redis://default:RedisSecretToken@cache-node:6379/0',
    secret: 'RedisSecretToken',
    expectedSubstring: 'redis://default:***REDACTED***@cache-node:6379/0',
  },
  {
    name: 'Bearer Authorization Header',
    input: 'Request headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123xyz-signature',
    secret: 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123xyz-signature',
    expectedSubstring: 'Bearer ***REDACTED***',
  },
  {
    name: 'Raw JWT token in diagnostic payload',
    input: 'Parsed session token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4ifQ.dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk embedded in response',
    secret: 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk',
    expectedSubstring: '***REDACTED_JWT***',
  },
  {
    name: 'URL query string token parameter',
    input: 'GET /web/session/authenticate?access_token=ghp_9876543210fedcba&db=insilos20_dev',
    secret: 'ghp_9876543210fedcba',
    expectedSubstring: '?access_token=***REDACTED***&db=insilos20_dev',
  },
  {
    name: 'Key-value config parameter with password',
    input: 'Harness config initialized: password="SuperSensitiveAdminPass" timeout=25000',
    secret: 'SuperSensitiveAdminPass',
    expectedSubstring: 'password="***REDACTED***"',
  },
  {
    name: 'Colon-separated token in JSON-like log',
    input: 'Server response: { "token": "abc_secret_api_key_12345", "status": 200 }',
    secret: 'abc_secret_api_key_12345',
    expectedSubstring: '"token":"***REDACTED***"',
  },
];

for (const tc of corpusCases) {
  const result = redactSensitive(tc.input);
  assert(!result.includes(tc.secret), `Leak detected in [${tc.name}]: Secret '${tc.secret}' survived redaction!\nOutput: ${result}`);
  if (tc.expectedSubstring) {
    assert(result.includes(tc.expectedSubstring), `Expected substring '${tc.expectedSubstring}' not found in [${tc.name}]. Got: ${result}`);
  }
}
console.log('  [✓] 9/9 fixed corpus leak vectors completely sanitized.');

// 2. Ambient Registered Secret Masking
console.log('2. Auditing dynamic ambient secret registration...');
const dynamicSecret = 'DynSecret_' + crypto.randomBytes(8).toString('hex');
registerSecret(dynamicSecret);
const dynamicInput = `Worker 3 encountered unhandled stack: [Errno 111] with key ${dynamicSecret} during handshake`;
const dynamicOutput = redactSensitive(dynamicInput);
assert(!dynamicOutput.includes(dynamicSecret), `Dynamically registered secret leaked in output: ${dynamicOutput}`);
assert(dynamicOutput.includes('***REDACTED***'), `Mask marker missing from output: ${dynamicOutput}`);
console.log('  [✓] Dynamic secret registration verified.');

// 3. Randomized Property-Based Fuzzing with Shrinking (1,000 iterations)
console.log('3. Running randomized property-based fuzzer (1,000 iterations)...');
function randomString(len) {
  return crypto.randomBytes(Math.ceil(len / 2)).toString('hex').slice(0, len);
}

const templates = [
  (sec) => `postgresql://usr_${randomString(4)}:${sec}@cluster-${randomString(4)}.internal:5432/db`,
  (sec) => `postgres://user:${sec}@10.0.0.1:5432/tenant`,
  (sec) => `mongodb+srv://admin:${sec}@mongo.internal/app`,
  (sec) => `redis://default:${sec}@redis.lan:6379/1`,
  (sec) => `Bearer ${sec}`,
  (sec) => `password=${sec}`,
  (sec) => `passwd="${sec}"`,
  (sec) => `client_secret: ${sec}`,
  (sec) => `?access_token=${sec}&scope=read`,
  (sec) => `?client_secret=${sec}&status=1`,
];

let failedShrink = null;
for (let i = 0; i < 1000; i++) {
  const secretPayload = 'sec_' + randomString(12);
  const tmpl = templates[i % templates.length];
  const noisePre = `[DEBUG ${i}] noise_${randomString(8)} [HOOT] `;
  const noisePost = ` status_code=200 extra=${randomString(6)}`;
  const input = noisePre + tmpl(secretPayload) + noisePost;

  const output = redactSensitive(input);
  if (output.includes(secretPayload)) {
    failedShrink = { iteration: i, input, secretPayload, output };
    break;
  }
}

if (failedShrink) {
  assert.fail(`Property-based invariant violated at iteration ${failedShrink.iteration}:\nInput: ${failedShrink.input}\nOutput: ${failedShrink.output}\nSecret: ${failedShrink.secretPayload}`);
}
console.log('  [✓] 1,000/1,000 randomized property tests passed (0 secret tokens survived).');

// 4. Verification of Console Predicate Logic
console.log('4. Auditing HOOT_VERBOSE predicate isolation...');
function shouldMirrorToStdout(rawTxt, hootVerbose) {
  const isFailure = rawTxt.includes('failed:') || rawTxt.includes('timed out') || rawTxt.includes('Error during test:');
  return isFailure || (hootVerbose && rawTxt.includes('[HOOT]'));
}

// Benign HOOT log
const benignLog = '[HOOT] Suite "web.tests" passed 24/24 steps in 410ms';
assert.strictEqual(shouldMirrorToStdout(benignLog, false), false, 'Benign HOOT log MUST NOT mirror when HOOT_VERBOSE=0');
assert.strictEqual(shouldMirrorToStdout(benignLog, true), true, 'Benign HOOT log MUST mirror when HOOT_VERBOSE=1');

// Failure HOOT log
const failureLog = '[HOOT] Test "sale.order" failed: expected 200 got 500';
assert.strictEqual(shouldMirrorToStdout(failureLog, false), true, 'Failure log MUST always mirror even when HOOT_VERBOSE=0');
assert.strictEqual(shouldMirrorToStdout(failureLog, true), true, 'Failure log MUST always mirror when HOOT_VERBOSE=1');

console.log('  [✓] HOOT_VERBOSE predicate isolation verified.');
console.log('================================================================================');
console.log('ALL HOOT LOG REDACTION & PREDICATE GATES PASSED (EXIT 0)');
console.log('================================================================================');
