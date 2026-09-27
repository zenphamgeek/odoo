import { Component } from "@odoo/owl";

export class WorkEntryCalendarMultiSelectionButtons extends Component {
    static template = "hr_work_entry.WorkEntryCalendarMultiSelectionButtons";
    static props = {
        reactive: {
            type: Object,
            shape: {
                onPlan: { type: Function, optional: true },
                onAdd: { type: Function, optional: true },
            },
            optional: true,
        },
    };
    makeValues(workEntryTypeId) {
        return { work_entry_type_id: workEntryTypeId };
    }
}
