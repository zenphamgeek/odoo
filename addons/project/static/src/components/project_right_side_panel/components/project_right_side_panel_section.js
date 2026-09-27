import { Component } from "@odoo/owl";

export class ProjectRightSidePanelSection extends Component {
    static props = {
        name: { type: String, optional: true },
        header: { type: Boolean, optional: true },
        show: { type: Boolean, optional: true },
        showData: { type: Boolean, optional: true },
        slots: {
            type: Object,
            optional: true,
        },
        dataClassName: { type: String, optional: true },
        headerClassName: { type: String, optional: true },
    };
    static defaultProps = {
        header: true,
        showData: true,
    };
}
