import { Component, t, useProps } from "@insilos/owl";

export class ActionHelper extends Component {
    static template = "web.ActionHelper";
    props = useProps({
        noContentHelp: t.string().optional(),
    });

    get showDefaultHelper() {
        return !this.props.noContentHelp;
    }

    onNocontentClick(ev) {
        const smilingFace = ev.target.closest(".o_view_nocontent_smiling_face");
        if (smilingFace) {
            const link = ev.currentTarget.querySelector("a[href]");
            if (link) {
                link.click();
                return;
            }
            const primaryBtn = document.querySelector(
                ".o_control_panel_main_buttons button.btn-primary, " +
                ".o_control_panel_main_buttons .o_gantt_button_add, " +
                ".o_control_panel_main_buttons .o-kanban-button-new, " +
                ".o_control_panel_main_buttons .o_list_button_add"
            );
            if (primaryBtn) {
                primaryBtn.click();
            }
        }
    }
}
