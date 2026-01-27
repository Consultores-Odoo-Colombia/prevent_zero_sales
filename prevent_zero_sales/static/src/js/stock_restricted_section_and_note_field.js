/** @odoo-module **/

import { SectionAndNoteFieldOne2Many } from "@account/components/section_and_note_fields_backend/section_and_note_fields_backend";
import { StockRestrictedListRenderer } from "./stock_restricted_list_renderer";
import { registry } from "@web/core/registry";

export class StockRestrictedSectionAndNoteField extends SectionAndNoteFieldOne2Many {
    static components = {
        ...SectionAndNoteFieldOne2Many.components,
        ListRenderer: StockRestrictedListRenderer,
    };
}

export const stockRestrictedSectionAndNoteField = {
    ...registry.category("fields").get("section_and_note_one2many"),
    component: StockRestrictedSectionAndNoteField,
};

registry.category("fields").add("stock_restricted_section_and_note_one2many", stockRestrictedSectionAndNoteField);
