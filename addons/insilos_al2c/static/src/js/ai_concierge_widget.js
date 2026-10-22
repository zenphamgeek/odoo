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
        icon: "ph-users-three",
        name: "Đội Ngũ Kỹ Sư Phần Mềm Chuyên Trách (Dedicated Software Engineering Squad)",
        short_label: "Đội Ngũ Kỹ Sư Chuyên Trách",
        badge: "TT 13/2020/TT-BTTTT • Agile Scrum Squad",
        summary:
            "Xây dựng và vận hành đội ngũ Kỹ sư Phần mềm, Solution Architect & QA/DevOps chuyên trách theo quy trình Agile/Scrum, quản trị tiến độ minh bạch qua Jira/GitLab và đáp ứng 7 công đoạn sản xuất phần mềm theo Thông tư 13/2020/TT-BTTTT.",
        unit_label: "Kỹ sư chuyên trách (FTE / Man-Month)",
        unit_options: [2, 4, 6, 8, 12],
        default_units: 4,
        base_unit_monthly_vnd: 45000000,
        starting_price: "Từ 90.000.000 ₫ / tháng",
        lead_option: "Đội Ngũ Kỹ Sư Phần Mềm Chuyên Trách (Dedicated Software Engineering Squad - TT 13/2020)",
        deliverables: [
            "Dedicated Full-Stack / Backend / Mobile / ERP Engineers + Scrum Master",
            "Báo cáo Sprint Velocity, Burn-down & Timesheet đối soát qua info@inno.ai.vn",
            "Kiểm thử tự động CI/CD, rà soát bảo mật SAST/DAST & bàn giao 100% quyền sở hữu trí tuệ (IP)",
        ],
        payment_schedule:
            "Thanh toán định kỳ hàng tháng theo biên bản nghiệm thu Sprint & bảng chấm công điện tử xác thực (HĐĐT 1C26TAA theo Nghị định 70/2025/NĐ-CP).",
        lifecycle_steps: [
            "1. Xác định yêu cầu tính năng & Lập kế hoạch Sprint (Sprint Planning)",
            "2. Phân tích nghiệp vụ & Thiết kế kỹ thuật hệ thống (Technical Design)",
            "3. Lập trình tính năng, viết Unit Test, Code Review & Kiểm thử CI/CD",
            "4. Kiểm thử chấp nhận (UAT), phát hành Release & bàn giao mã nguồn",
        ],
        compliance_guarantees: [
            "Tuân thủ 7 công đoạn sản xuất phần mềm Thông tư 13/2020/TT-BTTTT",
            "Cam kết bảo mật NDA & Bảo vệ dữ liệu cá nhân Nghị định 13/2023/NĐ-CP",
            "Xuất hóa đơn điện tử hợp lệ 1C26TAA (Nghị định 70/2025/NĐ-CP)",
        ],
    },
    {
        code: "sw_turnkey",
        icon: "ph-stack",
        name: "Phát Triển Phần Mềm Chuyên Biệt Trọn Gói (Custom Software & Turnkey Delivery)",
        short_label: "Phần Mềm Trọn Gói",
        badge: "Turnkey Fixed-Scope • 100% Source Code",
        summary:
            "Khảo sát, thiết kế kiến trúc và phát triển trọn gói hệ thống phần mềm doanh nghiệp, cổng giao dịch B2B/B2C, Web/Mobile App chuyên biệt theo phạm vi, tiến độ và chất lượng (SLA) cam kết bằng hợp đồng.",
        unit_label: "Phân hệ nghiệp vụ (Modules)",
        unit_options: [1, 2, 3, 5, 8],
        default_units: 3,
        base_unit_monthly_vnd: 48000000,
        starting_price: "Từ 180.000.000 ₫ / dự án",
        lead_option: "Phát Triển Phần Mềm Chuyên Biệt Trọn Gói (Custom Software & Turnkey Delivery)",
        deliverables: [
            "Tài liệu đặc tả yêu cầu phần mềm (SRS), Thiết kế CSDL & UI/UX Design System",
            "Mã nguồn Full-Stack chuẩn hóa, tài liệu API & bộ kiểm thử tự động E2E",
            "Triển khai hạ tầng Cloud/Kubernetes HA, đào tạo vận hành & bảo hành 12 tháng",
        ],
        payment_schedule:
            "Thanh toán theo 3 mốc nghiệm thu: 30% Khởi động & Phê duyệt SRS • 40% Bàn giao Kiểm thử UAT • 30% Nghiệm thu Go-Live & Chuyển giao Source Code.",
        lifecycle_steps: [
            "1. Khảo sát nghiệp vụ, phân tích & Đặc tả yêu cầu phần mềm (SRS)",
            "2. Thiết kế kiến trúc giải pháp, CSDL & Nguyên mẫu giao diện UI/UX",
            "3. Phát triển Full-Stack Web/Mobile, tích hợp API & Kiểm thử tải/bảo mật",
            "4. Kiểm thử UAT, chuyển đổi dữ liệu, Go-Live & Bảo hành 12 tháng",
        ],
        compliance_guarantees: [
            "Đáp ứng đầy đủ 7 công đoạn sản xuất phần mềm Thông tư 13/2020/TT-BTTTT",
            "Kiểm định an toàn ứng dụng theo tiêu chuẩn ISO/IEC 27001 & OWASP Top 10",
            "Bàn giao 100% Source Code, Docker/K8s Manifests & hồ sơ thiết kế kỹ thuật",
        ],
    },
    {
        code: "erp",
        icon: "ph-chart-bar",
        name: "Triển Khai & Tùy Biến Hệ Thống ERP Doanh Nghiệp (Insilos Clean-Core ERP)",
        short_label: "Hệ Thống ERP Doanh Nghiệp",
        badge: "Clean-Core ERP • VAS TT200 • NĐ 70/2025",
        summary:
            "Tư vấn quy trình, triển khai và tùy biến hệ thống quản trị nguồn lực doanh nghiệp hợp nhất Kế toán chuẩn VAS (Thông tư 200/133) & IFRS, Mua hàng, Bán hàng B2B, Kho vận WMS, Sản xuất MRP và Hóa đơn điện tử 1C26TAA.",
        unit_label: "Người dùng hệ thống (Users)",
        unit_options: [10, 25, 50, 100, 250],
        default_units: 25,
        base_unit_monthly_vnd: 35000000,
        starting_price: "Từ 150.000.000 ₫ / gói",
        lead_option: "Hệ Thống ERP Doanh Nghiệp (Insilos Clean-Core ERP & HĐĐT NĐ 70/2025)",
        deliverables: [
            "Hệ thống Kế toán VAS/IFRS, Mua hàng, Bán hàng B2B, Kho WMS & Nhân sự Tiền lương",
            "Tích hợp trực tiếp Hóa đơn điện tử Nghị định 70/2025 & Ngân hàng số Doanh nghiệp",
            "Báo cáo quản trị thời gian thực CFO/CEO Dashboard & phân quyền đa chi nhánh",
        ],
        payment_schedule:
            "30% Khởi động & Phân tích Fit-Gap • 40% Cấu hình, Tùy biến & Kiểm thử UAT • 30% Nghiệm thu Go-Live & Đào tạo.",
        lifecycle_steps: [
            "1. Phân tích khoảng cách quy trình (Fit-Gap) & Chuẩn hóa Master Data",
            "2. Thiết kế mô hình Clean-Core ERP, cấu hình nghiệp vụ & tích hợp API",
            "3. Chuyển đổi số dư đầu kỳ, kiểm thử tích hợp E2E & đào tạo Key Users",
            "4. Vận hành Go-Live chính thức & hỗ trợ quyết toán kỳ kế toán",
        ],
        compliance_guarantees: [
            "Chuẩn mực Kế toán Việt Nam (TT 200/2014 & TT 133/2016) & IFRS",
            "Tích hợp Hóa đơn điện tử có mã CQT theo Nghị định 70/2025/NĐ-CP",
            "Kiến trúc Clean-Core tách biệt lớp lõi và mô-đun mở rộng, dễ dàng nâng cấp",
        ],
    },
    {
        code: "grc",
        icon: "ph-shield-check",
        name: "Phần Mềm Quản Trị Rủi Ro, Tuân Thủ Bảo Mật & Kiểm Toán Nội Bộ (Enterprise GRC)",
        short_label: "Phần Mềm GRC & Bảo Mật",
        badge: "ISO/IEC 27001 & 27701 • NĐ 13/2023",
        summary:
            "Phần mềm Quản trị Rủi ro Doanh nghiệp (ERM), Ma trận Kiểm soát Nội bộ (RCM), quản lý tuân thủ bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP (ISO/IEC 27701), an toàn vận hành EHS và hồ sơ xuất xứ e-CO.",
        unit_label: "Quy trình / Chốt kiểm soát rủi ro",
        unit_options: [10, 20, 50, 100],
        default_units: 20,
        base_unit_monthly_vnd: 38000000,
        starting_price: "Từ 180.000.000 ₫ / gói",
        lead_option: "Phần Mềm Quản Trị Rủi Ro & Tuân Thủ GRC (ISO 27001/27701 & NĐ 13/2023)",
        deliverables: [
            "Phần mềm Quản lý Sổ đăng ký Rủi ro (Risk Register) & Ma trận Kiểm soát (RCM)",
            "Mô-đun che giấu dữ liệu nhạy cảm (PII Masking), phân quyền RBAC & Audit Log",
            "Hệ thống quản lý bằng chứng kiểm toán ISO 27001/27701 & truy xuất nguồn gốc e-CO",
        ],
        payment_schedule:
            "30% Đánh giá hiện trạng & Thiết kế khung kiểm soát • 40% Triển khai phần mềm GRC • 30% Nghiệm thu vận hành & Hồ sơ kiểm toán.",
        lifecycle_steps: [
            "1. Đánh giá hiện trạng tuân thủ, kiểm kê tài sản dữ liệu & Ma trận rủi ro",
            "2. Triển khai mô-đun quản trị rủi ro, phân quyền RBAC/ABAC & PII Masking",
            "3. Tích hợp giám sát nhật ký kiểm toán tập trung & kiểm thử an ninh SAST",
            "4. Nghiệm thu kỹ thuật, diễn tập ứng phó sự cố & vận hành chính thức",
        ],
        compliance_guarantees: [
            "Đáp ứng yêu cầu kỹ thuật Nghị định 13/2023/NĐ-CP về Bảo vệ dữ liệu cá nhân",
            "Chuẩn hóa theo khung tiêu chuẩn quốc tế ISO/IEC 27001:2022 & ISO/IEC 27701",
            "Tự động hóa kết xuất bằng chứng kiểm toán nội bộ và hồ sơ xuất xứ e-CO",
        ],
    },
    {
        code: "ai",
        icon: "ph-robot",
        name: "Phát Triển Phần Mềm AI Ứng Dụng, Bóc Tách Tài Liệu (OCR/IDP) & Tìm Kiếm Tri Thức",
        short_label: "Phần Mềm AI & OCR/IDP",
        badge: "Applied AI • OCR/IDP & Enterprise RAG",
        summary:
            "Phát triển và tích hợp các mô-đun phần mềm AI chuyên dụng: bóc tách tự động hóa đơn, hợp đồng, chứng từ (OCR/IDP), hệ thống tìm kiếm tri thức doanh nghiệp có kiểm chứng trích dẫn (Enterprise RAG) và trợ lý ảo nội bộ.",
        unit_label: "Luồng xử lý AI & Đường ống dữ liệu",
        unit_options: [2, 5, 10, 25],
        default_units: 5,
        base_unit_monthly_vnd: 45000000,
        starting_price: "Từ 150.000.000 ₫ / giải pháp",
        lead_option: "Phát Triển Phần Mềm AI Ứng Dụng, Bóc Tách OCR/IDP & Tìm Kiếm Tri Thức",
        deliverables: [
            "Dịch vụ OCR/IDP bóc tách hóa đơn, chứng từ, hợp đồng & đối soát 3 chiều tự động",
            "Hệ thống tìm kiếm tri thức doanh nghiệp (Vector Search + Citation Verification)",
            "Triển khai độc lập trên hạ tầng Private Cloud / On-Premise kèm API tích hợp ERP/CRM",
        ],
        payment_schedule:
            "30% Chuẩn hóa dữ liệu & Xây dựng PoC • 40% Phát triển mô-đun AI & Tích hợp API • 30% Nghiệm thu độ chính xác & Go-Live.",
        lifecycle_steps: [
            "1. Thu thập, làm sạch & Chuẩn hóa tập dữ liệu nghiệp vụ (Data Preprocessing)",
            "2. Phát triển mô-đun trích xuất OCR/IDP & Cơ sở dữ liệu Vector (Enterprise RAG)",
            "3. Lập trình API tích hợp vào hệ thống ERP/CRM/DMS & Kiểm thử độ chính xác",
            "4. Đóng gói triển khai VPC/On-Premise & Giám sát chất lượng vận hành",
        ],
        compliance_guarantees: [
            "100% câu trả lời tra cứu tri thức đều đính kèm trích dẫn tài liệu gốc xác thực",
            "Tự động ẩn thông tin định danh cá nhân (PII) & kiểm soát truy cập theo vai trò",
            "Triển khai trong mạng nội bộ doanh nghiệp, không chia sẻ dữ liệu ra bên ngoài",
        ],
    },
    {
        code: "zencode",
        icon: "ph-lightning",
        name: "Hiện Đại Hóa Ứng Dụng Legacy, Tái Kiến Trúc Microservices & Tích Hợp Hệ Thống API",
        short_label: "Hiện Đại Hóa Legacy & API",
        badge: "Legacy Modernization • Cloud-Native",
        summary:
            "Dịch vụ đánh giá nợ kỹ thuật, tái cấu trúc và chuyển đổi hệ thống phần mềm kế thừa (Legacy Monolith, .NET/Java/PHP/ERP cũ) sang kiến trúc Microservices Cloud-Native, chuẩn hóa API Gateway và tự động hóa CI/CD.",
        unit_label: "Phân hệ Legacy / Microservices chuyển đổi",
        unit_options: [1, 3, 5, 10],
        default_units: 3,
        base_unit_monthly_vnd: 52000000,
        starting_price: "Từ 220.000.000 ₫ / dự án",
        lead_option: "Hiện Đại Hóa Ứng Dụng Legacy, Tái Kiến Trúc Microservices & Tích Hợp API",
        deliverables: [
            "Báo cáo đánh giá kiến trúc hiện trạng, phân tích phụ thuộc & đo lường nợ kỹ thuật",
            "Tái cấu trúc dịch vụ theo mô hình Domain-Driven Design (DDD) & API Gateway",
            "Bộ kiểm thử hồi quy tự động (Automated Regression Suite), CI/CD & Zero-Downtime Migration",
        ],
        payment_schedule:
            "30% Khảo sát Kiến trúc & Thiết kế đích • 40% Tái cấu trúc Microservices & Kiểm thử hồi quy • 30% Cắt chuyển dữ liệu & Go-Live.",
        lifecycle_steps: [
            "1. Rà soát kiến trúc hiện hữu, phân tích phụ thuộc mã nguồn & nợ kỹ thuật",
            "2. Thiết kế kiến trúc Cloud-Native, chia tách Domain (DDD) & xây dựng cầu nối Strangler Fig",
            "3. Tái cấu trúc dịch vụ, chuẩn hóa RESTful/gRPC API & viết kiểm thử hồi quy tự động",
            "4. Di chuyển dữ liệu không gián đoạn (Zero-Downtime Cutover) & bàn giao vận hành",
        ],
        compliance_guarantees: [
            "Bảo toàn 100% tính toàn vẹn dữ liệu lịch sử và luồng nghiệp vụ đang vận hành",
            "Kiểm soát chất lượng mã nguồn tự động qua SonarQube, SAST/DAST & E2E Testing",
            "Giảm thiểu 40% - 60% chi phí vận hành hạ tầng và thời gian phát triển tính năng mới",
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

function stripLeadingEmojiStr(text) {
    return String(text || "")
        .replace(/^[\s\uFE0F\u200D\u2600-\u27BF\u{1F300}-\u{1FAFF}]+/gu, "")
        .trim();
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
        icon: raw.icon || fallback.icon || "ph-stack",
        name: stripLeadingEmojiStr(raw.name || raw.title || fallback.name),
        short_label: stripLeadingEmojiStr(raw.short_label || fallback.short_label || raw.name || fallback.name),
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
            isFanOutOpen: false,
            isBackend: Boolean(
                (typeof window !== "undefined" && (window.location.pathname.startsWith("/web") || window.location.pathname.startsWith("/odoo"))) ||
                (typeof odoo !== "undefined" && odoo.__session_info__ && !odoo.__session_info__.is_website)
            ),
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
                attachments: [],
            },
            messages: [
                {
                    id: "welcome-01",
                    sender: "assistant",
                    text: "Kính chào Quý khách! Tôi là **Executive AI Concierge & Kiến trúc sư Dự toán** của Innoria.\n\nTôi hỗ trợ tư vấn kiến trúc giải pháp, cấu hình **Đội Ngũ Kỹ Sư Phần Mềm Chuyên Trách** (theo chuẩn 7 công đoạn **Thông tư 13/2020/TT-BTTTT**), **Phát Triển Phần Mềm Trọn Gói** và báo giá dự toán tức thì cho:\n• **Đội Ngũ Kỹ Sư Chuyên Trách & Phần Mềm Trọn Gói (Turnkey):** Xây dựng hệ thống phần mềm chuyên biệt, Web/Mobile App & tích hợp hệ thống API.\n• **Hệ Thống ERP Doanh Nghiệp (Insilos Clean-Core ERP):** Quản trị tài chính kế toán VAS (TT 200/133), Kho vận WMS & Hóa đơn điện tử **1C26TAA** (Nghị định 70/2025/NĐ-CP).\n• **Phần Mềm Quản Trị Rủi Ro GRC & Bảo Mật:** Kiểm soát nội bộ, bảo vệ dữ liệu cá nhân **ISO/IEC 27701 / Nghị định 13/2023** & truy xuất e-CO.\n• **Phần Mềm AI Ứng Dụng & Hiện Đại Hóa Legacy:** Bóc tách chứng từ tự động OCR/IDP, tìm kiếm tri thức doanh nghiệp (Enterprise RAG) & tái cấu trúc Microservices.\n\nQuý khách có thể chọn trực tiếp gói dịch vụ bên dưới để **Cấu hình & Xem dự toán tự động** hoặc đặt câu hỏi cho chuyên gia!",
                    formattedText: null,
                    service_cards: initialCatalog.slice(0, 4),
                    citations: [
                        "[KMS | Software Services & TT 13/2020 | SOP-SW-01 | innoria]",
                        "[KMS | Master Architecture & AL2C | SOP-12 | innoria]",
                    ],
                    citationsExpanded: false,
                    grounded: true,
                    entailment_score: 0.98,
                    reason: "Thông tin được trích xuất từ khung năng lực Dịch vụ Phát triển Phần mềm & Giải pháp Doanh nghiệp Innoria (Thông tư 13/2020/TT-BTTTT, Nghị định 70/2025/NĐ-CP, Nghị định 13/2023/NĐ-CP).",
                    suggested_actions: [
                        {
                            icon: "ph-calculator",
                            label: "Mở Công Cụ Dự Toán Dịch Vụ Phần Mềm",
                            type: "open_configurator",
                            action: "open_configurator",
                            service_code: "sw_squad",
                        },
                        {
                            icon: "ph-users-three",
                            label: "Tư vấn Đội Ngũ Kỹ Sư (TT 13/2020)",
                            type: "prompt",
                            action: "prompt",
                            prompt: "Tư vấn mô hình Đội ngũ Kỹ sư Phần mềm Chuyên trách theo Thông tư 13/2020/TT-BTTTT và cơ chế nghiệm thu Sprint?",
                        },
                        {
                            icon: "ph-stack",
                            label: "Quy trình Phần mềm Trọn gói (Turnkey)",
                            type: "prompt",
                            action: "prompt",
                            prompt: "Quy trình phát triển phần mềm trọn gói (Turnkey) theo chuẩn 5-Gate Enterprise và cam kết bàn giao mã nguồn?",
                        },
                        {
                            icon: "ph-calendar-check",
                            label: "Nhận Báo Giá & Hồ Sơ Năng Lực",
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
        this._onDocumentKeyDown = (e) => {
            if (e.key === "Escape") {
                if (this.state.isFanOutOpen) {
                    this.state.isFanOutOpen = false;
                } else if (this.state.isOpen) {
                    this.state.isOpen = false;
                }
            }
        };

        onMounted(() => {
            this.scrollToBottom();
            this.loadServicesCatalog();
            this._registerGlobalBridge();
            document.addEventListener("click", this._onDocumentConciergeClick);
            document.addEventListener("keydown", this._onDocumentKeyDown);
        });

        onWillUnmount(() => {
            document.removeEventListener("click", this._onDocumentConciergeClick);
            document.removeEventListener("keydown", this._onDocumentKeyDown);
            if (this._cooldownTimer) {
                clearInterval(this._cooldownTimer);
                this._cooldownTimer = null;
            }
            delete window.InnoriaConcierge;
            delete window.InnoriaAiConcierge;
        });
    }

    /**
     * Strip any leading Unicode emoji / symbol prefix from a label so Phosphor Duotone SVG icons render cleanly.
     * @param {string} text
     * @returns {string}
     */
    stripLeadingEmoji(text) {
        return stripLeadingEmojiStr(text);
    }

    /**
     * Resolve canonical Phosphor Duotone symbol ID for a service catalog item.
     * @param {Object} svc
     * @returns {string}
     */
    getServiceIcon(svc) {
        if (!svc) {
            return "ph-stack";
        }
        if (svc.icon && String(svc.icon).startsWith("ph-")) {
            return svc.icon;
        }
        const map = {
            sw_squad: "ph-users-three",
            sw_turnkey: "ph-stack",
            erp: "ph-chart-bar",
            grc: "ph-shield-check",
            ai: "ph-robot",
            zencode: "ph-lightning",
        };
        return map[svc.code] || "ph-stack";
    }

    /**
     * Resolve canonical Phosphor Duotone symbol ID for a suggested action chip.
     * @param {Object} act
     * @returns {string}
     */
    getActionIcon(act) {
        if (!act) {
            return "ph-arrow-circle-right";
        }
        if (act.icon && String(act.icon).startsWith("ph-")) {
            return act.icon;
        }
        const actionType = act.type || act.action || "";
        const lbl = String(act.label || "").toLowerCase();
        if (actionType === "open_configurator" || lbl.includes("dự toán") || lbl.includes("cấu hình") || lbl.includes("estimat")) {
            return "ph-calculator";
        }
        if (
            actionType === "open_lead" ||
            actionType === "book_lead" ||
            actionType === "book_meeting" ||
            lbl.includes("báo giá") ||
            lbl.includes("tư vấn trực tiếp") ||
            lbl.includes("quote")
        ) {
            return "ph-calendar-check";
        }
        if (lbl.includes("squad") || lbl.includes("kỹ sư") || lbl.includes("13/2020")) {
            return "ph-users-three";
        }
        if (lbl.includes("trọn gói") || lbl.includes("turnkey") || lbl.includes("phần mềm")) {
            return "ph-stack";
        }
        if (lbl.includes("erp") || lbl.includes("1c26taa") || lbl.includes("kế toán")) {
            return "ph-chart-bar";
        }
        if (lbl.includes("grc") || lbl.includes("27701") || lbl.includes("e-co") || lbl.includes("tuân thủ")) {
            return "ph-shield-check";
        }
        if (lbl.includes("ai") || lbl.includes("rag") || lbl.includes("mojo")) {
            return "ph-robot";
        }
        return "ph-arrow-circle-right";
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
     * Register global window.InnoriaConcierge and window.InnoriaAiConcierge bridge for website CTA buttons.
     */
    _registerGlobalBridge() {
        const bridge = {
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
            openLead: (serviceCode = "sw_squad") => {
                this.state.isOpen = true;
                this.state.proactiveNudgeVisible = false;
                this.openLeadFormForService(serviceCode);
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
        window.InnoriaConcierge = bridge;
        window.InnoriaAiConcierge = bridge;
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
        return this.updateServiceEstimate();
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
        return this.updateServiceEstimate();
    }

    /**
     * Set exact unit count and update estimate.
     * @param {number} units
     */
    setConfiguratorUnits(units) {
        const safeUnits = Math.max(1, Math.min(50, Number(units) || 1));
        this.state.configurator.units = safeUnits;
        return this.updateServiceEstimate();
    }

    /**
     * Increment or decrement configurator units via - / + controls.
     * @param {number} delta
     */
    adjustConfiguratorUnits(delta) {
        const next = Math.max(1, Math.min(50, (Number(this.state.configurator.units) || 1) + delta));
        this.state.configurator.units = next;
        return this.updateServiceEstimate();
    }

    /**
     * Set contract/project duration in months (3 | 6 | 12) and update estimate.
     * @param {number} months
     */
    setConfiguratorDuration(months) {
        const safeMonths = [3, 6, 12].includes(Number(months)) ? Number(months) : 6;
        this.state.configurator.duration_months = safeMonths;
        return this.updateServiceEstimate();
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
     * Toggle Fan-Out Quarter-Circle 90-degree radial menu.
     */
    toggleFanOut(ev) {
        if (ev) {
            ev.stopPropagation();
            ev.preventDefault();
        }
        if (this.state.isOpen) {
            this.state.isOpen = false;
            this.state.isFanOutOpen = false;
            return;
        }
        this.state.isFanOutOpen = !this.state.isFanOutOpen;
        if (this.state.isFanOutOpen) {
            this.state.proactiveNudgeVisible = false;
        }
    }

    /**
     * Close Fan-Out Quarter-Circle menu cleanly.
     */
    closeFanOut(ev) {
        if (ev) {
            ev.stopPropagation();
        }
        this.state.isFanOutOpen = false;
    }

    /**
     * Handle direct option selection from Fan-Out radial node.
     * @param {'chat' | 'services' | 'lead'} tab
     */
    selectFanOutOption(tab, ev) {
        if (ev) {
            ev.stopPropagation();
            ev.preventDefault();
        }
        this.state.isFanOutOpen = false;
        this.state.proactiveNudgeVisible = false;
        this.state.isOpen = true;
        if (tab === "lead") {
            this.openLeadForm("all");
        } else {
            this.setActiveTab(tab);
        }
        this.scrollToBottom();
        if (tab === "chat") {
            setTimeout(() => {
                if (this.queryInputRef && this.queryInputRef.el) {
                    this.queryInputRef.el.focus();
                }
            }, 200);
        }
    }

    /**
     * Toggle open/close state of chat drawer.
     * When closed, clicking the launcher opens the 90-degree fan-out quarter-circle interaction.
     * When open, clicking the launcher closes the drawer.
     */
    toggleDrawer(ev) {
        if (ev) {
            ev.stopPropagation();
        }
        if (this.state.isOpen) {
            this.state.isOpen = false;
            this.state.isFanOutOpen = false;
        } else {
            this.toggleFanOut(ev);
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
                sw_squad: "Đội Ngũ Kỹ Sư Phần Mềm Chuyên Trách (Dedicated Software Engineering Squad - TT 13/2020)",
                sw_turnkey: "Phát Triển Phần Mềm Chuyên Biệt Trọn Gói (Custom Software & Turnkey Delivery)",
                erp: "Hệ Thống ERP Doanh Nghiệp (Insilos Clean-Core ERP & HĐĐT NĐ 70/2025)",
                grc: "Phần Mềm Quản Trị Rủi Ro & Tuân Thủ GRC (ISO 27001/27701 & NĐ 13/2023)",
                ai: "Phát Triển Phần Mềm AI Ứng Dụng, Bóc Tách OCR/IDP & Tìm Kiếm Tri Thức",
                zencode: "Hiện Đại Hóa Ứng Dụng Legacy, Tái Kiến Trúc Microservices & Tích Hợp API",
                enterprise: "Tổ Hợp Giải Pháp Phần Mềm Doanh Nghiệp Toàn Diện (ERP + GRC + AI + Modernization)",
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

            if (result && (result.success || (result.answer && !result.blocked))) {
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
                                  icon: "ph-calculator",
                                  label: "Dự Toán Dịch Vụ Phần Mềm",
                                  type: "open_configurator",
                                  action: "open_configurator",
                                  service_code: "sw_squad",
                              },
                              {
                                  icon: "ph-calendar-check",
                                  label: "Đăng Ký Tư Vấn Trực Tiếp",
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
                "Đã xảy ra sự cố kết nối tới dịch vụ AI Concierge. Quý khách có thể sử dụng ngay tab **Dịch Vụ & Dự Toán** hoặc gửi yêu cầu để Chuyên gia Innoria hỗ trợ trực tiếp.";
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
                        icon: "ph-calculator",
                        label: "Mở Công Cụ Dự Toán",
                        type: "open_configurator",
                        action: "open_configurator",
                        service_code: "sw_squad",
                    },
                    {
                        icon: "ph-calendar-check",
                        label: "Đăng Ký Tư Vấn Doanh Nghiệp",
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
     * Read selected project files (RFP/SRS/BoQ) into base64 for Fast-Track Priority Quote submission.
     * @param {Event} ev
     */
    async onLeadFilesChange(ev) {
        const input = ev && ev.target;
        const files = input && input.files ? Array.from(input.files).slice(0, 8) : [];
        if (!files.length) {
            this.state.leadForm.attachments = [];
            return;
        }
        const readOne = (file) =>
            new Promise((resolve) => {
                if (file.size > 25 * 1024 * 1024) {
                    resolve(null);
                    return;
                }
                const reader = new FileReader();
                reader.onload = () => {
                    const dataUrl = String(reader.result || "");
                    const b64 = dataUrl.includes(",") ? dataUrl.split(",", 2)[1] : dataUrl;
                    resolve({
                        name: file.name || "Project_Document.pdf",
                        type: file.type || "application/octet-stream",
                        size: file.size || 0,
                        data: b64,
                    });
                };
                reader.onerror = () => resolve(null);
                reader.readAsDataURL(file);
            });
        const loaded = (await Promise.all(files.map(readOne))).filter(Boolean);
        this.state.leadForm.attachments = loaded;
    }

    /**
     * Submit lead capture form to /innoria/ai_concierge/book_lead including configurator & anti-spam parameters.
     */
    async submitLeadForm() {
        const form = this.state.leadForm;

        // 0. Honeypot check
        if (form.website_url_hp && String(form.website_url_hp).trim()) {
            this.state.leadErrorMessage = "Hệ thống Bảo mật Chống Spam đã chặn yêu cầu tự động (Honeypot Guard).";
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
                attachments_json: Array.isArray(form.attachments) ? form.attachments : [],
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
                    `**Tiếp nhận hồ sơ & cấu hình dự toán thành công!**\n\n` +
                    `Kính chào Quý khách **${form.name}** (${form.company_name}), yêu cầu tư vấn giải pháp **${form.product_interest}** ` +
                    `đã được khởi tạo thành công trên hệ thống Innoria AL2C.\n` +
                    `• **Mã hồ sơ CRM:** #${result.lead_id} (${result.lead_name})\n` +
                    `• **Cấu hình dự toán:** ${est.scale_label || cfg.scale_tier} • ${cfg.units} ${est.unit_label || "đơn vị"} • ${cfg.duration_months} tháng (**${est.formatted_total_vnd || "Theo khảo sát"}**)\n` +
                    `• **Điểm đánh giá tiềm năng B2B (Fit Score):** ${Math.round(result.fit_score)}/100\n` +
                    `• **Phân hạng:** ${result.fast_track_priority ? "ƯU TIÊN CAO (SLA < 2h · Đã đính kèm tài liệu)" : result.qualification_state === "qualified" ? "Ưu tiên cao (Qualified)" : "Đang xử lý (In Progress)"}\n\n` +
                    `Chuyên gia Solution Architect phụ trách khối doanh nghiệp sẽ liên hệ với Quý khách qua **${form.email || form.phone}** theo cam kết SLA.`;

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
                    reason: "Đã tạo Lead trên hệ thống crm.lead với BANT qualification, cấu hình dự toán dịch vụ và cam kết SLA phản hồi.",
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

                // Reset notes, attachments & security answer
                this.state.leadForm.notes = "";
                this.state.leadForm.security_answer = "";
                this.state.leadForm.attachments = [];
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

