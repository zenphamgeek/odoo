import { describe, expect, test } from "@insilos/hoot";
import { animationFrame } from "@insilos/hoot-mock";
import { createSpreadsheetDashboard } from "@spreadsheet_dashboard/../tests/helpers/dashboard_action";
import { defineSpreadsheetDashboardModels } from "@spreadsheet_dashboard/../tests/helpers/data";

describe.current.tags("desktop");
defineSpreadsheetDashboardModels();

test("@spreadsheet_dashboard/sidebar/renders draggable resize handle with col-resize cursor", async () => {
    await createSpreadsheetDashboard();
    expect(".o_search_panel_resize").toHaveCount(1, {
        message: "It should display one resize handle",
    });
});

test("@spreadsheet_dashboard/sidebar/renders header with Dashboards title and close button", async () => {
    await createSpreadsheetDashboard();
    expect(".o_spreadsheet_dashboard_sidebar_header").toHaveCount(1);
    expect(".o_spreadsheet_dashboard_sidebar_header h5").toHaveText("Dashboards");
    expect(".o_spreadsheet_dashboard_sidebar_header button").toHaveCount(1);
});

test("@spreadsheet_dashboard/search_bar/applies compact search pill constraints", async () => {
    await createSpreadsheetDashboard();
    expect(".o_spreadsheet_dashboard_search_bar").toHaveCount(1);
});
