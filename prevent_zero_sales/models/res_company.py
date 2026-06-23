# -*- coding: utf-8 -*-

from odoo import fields, models

# Sentinel returned to the list renderer when a line has no stock restriction,
# so the client-side check never blocks it.
UNLIMITED_QTY = 999999999.0


class ResCompany(models.Model):
    _inherit = 'res.company'

    restrict_zero_sale = fields.Boolean(
        "Prevent Zero Sales", default=True,
        help="Block confirmation of sales orders containing lines with zero or "
             "negative quantity/price, or with insufficient forecasted stock.")
    restrict_zero_invoice = fields.Boolean(
        "Prevent Zero Invoicing", default=True,
        help="Block posting of customer invoices containing lines with zero or "
             "negative quantity/price, or with insufficient forecasted stock.")

    lock_draft_invoice_from_sale = fields.Boolean(
        "Lock Draft Invoices from Sales Orders", default=False,
        help="Prevent editing customer invoices generated from a sales order "
             "while they are still in draft. They can only be posted, or "
             "unlocked by an authorized user, but not modified.")

    strict_stock_validation = fields.Boolean(
        "Strict Stock Validation", default=True,
        help="If checked, stock restrictions apply regardless of the product "
             "invoicing policy. If unchecked, products invoiced on delivered "
             "quantities are not restricted.")

    # --- Validadores activables individualmente (default off: opt-in) ---
    sale_restrict_qty = fields.Boolean("Block Zero/Negative Quantity (Sales)", default=False)
    sale_restrict_price = fields.Boolean("Block Zero/Negative Price (Sales)", default=False)
    sale_restrict_stock = fields.Boolean("Block Insufficient Stock (Sales)", default=False)

    invoice_restrict_qty = fields.Boolean("Block Zero/Negative Quantity (Invoices)", default=False)
    invoice_restrict_price = fields.Boolean("Block Zero/Negative Price (Invoices)", default=False)
    invoice_restrict_stock = fields.Boolean("Block Insufficient Stock (Invoices)", default=False)
    invoice_validate_from_sale = fields.Boolean(
        "Also Validate Invoice Lines from Sales Orders", default=False,
        help="Apply the invoice validators (quantity, price, insufficient stock) "
             "also to lines coming from a sales order. When off, those lines are "
             "assumed already validated at the order and are skipped. Out-of-stock "
             "lines from a sales order are blocked with an error, never removed, "
             "to preserve the order↔invoice link.")

    # --- A qué tipo de producto aplica el chequeo de stock ---
    sale_restrict_storable = fields.Boolean("Restrict Storable (Sales)", default=True)
    sale_restrict_consumable = fields.Boolean("Restrict Consumables (Sales)", default=False)
    sale_restrict_service = fields.Boolean("Restrict Services (Sales)", default=False)
    sale_restrict_duplicate = fields.Boolean("Restrict Duplicate Lines (Sales)", default=False)

    invoice_restrict_storable = fields.Boolean("Restrict Storable (Invoices)", default=True)
    invoice_restrict_consumable = fields.Boolean("Restrict Consumables (Invoices)", default=False)
    invoice_restrict_service = fields.Boolean("Restrict Services (Invoices)", default=False)
    invoice_restrict_duplicate = fields.Boolean("Restrict Duplicate Lines (Invoices)", default=False)

    def _pzs_is_product_restricted(self, product, mode):
        """Return True when stock restrictions apply to ``product``.

        :param product: a ``product.product`` record
        :param mode: ``'sale'`` or ``'invoice'``
        """
        self.ensure_one()
        if mode == 'sale':
            storable = self.sale_restrict_storable
            consumable = self.sale_restrict_consumable
            service = self.sale_restrict_service
        else:
            storable = self.invoice_restrict_storable
            consumable = self.invoice_restrict_consumable
            service = self.invoice_restrict_service

        # Odoo 18: storable goods are type 'consu' with is_storable=True.
        if product.is_storable:
            restricted = storable
        elif product.type in ('consu', 'combo'):
            restricted = consumable
        elif product.type == 'service':
            restricted = service
        else:
            restricted = False

        if restricted and not self.strict_stock_validation \
                and product.invoice_policy == 'delivery':
            return False
        return restricted
