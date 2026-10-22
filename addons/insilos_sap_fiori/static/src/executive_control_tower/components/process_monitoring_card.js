/** @insilos-module **/

import { Component } from "@insilos/owl";

export class ProcessMonitoringCard extends Component {
    static template = "insilos_sap_fiori.ProcessMonitoringCard";
    static props = {
        pipelines: { type: Object, optional: true },
        onStageClick: { type: Function, optional: true },
    };

    get defaultPipelines() {
        return {
            lead_to_cash: {
                title: "Lead-to-Cash (L2C)",
                code: "L2C",
                icon: "ph-currency-dollar",
                description: "Chuỗi giá trị kinh doanh & doanh thu thuần",
                stages: [
                    { id: "inquiries", name: "Inquiries", count: 24, status: "info", model: "sale.order", domain: "[['state', '=', 'draft']]" },
                    { id: "quotations", name: "Quotations", count: 18, status: "info", model: "sale.order", domain: "[['state', '=', 'sent']]" },
                    { id: "orders", name: "Sales Orders", count: 42, status: "success", model: "sale.order", domain: "[['state', '=', 'sale']]" },
                    { id: "deliveries", name: "Deliveries", count: 38, status: "success", model: "stock.picking", domain: "[['picking_type_code', '=', 'outgoing']]" },
                    { id: "billing", name: "Billing Documents", count: 36, status: "success", model: "account.move", domain: "[['move_type', '=', 'out_invoice']]" },
                    { id: "cash", name: "Cash Inflow", count: 36, status: "success", model: "account.payment", domain: "[['payment_type', '=', 'inbound']]" },
                ],
            },
            procure_to_pay: {
                title: "Procure-to-Pay (P2P)",
                code: "P2P",
                icon: "ph-shopping-bag",
                description: "Chuỗi cung ứng mua sắm & chi phí vật tư",
                stages: [
                    { id: "requisitions", name: "Requisitions", count: 12, status: "info", model: "purchase.requisition", domain: "[]" },
                    { id: "rfqs", name: "Vendor RFQs", count: 8, status: "info", model: "purchase.order", domain: "[['state', 'in', ['draft', 'sent']]]" },
                    { id: "pos", name: "Purchase Orders", count: 26, status: "success", model: "purchase.order", domain: "[['state', '=', 'purchase']]" },
                    { id: "receipts", name: "Inbound Receipts", count: 24, status: "success", model: "stock.picking", domain: "[['picking_type_code', '=', 'incoming']]" },
                    { id: "invoices", name: "Vendor Invoices", count: 22, status: "success", model: "account.move", domain: "[['move_type', '=', 'in_invoice']]" },
                    { id: "payment", name: "Disbursements", count: 22, status: "success", model: "account.payment", domain: "[['payment_type', '=', 'outbound']]" },
                ],
            },
            order_to_delivery: {
                title: "Order-to-Delivery (O2D)",
                code: "O2D",
                icon: "ph-arrows-clockwise",
                description: "Quy trình điều phối sản xuất, kiểm định & giao nhận cảng",
                stages: [
                    { id: "confirmed", name: "SO Confirmed", count: 10, status: "info", model: "sale.order", domain: "[['state', '=', 'sale']]" },
                    { id: "production", name: "Production Orders", count: 8, status: "success", model: "mrp.production", domain: "[['state', 'in', ['confirmed', 'progress']]]" },
                    { id: "qa", name: "Quality Lot (QA01)", count: 6, status: "warning", model: "quality.check", domain: "[]" },
                    { id: "dispatch", name: "Drayage Dispatch", count: 14, status: "success", model: "stock.picking", domain: "[]" },
                    { id: "pgi", name: "PGI Completed", count: 14, status: "success", model: "stock.picking", domain: "[['state', '=', 'done']]" },
                ],
            },
        };
    }

    get pipelineList() {
        const raw = this.props.pipelines || this.defaultPipelines;
        const result = [];
        const meta = {
            lead_to_cash: {
                title: "Lead-to-Cash (L2C)",
                code: "L2C",
                icon: "ph-currency-dollar",
                description: "Chuỗi giá trị kinh doanh & doanh thu thuần",
            },
            procure_to_pay: {
                title: "Procure-to-Pay (P2P)",
                code: "P2P",
                icon: "ph-shopping-bag",
                description: "Chuỗi cung ứng mua sắm & chi phí vật tư",
            },
            order_to_delivery: {
                title: "Order-to-Delivery (O2D)",
                code: "O2D",
                icon: "ph-arrows-clockwise",
                description: "Quy trình điều phối sản xuất, kiểm định & giao nhận cảng",
            },
        };

        for (const [key, val] of Object.entries(raw || {})) {
            const m = meta[key] || {
                title: key.replace(/_/g, " ").toUpperCase(),
                code: key.slice(0, 3).toUpperCase(),
                icon: "ph-activity",
                description: "",
            };

            let rawStages = [];
            if (Array.isArray(val)) {
                rawStages = val;
            } else if (val && Array.isArray(val.stages)) {
                rawStages = val.stages;
            }

            const stages = rawStages.map((st, idx) => ({
                id: st.id || st.stage || `st_${idx}`,
                name: st.name || st.stage || `Stage ${idx + 1}`,
                count: st.count !== undefined ? st.count : 0,
                status: st.status || "info",
                model: st.model || st.action_model || "sale.order",
                domain: st.domain || "[]",
            }));

            result.push({
                key,
                title: val.title || m.title,
                code: val.code || m.code,
                icon: val.icon || m.icon,
                description: val.description || m.description,
                stages,
            });
        }
        return result;
    }

    handleStageClick(pipelineKey, stage) {
        if (this.props.onStageClick) {
            this.props.onStageClick(pipelineKey, stage);
        }
    }
}
