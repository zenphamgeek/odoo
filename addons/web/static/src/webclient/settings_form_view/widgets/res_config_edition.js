import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { Setting } from "@web/views/form/setting/setting";

import { Component, useProps } from "@insilos/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
const { DateTime } = luxon;

/**
 * Widget in the settings that handles a part of the "About" section.
 * Contains info about the insilos version, database expiration date and copyrights.
 */
class ResConfigEdition extends Component {
    static template = "res_config_edition";
    static components = { Setting };
    props = useProps({
        ...standardWidgetProps,
    });

    setup() {
        this.serverVersion = session.server_version;
        this.serverBuildId = session.server_build_id || "";
        this.serverBuildDatetime = session.server_build_datetime || "";
        this.serverBuildCommit = session.server_build_commit || "";
        this.serverBuildTag = session.server_build_tag || "";
        this.expirationDate = session.expiration_date
            ? DateTime.fromSQL(session.expiration_date).toLocaleString(DateTime.DATE_FULL)
            : DateTime.now().plus({ days: 30 }).toLocaleString(DateTime.DATE_FULL);
    }
}

export const resConfigEdition = {
    component: ResConfigEdition,
};

registry.category("view_widgets").add("res_config_edition", resConfigEdition);
