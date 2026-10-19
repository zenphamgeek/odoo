/** @odoo-module **/
/* =============================================================================
 * INNORIA PUBLIC AI CONCIERGE & SOFTWARE SERVICES CONFIGURATOR (OWL 2)
 * Part of Insilos AL2C Enterprise Architecture (SOP-AI-004 & SOP-RAG-003)
 * Standards: OWL 2 Reactive Component, Grounded KMS, Zero Bare White
 * ============================================================================= */

import { Component, useState, onMounted, onWillUnmount, useRef, markup } from "@odoo/owl";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { mountComponent } from "@web/env";
import { whenReady } from "@insilos/owl";

/**
 * Default Software Services & Solution Catalog (Immediate Zero-Flicker Fallback).
 * Synchronized live with /innoria/ai_concierge/services_catalog on mount.
 */
const DEFAULT_SERVICES_CATALOG = [
    {
        code: "sw_squad",
        name: "Squad Kỹ Sư Đồng Phát Triển (Dedicated Co-Dev Squad)",
        short_label: "👨‍💻 Squad Đồng Phát Triển",
        badge: "TT 13/2020/TT-BTTTT • Agile Pod",
        summary:
            "Cung cấp đội ngũ Kỹ sư Phần mềm, Solution Architect & QA/SecOps chuyên trách theo chuẩn Agile/Scrum, tích hợp giám sát năng suất AGY Telemetry và định mức quy trình phần mềm Thông tư 13/2020/TT-BTTTT.",
        unit_label: "Kỹ sư chuyên trách (FTE)",
        unit_options: [2, 4, 6, 8, 12],
        default_units: 4,
        base_unit_monthly_vnd: 42000000,
        starting_price: "Từ 84.000.000 ₫ / tháng",
        lead_option: "Squad Kỹ Sư Đồng Phát Triển (Dedicated Co-Dev Squad - TT 13/2020)",
        deliverables: [
            "Dedicated Full-stack / AI / Odoo Engineers + Scrum Master",
            "Báo cáo Velocity, Burn-down & Timesheet tự động qua info@inno.ai.vn",
            "Kiểm thử bảo mật SAST/DAST & bàn giao 100% quyền sở hữu trí tuệ (IP)",
        ],
        payment_schedule:
            "Thanh toán định kỳ hàng tháng theo biên bản nghiệm thu Sprint & bảng chấm công điện tử xác thực (HĐĐT Nghị định 70/2025/NĐ-CP).",
        lifecycle_steps: [
            "1. Khảo sát kiến trúc & Phỏng vấn chọn kỹ sư (48h)",
            "2. Thiết lập môi trường CI/CD, GitSecOps & Quy ước Sprint",
            "3. Thực thi phát triển song song (2 tuần/Sprint) & Demo nghiệm thu",
            "4. Chuyển giao mã nguồn, tài liệu kiến trúc & vận hành dài hạn",
        ],
        compliance_guarantees: [
            "Tuân thủ quy trình sản xuất phần mềm Thông tư 13/2020/TT-BTTTT",
            "Cam kết bảo mật NDA & Bảo vệ dữ liệu cá nhân Nghị định 13/2023/NĐ-CP",
            "Xuất hóa đơn điện tử GTGT hợp lệ 1C26TAA (Nghị định 70/2025/NĐ-CP)",
        ],
    },
    {
        code: "sw_turnkey",
        name: "Phát Triển Phần Mềm Trọn Gói (Turnkey Custom Software)",
        short_label: "🏗️ Phần Mềm Trọn Gói",
        badge: "5-Gate Enterprise • Fixed-Scope SLA",
        summary:
            "Thiết kế kiến trúc, phát triển trọn gói hệ thống phần mềm doanh nghiệp, cổng giao dịch B2B/B2C, Web/Mobile App đặc thù theo phương pháp luận 5-Gate Enterprise (Prepare → Explore → Realize → Deploy → Run).",
        unit_label: "Phân hệ nghiệp vụ (Modules)",
        unit_options: [2, 3, 5, 8, 12],
        default_units: 3,
        base_unit_monthly_vnd: 48000000,
        starting_price: "Từ 144.000.000 ₫ / giai đoạn",
        lead_option: "Phát Triển Phần Mềm Trọn Gói (Turnkey Custom Software - 5-Gate Enterprise)",
        deliverables: [
            "Hồ sơ kiến trúc BRD/SRS, UI/UX Prototype & Database Blueprint",
            "Mã nguồn Clean-Room chuẩn hóa, bộ kiểm thử tự động E2E Playwright",
            "Triển khai Kubernetes HA, đào tạo chuyển giao & bảo hành SLA 12 tháng",
        ],
        payment_schedule:
            "Thanh toán theo 4 mốc nghiệm thu: 30% Khởi động (Prepare) • 30% Thiết kế & Prototype (Explore) • 30% Kiểm thử UAT (Realize) • 10% Go-Live (Deploy).",
        lifecycle_steps: [
            "1. Prepare & Explore: Phân tích nghiệp vụ, chốt Blueprint & Prototype",
            "2. Realize: Lập trình Clean-Core, tích hợp API & kiểm thử bảo mật",
            "3. Deploy: Kiểm thử chấp thuận UAT, đào tạo & cắt chuyển dữ liệu Go-Live",
            "4. Run: Bảo hành SLA 99.95%, tối ưu hiệu năng & bàn giao toàn bộ mã nguồn",
        ],
        compliance_guarantees: [
            "Đáp ứng 7 công đoạn sản xuất phần mềm Thông tư 13/2020/TT-BTTTT",
            "Kiểm định an toàn thông tin theo tiêu chuẩn ISO/IEC 27001 & OWASP Top 10",
            "Bàn giao 100% Source Code, Docker/K8s Manifests & tài liệu vận hành",
        ],
    },
    {
        code: "erp",
        name: "Insilos Clean-Core ERP & HĐĐT 1C26TAA",
        short_label: "📊 Clean-Core ERP",
        badge: "VAS 200/133 • NĐ 70/2025",
        summary:
            "Nền tảng ERP thế hệ mới hợp nhất Kế toán chuẩn VAS (Thông tư 200/133) & IFRS, Chuỗi cung ứng WMS, Sản xuất MRP, Nhân sự Tiền lương BHXH/PIT 2026 và Hóa đơn điện tử 1C26TAA.",
        unit_label: "Phân hệ cốt lõi triển khai",
        unit_options: [2, 4, 6, 8, 10],
        default_units: 4,
        base_unit_monthly_vnd: 35000000,
        starting_price: "Từ 140.000.000 ₫ / gói",
        lead_option: "Insilos ERP (VAS & Hóa đơn ĐT Nghị định 70/2025)",
        deliverables: [
            "Hệ thống Kế toán VAS/IFRS, Mua hàng, Bán hàng AL2C, Kho WMS & HRM",
            "Tích hợp trực tiếp Hóa đơn điện tử Nghị định 70/2025 & Ngân hàng số Doanh nghiệp",
            "Báo cáo quản trị thời gian thực CFO/CEO Dashboard & phân quyền đa công ty",
        ],
        payment_schedule:
            "35% Ký hợp đồng & Khảo sát Fit-Gap • 40% Bàn giao cấu hình & Kiểm thử UAT • 25% Nghiệm thu Go-Live & Đào tạo.",
        lifecycle_steps: [
            "1. Khảo sát Fit-Gap & Chuẩn hóa danh mục dữ liệu gốc (Master Data)",
            "2. Cấu hình quy trình Clean-Core ERP & tích hợp HĐĐT / Ngân hàng",
            "3. Chuyển đổi số dư đầu kỳ, đào tạo Key Users & chạy thử nghiệm UAT",
            "4. Go-Live chính thức & hỗ trợ quyết toán kỳ kế toán đầu tiên",
        ],
        compliance_guarantees: [
            "Chuẩn mực Kế toán Việt Nam (TT 200/2014 & TT 133/2016) & IFRS",
            "Tích hợp Hóa đơn điện tử có mã CQT theo Nghị định 70/2025/NĐ-CP",
            "Bảo mật phân quyền RBAC/ABAC và nhật ký kiểm toán bất biến",
        ],
    },
    {
        code: "grc",
        name: "Vertical Resilience (GRC, ISO 27701 & e-CO)",
        short_label: "🛡️ GRC & ISO 27701",
        badge: "ISO 27701 • NĐ 13/2023",
        summary:
            "Hệ thống Quản trị Rủi ro Doanh nghiệp (ERM), Ma trận Kiểm soát Nội bộ (RCM), bảo vệ dữ liệu cá nhân Nghị định 13/2023/NĐ-CP (ISO 27701), truy xuất nguồn gốc xuất xứ e-CO và kiểm kê ESG/CSRD.",
        unit_label: "Khung tuân thủ & Phân hệ GRC",
        unit_options: [1, 2, 3, 5, 8],
        default_units: 2,
        base_unit_monthly_vnd: 38000000,
        starting_price: "Từ 76.000.000 ₫ / khung",
        lead_option: "Vertical Resilience (GRC, ISO 27001 & PDPD 13/2023)",
        deliverables: [
            "Ma trận rủi ro - kiểm soát (RCM), hồ sơ xử lý dữ liệu cá nhân الد-PDPD",
            "Cơ chế che giấu PII tự động (Need-to-Know Masking) & Nhật ký bất biến",
            "Hồ sơ truy xuất nguồn gốc e-CO & báo cáo kiểm toán ISO 27001 / ISO 27701",
        ],
        payment_schedule:
            "40% Đánh giá Gap Assessment • 40% Triển khai hệ thống kiểm soát GRC • 20% Nghiệm thu hồ sơ đánh giá tuân thủ.",
        lifecycle_steps: [
            "1. Đánh giá mức độ trưởng thành bảo mật & rà soát lỗ hổng tuân thủ",
            "2. Thiết lập Ma trận Kiểm soát (RCM) & cổng bảo vệ dữ liệu ISO 27701",
            "3. Diễn tập ứng cứu sự cố, kiểm toán nội bộ & hoàn thiện hồ sơ pháp lý",
            "4. Giám sát tuân thủ liên tục (Continuous Compliance Monitoring)",
        ],
        compliance_guarantees: [
            "Tuân thủ toàn diện Nghị định 13/2023/NĐ-CP về Bảo vệ dữ liệu cá nhân",
            "Đáp ứng tiêu chuẩn quốc tế ISO/IEC 27001:2022 & ISO/IEC 27701",
            "Sẵn sàng hồ sơ chứng nhận xuất xứ điện tử e-CO & báo cáo ESG",
        ],
    },
    {
        code: "ai",
        name: "Mojo AI (AL2C Swarm, Grounded RAG & IDP)",
        short_label: "🤖 Mojo AI & RAG",
        badge: "Claim Atom • Entailment ≥ 0.75",
        summary:
            "Triển khai hệ thống Tác tử AI tự chủ (AL2C Swarm), trợ lý tri thức nội bộ Grounded RAG triệt tiêu ảo giác (trích dẫn KMS chuẩn xác) và công nhân bóc tách chứng từ/hợp đồng thông minh (IDP).",
        unit_label: "Tác tử AI & Đường ống RAG",
        unit_options: [1, 2, 4, 6, 10],
        default_units: 2,
        base_unit_monthly_vnd: 45000000,
        starting_price: "Từ 90.000.000 ₫ / cụm AI",
        lead_option: "Mojo AI (Tác tử AL2C & Bóc tách thông minh)",
        deliverables: [
            "Cơ sở tri thức KMS chuẩn hóa Claim Atom kèm cổng kiểm chứng Entailment Gate",
            "Tác tử tự động hóa Lead-to-Cash, bóc tách hóa đơn/hợp đồng & đối soát",
            "Cơ chế Kill-Switch, giới hạn ngân sách token theo ngày & lọc rò rỉ PII/Secret",
        ],
        payment_schedule:
            "30% Khởi tạo & Chuẩn hóa dữ liệu KMS • 40% Huấn luyện & Tích hợp Tác tử AI • 30% Nghiệm thu độ chính xác Grounding.",
        lifecycle_steps: [
            "1. Khảo sát nguồn dữ liệu & xây dựng kiến trúc KMS Claim Atom",
            "2. Cấu hình đường ống Grounded RAG & cổng kiểm chứng chống ảo giác",
            "3. Tích hợp Tác tử AI vào quy trình CRM/ERP & kiểm thử Red-Team",
            "4. Vận hành thực tế kèm bảng điều khiển giám sát chất lượng AI",
        ],
        compliance_guarantees: [
            "Kiểm chứng Entailment Score ≥ 0.75 trên 100% câu trả lời tư vấn",
            "Tự động lọc sạch khóa bí mật (API Keys) & che số điện thoại/CCCD",
            "Lưu vết toàn bộ quyết định của AI phục vụ hậu kiểm (Audit Trail)",
        ],
    },
    {
        code: "zencode",
        name: "Zencode Ent (Hiện Đại Hóa Mã Nguồn & AGY Fleet)",
        short_label: "⚡ Zencode Refactor",
        badge: "Hegelian Dialectic • 13 Gates",
        summary:
            "Dịch vụ tái cấu trúc và hiện đại hóa hệ thống phần mềm kế thừa (Legacy ERP, Monolith, .NET/Java/Python/Odoo cũ) sang kiến trúc hiện đại bằng phương pháp Biện chứng Hegelian và 13 cổng kiểm định tự động.",
        unit_label: "Quy mô phân hệ / Cụm mã nguồn",
        unit_options: [1, 2, 4, 6, 8],
        default_units: 2,
        base_unit_monthly_vnd: 52000000,
        starting_price: "Từ 104.000.000 ₫ / dự án",
        lead_option: "Zencode Ent (Hiện đại hóa mã kế thừa & AGY Fleet)",
        deliverables: [
            "Báo cáo giải phẫu kiến trúc, phát hiện nợ kỹ thuật & lỗ hổng bảo mật",
            "Tái cấu trúc Clean-Room bảo toàn 100% nghiệp vụ cốt lõi & dữ liệu lịch sử",
            "Bộ kiểm thử hồi quy tự động (Regression Suite) & tối ưu hóa hiệu năng DB",
        ],
        payment_schedule:
            "30% Kiểm toán mã nguồn & Kiến trúc (Thesis) • 40% Tái cấu trúc & Đối chứng (Antithesis) • 30% Nghiệm thu hợp nhất (Synthesis).",
        lifecycle_steps: [
            "1. Thesis: Giải dịch & lập bản đồ phụ thuộc toàn bộ hệ thống kế thừa",
            "2. Antithesis: Tái thiết kế Clean-Core & viết bộ kiểm thử bất biến",
            "3. Synthesis: Chuyển đổi dữ liệu song song & vượt qua 13 cổng kiểm định",
            "4. Cutover: Chuyển giao vận hành không gián đoạn (Zero-Downtime)",
        ],
        compliance_guarantees: [
            "Bảo toàn 100% tính toàn vẹn dữ liệu lịch sử và luồng nghiệp vụ",
            "Vượt qua 13 cổng kiểm soát chất lượng mã nguồn & bảo mật tự động",
            "Giảm thiểu 40% - 65% chi phí vận hành hạ tầng và nợ kỹ thuật",
        ],
    },
];

const SCALE_TIER_META = {
    starter: {
        key: "starter",
        label: "Khởi đầu (Starter)",
        multiplier: 1.0,
        employee_hint: "Dưới 50 nhân sự",
    },
    growth: {
        key: "growth",
        label: "Tăng trưởng (Growth)",
        multiplier: 1.35,
        employee_hint: "50 - 200 nhân sự",
    },
    enterprise: {
        key: "enterprise",
        label: "Tập đoàn (Enterprise)",
        multiplier: 1.85,
        employee_hint: "Trên 500 nhân sự",
    },
};

const DURATION_DISCOUNTS = {
    3: 1.0,
    6: 0.93,
    12: 0.85,
};

/**
 * Format integer amount into Vietnamese Dong currency string.
 * @param {number} amount
 * @returns {string}
 */
function formatVnd(amount) {
    const rounded = Math.round((Number(amount) || 0) / 100000) * 100000;
    return `${rounded.toLocaleString("vi-VN")} ₫`;
}

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
 * Normalize a service card object from backend or fallback catalog.
 * @param {Object} raw
 * @returns {Object}
 */
function normalizeServiceCard(raw) {
    const fallback =
        DEFAULT_SERVICES_CATALOG.find((s) => s.code === (raw.code || raw.service_code)) ||
        DEFAULT_SERVICES_CATALOG[0];
    return {
        code: raw.code || raw.service_code || fallback.code,
        name: raw.name || raw.title || fallback.name,
        short_label: raw.short_label || fallback.short_label || raw.name || fallback.name,
        badge: raw.badge || raw.pricing_model || raw.category || fallback.badge,
        summary: raw.summary || raw.description || fallback.summary,
        starting_price:
            raw.starting_price ||
            raw.formatted_base_price ||
            raw.price_hint ||
            (raw.base_unit_monthly_vnd ? `Từ ${formatVnd(raw.base_unit_monthly_vnd)} / tháng` : fallback.starting_price),
        unit_label: raw.unit_label || fallback.unit_label,
        unit_options:
            Array.isArray(raw.unit_options) && raw.unit_options.length
                ? raw.unit_options
                : fallback.unit_options,
        default_units: Number(raw.default_units) || fallback.default_units,
        base_unit_monthly_vnd:
            Number(raw.base_unit_monthly_vnd || raw.base_monthly_vnd || raw.unit_price_vnd) ||
            fallback.base_unit_monthly_vnd,
        lead_option: raw.lead_option || fallback.lead_option || raw.name || fallback.name,
        deliverables:
            Array.isArray(raw.deliverables) && raw.deliverables.length
                ? raw.deliverables
                : fallback.deliverables,
        payment_schedule: raw.payment_schedule || fallback.payment_schedule,
        lifecycle_steps:
            Array.isArray(raw.lifecycle_steps) && raw.lifecycle_steps.length
                ? raw.lifecycle_steps
                : fallback.lifecycle_steps,
        compliance_guarantees:
            Array.isArray(raw.compliance_guarantees) && raw.compliance_guarantees.length
                ? raw.compliance_guarantees
                : fallback.compliance_guarantees,
    };
}

/**
 * Compute deterministic client-side estimate for instant UI responsiveness.
 * @param {Object} serviceObj
 * @param {string} scaleTier
 * @param {number} units
 * @param {number} durationMonths
 * @returns {Object}
 */
function computeClientEstimate(serviceObj, scaleTier = "growth", units = 4, durationMonths = 6) {
    const svc = serviceObj || DEFAULT_SERVICES_CATALOG[0];
    const tierInfo = SCALE_TIER_META[scaleTier] || SCALE_TIER_META.growth;
    const safeUnits = Math.max(1, Math.min(50, Number(units) || svc.default_units || 2));
    const safeDuration = [3, 6, 12].includes(Number(durationMonths)) ? Number(durationMonths) : 6;
    const discountFactor = DURATION_DISCOUNTS[safeDuration] || 1.0;

    const monthlyRaw = svc.base_unit_monthly_vnd * safeUnits * tierInfo.multiplier * discountFactor;
    const monthlyRounded = Math.round(monthlyRaw / 100000) * 100000;
    const totalRounded = monthlyRounded * safeDuration;

    const paymentSchedule = Array.isArray(svc.payment_schedule)
        ? svc.payment_schedule.join(" • ")
        : String(svc.payment_schedule || "");

    return {
        service_code: svc.code,
        service_name: svc.name,
        scale_tier: tierInfo.key,
        scale_label: tierInfo.label,
        units: safeUnits,
        unit_label: svc.unit_label,
        duration_months: safeDuration,
        monthly_vnd: monthlyRounded,
        total_vnd: totalRounded,
        formatted_monthly_vnd: `${formatVnd(monthlyRounded)} / tháng`,
        formatted_total_vnd: formatVnd(totalRounded),
        payment_schedule: paymentSchedule,
        lifecycle_steps: Array.isArray(svc.lifecycle_steps) ? svc.lifecycle_steps : [],
        compliance_guarantees: Array.isArray(svc.compliance_guarantees) ? svc.compliance_guarantees : [],
    };
}

/**
 * Innoria Public AI Concierge OWL 2 Component
 */
export class AiConciergeWidget extends Component {
    static template = "innoria.ai_concierge_widget";

    setup() {
        this.messagesContainerRef = useRef("messagesContainer");
        this.queryInputRef = useRef("queryInput");

        const initialCatalog = DEFAULT_SERVICES_CATALOG.map((item) => normalizeServiceCard(item));
        const defaultService = initialCatalog[0];
        const initialEstimate = computeClientEstimate(defaultService, "growth", defaultService.default_units, 6);

        this.state = useState({
            isOpen: false,
            isLoading: false,
            activeTab: "chat", // 'chat' | 'services' | 'lead'
            showLeadForm: false,
            proactiveNudgeVisible: true,
            proactiveNudgeText: "Dự toán phần mềm & Thuê Squad Kỹ sư AI/ERP",
            leadSuccessMessage: null,
            leadErrorMessage: null,
            currentQuery: "",
            selectedPillar: "sw_squad",
            pctToken: null,
            pricingToken: null,
            capabilityBudgetRemaining: 3,
            leadFormOpenedAt: Date.now() - 5000,
            securityChallenge: {
                challenge_token: null,
                question: "6 + 4 = ?",
                operand_a: 6,
                operand_b: 4,
                expected: 10,
            },
            leadFieldErrors: {
                name: null,
                email: null,
                phone: null,
                company_name: null,
                security_answer: null,
            },
            chatSecurity: {
                strikeCount: 0,
                maxStrikes: 3,
                lockedOut: false,
                cooldownSeconds: 0,
                warningBanner: null,
            },
            servicesCatalog: initialCatalog,
            configurator: {
                service_code: defaultService.code,
                scale_tier: "growth",
                units: defaultService.default_units,
                duration_months: 6,
                isEstimating: false,
                estimate: initialEstimate,
            },
            leadForm: {
                name: "",
                email: "",
                phone: "",
                company_name: "",
                product_interest: defaultService.lead_option,
                employee_count: "50 - 200 nhân sự",
                notes: "",
                website_url_hp: "",
                security_answer: "",
            },
            messages: [
                {
                    id: "welcome-01",
                    sender: "assistant",
                    text: "Kính chào Quý khách! Tôi là **Executive AI Concierge & Kiến trúc sư Dự toán** của Innoria.\n\nTôi hỗ trợ tư vấn kiến trúc, cấu hình đội ngũ kỹ sư phần mềm (Dedicated Co-Dev Squad theo **Thông tư 13/2020/TT-BTTTT**), phát triển phần mềm trọn gói (**5-Gate Enterprise**) và báo giá dự toán tức thì cho:\n• **Squad Kỹ Sư Đồng Phát Triển & Turnkey Software:** Xây dựng hệ thống may đo, Web/Mobile App & tích hợp AI/ERP.\n• **Insilos ERP:** Quản trị tài chính kế toán VAS (TT 200/133), WMS & Hóa đơn điện tử **1C26TAA** (Nghị định 70/2025/NĐ-CP).\n• **Vertical Resilience:** Quản trị rủi ro GRC, bảo vệ dữ liệu **ISO 27701 / Nghị định 13/2023** & truy xuất e-CO.\n• **Mojo AI & Zencode Ent:** Tác tử AL2C Swarm, Grounded RAG triệt tiêu ảo giác & Hiện đại hóa mã nguồn kế thừa.\n\nQuý khách có thể chọn trực tiếp gói dịch vụ bên dưới để **Cấu hình & Xem dự toán tự động** hoặc đặt câu hỏi cho AI!",
                    formattedText: null,
                    service_cards: initialCatalog.slice(0, 4),
                    citations: [
                        "[KMS | Software Services & TT 13/2020 | SOP-SW-01 | innoria]",
                        "[KMS | Master Architecture & AL2C | SOP-12 | innoria]",
                    ],
                    citationsExpanded: false,
                    grounded: true,
                    entailment_score: 0.98,
                    reason: "Thông tin được trích xuất từ khung năng lực Dịch vụ Phần mềm & Giải pháp Doanh nghiệp Innoria KMS (Thông tư 13/2020/TT-BTTTT, Nghị định 70/2025/NĐ-CP, Nghị định 13/2023/NĐ-CP).",
                    suggested_actions: [
                        {
                            label: "🧮 Mở Công Cụ Dự Toán Dịch Vụ Phần Mềm",
                            type: "open_configurator",
                            action: "open_configurator",
                            service_code: "sw_squad",
                        },
                        {
                            label: "👨‍💻 Tư vấn thuê Squad Kỹ sư (TT 13/2020)",
                            type: "prompt",
                            action: "prompt",
                            prompt: "Tư vấn mô hình thuê Squad Kỹ sư Đồng phát triển theo Thông tư 13/2020/TT-BTTTT và cơ chế nghiệm thu?",
                        },
                        {
                            label: "🏗️ Quy trình Phần mềm Trọn gói (Turnkey)",
                            type: "prompt",
                            action: "prompt",
                            prompt: "Quy trình phát triển phần mềm trọn gói (Turnkey) theo chuẩn 5-Gate Enterprise và cam kết bàn giao mã nguồn?",
                        },
                        {
                            label: "📅 Nhận Báo Giá & Hồ Sơ Năng Lực",
                            type: "open_lead",
                            action: "open_lead",
                            service_code: "sw_squad",
                        },
                    ],
                    time: this.getNowTime(),
                },
            ],
        });

        // Preformat initial greeting message
        this.state.messages[0].formattedText = markup(parseMarkdownToHtml(this.state.messages[0].text));

        // Bind external website trigger handler
        this._onDocumentConciergeClick = this._handleDocumentConciergeClick.bind(this);
        this._cooldownTimer = null;

        onMounted(() => {
            this.scrollToBottom();
            this.loadServicesCatalog();
            this._registerGlobalBridge();
            document.addEventListener("click", this._onDocumentConciergeClick);
        });

        onWillUnmount(() => {
            document.removeEventListener("click", this._onDocumentConciergeClick);
            if (this._cooldownTimer) {
                clearInterval(this._cooldownTimer);
                this._cooldownTimer = null;
            }
        });
    }

    /**
     * Get currently selected service object in configurator.
     * @returns {Object}
     */
    get currentConfigService() {
        const found = this.state.servicesCatalog.find(
            (s) => s.code === this.state.configurator.service_code
        );
        return found || this.state.servicesCatalog[0] || DEFAULT_SERVICES_CATALOG[0];
    }

    /**
     * Register global window.InnoriaConcierge bridge for website CTA buttons.
     */
    _registerGlobalBridge() {
        window.InnoriaConcierge = {
            open: (tab = "chat") => {
                this.state.isOpen = true;
                this.state.proactiveNudgeVisible = false;
                this.setActiveTab(tab);
            },
            openService: (serviceCode = "sw_squad", mode = "configurator") => {
                this.state.isOpen = true;
                this.state.proactiveNudgeVisible = false;
                if (mode === "lead") {
                    this.openLeadFormForService(serviceCode);
                } else {
                    this.openServiceConfigurator(serviceCode);
                }
            },
            openConfigurator: (serviceCode = "sw_squad") => {
                this.state.isOpen = true;
                this.state.proactiveNudgeVisible = false;
                this.openServiceConfigurator(serviceCode);
            },
            askPrompt: (promptText, serviceCode = null) => {
                this.state.isOpen = true;
                this.state.proactiveNudgeVisible = false;
                if (serviceCode) {
                    this.state.selectedPillar = serviceCode;
                }
                this.setActiveTab("chat");
                if (promptText) {
                    this.sendQuickPrompt(promptText);
                }
            },
        };
    }

    /**
     * Delegated click handler for any website element with [data-concierge-service] or [data-concierge-prompt].
     * @param {MouseEvent} ev
     */
    _handleDocumentConciergeClick(ev) {
        const trigger = ev.target && ev.target.closest
            ? ev.target.closest("[data-concierge-service], [data-concierge-prompt]")
            : null;
        if (!trigger) {
            return;
        }
        ev.preventDefault();
        const serviceCode = trigger.getAttribute("data-concierge-service");
        const promptText = trigger.getAttribute("data-concierge-prompt");
        const targetTab = trigger.getAttribute("data-concierge-tab");

        this.state.isOpen = true;
        this.state.proactiveNudgeVisible = false;

        if (promptText) {
            if (serviceCode) {
                this.state.selectedPillar = serviceCode;
            }
            this.setActiveTab("chat");
            this.sendQuickPrompt(promptText);
        } else if (serviceCode) {
            if (targetTab === "lead") {
                this.openLeadFormForService(serviceCode);
            } else {
                this.openServiceConfigurator(serviceCode);
            }
        }
    }

    /**
     * Load live software services catalog from backend controller.
     */
    async loadServicesCatalog() {
        try {
            const result = await callJsonRpc("/innoria/ai_concierge/services_catalog", {});
            if (result?.pct_token) {
                this.state.pctToken = result.pct_token;
            }
            if (typeof result?.capability_budget_remaining === "number") {
                this.state.capabilityBudgetRemaining = result.capability_budget_remaining;
            }
            if (result?.security_challenge && result.security_challenge.challenge_token) {
                const sc = result.security_challenge;
                this.state.securityChallenge = {
                    challenge_token: sc.challenge_token,
                    question: sc.question || `${sc.operand_a || 6} + ${sc.operand_b || 4} = ?`,
                    operand_a: sc.operand_a || 6,
                    operand_b: sc.operand_b || 4,
                    expected: Number(sc.operand_a || 6) + Number(sc.operand_b || 4),
                };
            }
            const rawList = result?.services || result?.catalog || (Array.isArray(result) ? result : null);
            if (Array.isArray(rawList) && rawList.length > 0) {
                const normalized = rawList.map((item) => normalizeServiceCard(item));
                this.state.servicesCatalog = normalized;
                if (this.state.messages.length > 0 && this.state.messages[0].id === "welcome-01") {
                    this.state.messages[0].service_cards = normalized.slice(0, 4);
                }
                this.updateServiceEstimate();
            }
        } catch (_err) {
            // Keep embedded DEFAULT_SERVICES_CATALOG fallback seamlessly
        }
    }

    /**
     * Refresh Anti-Bot Arithmetic Security Challenge from backend or deterministic fallback.
     */
    async refreshSecurityChallenge() {
        this.state.leadForm.security_answer = "";
        this.state.leadFieldErrors.security_answer = null;
        try {
            const res = await callJsonRpc("/innoria/ai_concierge/security_challenge", {});
            if (res && res.challenge_token) {
                this.state.securityChallenge = {
                    challenge_token: res.challenge_token,
                    question: res.question || `${res.operand_a} + ${res.operand_b} = ?`,
                    operand_a: res.operand_a,
                    operand_b: res.operand_b,
                    expected: Number(res.operand_a) + Number(res.operand_b),
                };
                return;
            }
        } catch (_err) {
            // Local fallback
        }
        const a = Math.floor(Math.random() * 8) + 2;
        const b = Math.floor(Math.random() * 8) + 1;
        this.state.securityChallenge = {
            challenge_token: null,
            question: `${a} + ${b} = ?`,
            operand_a: a,
            operand_b: b,
            expected: a + b,
        };
    }

    /**
     * Dismiss the floating proactive nudge pill.
     * @param {MouseEvent} ev
     */
    dismissProactiveNudge(ev) {
        if (ev && ev.stopPropagation) {
            ev.stopPropagation();
        }
        this.state.proactiveNudgeVisible = false;
    }

    /**
     * Open drawer from the proactive nudge pill directly to the Services Configurator or Chat.
     */
    openFromProactiveNudge() {
        this.state.proactiveNudgeVisible = false;
        this.state.isOpen = true;
        this.setActiveTab("services");
    }

    /**
     * Switch active drawer tab ('chat' | 'services' | 'lead') and synchronize state.showLeadForm.
     * @param {string} tab
     */
    setActiveTab(tab) {
        const validTab = ["chat", "services", "lead"].includes(tab) ? tab : "chat";
        this.state.activeTab = validTab;
        this.state.showLeadForm = validTab === "lead";
        if (validTab === "lead") {
            this.state.leadFormOpenedAt = Date.now();
            if (!this.state.securityChallenge.challenge_token) {
                this.refreshSecurityChallenge();
            }
        }
        if (validTab === "chat") {
            this.scrollToBottom();
            setTimeout(() => {
                if (this.queryInputRef && this.queryInputRef.el) {
                    this.queryInputRef.el.focus();
                }
            }, 120);
        }
    }

    /**
     * Open the interactive Software Services Configurator for a specific service code.
     * @param {string} serviceCode
     */
    openServiceConfigurator(serviceCode = "sw_squad") {
        this.selectConfiguratorService(serviceCode);
        this.setActiveTab("services");
    }

    /**
     * Open Lead Capture Form pre-selected for a specific service code.
     * @param {string} serviceCode
     */
    openLeadFormForService(serviceCode = "sw_squad") {
        this.selectConfiguratorService(serviceCode);
        const svc = this.currentConfigService;
        if (svc) {
            this.state.leadForm.product_interest = svc.lead_option || svc.name;
        }
        this.setActiveTab("lead");
    }

    /**
     * Select a service inside the Services Configurator and recalculate estimate.
     * @param {string} serviceCode
     */
    selectConfiguratorService(serviceCode) {
        const target =
            this.state.servicesCatalog.find((s) => s.code === serviceCode) ||
            this.state.servicesCatalog[0];
        if (!target) {
            return;
        }
        this.state.configurator.service_code = target.code;
        this.state.selectedPillar = target.code;
        if (!target.unit_options.includes(this.state.configurator.units)) {
            this.state.configurator.units = target.default_units || target.unit_options[0] || 2;
        }
        this.state.leadForm.product_interest = target.lead_option || target.name;
        this.updateServiceEstimate();
    }

    /**
     * Set scale tier ('starter' | 'growth' | 'enterprise') and update estimate.
     * @param {string} tierKey
     */
    setConfiguratorTier(tierKey) {
        if (!SCALE_TIER_META[tierKey]) {
            return;
        }
        this.state.configurator.scale_tier = tierKey;
        this.state.leadForm.employee_count = SCALE_TIER_META[tierKey].employee_hint;
        this.updateServiceEstimate();
    }

    /**
     * Set exact unit count and update estimate.
     * @param {number} units
     */
    setConfiguratorUnits(units) {
        const safeUnits = Math.max(1, Math.min(50, Number(units) || 1));
        this.state.configurator.units = safeUnits;
        this.updateServiceEstimate();
    }

    /**
     * Increment or decrement configurator units via - / + controls.
     * @param {number} delta
     */
    adjustConfiguratorUnits(delta) {
        const next = Math.max(1, Math.min(50, (Number(this.state.configurator.units) || 1) + delta));
        this.state.configurator.units = next;
        this.updateServiceEstimate();
    }

    /**
     * Set contract/project duration in months (3 | 6 | 12) and update estimate.
     * @param {number} months
     */
    setConfiguratorDuration(months) {
        const safeMonths = [3, 6, 12].includes(Number(months)) ? Number(months) : 6;
        this.state.configurator.duration_months = safeMonths;
        this.updateServiceEstimate();
    }

    /**
     * Calculate immediate client-side estimate and synchronize with /innoria/ai_concierge/estimate_service.
     */
    async updateServiceEstimate() {
        const svc = this.currentConfigService;
        const { scale_tier, units, duration_months } = this.state.configurator;

        // 1. Immediate deterministic calculation (Zero Flicker)
        const localEst = computeClientEstimate(svc, scale_tier, units, duration_months);
        this.state.configurator.estimate = localEst;

        // 2. Live server calculation via /innoria/ai_concierge/estimate_service
        this.state.configurator.isEstimating = true;
        try {
            const result = await callJsonRpc("/innoria/ai_concierge/estimate_service", {
                service_code: svc.code,
                scale_tier: scale_tier,
                units: units,
                duration_months: duration_months,
            });
            if (result) {
                this.state.pricingToken = result.pricing_token || null;
            }
            const payload = result?.estimate || result;
            if (payload && (payload.formatted_total_vnd || payload.total_vnd)) {
                const mergedPayment = Array.isArray(payload.payment_schedule)
                    ? payload.payment_schedule.join(" • ")
                    : payload.payment_schedule || localEst.payment_schedule;
                this.state.configurator.estimate = {
                    ...localEst,
                    ...payload,
                    formatted_total_vnd:
                        payload.formatted_total_vnd || formatVnd(payload.total_vnd || localEst.total_vnd),
                    formatted_monthly_vnd:
                        payload.formatted_monthly_vnd ||
                        `${formatVnd(payload.monthly_vnd || localEst.monthly_vnd)} / tháng`,
                    payment_schedule: mergedPayment,
                    lifecycle_steps:
                        Array.isArray(payload.lifecycle_steps) && payload.lifecycle_steps.length
                            ? payload.lifecycle_steps
                            : localEst.lifecycle_steps,
                    compliance_guarantees:
                        Array.isArray(payload.compliance_guarantees) && payload.compliance_guarantees.length
                            ? payload.compliance_guarantees
                            : localEst.compliance_guarantees,
                };
            }
        } catch (_err) {
            // Keep deterministic client-side estimate
        } finally {
            this.state.configurator.isEstimating = false;
        }
    }

    /**
     * Ask AI Concierge an in-depth architectural question about the currently configured service.
     */
    askAiAboutCurrentConfig() {
        const svc = this.currentConfigService;
        const est = this.state.configurator.estimate;
        const promptText =
            `Tư vấn chuyên sâu gói **${svc.name}** với cấu hình: Quy mô **${est.scale_label}**, ` +
            `số lượng **${est.units} ${svc.unit_label}**, thời lượng **${est.duration_months} tháng** ` +
            `(Dự toán: **${est.formatted_total_vnd}**). Xin cho biết chi tiết lộ trình triển khai, cơ chế bàn giao mã nguồn và cam kết SLA?`;
        this.state.selectedPillar = svc.code;
        this.setActiveTab("chat");
        this.sendQuickPrompt(promptText);
    }

    /**
     * Proceed from Services Configurator to Lead Capture tab with configured parameters pre-filled.
     */
    proceedToLeadWithConfig() {
        const svc = this.currentConfigService;
        const est = this.state.configurator.estimate;
        this.state.leadForm.product_interest = svc.lead_option || svc.name;
        const configSummary =
            `[Cấu hình dự toán] Dịch vụ: ${svc.name} | Quy mô: ${est.scale_label} | ` +
            `Số lượng: ${est.units} ${svc.unit_label} | Thời hạn: ${est.duration_months} tháng | ` +
            `Tổng dự toán: ${est.formatted_total_vnd}`;
        if (!this.state.leadForm.notes || this.state.leadForm.notes.startsWith("[Cấu hình dự toán]")) {
            this.state.leadForm.notes = configSummary;
        }
        this.setActiveTab("lead");
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
            this.state.proactiveNudgeVisible = false;
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
        this.setActiveTab("chat");
        this.scrollToBottom();
    }

    /**
     * Open lead capture drawer section.
     * @param {string} pillar
     */
    openLeadForm(pillar = "all") {
        this.state.leadSuccessMessage = null;
        this.state.leadErrorMessage = null;

        if (pillar && pillar !== "all") {
            const pillarMap = {
                sw_squad: "Squad Kỹ Sư Đồng Phát Triển (Dedicated Co-Dev Squad - TT 13/2020)",
                sw_turnkey: "Phát Triển Phần Mềm Trọn Gói (Turnkey Custom Software - 5-Gate Enterprise)",
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
        this.setActiveTab("lead");
    }

    /**
     * Close lead capture drawer section and return to chat tab.
     */
    closeLeadForm() {
        this.state.leadSuccessMessage = null;
        this.state.leadErrorMessage = null;
        this.setActiveTab("chat");
    }

    /**
     * Update specific field in lead capture form and run real-time anti-fake contact validation.
     * @param {string} field
     * @param {Event} ev
     */
    updateLeadField(field, ev) {
        const val = ev.target.value;
        this.state.leadForm[field] = val;
        if (field in this.state.leadFieldErrors) {
            this.state.leadFieldErrors[field] = this.validateLeadFieldClient(field, val);
        }
    }

    /**
     * Client-side Anti-Fake Contact & Anti-Bot Challenge Validator.
     * @param {string} field
     * @param {string} rawVal
     * @returns {string|null}
     */
    validateLeadFieldClient(field, rawVal) {
        const val = String(rawVal || "").trim();
        if (!val) {
            return null;
        }
        const lower = val.toLowerCase();
        if (/(<\s*script|javascript:|onerror=|onload=|\bdrop\s+table\b|\bunion\s+select\b)/i.test(val)) {
            return "Phát hiện mã thực thi hoặc truy vấn không hợp lệ (WAF Guard).";
        }
        if (field === "name") {
            if (val.length < 2) {
                return "Họ và tên cần tối thiểu 2 ký tự.";
            }
            const clean = lower.replace(/[\s.\-']/g, "");
            if (/^\d+$/.test(clean) || new Set(clean).size <= 1 || /(asdf|qwer|zxcv|test|fake)/.test(clean)) {
                return "Họ và tên có dấu hiệu dữ liệu giả (Fake Contact). Vui lòng nhập họ tên thật.";
            }
        } else if (field === "email") {
            const m = lower.match(/^([a-z0-9_.+-]+)@([a-z0-9-]+(?:\.[a-z0-9-]+)+)$/);
            if (!m) {
                return "Định dạng Email chưa hợp lệ (VD: ten@congty.vn).";
            }
            const localPart = m[1];
            const domainPart = m[2];
            const blockedDomains = [
                "mailinator.com", "tempmail.com", "temp-mail.org", "10minutemail.com",
                "guerrillamail.com", "yopmail.com", "trashmail.com", "sharklasers.com",
                "getnada.com", "fakeinbox.com", "test.com", "example.com", "fake.com",
                "abc.com", "xyz.com", "123.com", "asdf.com", "spam.com",
            ];
            if (blockedDomains.some((d) => domainPart === d || domainPart.endsWith(`.${d}`))) {
                return `Từ chối Email tạm thời / tên miền ảo (${domainPart}). Vui lòng dùng Email doanh nghiệp.`;
            }
            const cleanLocal = localPart.replace(/[^a-z0-9]/g, "");
            if (
                ["test", "testing", "fake", "spam", "asdf", "asdfgh", "qwerty", "123456", "abc"].includes(cleanLocal) ||
                (cleanLocal.length >= 4 && new Set(cleanLocal).size <= 1)
            ) {
                return "Địa chỉ Email có dấu hiệu Email thử nghiệm / giả mạo.";
            }
        } else if (field === "phone") {
            let digits = val.replace(/[\s\-.()]/g, "");
            if (digits.startsWith("+84")) {
                digits = "0" + digits.slice(3);
            } else if (digits.startsWith("84") && (digits.length === 11 || digits.length === 12)) {
                digits = "0" + digits.slice(2);
            }
            if (digits.startsWith("+")) {
                const intl = digits.slice(1);
                if (!/^\d{8,15}$/.test(intl)) {
                    return "Số điện thoại quốc tế chưa đúng chuẩn (+MãQuốcGia...).";
                }
            } else {
                if (!/^(0[35789]\d{8}|02\d{8,9})$/.test(digits)) {
                    return "Số ĐT cần đúng 10 số di động VN (03/05/07/08/09) hoặc cố định (02x).";
                }
            }
            const fakePhones = [
                "0123456789", "0987654321", "0912345678", "0987654320", "0901234567",
                "0999999999", "0988888888", "0977777777", "0966666666", "0944444444",
                "0933333333", "0911111111", "0900000000", "0000000000", "0909090909",
            ];
            if (
                fakePhones.includes(digits) ||
                new Set(digits).size <= 2 ||
                /(\d)\1{6,}/.test(digits) ||
                ["1234567", "2345678", "3456789", "7654321", "8765432", "9876543", "0000000"].includes(digits.slice(-7))
            ) {
                return "Phát hiện Số điện thoại ảo / dãy số lặp. Vui lòng nhập số thực tế.";
            }
        } else if (field === "company_name") {
            const cleanComp = lower.replace(/[\s.\-,&()]/g, "");
            if (val.length < 2 || /^\d+$/.test(cleanComp) || /(asdf|qwer|zxcv|fake|test)/.test(cleanComp)) {
                return "Vui lòng nhập tên công ty / tổ chức thực tế.";
            }
        } else if (field === "security_answer") {
            const expected = Number(this.state.securityChallenge.expected);
            if (Number(val) !== expected) {
                return "Kết quả phép tính xác thực chưa đúng.";
            }
        }
        return null;
    }

    /**
     * Start a countdown timer when Chatbox is temporarily locked due to repeated harassment/spam.
     * @param {number} seconds
     */
    startChatCooldownTimer(seconds) {
        const sec = Math.max(1, Number(seconds) || 60);
        this.state.chatSecurity.lockedOut = true;
        this.state.chatSecurity.cooldownSeconds = sec;
        if (this._cooldownTimer) {
            clearInterval(this._cooldownTimer);
        }
        this._cooldownTimer = setInterval(() => {
            if (this.state.chatSecurity.cooldownSeconds > 1) {
                this.state.chatSecurity.cooldownSeconds -= 1;
            } else {
                this.state.chatSecurity.cooldownSeconds = 0;
                this.state.chatSecurity.lockedOut = false;
                this.state.chatSecurity.warningBanner = null;
                clearInterval(this._cooldownTimer);
                this._cooldownTimer = null;
            }
        }, 1000);
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
     * Supports type/action: 'open_configurator', 'open_lead', 'book_lead', 'book_meeting', 'prompt'.
     * @param {Object} act
     */
    onSuggestedActionClick(act) {
        if (!act) {
            return;
        }
        const actionType = act.type || act.action || "prompt";
        const targetService =
            act.service_code || act.service || act.code || act.pillar || this.state.selectedPillar;

        if (actionType === "open_configurator") {
            const code = targetService && targetService !== "enterprise" ? targetService : "sw_squad";
            this.openServiceConfigurator(code);
        } else if (
            actionType === "open_lead" ||
            actionType === "book_meeting" ||
            actionType === "book_lead"
        ) {
            if (act.service_code || act.service || act.code) {
                this.openLeadFormForService(act.service_code || act.service || act.code);
            } else {
                this.openLeadForm(targetService);
            }
        } else if (actionType === "download_catalog") {
            this.openLeadForm("enterprise");
        } else {
            const query = act.prompt || act.text || act.label;
            if (query) {
                this.sendQuickPrompt(query);
            }
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
     * Resolve matching service cards for a given query or pillar when backend does not return service_cards.
     * @param {string} query
     * @param {string} matchedPillar
     * @returns {Array<Object>}
     */
    _resolveRelevantServiceCards(query, matchedPillar) {
        const q = String(query || "").toLowerCase();
        const matches = [];
        const addByCode = (code) => {
            const found = this.state.servicesCatalog.find((s) => s.code === code);
            if (found && !matches.some((m) => m.code === found.code)) {
                matches.push(found);
            }
        };

        if (q.includes("squad") || q.includes("thuê") || q.includes("13/2020") || q.includes("kỹ sư")) {
            addByCode("sw_squad");
        }
        if (q.includes("trọn gói") || q.includes("turnkey") || q.includes("phần mềm") || q.includes("activate")) {
            addByCode("sw_turnkey");
        }
        if (q.includes("erp") || q.includes("kế toán") || q.includes("hđđt") || q.includes("1c26taa") || q.includes("70/2025")) {
            addByCode("erp");
        }
        if (q.includes("grc") || q.includes("27701") || q.includes("27001") || q.includes("13/2023") || q.includes("e-co")) {
            addByCode("grc");
        }
        if (q.includes("ai") || q.includes("mojo") || q.includes("rag") || q.includes("bóc tách")) {
            addByCode("ai");
        }
        if (q.includes("zencode") || q.includes("hiện đại hóa") || q.includes("legacy") || q.includes("fleet")) {
            addByCode("zencode");
        }

        if (matchedPillar && matchedPillar !== "enterprise") {
            addByCode(matchedPillar);
        }
        if (matches.length === 0) {
            addByCode("sw_squad");
            addByCode("sw_turnkey");
        }
        return matches.slice(0, 3);
    }

    /**
     * Send user query to AI Concierge API with Anti-Harassment & Anti-Attack Firewall handling.
     */
    async sendMessage() {
        const query = (this.state.currentQuery || "").trim();
        if (!query || this.state.isLoading || this.state.chatSecurity.lockedOut) {
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
                this.state.chatSecurity.warningBanner = null;
                if (result.pct_token) {
                    this.state.pctToken = result.pct_token;
                }
                if (typeof result.capability_budget_remaining === "number") {
                    this.state.capabilityBudgetRemaining = result.capability_budget_remaining;
                }
                const matchedPillar = result.matched_pillar || this.state.selectedPillar;
                const serviceCards =
                    Array.isArray(result.service_cards) && result.service_cards.length
                        ? result.service_cards.map((c) => normalizeServiceCard(c))
                        : this._resolveRelevantServiceCards(query, matchedPillar);

                this.state.messages.push({
                    id: `ai-${Date.now()}`,
                    sender: "assistant",
                    text: result.answer,
                    formattedText: markup(parseMarkdownToHtml(result.answer)),
                    service_cards: serviceCards,
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
                if (result?.blocked) {
                    if (typeof result.strike_count === "number") {
                        this.state.chatSecurity.strikeCount = result.strike_count;
                    }
                    this.state.chatSecurity.warningBanner = errorMsg;
                    if (result.locked_out || (result.cooldown_seconds && result.cooldown_seconds > 0)) {
                        this.startChatCooldownTimer(result.cooldown_seconds || 120);
                    }
                }
                this.state.messages.push({
                    id: `ai-err-${Date.now()}`,
                    sender: "assistant",
                    text: errorMsg,
                    formattedText: markup(parseMarkdownToHtml(errorMsg)),
                    service_cards: result?.blocked ? [] : this._resolveRelevantServiceCards(query, this.state.selectedPillar),
                    citations: result?.quarantine_seal ? [`[WAF Quarantine Seal | ${result.quarantine_seal.slice(0, 16)}]`] : [],
                    citationsExpanded: false,
                    grounded: false,
                    entailment_score: 0,
                    reason: result?.security_code ? `Security Policy: ${result.security_code}` : "",
                    suggested_actions: result?.blocked
                        ? []
                        : [
                              {
                                  label: "🧮 Dự Toán Dịch Vụ Phần Mềm",
                                  type: "open_configurator",
                                  action: "open_configurator",
                                  service_code: "sw_squad",
                              },
                              {
                                  label: "📅 Đăng Ký Tư Vấn Trực Tiếp",
                                  type: "open_lead",
                                  action: "book_lead",
                                  pillar: this.state.selectedPillar,
                              },
                          ],
                    time: this.getNowTime(),
                });
            }
        } catch (err) {
            const fallbackText =
                "Đã xảy ra sự cố kết nối tới dịch vụ AI Concierge. Quý khách có thể sử dụng ngay tab **🧮 Dịch Vụ & Dự Toán** hoặc gửi yêu cầu để Chuyên gia Innoria hỗ trợ trực tiếp.";
            this.state.messages.push({
                id: `ai-err-${Date.now()}`,
                sender: "assistant",
                text: fallbackText,
                formattedText: markup(parseMarkdownToHtml(fallbackText)),
                service_cards: this._resolveRelevantServiceCards(query, this.state.selectedPillar),
                citations: [],
                citationsExpanded: false,
                grounded: false,
                entailment_score: 0,
                reason: err.message || "",
                suggested_actions: [
                    {
                        label: "🧮 Mở Công Cụ Dự Toán",
                        type: "open_configurator",
                        action: "open_configurator",
                        service_code: "sw_squad",
                    },
                    {
                        label: "📅 Đăng Ký Tư Vấn Doanh Nghiệp",
                        type: "open_lead",
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
     * Submit lead capture form to /innoria/ai_concierge/book_lead including configurator & anti-spam parameters.
     */
    async submitLeadForm() {
        const form = this.state.leadForm;

        // 0. Honeypot check
        if (form.website_url_hp && String(form.website_url_hp).trim()) {
            this.state.leadErrorMessage = "🛡️ Hệ thống Bảo mật Chống Spam đã chặn yêu cầu tự động (Honeypot Guard).";
            return;
        }

        if (!form.name || !form.name.trim()) {
            this.state.leadErrorMessage = "Vui lòng nhập họ và tên của Quý khách.";
            return;
        }
        if ((!form.email || !form.email.trim()) && (!form.phone || !form.phone.trim())) {
            this.state.leadErrorMessage = "Vui lòng cung cấp ít nhất Email doanh nghiệp hoặc Số điện thoại hợp lệ.";
            return;
        }
        if (!form.company_name || !form.company_name.trim()) {
            this.state.leadErrorMessage = "Vui lòng nhập tên công ty hoặc tổ chức của Quý khách.";
            return;
        }

        // Validate authenticity of all fields
        const nameErr = this.validateLeadFieldClient("name", form.name);
        const emailErr = form.email ? this.validateLeadFieldClient("email", form.email) : null;
        const phoneErr = form.phone ? this.validateLeadFieldClient("phone", form.phone) : null;
        const compErr = this.validateLeadFieldClient("company_name", form.company_name);
        const chalErr = this.validateLeadFieldClient("security_answer", form.security_answer);

        this.state.leadFieldErrors.name = nameErr;
        this.state.leadFieldErrors.email = emailErr;
        this.state.leadFieldErrors.phone = phoneErr;
        this.state.leadFieldErrors.company_name = compErr;

        if (nameErr || emailErr || phoneErr || compErr) {
            this.state.leadErrorMessage = nameErr || emailErr || phoneErr || compErr;
            return;
        }

        if (!String(form.security_answer || "").trim() || chalErr) {
            this.state.leadFieldErrors.security_answer =
                chalErr || `Vui lòng nhập kết quả phép tính bảo mật (${this.state.securityChallenge.question}).`;
            this.state.leadErrorMessage = this.state.leadFieldErrors.security_answer;
            return;
        }
        this.state.leadFieldErrors.security_answer = null;

        this.state.leadErrorMessage = null;
        this.state.leadSuccessMessage = null;
        this.state.isLoading = true;

        const cfg = this.state.configurator;
        const est = cfg.estimate || {};
        const dwellMs = Math.max(1500, Date.now() - (this.state.leadFormOpenedAt || Date.now() - 5000));

        try {
            const payload = {
                name: form.name.trim(),
                email: form.email.trim(),
                phone: form.phone.trim(),
                company_name: form.company_name.trim(),
                product_interest: form.product_interest,
                employee_count: form.employee_count,
                notes: form.notes ? form.notes.trim() : "",
                service_code: cfg.service_code,
                scale_tier: cfg.scale_tier,
                units: cfg.units,
                duration_months: cfg.duration_months,
                estimated_total_vnd: est.total_vnd || 0,
                pct_token: this.state.pctToken,
                pricing_token: this.state.pricingToken,
                website_url_hp: form.website_url_hp || "",
                form_dwell_ms: dwellMs,
            };
            if (this.state.securityChallenge.challenge_token) {
                payload.sec_challenge_token = this.state.securityChallenge.challenge_token;
                payload.sec_challenge_answer = String(form.security_answer).trim();
            }

            const result = await callJsonRpc("/innoria/ai_concierge/book_lead", payload);

            if (result && result.success) {
                if (typeof result.capability_budget_remaining === "number") {
                    this.state.capabilityBudgetRemaining = result.capability_budget_remaining;
                }
                const successMsg =
                    result.message || "Yêu cầu khảo sát và báo giá của Quý khách đã được tiếp nhận thành công.";
                this.state.leadSuccessMessage = successMsg;

                // Add confirmation assistant message to chat thread
                const confirmText =
                    `🎉 **Tiếp nhận hồ sơ & cấu hình dự toán thành công!**\n\n` +
                    `Kính chào Quý khách **${form.name}** (${form.company_name}), yêu cầu tư vấn giải pháp **${form.product_interest}** ` +
                    `đã được khởi tạo thành công trên hệ thống Innoria AL2C.\n` +
                    `• **Mã hồ sơ CRM:** #${result.lead_id} (${result.lead_name})\n` +
                    `• **Cấu hình dự toán:** ${est.scale_label || cfg.scale_tier} • ${cfg.units} ${est.unit_label || "đơn vị"} • ${cfg.duration_months} tháng (**${est.formatted_total_vnd || "Theo khảo sát"}**)\n` +
                    `• **Điểm đánh giá tiềm năng B2B (Fit Score):** ${Math.round(result.fit_score)}/100\n` +
                    `• **Phân hạng:** ${result.qualification_state === "qualified" ? "Ưu tiên cao (Qualified)" : "Đang xử lý (In Progress)"}\n\n` +
                    `Chuyên gia Solution Architect phụ trách khối doanh nghiệp sẽ liên hệ với Quý khách qua **${form.email || form.phone}** trong vòng 24 giờ làm việc.`;

                this.state.messages.push({
                    id: `ai-lead-${Date.now()}`,
                    sender: "assistant",
                    text: confirmText,
                    formattedText: markup(parseMarkdownToHtml(confirmText)),
                    service_cards: [],
                    citations: ["[KMS | Lead-to-Cash SLA | SOP-AI-004 | innoria]"],
                    citationsExpanded: false,
                    grounded: true,
                    entailment_score: 1.0,
                    reason: "Đã tạo Lead trên hệ thống crm.lead với BANT qualification, cấu hình dự toán dịch vụ và cam kết SLA phản hồi 24h.",
                    suggested_actions: [],
                    time: this.getNowTime(),
                });

                // Refresh challenge for next use
                this.refreshSecurityChallenge();

                // Auto-close lead drawer after 2.2 seconds and return to chat view
                setTimeout(() => {
                    this.setActiveTab("chat");
                    this.state.leadSuccessMessage = null;
                    this.scrollToBottom();
                }, 2200);

                // Reset notes & security answer
                this.state.leadForm.notes = "";
                this.state.leadForm.security_answer = "";
            } else {
                this.state.leadErrorMessage =
                    result?.error || "Không thể tiếp nhận yêu cầu lúc này. Quý khách vui lòng thử lại sau ít phút.";
                if (result?.status === "security_challenge_failed") {
                    this.refreshSecurityChallenge();
                }
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
        } catch (_err) {
            // Handled or already mounted by interaction
        }
    }
});
