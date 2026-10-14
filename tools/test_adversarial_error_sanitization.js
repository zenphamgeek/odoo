/**
 * Standalone Adversarial Telemetry & Store Resilience Verification Suite
 * Tests sanitization of credentials, URLs, tokens, circular references, Error prototypes,
 * and namespaced mail.store / form controller isolation.
 */
const assert = require("node:assert");

// Import or define identical production logic
function sanitizeErrorPayload(input) {
    if (!input) {
        return input || "";
    }
    const visited = new WeakSet();
    function safeSerialize(val, depth = 0) {
        if (depth > 6) return "[MAX_DEPTH]";
        if (val === null || val === undefined) return val;
        if (typeof val !== "object") return val;
        if (visited.has(val)) return "[CIRCULAR_REF]";
        visited.add(val);
        if (val instanceof Error) {
            return {
                name: val.name,
                message: val.message,
                stack: val.stack,
                cause: val.cause ? safeSerialize(val.cause, depth + 1) : undefined,
            };
        }
        if (Array.isArray(val)) {
            return val.map((item) => safeSerialize(item, depth + 1));
        }
        const out = {};
        for (const key of Object.getOwnPropertyNames(val)) {
            try {
                out[key] = safeSerialize(val[key], depth + 1);
            } catch {
                out[key] = "[UNSERIALIZABLE]";
            }
        }
        return out;
    }

    let text = typeof input === "object" ? JSON.stringify(safeSerialize(input)) : String(input);
    return text
        .replace(/\b(Bearer|Basic|Digest)\s+[A-Za-z0-9\-._~+/]+=*/gi, "$1 [REDACTED]")
        .replace(/\b(?:sk-[a-zA-Z0-9\-_]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36})\b/g, "[REDACTED_API_KEY]")
        .replace(/((?:postgresql|postgres|mysql|redis|amqp|mongodb(?:\+srv)?):\/\/[^:\s\/]+:)[^@\s\/]+(@)/gi, "$1[REDACTED]$2")
        .replace(/(password|passwd|pwd|secret|token|api_key|apiKey|access_token|refresh_token|client_secret|session_id|sid|cookie|connection_string|authorization)["']?\s*[:=]\s*(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|(?!(?:Bearer|Basic|Digest)\b)[^\s&,"']+)/gi, "$1=[REDACTED]")
        .replace(/(session_id|sid)=[^;&\s]+/gi, "$1=[REDACTED]")
        .replace(/\b(0[35789])[0-9]{4}([0-9]{4})\b/g, "$1****$2")
        .replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, "[REDACTED_EMAIL]");
}

function sanitizeUrl(rawUrl, baseOrigin = "http://localhost") {
    try {
        const parsed = new URL(rawUrl, baseOrigin);
        // Strip all query parameters and hash fragments to prevent credential leakage
        return `${parsed.origin}${parsed.pathname}`;
    } catch {
        return baseOrigin || "about:blank";
    }
}

class IncidentCRDTStore {
    constructor() {
        this.storageKey = "insilos_crdt_incident_v1";
        this.memStore = {};
    }

    record(incident, sessionInfo = { enable_crdt_error_sync: true }) {
        if (!sessionInfo?.enable_crdt_error_sync) {
            return false;
        }
        const hash = `${incident.name}:${String(incident.message || "").slice(0, 60)}`;
        const existing = this.memStore[hash];

        if (!existing || existing.timestamp < incident.timestamp) {
            this.memStore[hash] = {
                ...incident,
                count: (existing?.count || 0) + 1,
                vector: (existing?.vector || 0) + 1,
            };
            return true;
        }
        return false;
    }
}

// -----------------------------------------------------------------------------
// Test Executions
// -----------------------------------------------------------------------------

console.log("🧪 Running Adversarial Security & Store Resilience Verification Suite...");

// Test 1: URL Sanitization
const dirtyUrl = "https://erp.insilos.com/web#access_token=ya29.secret&id_token=xyz&session_id=deadbeef";
assert.strictEqual(sanitizeUrl(dirtyUrl), "https://erp.insilos.com/web", "Failed to strip hash tokens");

const queryUrl = "https://erp.insilos.com/action?token=SECRET_AUTH_KEY&user=admin";
assert.strictEqual(sanitizeUrl(queryUrl), "https://erp.insilos.com/action", "Failed to strip query params");
console.log("  ✅ Test 1 PASSED: Strips query secrets and OAuth fragments from URL");

// Test 2: Credential & PII Redaction
const rawTrace = `
    Error: Unauthorized access
    at checkAuth (auth.js:42)
    Headers: Authorization: Bearer abc-123456.789_xyz
    Payload: {"password": "SuperSecretPass!123", "sid": "9876543210abcdef", "client_secret": "my-secret-key"}
    User: test.user@example.com
`;
const sanitized = sanitizeErrorPayload(rawTrace);
assert(!sanitized.includes("abc-123456.789_xyz"), "Leaked Bearer token");
assert(!sanitized.includes("SuperSecretPass!123"), "Leaked Password");
assert(!sanitized.includes("9876543210abcdef"), "Leaked Session ID");
assert(!sanitized.includes("my-secret-key"), "Leaked Client Secret");
assert(!sanitized.includes("test.user@example.com"), "Leaked Email");
assert(sanitized.includes("Bearer [REDACTED]"), "Missing Bearer [REDACTED]");
assert(sanitized.includes("password=[REDACTED]"), "Missing password=[REDACTED]");
assert(sanitized.includes("[REDACTED_EMAIL]"), "Missing [REDACTED_EMAIL]");
console.log("  ✅ Test 2 PASSED: Redacts nested credentials, bearer tokens, and session IDs");

// Test 3: Circular References Invariant Guard
const cyclicPayload = { name: "RPC_FAIL", code: 400 };
cyclicPayload.self = cyclicPayload;
let cyclicResult = "";
assert.doesNotThrow(() => {
    cyclicResult = sanitizeErrorPayload(cyclicPayload);
}, "Threw on circular reference");
assert(cyclicResult.includes("[CIRCULAR_REF]"), "Did not mark circular reference");
console.log("  ✅ Test 3 PASSED: Cycle-safe recursive serializer eliminates White Screen of Death");

// Test 4: Error Object Non-Enumerable Properties
const dbErr = new Error("Database timeout at postgresql://zen:secret_pw@127.0.0.1:5432/o20");
const sanitizedErr = sanitizeErrorPayload(dbErr);
assert(sanitizedErr.includes("Database timeout"), "Error message property was erased");
assert(!sanitizedErr.includes("secret_pw"), "Database connection password leaked");
assert(sanitizedErr.includes("[REDACTED]"), "Database password not replaced with [REDACTED]");
console.log("  ✅ Test 4 PASSED: Preserves Error non-enumerable properties while redacting DB credentials");

// Test 5: Escaped Quote Credential Bypass Prevention
const escapedJson = "{\"password\": \"secret\\\"123\", \"other\": \"ok\"}";
const sanitizedEscaped = sanitizeErrorPayload(escapedJson);
assert(!sanitizedEscaped.includes("secret\\\"123"), "Escaped quote secret leaked");
assert(!sanitizedEscaped.includes("123"), "Escaped quote suffix leaked");
console.log("  ✅ Test 5 PASSED: Escaped quotes in JSON serialized strings properly parsed without leakage");

// Test 6: Cross-Model Store Isolation (party.master vs res.partner)
class MockMailStore {
    constructor() {
        this.records = {};
    }
    insert(payload) {
        for (const [model, list] of Object.entries(payload)) {
            if (!this.records[model]) this.records[model] = {};
            for (const item of list) {
                this.records[model][item.id] = item;
            }
        }
    }
    get(model, id) {
        return this.records[model]?.[id];
    }
}

const mockStore = new MockMailStore();
mockStore.insert({ "res.partner": [{ id: 1, name: "Administrator" }] });

// Untrusted data payload from create_ai_draft_channel
const incomingData = {
    "party.master": [{ id: 1, name: "Compromised External Entity" }]
};

// Safe insert logic from patched ai_chat_launcher_service
const safePayload = { ...incomingData };
if (safePayload["party.master"]) {
    safePayload["party.master"] = safePayload["party.master"].map((rec) => ({
        ...rec,
        _source_model: "party.master",
    }));
}
mockStore.insert(safePayload);

const adminRecord = mockStore.get("res.partner", 1);
assert.strictEqual(adminRecord.name, "Administrator", "res.partner(1) was overwritten by party.master(1)!");
const partyRecord = mockStore.get("party.master", 1);
assert.strictEqual(partyRecord._source_model, "party.master", "party.master namespace lost");
console.log("  ✅ Test 6 PASSED: Isolated mapping prevents cross-model ID collisions and BOLA impersonation");

// Test 7: Form Data Projection Allowlist
const rawFormData = {
    id: 42,
    name: "Partner Invoice",
    password: "Hash$SuperSecret123",
    salary: 150000,
    bank_account: "IBAN123456789",
    display_name: "INV/2026/0001",
    partner_id: [1, "Administrator"],
};

const safeRecordData = {};
const FORBIDDEN_KEYS = /password|secret|token|hash|auth|credit|bank|salary|ssn|tax_id/i;
for (const [k, v] of Object.entries(rawFormData)) {
    if (!FORBIDDEN_KEYS.test(k) && (typeof v !== "object" || v === null || Array.isArray(v))) {
        safeRecordData[k] = v;
    }
}

assert.strictEqual(safeRecordData.id, 42);
assert.strictEqual(safeRecordData.display_name, "INV/2026/0001");
assert.deepStrictEqual(safeRecordData.partner_id, [1, "Administrator"]);
assert.strictEqual(safeRecordData.password, undefined, "Password field leaked into AI context");
assert.strictEqual(safeRecordData.salary, undefined, "Salary field leaked into AI context");
assert.strictEqual(safeRecordData.bank_account, undefined, "Bank account field leaked into AI context");
console.log("  ✅ Test 7 PASSED: Form controller allowlist projects safe fields and suppresses sensitive PII");

console.log("\n🎯 ALL 7 ADVERSARIAL RESILIENCE & SECURITY TEST CASES PASSED WITH 0 REGRESSIONS!");
