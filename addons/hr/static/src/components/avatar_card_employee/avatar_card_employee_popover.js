import { AvatarCardResourcePopover } from "@resource_mail/components/avatar_card_resource/avatar_card_resource_popover";

export class AvatarCardEmployeePopover extends AvatarCardResourcePopover {
    get fieldNames() {
        const excludedFields = ["employee_id", "resource_type"];
        return super.fieldNames.filter((field) => !excludedFields.includes(field));
    }
}
