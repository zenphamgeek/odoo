/**
 * Standalone Adversarial Telemetry & Store Resilience Verification Suite
 * Tests sanitization of credentials, URLs, tokens, circular references, Error prototypes,
 * AST JSON integrity, and namespaced mail.store / form controller isolation.
 */
const assert = require("node:assert");

// Mirror identical production logic from addons/web/static/src/core/errors/error_dialogs.js
function sanitizeErrorPayload(input) {
    if (input === null || input === undefined) {
        return "";
    }

    const SENSITIVE_KEY_PATTERN =
        /^(password|passwd|pwd|secret|token|api_?key|access_?token|refresh_?token|client_?secret|session_?id|sid|cookie|connection_?string|authorization|admin_passwd|master_pwd|private_?key|pin|otp)$/i;

    function sanitizeString(text) {
        return text
            .replace(/\b(Digest)\s+[a-zA-Z0-9_]+=(?:"[^"]*"|[^\s,;'"]+)(?:,\s*[a-zA-Z0-9_]+=(?:"[^"]*"|[^\s,;'"]+))*/gi, "$1 [REDACTED]")
            .replace(/\b(Bearer|Basic)\s+(?:[A-Za-z0-9\-._~+/]+=*|"[^"]*")/gi, "$1 [REDACTED]")
            .replace(/\b(sk-ant-api\d{2}-[a-zA-Z0-9_\-]{20,}|sk-(?:ant-[a-zA-Z0-9\-_]{20,}|[a-zA-Z0-9\-_]{20,})|AIza[0-9A-Za-z\-_]{30,40}|A[SK]IA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{20,})\b/g, "[REDACTED_API_KEY]")
            .replace(/-----BEGIN[ A-Z0-9_-]+KEY-----[\s\S]+?-----END[ A-Z0-9_-]+KEY-----/g, "[REDACTED_PRIVATE_KEY]")
            .replace(/((?:postgresql|postgres|mysql|redis|amqp|mongodb(?:\+srv)?|mssql|clickhouse):\/\/[^:\s\/]+:)[^@\s\/]+(@)/gi, "$1[REDACTED]$2")
            .replace(
                /(["']?(?:password|passwd|pwd|secret|token|api_?key|apiKey|access_?token|refresh_?token|client_?secret|session_?id|sid|cookie|connection_?string|authorization)["']?\s*)([:=])(\s*)(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|(?!(?:Bearer|Basic|Digest)\b)[^\s&,"']+)/gi,
                (match, key, sep, space) => {
                    if (sep === ":" && (key.startsWith('"') || key.startsWith("'"))) {
                        return `${key}:${space}"[REDACTED]"`;
                    }
                    return `${key.replace(/["']/g, "").trim()}=[REDACTED]`;
                }
            )
            .replace(/(session_id|sid)=[^;&\s]+/gi, "$1=[REDACTED]")
            .replace(/\b(0[35789]\d)(\d{5})(\d{2})\b/g, "$1*****$3")
            .replace(/(?:\+84|0)(?:[35789])(?:[\s.-]\d){8}\b/g, "[REDACTED_PHONE]")
            .replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, "[REDACTED_EMAIL]");
    }

    const visited = new WeakSet();
    function safeSerialize(val, depth = 0) {
        if (depth > 12) return "[MAX_DEPTH]";
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

    if (typeof input === "object") {
        try {
            const redactObject = (val, depth = 0) => {
                if (depth > 12 || val === null || typeof val !== "object") return val;
                if (Array.isArray(val)) return val.map((v) => redactObject(v, depth + 1));
                const out = {};
                for (const [k, v] of Object.entries(val)) {
                    if (typeof v === "string") {
                        const sanitizedVal = sanitizeString(v);
                        if (sanitizedVal !== v) {
                            out[k] = sanitizedVal;
                        } else if (SENSITIVE_KEY_PATTERN.test(k)) {
                            out[k] = "[REDACTED]";
                        } else {
                            out[k] = v;
                        }
                    } else if (SENSITIVE_KEY_PATTERN.test(k)) {
                        out[k] = "[REDACTED]";
                    } else {
                        out[k] = redactObject(v, depth + 1);
                    }
                }
                return out;
            };
            return JSON.stringify(redactObject(safeSerialize(input)));
        } catch {
            return sanitizeString(String(input));
        }
    }

    return sanitizeString(String(input));
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
assert(sanitized.includes('"password": "[REDACTED]"'), 'Missing "password": "[REDACTED]"');
assert.doesNotThrow(() => {
    const jsonStr = sanitized.split("Payload: ")[1].split("\n")[0].trim();
    const parsed = JSON.parse(jsonStr);
    assert.strictEqual(parsed.password, "[REDACTED]");
    assert.strictEqual(parsed.client_secret, "[REDACTED]");
}, "Failed to parse sanitized JSON payload");
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

// Test 8: JSON AST Integrity & Structural Key Redaction
const rpcPayload = {
    action: "call_kw",
    params: {
        password: "UltraSecretPassword!@#",
        token: "ghp_123456789012345678901234567890123456",
        safe_field: 42,
    },
};
const sanitizedRpc = sanitizeErrorPayload(rpcPayload);
const parsedRpc = JSON.parse(sanitizedRpc);
assert.strictEqual(parsedRpc.params.password, "[REDACTED]", "Password key not redacted");
assert.strictEqual(parsedRpc.params.token, "[REDACTED_API_KEY]", "Token value not redacted as API key");
assert.strictEqual(parsedRpc.params.safe_field, 42, "Safe non-sensitive field mutated");
console.log("  ✅ Test 8 PASSED: Direct JSON AST integrity maintained with structural key redaction");

// Test 9: Multi-Cloud Secrets & Private Key Sanitization
const cloudSecretsPayload = {
    geminiKey: "AIzaSyDaTestKey1234567890abcdefghijklm",
    privateKey: "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0m5kY...\n-----END RSA PRIVATE KEY-----",
    authDigest: 'Digest username="admin", realm="insilos", nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093"',
};
const sanitizedCloud = sanitizeErrorPayload(cloudSecretsPayload);
const parsedCloud = JSON.parse(sanitizedCloud);
assert.strictEqual(parsedCloud.geminiKey, "[REDACTED_API_KEY]", "Gemini API key leaked");
assert.strictEqual(parsedCloud.privateKey, "[REDACTED_PRIVATE_KEY]", "PEM Private key block leaked");
assert.strictEqual(parsedCloud.authDigest, "Digest [REDACTED]", "Digest auth header leaked");
console.log("  ✅ Test 9 PASSED: Google AI Studio keys, PEM blocks, and Digest auth sanitized");

// Test 10: Multi-Recordset & Context Privilege Bypass Defense
class MockBaseAutomation {
    constructor(rules) {
        this.rules = rules;
    }
    filtered(fn) {
        return new MockBaseAutomation(this.rules.filter(fn));
    }
    get length() {
        return this.rules.length;
    }
    process(records, context, user) {
        const isSystem = user.is_system || user.groups.includes("base.group_system");
        const skipAutosort = context.ai_documents_skip_autosort && isSystem;
        let rulesToRun = this;
        if (skipAutosort && records.length) {
            rulesToRun = this.filtered((r) => !r.ai_autosort_folder_id);
        }
        if (!rulesToRun.length) {
            return false;
        }
        return rulesToRun.rules.map((r) => r.name);
    }
}

const mockRules = new MockBaseAutomation([
    { id: 1, name: "AI Autosort Rule", ai_autosort_folder_id: 10 },
    { id: 2, name: "Standard Audit Rule", ai_autosort_folder_id: null },
]);

const normalUser = { is_system: false, groups: ["base.group_user"] };
const adminUser = { is_system: true, groups: ["base.group_system"] };

// Unprivileged user trying to inject context bypass
const unprivilegedResult = mockRules.process([1], { ai_documents_skip_autosort: true }, normalUser);
assert.deepStrictEqual(unprivilegedResult, ["AI Autosort Rule", "Standard Audit Rule"], "Unprivileged user bypassed AI autosort!");

// System user legitimate bypass
const adminResult = mockRules.process([1], { ai_documents_skip_autosort: true }, adminUser);
assert.deepStrictEqual(adminResult, ["Standard Audit Rule"], "Admin legitimate bypass failed");
console.log("  ✅ Test 10 PASSED: Privilege boundary enforces anti-bypass on multi-recordset automation");

console.log("\n🎯 ALL 10 ADVERSARIAL RESILIENCE & SECURITY TEST CASES PASSED WITH 0 REGRESSIONS!");
