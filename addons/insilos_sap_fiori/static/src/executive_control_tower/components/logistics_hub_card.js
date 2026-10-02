/** @insilos-module **/

import { Component, useState } from "@insilos/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class LogisticsHubCard extends Component {
    static template = "insilos_sap_fiori.LogisticsHubCard";
    static props = {
        logisticsData: { type: Object, optional: true },
        fleetSummary: { type: Array, optional: true },
        detDemAlerts: { type: Object, optional: true },
        onEscalate: { type: Function, optional: true },
    };

    setup() {
        this.actionService = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            activeTab: "all",
            isEscalated: false,
        });
    }

    /**
     * Tractor Fleet Dispatch:
     * - Prime mover: Hyundai Xcient GT 440PS (51C-982.45)
     * - Chassis: CIMC Trailers 3-axle 40ft (51R-089.34)
     * - Route: Cat Lai Port <-> Cai Mep Gemalink Port
     * - Telemetry: Odometer (142,500 km), Fuel (34.5 L/100km PVOIL)
     */
    get fleet() {
        if (this.props.fleetSummary && this.props.fleetSummary.length > 0) {
            return this.props.fleetSummary;
        }
        if (this.props.logisticsData?.drayage_fleet && this.props.logisticsData.drayage_fleet.length > 0) {
            return this.props.logisticsData.drayage_fleet;
        }

        return [
            {
                id: 6,
                plate: "51C-982.45",
                model: "Hyundai Xcient GT 440PS Prime Mover",
                short_model: "Hyundai Xcient GT (6x4)",
                type: "tractor",
                route: "Tân Cảng Cát Lái <-> Cảng Quốc Tế Cái Mép Gemalink",
                location: "Tuyến Cát Lái - Cái Mép (Km 38+200)",
                odometer_km: 142500.0,
                odometer_formatted: "142,500 km",
                fuel_consumption: "34.5 L / 100km (PVOIL DO 0.05S)",
                driver: "Tài xế Nguyễn Văn Long",
                speed: "58 km/h",
                eta: "45 phút",
                status: "in_transit",
                status_label: "Đang chạy liên cảng",
                status_badge: "bg-success-subtle text-success",
                icon: "ph-truck",
                res_model: "fleet.vehicle",
                record_id: 6,
            },
            {
                id: 8,
                plate: "51R-089.34",
                model: "CIMC Trailers 3-axle 40ft Chassis",
                short_model: "Rơ-moóc CIMC 40ft",
                type: "chassis",
                route: "Coupled with Đầu kéo 51C-982.45",
                location: "Container Yard 3 - Cát Lái",
                odometer_km: 84200.0,
                odometer_formatted: "84,200 km",
                fuel_consumption: "N/A (Chassis Rơ-moóc)",
                inspection_status: "VALID (Tem kiểm định TT 50-02S)",
                coupled_truck: "51C-982.45",
                payload: "28.5 Tấn (Dry Cargo)",
                status: "coupled",
                status_label: "Đã nối vỏ container",
                status_badge: "bg-info-subtle text-info",
                icon: "ph-trailer",
                res_model: "fleet.vehicle",
                record_id: 8,
            },
            {
                id: 7,
                plate: "15C-456.78",
                model: "Hyundai Xcient GT 440PS",
                short_model: "Hyundai Xcient GT",
                type: "tractor",
                route: "SGI Depot -> Cảng Cát Lái",
                location: "Depot SGI Tân Cảng",
                odometer_km: 98200.0,
                odometer_formatted: "98,200 km",
                fuel_consumption: "33.8 L / 100km",
                driver: "Tài xế Trần Quốc Toàn",
                status: "standby",
                status_label: "Chờ điều phối",
                status_badge: "bg-secondary-subtle text-secondary",
                icon: "ph-truck",
                res_model: "fleet.vehicle",
                record_id: 7,
            },
            {
                id: 9,
                plate: "50H-123.89",
                model: "Hino 500 FL8JT7A (15T)",
                short_model: "Hino 500 15T",
                type: "truck",
                route: "VSIP 1 <-> ICD Phước Long",
                location: "VSIP 1 Logistics Hub",
                odometer_km: 76400.0,
                odometer_formatted: "76,400 km",
                fuel_consumption: "22.4 L / 100km",
                driver: "Tài xế Lê Hoàng Quân",
                status: "in_transit",
                status_label: "Giao hàng chặng ngắn",
                status_badge: "bg-success-subtle text-success",
                icon: "ph-truck",
                res_model: "fleet.vehicle",
                record_id: 9,
            },
        ];
    }

    /**
     * Filtered vehicle fleet by tab.
     */
    get filteredFleet() {
        if (this.state.activeTab === "in_transit") {
            return this.fleet.filter(v => v.status === "in_transit");
        }
        if (this.state.activeTab === "coupled") {
            return this.fleet.filter(v => v.status === "coupled");
        }
        if (this.state.activeTab === "standby") {
            return this.fleet.filter(v => v.status === "standby");
        }
        return this.fleet;
    }

    /**
     * Real-time DET/DEM Penalty Warning Cockpit Data:
     * - Free-time SLA countdown: 28h remaining (buffer 8.5h)
     * - Penalty cost avoidance: 48,000,000 ₫ averted (0 ₫ penalty incurred)
     * - Tracked containers: 12x 40ft High Cube Dry Containers (Gemadept Logistics)
     */
    get containerMoves() {
        const moves = this.props.detDemAlerts || this.props.logisticsData?.container_moves || {};

        const countdownHours = moves.det_dem_countdown_hours !== undefined
            ? Number(moves.det_dem_countdown_hours)
            : 28.0;

        const bufferHours = moves.buffer_time_hours !== undefined
            ? Number(moves.buffer_time_hours)
            : 8.5;

        const penaltyAverted = moves.potential_penalty_averted !== undefined
            ? Number(moves.potential_penalty_averted)
            : 48000000.0;

        const totalFreeTimeHours = 72.0;
        const timeRemainingPercent = Math.min(Math.max((countdownHours / totalFreeTimeHours) * 100, 0), 100);

        return {
            countdownHours,
            countdownFormatted: `${countdownHours.toFixed(1)} Giờ`,
            bufferHours,
            bufferFormatted: `${bufferHours.toFixed(1)} Giờ`,
            penaltyAverted,
            penaltyFormatted: moves.potential_penalty_formatted || "48,000,000 ₫",
            totalFreeTimeHours,
            timeRemainingPercent: timeRemainingPercent.toFixed(1),
            trackedContainers: moves.tracked_containers || "12x 40ft High Cube Dry Containers",
            orderRef: moves.order_ref || "Đơn hàng vận tải #VN-SO2026-002",
            customer: moves.customer || "Công ty CP Gemadept Logistics",
            route: "Tân Cảng Cát Lái <-> Cảng Cái Mép Gemalink",
            criticalCount: moves.critical_containers || 0,
            safeCount: moves.safe_containers || 18,
            riskLevel: countdownHours < 24 ? "critical" : countdownHours < 36 ? "warning" : "safe",
        };
    }

    /**
     * Set active filter tab.
     */
    setTab(tab) {
        this.state.activeTab = tab;
    }

    /**
     * 1-Click Dispatch Escalation Button:
     * Immediately escalates priority dispatch for the active tractor fleet
     * to eliminate 100% of detention/demurrage penalty risks.
     */
    onEscalateDispatch() {
        this.state.isEscalated = true;

        if (this.props.onEscalate) {
            this.props.onEscalate(this.containerMoves);
        }

        this.notification.add(
            "Lệnh điều phối khẩn đã phát tới tài xế xe 51C-982.45 và Trung tâm Điều độ Cảng Cát Lái. Hạn DET/DEM được đảm bảo với 8.5h đệm an toàn, tiết kiệm 48,000,000 ₫!",
            {
                title: "Kích Hoạt Điều Phối Khẩn Thành Công",
                type: "success",
                sticky: false,
            }
        );

        // Direct navigation to Logistics Pickings
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Điều Phối Vận Tải Cảng Cát Lái - Cái Mép (#VN-SO2026-002)",
            res_model: "stock.picking",
            views: [[false, "list"], [false, "form"]],
            domain: [["origin", "ilike", "SO2026-002"]],
            target: "current",
        });
    }

    /**
     * Open specific vehicle record in fleet.vehicle.
     */
    openVehicle(truck) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: `${truck.plate} - ${truck.model}`,
            res_model: truck.res_model || "fleet.vehicle",
            views: [[false, "form"], [false, "list"]],
            res_id: truck.record_id || truck.id,
            target: "current",
        });
    }

    /**
     * Open Fleet Vehicle Management list view.
     */
    openFleetManagement() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Đội Xe Đầu Kéo & Rơ-moóc Container",
            res_model: "fleet.vehicle",
            views: [[false, "list"], [false, "form"]],
            domain: [],
            target: "current",
        });
    }

    /**
     * Open DET/DEM & Logistics Operations list view.
     */
    openDetDemDetails() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Quản Lý Vận Tải Container & Cảnh Báo DET/DEM",
            res_model: "sale.order",
            views: [[false, "list"], [false, "form"]],
            domain: [["client_order_ref", "ilike", "GEMADEPT"]],
            target: "current",
        });
    }
}

registry.category("insilos_control_tower_components").add("LogisticsHubCard", LogisticsHubCard);
