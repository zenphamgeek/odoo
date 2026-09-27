import { Component, useState } from "@odoo/owl";
import { ProjectRightSidePanelSection } from "./components/project_right_side_panel_section";

export class ProjectRightSidePanel extends Component {
    static components = {
        ProjectRightSidePanelSection,
    };
    static props = {
        context: { type: Object, optional: true },
        domain: { type: Array, optional: true },
    };

    setup() {
        this.state = useState({
            data: {},
        });
    }

    get panelVisible() {
        return false;
    }
}
