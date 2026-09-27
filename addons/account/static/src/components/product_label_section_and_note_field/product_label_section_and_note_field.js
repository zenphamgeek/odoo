import { Component } from "@odoo/owl";

export class ProductLabelSectionAndNoteField extends Component {
    isNote(record = null) {
        record = record || this.props?.record;
        return record?.data?.display_type === "line_note";
    }
}

export const productLabelSectionAndNoteField = {
    component: ProductLabelSectionAndNoteField,
};
