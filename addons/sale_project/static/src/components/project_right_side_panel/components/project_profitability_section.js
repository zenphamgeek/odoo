import { Component, useState } from "@odoo/owl";

export class ProjectProfitabilitySection extends Component {
    static props = {
        revenue: { type: Object, optional: true },
        labels: { type: Object, optional: true },
        formatMonetary: { type: Function, optional: true },
        onProjectActionClick: { type: Function, optional: true },
        onClick: { type: Function, optional: true },
        projectId: { type: Number, optional: true },
        context: { type: Object, optional: true },
    };

    setup() {
        this.state = useState({
            isFolded: true,
            displayLoadMore: null,
        });
    }

    _getOrmValue(offset, section_id) {
        return {
            function: "get_sale_items_data",
            args: [this.props.projectId, offset, 5, true, section_id],
        };
    }
}
