/** @odoo-module **/

import { SectionAndNoteListRenderer } from "@account/components/section_and_note_fields_backend/section_and_note_fields_backend";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { _t } from "@web/core/l10n/translation";

export class StockRestrictedListRenderer extends SectionAndNoteListRenderer {
    static rowsTemplate = "prevent_zero_sales.StockRestrictedListRenderer.Rows";

    get displayRowCreates() {
        const shouldBlock = this.shouldBlockCreation();
        
        // Check if we should block creation
        if (shouldBlock) {
            return false;
        }
        return super.displayRowCreates;
    }

    setup() {
        super.setup();
        this.notification = this.env.services.notification;
    }

    async onCellKeydown(ev, record, column) {
        // Intercept Enter and Tab to prevent "Save & New" if stock is invalid
        // console.log("[StockRestricted] onCellKeydown:", ev.key, "Record:", record);
        if (ev.key === "Enter" || ev.key === "Tab") {
             // We rely on shouldBlockCreation() because it iterates all records (including the current one if it's in the list)
             // and checks for any violation. This bypasses the issue of 'record' being undefined in some contexts.
             if (this.shouldBlockCreation()) {
                ev.preventDefault();
                ev.stopPropagation();
                
                // Show a generic message because we might be blocking due to ANY bad line
                 this.notification.add(_t("Adding products with zero or insufficient stock is not allowed. Please correct existing lines."), {
                    type: "danger",
                    sticky: false,
                });
                return;
             }
        }
        
        return super.onCellKeydown(ev, record, column);
    }

    shouldBlockCreation() {
        // Iterate over records to check for stock issues
        // We look for the status set by our widget logic or checking fields directly
        for (const record of this.props.list.records) {
            const data = record.data;
            // Use correct field: qty_on_hand_check
            const limit = data.qty_on_hand_check !== undefined ? data.qty_on_hand_check : (data.virtual_available_at_date || 0);
            const qty = data.quantity || data.qty || data.product_uom_qty || 0;
            const productId = data.product_id;

            if (productId && (limit <= 0 || qty > limit)) {
                return true; 
            }
        }
        return false;
    }
}

export const stockRestrictedListView = {
    ...listView,
    Renderer: StockRestrictedListRenderer,
};

registry.category("views").add("stock_restricted_list", stockRestrictedListView);
