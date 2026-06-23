/** @odoo-module **/

import { SectionAndNoteListRenderer } from "@account/components/section_and_note_fields_backend/section_and_note_fields_backend";
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
        // Intercept Enter and Tab to prevent "Save & New" while a line has no
        // available stock (quantity auto-set to 0). Quantities over the limit are
        // capped automatically, so the only blocking case left is out-of-stock.
        // shouldBlockCreation() scans every record, so it works even when
        // `record` is undefined in some contexts.
        if (ev.key === "Enter" || ev.key === "Tab") {
            if (this.shouldBlockCreation()) {
                ev.preventDefault();
                ev.stopPropagation();
                this.notification.add(
                    _t("There is a line with no available stock (quantity set to 0). Please resolve it before adding more products."),
                    { type: "danger", sticky: false }
                );
                return;
            }
        }

        return super.onCellKeydown(ev, record, column);
    }

    shouldBlockCreation() {
        // Block row creation while any line violates the stock restriction.
        // qty_on_hand_check is the per-line limit computed server-side
        // (UNLIMITED_QTY when the line is not restricted).
        for (const record of this.props.list.records) {
            const data = record.data;
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
