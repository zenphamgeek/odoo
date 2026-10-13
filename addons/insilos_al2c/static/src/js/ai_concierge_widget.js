/** @odoo-module **/
/* =============================================================================
 * INNORIA PUBLIC AI CONCIERGE OWL 2 COMPONENT
 * Part of Insilos AL2C Enterprise Architecture (SOP-AI-004 & SOP-RAG-003)
 * Standards: OWL 2 Reactive Component, Grounded KMS, Zero Bare White
 * ============================================================================= */

import { Component, useState, onMounted, useRef, markup } from "@odoo/owl";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { mountComponent } from "@web/env";
import { whenReady } from "@insilos/owl";

/**
 * Safely escape HTML characters.
 * @param {string} text
 * @returns {string}
 */
function escapeHtml(text) {
    const map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    };
    return String(text || "").replace(/[&<>"']/g, (m) => map[m]);
}

/**
 * Parse basic markdown formatting into safe, styled HTML elements.
 * @param {string} markdown
 * @returns {string}
 */
function parseMarkdownToHtml(markdown) {
    if (!markdown) {
        return "";
    }
    let html = escapeHtml(markdown);

    // Markdown headers
    html = html.replace(/^###\s+(.+)$/gm, '<h6 class="al2c-bubble-heading mb-1 text-primary fw-bold">$1</h6>');
    html = html.replace(/^##\s+(.+)$/gm, '<h5 class="al2c-bubble-heading mb-1 text-primary fw-bold">$1</h5>');

    // Bold formatting: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="al2c-bold-text">$1</strong>');

    // Italic formatting: *text*
    html = html.replace(/\*([^*]+)\*/g, '<em class="al2c-italic-text">$1</em>');

    // Inline code: `text`
    html = html.replace(/`([^`]+)`/g, '<code class="al2c-inline-code">$1</code>');

    // Bullet points: • or - or *
    html = html.replace(
        /^[•\-*]\s+(.+)$/gm,
        '<div class="al2c-list-item"><span class="al2c-list-bullet" aria-hidden="true">•</span><span>$1</span></div>'
    );

    // Double line breaks -> paragraph separator
    html = html.replace(/\n\n+/g, '<div class="al2c-para-break"></div>');

    // Single line break -> <br/>
    html = html.replace(/\n/g, '<br/>');

    return html;
}

/**
 * Execute standard Odoo JSON-RPC 2.0 call with CSRF token support.
 * @param {string} url
 * @param {Object} params
 * @returns {Promise<any>}
 */
async function callJsonRpc(url, params = {}) {
    let csrfToken = "";
    if (typeof odoo !== "undefined" && odoo.csrf_token) {
        csrfToken = odoo.csrf_token;
    } else {
        const metaTag = document.querySelector("meta[name='csrf-token']");
        if (metaTag) {
            csrfToken = metaTag.getAttribute("content") || "";
        }
    }

    const payload = {
        jsonrpc: "2.0",
        method: "call",
        params: params,
        id: Math.floor(Math.random() * 1000000),
    };

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    if (data.error) {
        const errorMsg = data.error.data?.message || data.error.message || "Lỗi giao tiếp máy chủ";
        throw new Error(errorMsg);
    }
    return data.result;
}

/**
 * Innoria Public AI Concierge OWL 2 Component
 */
export class AiConciergeWidget extends Component {
    static template = "innoria.ai_concierge_widget";

    setup() {
        this.messagesContainerRef = useRef("messagesContainer");
        this.queryInputRef = useRef("queryInput");

        this.state = useState({
            isOpen: false,
            isLoading: false,
            showLeadForm: false,
            leadSuccessMessage: null,
            leadErrorMessage: null,
            currentQuery: "",
            selectedPillar: "enterprise",
            leadForm: {
                name: "",
                email: "",
                phone: "",
                company_name: "",
                product_interest: "Insilos ERP (VAS & Hóa đơn ĐT Nghị định 70/2025)",
                employee_count: "50 - 200 nhân sự",
                notes: "",
            },
            messages: [
                {
                    id: "welcome-01",
                    sender: "assistant",
                    text: "Kính chào Quý khách! Tôi là Executive AI Concierge của Innoria.\n\nTôi sẵn sàng giải đáp kiến trúc giải pháp, báo giá dự toán và phương pháp luận triển khai cho:\n• **Insilos ERP:** Nền tảng quản trị tài chính kế toán VAS & Hóa đơn điện tử Nghị định 70/2025/NĐ-CP.\n• **Vertical Resilience:** Hệ thống quản trị rủi ro GRC, kiểm soát nội bộ & ISO 27001 / PDPD 13/2023.\n• **Mojo AI:** Tác tử AL2C Swarm, RAG triệt tiêu ảo giác & bóc tách chứng từ thông minh.\n• **Zencode Ent:** Hiện đại hóa mã kế thừa, điều phối cụm AGY Fleet & 13 cổng kiểm soát kỹ thuật.\n\nQuý khách có thể bấm chọn câu hỏi nhanh bên dưới hoặc nhập câu hỏi trực tiếp!",
                    formattedText: null,
                    citations: [
                        "[KMS | Master Architecture | SOP-00 | innoria]",
                        "[KMS | AL2C Foundation | SOP-12 | innoria]",
                    ],
                    citationsExpanded: false,
                    grounded: true,
                    entailment_score: 0.96,
                    reason: "Thông tin được trích xuất trực tiếp từ tài liệu kiến trúc quy chuẩn Innoria KMS (SOP-00 đến SOP-12).",
                    suggested_actions: [
                        {
                            label: "Báo giá ERP Starter",
                            action: "prompt",
                            text: "Báo giá và phạm vi triển khai gói Insilos ERP Starter cho doanh nghiệp?",
                        },
                        {
                            label: "Tư vấn GRC & ISO 27001",
                            action: "prompt",
                            text: "Tư vấn giải pháp quản trị rủi ro GRC và tuân thủ ISO 27001, Nghị định 13/2023?",
                        },
                        {
                            label: "Đăng ký Demo Mojo AI",
                            action: "book_lead",
                            pillar: "ai",
                        },
                        {
                            label: "Hiện đại hóa mã nguồn Zencode",
                            action: "prompt",
                            text: "Năng lực và quy trình hiện đại hóa mã nguồn kế thừa của Zencode Ent?",
                        },
                    ],
                    time: this.getNowTime(),
                },
            ],
        });

        // Preformat initial greeting message
        this.state.messages[0].formattedText = markup(parseMarkdownToHtml(this.state.messages[0].text));

        onMounted(() => {
            this.scrollToBottom();
        });
    }

    /**
     * Get current HH:MM timestamp.
     * @returns {string}
     */
    getNowTime() {
        const d = new Date();
        return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
    }

    /**
     * Auto-scroll message container to bottom.
     */
    scrollToBottom() {
        setTimeout(() => {
            if (this.messagesContainerRef && this.messagesContainerRef.el) {
                this.messagesContainerRef.el.scrollTop = this.messagesContainerRef.el.scrollHeight;
            }
        }, 60);
    }

    /**
     * Toggle open/close state of chat drawer.
     */
    toggleDrawer() {
        this.state.isOpen = !this.state.isOpen;
        if (this.state.isOpen) {
            this.scrollToBottom();
            setTimeout(() => {
                if (this.queryInputRef && this.queryInputRef.el) {
                    this.queryInputRef.el.focus();
                }
            }, 200);
        }
    }

    /**
     * Reset chat messages to default welcome message.
     */
    clearChat() {
        const welcome = this.state.messages[0];
        welcome.citationsExpanded = false;
        this.state.messages = [welcome];
        this.state.currentQuery = "";
        this.state.leadSuccessMessage = null;
        this.state.leadErrorMessage = null;
        this.scrollToBottom();
    }

    /**
     * Open lead capture drawer section.
     * @param {string} pillar
     */
    openLeadForm(pillar = "all") {
        this.state.showLeadForm = true;
        this.state.leadSuccessMessage = null;
        this.state.leadErrorMessage = null;

        if (pillar && pillar !== "all") {
            const pillarMap = {
                erp: "Insilos ERP (VAS & Hóa đơn ĐT Nghị định 70/2025)",
                grc: "Vertical Resilience (GRC, ISO 27001 & PDPD 13/2023)",
                ai: "Mojo AI (Tác tử AL2C & Bóc tách thông minh)",
                zencode: "Zencode Ent (Hiện đại hóa mã kế thừa & AGY Fleet)",
                enterprise: "Hệ sinh thái Tứ Trụ Toàn Diện (ERP + GRC + AI + Zencode)",
            };
            if (pillarMap[pillar]) {
                this.state.leadForm.product_interest = pillarMap[pillar];
            }
        }
    }

    /**
     * Close lead capture drawer section.
     */
    closeLeadForm() {
        this.state.showLeadForm = false;
        this.state.leadSuccessMessage = null;
        this.state.leadErrorMessage = null;
        this.scrollToBottom();
    }

    /**
     * Update specific field in lead capture form.
     * @param {string} field
     * @param {Event} ev
     */
    updateLeadField(field, ev) {
        this.state.leadForm[field] = ev.target.value;
    }

    /**
     * Update query input value.
     * @param {Event} ev
     */
    updateQuery(ev) {
        this.state.currentQuery = ev.target.value;
    }

    /**
     * Handle keydown event in textarea (Enter to send, Shift+Enter for newline).
     * @param {KeyboardEvent} ev
     */
    onInputKeyDown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    /**
     * Toggle visibility of citation chips for a message.
     * @param {Object} msg
     */
    toggleCitations(msg) {
        msg.citationsExpanded = !msg.citationsExpanded;
    }

    /**
     * Handle clicks on suggested action chips.
     * @param {Object} act
     */
    onSuggestedActionClick(act) {
        if (act.action === "book_meeting" || act.action === "book_lead") {
            this.openLeadForm(act.pillar || this.state.selectedPillar);
        } else if (act.action === "prompt" || !act.action) {
            const query = act.text || act.label;
            this.sendQuickPrompt(query);
        } else if (act.action === "download_catalog") {
            this.openLeadForm("enterprise");
        }
    }

    /**
     * Dispatch a pre-defined quick prompt.
     * @param {string} promptText
     */
    sendQuickPrompt(promptText) {
        this.state.currentQuery = promptText;
        this.sendMessage();
    }

    /**
     * Send user query to AI Concierge API.
     */
    async sendMessage() {
        const query = (this.state.currentQuery || "").trim();
        if (!query || this.state.isLoading) {
            return;
        }

        this.state.currentQuery = "";
        this.state.messages.push({
            id: `usr-${Date.now()}`,
            sender: "user",
            text: query,
            time: this.getNowTime(),
        });
        this.scrollToBottom();

        this.state.isLoading = true;

        try {
            const result = await callJsonRpc("/innoria/ai_concierge/query", {
                query: query,
                product_focus: this.state.selectedPillar,
                lang: "vi",
            });

            if (result && result.success) {
                this.state.messages.push({
                    id: `ai-${Date.now()}`,
                    sender: "assistant",
                    text: result.answer,
                    formattedText: markup(parseMarkdownToHtml(result.answer)),
                    citations: result.citations || [],
                    citationsExpanded: false,
                    grounded: result.grounded !== false,
                    entailment_score: typeof result.entailment_score === "number" ? result.entailment_score : 0.88,
                    reason: result.reason || "",
                    suggested_actions: result.suggested_actions || [],
                    time: this.getNowTime(),
                });
                if (result.matched_pillar) {
                    this.state.selectedPillar = result.matched_pillar;
                }
            } else {
                const errorMsg = result?.error || "Không thể tải phản hồi từ AI Concierge lúc này.";
                this.state.messages.push({
                    id: `ai-err-${Date.now()}`,
                    sender: "assistant",
                    text: errorMsg,
                    formattedText: markup(parseMarkdownToHtml(errorMsg)),
                    citations: [],
                    citationsExpanded: false,
                    grounded: false,
                    entailment_score: 0,
                    reason: "",
                    suggested_actions: [
                        {
                            label: "Đăng Ký Tư Vấn Trực Tiếp",
                            action: "book_lead",
                            pillar: this.state.selectedPillar,
                        },
                    ],
                    time: this.getNowTime(),
                });
            }
        } catch (err) {
            const fallbackText =
                "Đã xảy ra sự cố kết nối tới dịch vụ AI Concierge. Quý khách vui lòng thử lại hoặc gửi yêu cầu tư vấn để Chuyên gia Innoria hỗ trợ trực tiếp.";
            this.state.messages.push({
                id: `ai-err-${Date.now()}`,
                sender: "assistant",
                text: fallbackText,
                formattedText: markup(parseMarkdownToHtml(fallbackText)),
                citations: [],
                citationsExpanded: false,
                grounded: false,
                entailment_score: 0,
                reason: err.message || "",
                suggested_actions: [
                    {
                        label: "Đăng Ký Tư Vấn Doanh Nghiệp",
                        action: "book_lead",
                        pillar: "enterprise",
                    },
                ],
                time: this.getNowTime(),
            });
        } finally {
            this.state.isLoading = false;
            this.scrollToBottom();
        }
    }

    /**
     * Submit lead capture form to /innoria/ai_concierge/book_lead.
     */
    async submitLeadForm() {
        const form = this.state.leadForm;
        if (!form.name || !form.name.trim()) {
            this.state.leadErrorMessage = "Vui lòng nhập họ và tên của Quý khách.";
            return;
        }
        if ((!form.email || !form.email.trim()) && (!form.phone || !form.phone.trim())) {
            this.state.leadErrorMessage = "Vui lòng cung cấp ít nhất Email hoặc Số điện thoại để chuyên gia liên hệ.";
            return;
        }
        if (!form.company_name || !form.company_name.trim()) {
            this.state.leadErrorMessage = "Vui lòng nhập tên công ty hoặc tổ chức của Quý khách.";
            return;
        }

        this.state.leadErrorMessage = null;
        this.state.leadSuccessMessage = null;
        this.state.isLoading = true;

        try {
            const result = await callJsonRpc("/innoria/ai_concierge/book_lead", {
                name: form.name.trim(),
                email: form.email.trim(),
                phone: form.phone.trim(),
                company_name: form.company_name.trim(),
                product_interest: form.product_interest,
                employee_count: form.employee_count,
                notes: form.notes ? form.notes.trim() : "",
            });

            if (result && result.success) {
                const successMsg =
                    result.message || "Yêu cầu khảo sát của Quý khách đã được tiếp nhận thành công.";
                this.state.leadSuccessMessage = successMsg;

                // Add confirmation assistant message to chat thread
                const confirmText =
                    `🎉 **Tiếp nhận hồ sơ thành công!**\n\n` +
                    `Kính chào Quý khách **${form.name}** (${form.company_name}), yêu cầu tư vấn giải pháp **${form.product_interest}** ` +
                    `đã được khởi tạo thành công trên hệ thống Innoria AL2C.\n` +
                    `• **Mã hồ sơ CRM:** #${result.lead_id} (${result.lead_name})\n` +
                    `• **Điểm đánh giá tiềm năng B2B (Fit Score):** ${Math.round(result.fit_score)}/100\n` +
                    `• **Phân hạng:** ${result.qualification_state === "qualified" ? "Ưu tiên cao (Qualified)" : "Đang xử lý (In Progress)"}\n\n` +
                    `Chuyên gia Solution Architect phụ trách khối doanh nghiệp sẽ liên hệ với Quý khách qua **${form.email || form.phone}** trong vòng 24 giờ làm việc.`;

                this.state.messages.push({
                    id: `ai-lead-${Date.now()}`,
                    sender: "assistant",
                    text: confirmText,
                    formattedText: markup(parseMarkdownToHtml(confirmText)),
                    citations: ["[KMS | Lead-to-Cash SLA | SOP-AI-004 | innoria]"],
                    citationsExpanded: false,
                    grounded: true,
                    entailment_score: 1.0,
                    reason: "Đã tạo Lead trên hệ thống crm.lead với BANT qualification và cam kết SLA phản hồi 24h.",
                    suggested_actions: [],
                    time: this.getNowTime(),
                });

                // Auto-close lead drawer after 2.5 seconds and return to chat view
                setTimeout(() => {
                    this.state.showLeadForm = false;
                    this.state.leadSuccessMessage = null;
                    this.scrollToBottom();
                }, 2500);

                // Reset notes
                this.state.leadForm.notes = "";
            } else {
                this.state.leadErrorMessage =
                    result?.error || "Không thể tiếp nhận yêu cầu lúc này. Quý khách vui lòng thử lại sau ít phút.";
            }
        } catch (err) {
            this.state.leadErrorMessage = err.message || "Đã xảy ra lỗi khi gửi yêu cầu.";
        } finally {
            this.state.isLoading = false;
        }
    }
}

/**
 * Public Interaction Hook for mounting on #innoria_ai_concierge_root
 */
export class AiConciergeInteraction extends Interaction {
    static selector = "#innoria_ai_concierge_root";

    setup() {
        if (!this.el.dataset.conciergeMounted) {
            this.el.dataset.conciergeMounted = "true";
            this.mountComponent(this.el, AiConciergeWidget);
        }
    }
}

registry.category("public.interactions").add("insilos_al2c.ai_concierge", AiConciergeInteraction);

/**
 * Standalone DOM ready fallback mounting
 */
whenReady(async () => {
    const el = document.getElementById("innoria_ai_concierge_root");
    if (el && !el.dataset.conciergeMounted) {
        el.dataset.conciergeMounted = "true";
        try {
            await mountComponent(AiConciergeWidget, el, { name: "Innoria AI Concierge" });
        } catch (err) {
            // Handled or already mounted by interaction
        }
    }
});
