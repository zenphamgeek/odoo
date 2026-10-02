import { Component } from "@insilos/owl";

export class TimeframeFilterBar extends Component {
    static template = "insilos_sap_fiori.TimeframeFilterBar";
    static props = {
        activeTimeframe: { type: String, optional: true },
        activeDomain: { type: String, optional: true },
        onTimeframeChange: { type: Function, optional: true },
        onDomainChange: { type: Function, optional: true },
        lastUpdated: { type: String, optional: true },
        isLoading: { type: Boolean, optional: true },
    };

    get timeframes() {
        return [
            { id: "today", label: "Today", sublabel: "Hôm nay", icon: "ph-clock" },
            { id: "7d", label: "7D", sublabel: "7 Ngày", icon: "ph-calendar-blank" },
            { id: "month", label: "Month", sublabel: "Tháng này", icon: "ph-calendar" },
            { id: "quarter", label: "Quarter", sublabel: "Quý này", icon: "ph-chart-pie-slice" },
            { id: "fy2026", label: "FY2026", sublabel: "Năm 2026", icon: "ph-calendar-check" },
        ];
    }

    get domains() {
        return [
            { id: "all", label: "All Domains", icon: "ph-squares-four" },
            { id: "sd", label: "Sales (SD)", icon: "ph-chart-line-up" },
            { id: "mm", label: "Procurement (MM)", icon: "ph-shopping-cart" },
            { id: "pp", label: "Manufacturing (PP)", icon: "ph-factory" },
            { id: "le", label: "Logistics (LE)", icon: "ph-truck" },
            { id: "hse", label: "HSE & GRC", icon: "ph-shield-check" },
        ];
    }

    selectTimeframe(id) {
        if (this.props.onTimeframeChange) {
            this.props.onTimeframeChange(id);
        }
    }

    selectDomain(id) {
        if (this.props.onDomainChange) {
            this.props.onDomainChange(id);
        }
    }
}
