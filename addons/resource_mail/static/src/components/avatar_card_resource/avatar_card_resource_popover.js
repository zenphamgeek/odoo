import { Component } from "@odoo/owl";

export class AvatarCardResourcePopover extends Component {
    async onWillStart() {}
    get fieldNames() {
        return ["email", "im_status", "name", "phone", "resource_type", "share", "user_id"];
    }
    get hasFooter() {
        return false;
    }
}
