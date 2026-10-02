/** @insilos-module **/

import { Component } from "@insilos/owl";
import { useService } from "@web/core/utils/hooks";

export class KPISummaryTile extends Component {
    static template = "insilos_sap_fiori.KPISummaryTile";
    static props = {
        kpi: { type: Object, optional: false },
        timeframe: { type: String, optional: true },
        onClick: { type: Function, optional: true },
    };

    setup() {
        this.action = useService("action");
    }

    /**
     * Resolve pure mathematical SVG sparkline paths.
     * Uses pre-computed line_d and area_d if provided by backend, or dynamically
     * computes SVG coordinates on 120x36 viewBox from raw points array.
     */
    get sparklineData() {
        const kpi = this.props.kpi;
        if (!kpi) {
            return null;
        }

        const spark = kpi.sparkline || {};
        if (spark.line_d && spark.area_d) {
            return spark;
        }

        const points = spark.points || [];
        if (!points || points.length < 2) {
            return null;
        }

        const W = 120;
        const H = 36;
        const Px = 4.0;
        const Py = 4.0;

        const numPoints = points.map(p => Number(p) || 0);
        const minV = Math.min(...numPoints);
        const maxV = Math.max(...numPoints);
        const diff = maxV !== minV ? maxV - minV : 1.0;
        const n = numPoints.length;

        const coords = numPoints.map((v, i) => {
            const x = Px + i * ((W - 2.0 * Px) / (n - 1));
            const y = H - Py - ((v - minV) / diff) * (H - 2.0 * Py);
            return [Number(x.toFixed(1)), Number(y.toFixed(1))];
        });

        const line_d = "M " + coords.map(([x, y]) => `${x} ${y}`).join(" L ");
        const lastPt = coords[coords.length - 1];
        const firstPt = coords[0];
        const area_d = `${line_d} L ${lastPt[0]} ${H} L ${firstPt[0]} ${H} Z`;
        const strokeColor = spark.stroke_color || (kpi.delta_semantic === "positive" ? "#10B981" : "#00F2FE");

        return {
            points,
            min: minV,
            max: maxV,
            svg_width: W,
            svg_height: H,
            line_d,
            area_d,
            endpoint: { cx: lastPt[0], cy: lastPt[1] },
            stroke_color: strokeColor,
            fill_gradient_start: spark.fill_gradient_start || "rgba(0, 242, 254, 0.28)",
            fill_gradient_stop: spark.fill_gradient_stop || "rgba(0, 242, 254, 0.0)",
        };
    }

    /**
     * Unique gradient ID per KPI tile to prevent SVG clip-path/gradient collision.
     */
    get gradientId() {
        return `ins-grad-${this.props.kpi?.id || "tile"}-${Math.random().toString(36).substring(2, 7)}`;
    }

    /**
     * Semantic delta badge class.
     * Evaluates inverted semantics: positive for revenue/OTIF/OEE up,
     * positive for costs/DOH down.
     */
    get deltaBadgeClass() {
        const semantic = this.props.kpi?.delta_semantic;
        if (semantic === "positive") {
            return "ins-delta-badge ins-delta-badge--positive";
        } else if (semantic === "negative") {
            return "ins-delta-badge ins-delta-badge--negative";
        }
        return "ins-delta-badge ins-delta-badge--neutral";
    }

    /**
     * Directional arrow icon / symbol for delta badge.
     */
    get deltaArrow() {
        const trend = this.props.kpi?.delta_trend;
        if (trend === "up") {
            return "↑";
        } else if (trend === "down") {
            return "↓";
        }
        return "→";
    }

    get deltaFormatted() {
        const delta = this.props.kpi?.delta_percent;
        if (delta === undefined || delta === null) {
            return "";
        }
        const sign = delta > 0 ? "+" : "";
        return `${sign}${delta}%`;
    }

    /**
     * Tile Click-Through Handler: Opens filtered views or triggers custom callback.
     */
    onTileClick(event) {
        if (this.props.onClick) {
            this.props.onClick(this.props.kpi, event);
            return;
        }

        const drilldown = this.props.kpi?.drilldown_action;
        if (drilldown) {
            if (typeof drilldown === "string") {
                this.action.doAction(drilldown);
            } else if (typeof drilldown === "object") {
                this.action.doAction({
                    type: drilldown.type || "ir.actions.act_window",
                    name: drilldown.name || this.props.kpi.label || "KPI Details",
                    res_model: drilldown.res_model || drilldown.model,
                    views: drilldown.views || [[false, drilldown.view_type || "list"], [false, "form"]],
                    domain: drilldown.domain || [],
                    target: drilldown.target || "current",
                });
            }
        }
    }

    onKeyDown(event) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            this.onTileClick(event);
        }
    }
}
