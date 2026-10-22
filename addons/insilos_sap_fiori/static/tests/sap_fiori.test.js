/** @odoo-module **/

import { expect, test } from "@insilos/hoot";
import { animationFrame } from "@insilos/hoot-mock";
import { mockService, mountWithCleanup } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { ExecutiveControlTower } from "@insilos_sap_fiori/executive_control_tower/executive_control_tower";
import { KPISummaryTile } from "@insilos_sap_fiori/executive_control_tower/components/kpi_summary_tile";
import { TimeframeFilterBar } from "@insilos_sap_fiori/executive_control_tower/components/timeframe_filter_bar";

defineMailModels();

test("@insilos_sap_fiori/control_tower/renders initial KPIs, MES OEE, and Logistics Hub with fallback ORM", async () => {
    mockService("orm", {
        call: async () => ({ success: true }),
    });

    const tower = await mountWithCleanup(ExecutiveControlTower, {
        props: { action: {} },
    });
    await animationFrame();

    expect(Boolean(tower.state.kpis)).toBe(true);
    expect(Boolean(tower.state.kpis.net_revenue)).toBe(true);
    expect(Boolean(tower.state.kpis.procurement_tco)).toBe(true);
    expect(Boolean(tower.state.kpis.otif_delivery)).toBe(true);
    expect(Boolean(tower.state.kpis.days_on_hand)).toBe(true);
    expect(Boolean(tower.state.kpis.safety_index)).toBe(true);
    expect(Boolean(tower.state.kpis.operating_cash_flow)).toBe(true);
    expect(Boolean(tower.state.kpis.cnc_energy)).toBe(true);
    expect(Boolean(tower.state.kpis.det_dem_penalty)).toBe(true);

    expect(tower.state.industrial_mes.oee_composite).toBe(93.4);
    expect(Boolean(tower.state.logistics_hub)).toBe(true);
});

test("@insilos_sap_fiori/control_tower/sanitizeId blocks prototype pollution and normalizes CSS tokens", async () => {
    mockService("orm", {
        call: async () => ({ success: true }),
    });

    const tower = await mountWithCleanup(ExecutiveControlTower, {
        props: { action: {} },
    });

    expect(tower.sanitizeId("__proto__")).toBe("_reserved_token_");
    expect(tower.sanitizeId("constructor")).toBe("_reserved_token_");
    expect(tower.sanitizeId("123-abc.def")).toBe("id_123-abc_def");
    expect(tower.sanitizeId("valid_id-01")).toBe("valid_id-01");
});

test("@insilos_sap_fiori/control_tower/calculateSparkline computes valid SVG path coordinates", async () => {
    mockService("orm", {
        call: async () => ({ success: true }),
    });

    const tower = await mountWithCleanup(ExecutiveControlTower, {
        props: { action: {} },
    });

    const sparkline = tower.calculateSparkline([100, 150, 200], 120, 36, 4);
    expect(sparkline.line_d.startsWith("M ")).toBe(true);
    expect(sparkline.area_d.endsWith(" Z")).toBe(true);
    expect(typeof sparkline.endX).toBe("number");
    expect(typeof sparkline.endY).toBe("number");
    expect(sparkline.endX).toBeGreaterThan(0);
});

test("@insilos_sap_fiori/control_tower/timeframe and domain filter switches trigger ORM reload", async () => {
    const recordedCalls = [];
    mockService("orm", {
        async call(model, method, args) {
            recordedCalls.push({ model, method, args });
            return { success: true };
        },
    });

    const tower = await mountWithCleanup(ExecutiveControlTower, {
        props: { action: {} },
    });
    await animationFrame();

    await tower.onTimeframeChange("month");
    await animationFrame();

    await tower.onDomainChange("sd");
    await animationFrame();

    expect(tower.state.timeframe).toBe("month");
    expect(tower.state.domain).toBe("sd");

    const matchedCall = recordedCalls.find(
        (c) => c.args && c.args[0] === "month" && c.args[1]?.domain === "sd"
    );
    expect(Boolean(matchedCall)).toBe(true);
    expect(matchedCall.args).toEqual(["month", { domain: "sd" }]);
});

test("@insilos_sap_fiori/kpi_summary_tile/computes dynamic sparklineData and semantic delta classes", async () => {
    const tile = await mountWithCleanup(KPISummaryTile, {
        props: {
            kpi: {
                id: "rev",
                title: "Doanh Thu",
                value_formatted: "1.86 Tỷ",
                delta_percent: 14.2,
                delta_semantic: "positive",
                trend_direction: "up",
                sparkline: { points: [10, 20, 30, 40] },
            },
        },
    });
    await animationFrame();

    expect(Boolean(tile.sparklineData)).toBe(true);
    expect(tile.sparklineData.line_d.startsWith("M ")).toBe(true);
    expect(tile.deltaBadgeClass.includes("ins-delta-badge--positive")).toBe(true);
});

test("@insilos_sap_fiori/timeframe_filter_bar/emits timeframe and domain selection callbacks", async () => {
    let receivedTimeframe = null;
    let receivedDomain = null;

    const bar = await mountWithCleanup(TimeframeFilterBar, {
        props: {
            activeTimeframe: "7d",
            activeDomain: "all",
            onTimeframeChange: (tf) => {
                receivedTimeframe = tf;
            },
            onDomainChange: (dom) => {
                receivedDomain = dom;
            },
        },
    });
    await animationFrame();

    bar.selectTimeframe("quarter");
    bar.selectDomain("le");

    expect(receivedTimeframe).toBe("quarter");
    expect(receivedDomain).toBe("le");
});
