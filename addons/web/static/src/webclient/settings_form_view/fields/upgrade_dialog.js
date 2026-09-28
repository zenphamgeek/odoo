import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

import { Component, t, useProps } from "@insilos/owl";

export class UpgradeDialog extends Component {
    static template = "web.UpgradeDialog";
    static components = { Dialog };
    props = useProps({
        close: t.function(),
    });
    setup() {
        this.orm = useService("orm");
    }
    async _confirmUpgrade() {
        const usersCount = await this.orm.call("res.users", "search_count", [
            [["share", "=", false]],
        ]);
        window.open(
            "https://insilos.com",
            "_blank"
        );
        this.props.close();
    }
}
