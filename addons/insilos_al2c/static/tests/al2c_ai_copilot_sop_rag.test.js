/** @odoo-module **/

import { expect, test } from "@insilos/hoot";
import { animationFrame } from "@insilos/hoot-mock";
import { mountWithCleanup, onRpc } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { AiConciergeWidget } from "@insilos_al2c/js/ai_concierge_widget";

defineMailModels();

/**
 * Register MockServer RPC handlers for /innoria/ai_concierge/* routes via onRpc.
 *
 * @param {Function} handler - Optional custom handler (url, params) => result
 * @returns {Function} no-op restore function (MockServer auto-cleans after test)
 */
function stubFetch(handler) {
    const routes = [
        "/innoria/ai_concierge/services_catalog",
        "/innoria/ai_concierge/estimate_service",
        "/innoria/ai_concierge/security_challenge",
        "/innoria/ai_concierge/query",
        "/innoria/ai_concierge/ask",
        "/innoria/ai_concierge/book_lead",
    ];
    for (const route of routes) {
        onRpc(route, async (request) => {
            let params = {};
            try {
                const parsed = await request.json();
                params = parsed?.params || parsed || {};
            } catch {
                params = {};
            }

            let customResult = handler ? handler(route, params) : null;
            if (customResult && typeof customResult.then === "function") {
                customResult = await customResult;
            }
            if (customResult !== undefined && customResult !== null) {
                return customResult;
            }

            if (route.includes("/services_catalog")) {
                return {
                    services: null,
                    pct_token: "pct.test.token.01",
                    capability_budget_remaining: 3,
                    security_challenge: {
                        challenge_token: "chal_default_123",
                        question: "6 + 4 = ?",
                        operand_a: 6,
                        operand_b: 4,
                    },
                };
            }
            if (route.includes("/estimate_service")) {
                return new Response("Fallback to local estimate", { status: 503 });
            }
            if (route.includes("/security_challenge")) {
                return {
                    challenge_token: "chal_default_123",
                    question: "6 + 4 = ?",
                    operand_a: 6,
                    operand_b: 4,
                };
            }
            if (route.includes("/query") || route.includes("/ask")) {
                return {
                    success: true,
                    answer: "Mặc định AI Concierge phản hồi câu hỏi kiến trúc.",
                    citations: ["[KMS | Software Squad | SOP-SW-01 | innoria]"],
                    grounded: true,
                    entailment_score: 0.95,
                    matched_pillar: "sw_squad",
                };
            }
            if (route.includes("/book_lead")) {
                return {
                    success: true,
                    lead_id: 101,
                    lead_name: "INNORIA-AL2C-101",
                    fit_score: 90,
                    fast_track_priority: false,
                    qualification_state: "qualified",
                    message: "Tiếp nhận thành công",
                };
            }
            return {};
        });
    }

    return () => {};
}

test("@insilos_al2c/ai_concierge/initializes 6 software engineering services catalog and default estimate", async () => {
    const restoreFetch = stubFetch((url) => {
        if (url.includes("/services_catalog")) {
            return {
                services: null,
                pct_token: "pct.test.token.01",
                capability_budget_remaining: 3,
            };
        }
        return null;
    });

    try {
        const comp = await mountWithCleanup(AiConciergeWidget);
        await animationFrame();

        expect(comp.state.servicesCatalog.length).toBe(6);
        const codes = comp.state.servicesCatalog.map((s) => s.code);
        expect(codes).toEqual(["sw_squad", "sw_turnkey", "erp", "grc", "ai", "zencode"]);

        const swSquad = comp.state.servicesCatalog.find((s) => s.code === "sw_squad");
        expect(swSquad.badge.includes("TT 13/2020/TT-BTTTT")).toBe(true);

        expect(comp.state.configurator.estimate.total_vnd > 0).toBe(true);
    } finally {
        restoreFetch();
    }
});

test("@insilos_al2c/ai_concierge/configurator recalculates estimate across service, tier, units, and duration", async () => {
    const restoreFetch = stubFetch((url) => {
        if (url.includes("/estimate_service")) {
            return null; // Delegate to deterministic local calculation in component
        }
        return null;
    });

    try {
        const comp = await mountWithCleanup(AiConciergeWidget);
        await animationFrame();

        await comp.selectConfiguratorService("sw_turnkey");
        await comp.setConfiguratorTier("enterprise");
        await comp.setConfiguratorUnits(5);
        await comp.setConfiguratorDuration(12);
        await animationFrame();

        const est = comp.state.configurator.estimate;
        expect(est.service_code).toBe("sw_turnkey");
        expect(est.scale_tier).toBe("enterprise");
        expect(est.units).toBe(5);
        expect(est.duration_months).toBe(12);
        expect(est.total_vnd).toBe(est.monthly_vnd * 12);
    } finally {
        restoreFetch();
    }
});

test("@insilos_al2c/ai_concierge/sop_rag grounded chat appends assistant answer with KMS citations and entailment score", async () => {
    const restoreFetch = stubFetch((url) => {
        if (url.includes("/ask") || url.includes("/query")) {
            return {
                success: true,
                answer: "Mô hình **Dedicated Squad** tuân thủ 7 công đoạn Thông tư 13/2020/TT-BTTTT.",
                grounded: true,
                entailment_score: 0.96,
                matched_pillar: "sw_squad",
                citations: ["[KMS | Software Squad | SOP-SW-01 | innoria]"],
                suggested_actions: [
                    {
                        icon: "ph-calculator",
                        label: "Dự Toán Squad",
                        type: "open_configurator",
                        service_code: "sw_squad",
                    },
                ],
            };
        }
        return null;
    });

    try {
        const comp = await mountWithCleanup(AiConciergeWidget);
        await animationFrame();

        comp.state.isLoading = false;
        comp.state.currentQuery = "Tư vấn thuê Squad kỹ sư";
        await comp.sendMessage();
        await animationFrame();

        const lastMsg = comp.state.messages[comp.state.messages.length - 1];
        expect(lastMsg.sender).toBe("assistant");
        expect(lastMsg.grounded).toBe(true);
        expect(lastMsg.entailment_score).toBe(0.96);
        expect(lastMsg.citations[0]).toBe("[KMS | Software Squad | SOP-SW-01 | innoria]");
    } finally {
        restoreFetch();
    }
});

test("@insilos_al2c/ai_concierge/waf security guard increments strike count and activates cooldown lockout", async () => {
    const restoreFetch = stubFetch((url) => {
        if (url.includes("/ask") || url.includes("/query")) {
            return {
                blocked: true,
                error: "WAF Policy Violation",
                strike_count: 3,
                locked_out: true,
                cooldown_seconds: 60,
                quarantine_seal: "abcdef1234567890abcdef",
            };
        }
        return null;
    });

    try {
        const comp = await mountWithCleanup(AiConciergeWidget);
        await animationFrame();

        comp.state.isLoading = false;
        comp.state.currentQuery = "SELECT * FROM users; DROP TABLE crm_lead;";
        await comp.sendMessage();
        await animationFrame();

        expect(comp.state.chatSecurity.strikeCount).toBe(3);
        expect(comp.state.chatSecurity.lockedOut).toBe(true);
        expect(comp.state.chatSecurity.warningBanner).toBe("WAF Policy Violation");

        if (comp._cooldownTimer) {
            clearInterval(comp._cooldownTimer);
            comp._cooldownTimer = null;
        }
    } finally {
        restoreFetch();
    }
});

test("@insilos_al2c/ai_concierge/lead capture anti_spam blocks honeypot and validates fields and arithmetic challenge", async () => {
    const restoreFetch = stubFetch(() => null);

    try {
        const comp = await mountWithCleanup(AiConciergeWidget);
        await animationFrame();

        // 1. Honeypot injection
        comp.state.leadForm.website_url_hp = "http://bot.spam";
        await comp.submitLeadForm();
        await animationFrame();

        expect(Boolean(comp.state.leadErrorMessage)).toBe(true);
        expect(comp.state.leadErrorMessage.includes("Honeypot")).toBe(true);

        // 2. Clear honeypot, set valid contact information but wrong arithmetic answer
        comp.state.leadForm.website_url_hp = "";
        comp.state.leadForm.name = "Nguyễn Văn An";
        comp.state.leadForm.email = "an.nguyen@enterprise.vn";
        comp.state.leadForm.company_name = "Công ty CP Công Nghệ Số Quốc Gia";
        comp.state.leadForm.security_answer = "999";

        await comp.submitLeadForm();
        await animationFrame();

        expect(Boolean(comp.state.leadFieldErrors.security_answer)).toBe(true);
    } finally {
        restoreFetch();
    }
});

test("@insilos_al2c/ai_concierge/lead capture submits valid B2B inquiry with fast_track priority attachments", async () => {
    const restoreFetch = stubFetch((url) => {
        if (url.includes("/book_lead")) {
            return {
                success: true,
                lead_id: 889,
                lead_name: "INNORIA-AL2C-889",
                fit_score: 95,
                fast_track_priority: true,
                qualification_state: "qualified",
                message: "Tiếp nhận thành công",
            };
        }
        return null;
    });

    try {
        const comp = await mountWithCleanup(AiConciergeWidget);
        await animationFrame();

        comp.state.leadForm.name = "Nguyễn Văn An";
        comp.state.leadForm.email = "an.nguyen@enterprise.vn";
        comp.state.leadForm.phone = "0903123456";
        comp.state.leadForm.company_name = "Công ty CP Công Nghệ Số Quốc Gia";
        comp.state.leadForm.security_answer = String(comp.state.securityChallenge.expected);
        comp.state.leadForm.attachments = [
            {
                name: "RFP_Spec.pdf",
                type: "application/pdf",
                size: 12400,
                data: "JVBERi0xLjQK",
            },
        ];

        await comp.submitLeadForm();
        await animationFrame();

        expect(comp.state.leadSuccessMessage).toBe("Tiếp nhận thành công");

        const lastMsg = comp.state.messages[comp.state.messages.length - 1];
        expect(lastMsg.text.includes("#889")).toBe(true);
        expect(lastMsg.text.includes("ƯU TIÊN CAO")).toBe(true);
    } finally {
        restoreFetch();
    }
});

test("@insilos_al2c/ai_concierge/phosphor duotone icon helpers resolve canonical symbol IDs and strip emojis", async () => {
    const restoreFetch = stubFetch(() => null);

    try {
        const comp = await mountWithCleanup(AiConciergeWidget);
        await animationFrame();

        expect(comp.getServiceIcon({ code: "sw_squad" })).toBe("ph-users-three");
        expect(comp.getServiceIcon({ code: "grc" })).toBe("ph-shield-check");
        expect(comp.getActionIcon({ type: "open_configurator" })).toBe("ph-calculator");
        expect(comp.stripLeadingEmoji("👨‍💻 Đội Ngũ Kỹ Sư")).toBe("Đội Ngũ Kỹ Sư");
    } finally {
        restoreFetch();
    }
});

test("@insilos_al2c/ai_concierge/global bridge window.InnoriaAiConcierge opens configurator and lead tabs", async () => {
    const restoreFetch = stubFetch(() => null);

    try {
        const comp = await mountWithCleanup(AiConciergeWidget);
        await animationFrame();

        expect(Boolean(window.InnoriaAiConcierge)).toBe(true);

        window.InnoriaAiConcierge.openConfigurator("erp");
        await animationFrame();

        expect(comp.state.isOpen).toBe(true);
        expect(comp.state.activeTab).toBe("services");
        expect(comp.state.configurator.service_code).toBe("erp");

        window.InnoriaAiConcierge.openLead("grc");
        await animationFrame();

        expect(comp.state.activeTab).toBe("lead");
    } finally {
        restoreFetch();
    }
});
