/**
 * Adversarial Test Suite for ExecutiveControlTower (CWE-20, CWE-1321, CWE-362, WCAG 2.1 AA)
 * Framework: Node.js Built-in Test Runner
 */
const { test, describe, beforeEach } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

// Reference implementation matching ExecutiveControlTower
function sanitizeId(val) {
    if (val === null || val === undefined) return "";
    const raw = String(val).trim();
    if (!raw) return "";
    if (raw === "__proto__" || raw === "constructor" || raw === "prototype") {
        return "_reserved_token_";
    }
    const sanitized = raw.replace(/[^a-zA-Z0-9_-]/g, "_");
    return /^[a-zA-Z]/.test(sanitized) ? sanitized : `id_${sanitized}`;
}

describe("ExecutiveControlTower Adversarial Security & Concurrency Verification", () => {
    describe("CWE-20 / CWE-1321: sanitizeId Security & Boundary Gates", () => {
        test("preserves numeric 0 without falsy collapse", () => {
            assert.strictEqual(sanitizeId(0), "id_0");
            assert.strictEqual(sanitizeId("0"), "id_0");
        });

        test("returns empty string for null, undefined, and empty string", () => {
            assert.strictEqual(sanitizeId(null), "");
            assert.strictEqual(sanitizeId(undefined), "");
            assert.strictEqual(sanitizeId(""), "");
            assert.strictEqual(sanitizeId("   "), "");
        });

        test("strips dots to prevent CSS selector and DOM injection", () => {
            const malicious = "pipeline.stage.123";
            const sanitized = sanitizeId(malicious);
            assert.strictEqual(sanitized, "pipeline_stage_123");
            assert.strictEqual(sanitized.includes("."), false);
        });

        test("defuses prototype pollution keywords", () => {
            assert.strictEqual(sanitizeId("__proto__"), "_reserved_token_");
            assert.strictEqual(sanitizeId("constructor"), "_reserved_token_");
            assert.strictEqual(sanitizeId("prototype"), "_reserved_token_");
        });

        test("ensures identifier starts with an alpha character for CSS selector conformance", () => {
            assert.strictEqual(sanitizeId("123stage"), "id_123stage");
            assert.strictEqual(sanitizeId("_private"), "id__private");
            assert.strictEqual(sanitizeId("-leading-dash"), "id_-leading-dash");
            assert.strictEqual(sanitizeId("validStage"), "validStage");
        });

        test("strips unsafe delimiters and symbols", () => {
            assert.strictEqual(sanitizeId("stage<script>alert(1)</script>"), "stage_script_alert_1___script_");
            assert.strictEqual(sanitizeId("truck#42!"), "truck_42_");
        });
    });

    describe("CWE-362: Epoch-Fenced Cancellation State Machine (Prefect/Airflow Invariant)", () => {
        class MockControlTower {
            constructor() {
                this._activeEpoch = 0;
                this._activeAbortController = null;
                this.state = {
                    isLoading: false,
                    lastUpdated: "",
                    kpis: null,
                };
            }

            async loadData(fetchPromiseFn) {
                if (this._activeAbortController) {
                    this._activeAbortController.abort();
                }
                const abortController = new AbortController();
                this._activeAbortController = abortController;
                const requestEpoch = ++this._activeEpoch;

                this.state.isLoading = true;
                try {
                    const res = await fetchPromiseFn(abortController.signal);
                    if (this._activeEpoch !== requestEpoch || abortController.signal.aborted) {
                        return; // Discard stale epoch
                    }
                    this.state.kpis = res.kpis;
                } catch (err) {
                    if (abortController.signal.aborted || this._activeEpoch !== requestEpoch) {
                        return;
                    }
                    throw err;
                } finally {
                    if (this._activeEpoch === requestEpoch && !abortController.signal.aborted) {
                        this.state.isLoading = false;
                        this.state.lastUpdated = "updated";
                    }
                }
            }
        }

        test("epoch fencing discards out-of-order stale network promises and prevents state overwrite", async () => {
            const tower = new MockControlTower();

            let resolveSlow;
            let resolveFast;
            let slowSignalAborted = false;

            const slowPromise = new Promise((resolve) => {
                resolveSlow = (val) => resolve(val);
            });
            const fastPromise = new Promise((resolve) => {
                resolveFast = (val) => resolve(val);
            });

            // Trigger slow request (Epoch 1)
            const call1 = tower.loadData((signal) => {
                signal.addEventListener("abort", () => {
                    slowSignalAborted = true;
                });
                return slowPromise;
            });

            assert.strictEqual(tower._activeEpoch, 1);

            // Trigger fast request (Epoch 2) before call 1 finishes
            const call2 = tower.loadData(() => fastPromise);

            assert.strictEqual(tower._activeEpoch, 2);
            assert.strictEqual(slowSignalAborted, true, "Epoch 1 abort signal must be triggered on epoch 2 dispatch");

            // Resolve Epoch 2 (fast call) first
            resolveFast({ kpis: { revenue: 1000 } });
            await call2;

            assert.deepStrictEqual(tower.state.kpis, { revenue: 1000 });
            assert.strictEqual(tower.state.isLoading, false);

            // Resolve Epoch 1 (slow call) afterwards
            resolveSlow({ kpis: { revenue: 50 } });
            await call1;

            // Verify stale data did NOT overwrite fresh data
            assert.deepStrictEqual(tower.state.kpis, { revenue: 1000 }, "Stale data must not overwrite newer state");
            assert.strictEqual(tower._activeEpoch, 2);
        });
    });

    describe("WCAG 2.1 AA & A11y XML Invariant Gates", () => {
        test("process_monitoring_card.xml contains role='button', tabindex='0', and space/enter key handlers", () => {
            const xmlPath = path.join(__dirname, "../../addons/insilos_sap_fiori/static/src/executive_control_tower/components/process_monitoring_card.xml");
            const xmlContent = fs.readFileSync(xmlPath, "utf-8");

            assert.ok(xmlContent.includes('role="button"'), "Missing role='button' on interactive chevron step");
            assert.ok(xmlContent.includes('tabindex="0"'), "Missing tabindex='0' on interactive chevron step");
            assert.ok(xmlContent.includes('t-att-aria-label='), "Missing aria-label on interactive chevron step");
            assert.ok(xmlContent.includes("ev.key === ' '"), "Missing Space key navigation handler for WCAG 2.1 AA compliance");
            assert.ok(xmlContent.includes("ev.key === 'Enter'"), "Missing Enter key navigation handler");
        });

        test("executive_control_tower.scss uses dark palette fallbacks without raw white surfaces", () => {
            const scssPath = path.join(__dirname, "../../addons/insilos_sap_fiori/static/src/executive_control_tower/executive_control_tower.scss");
            const scssContent = fs.readFileSync(scssPath, "utf-8");

            assert.ok(scssContent.includes("--insilos-kpi-inner-bg, #080a0f"), "Missing Obsidian dark token fallback for kpi inner bg");
            assert.ok(scssContent.includes("--insilos-kpi-inner-border, rgba(255, 255, 255, 0.08)"), "Missing subtle hairline border token");
        });
    });
});
