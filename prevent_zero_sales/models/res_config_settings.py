# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restrict_zero_sale = fields.Boolean(
        related='company_id.restrict_zero_sale', readonly=False,
        string="Prevent Sales with Zero/Negative Stock")
    restrict_zero_invoice = fields.Boolean(
        related='company_id.restrict_zero_invoice', readonly=False,
        string="Prevent Invoices with Zero/Negative Stock")

    strict_stock_validation = fields.Boolean(
        related='company_id.strict_stock_validation', readonly=False,
        string="Strict Stock Validation (Ordered and Delivered)")

    lock_draft_invoice_from_sale = fields.Boolean(
        related='company_id.lock_draft_invoice_from_sale', readonly=False,
        string="Lock Draft Invoices from Sales Orders")

    sale_restrict_qty = fields.Boolean(
        related='company_id.sale_restrict_qty', readonly=False,
        string="Block Zero/Negative Quantity (Sales)")
    sale_restrict_price = fields.Boolean(
        related='company_id.sale_restrict_price', readonly=False,
        string="Block Zero/Negative Price (Sales)")
    sale_restrict_stock = fields.Boolean(
        related='company_id.sale_restrict_stock', readonly=False,
        string="Block Insufficient Stock (Sales)")

    invoice_restrict_qty = fields.Boolean(
        related='company_id.invoice_restrict_qty', readonly=False,
        string="Block Zero/Negative Quantity (Invoices)")
    invoice_restrict_price = fields.Boolean(
        related='company_id.invoice_restrict_price', readonly=False,
        string="Block Zero/Negative Price (Invoices)")
    invoice_restrict_stock = fields.Boolean(
        related='company_id.invoice_restrict_stock', readonly=False,
        string="Block Insufficient Stock (Invoices)")
    invoice_validate_from_sale = fields.Boolean(
        related='company_id.invoice_validate_from_sale', readonly=False,
        string="Also Validate Invoice Lines from Sales Orders")

    sale_restrict_storable = fields.Boolean(
        related='company_id.sale_restrict_storable', readonly=False,
        string="Restrict Storable Products (Sales)")
    sale_restrict_consumable = fields.Boolean(
        related='company_id.sale_restrict_consumable', readonly=False,
        string="Restrict Consumable Products (Sales)")
    sale_restrict_service = fields.Boolean(
        related='company_id.sale_restrict_service', readonly=False,
        string="Restrict Service Products (Sales)")
    sale_restrict_duplicate = fields.Boolean(
        related='company_id.sale_restrict_duplicate', readonly=False,
        string="Prevent Duplicate Lines (Sales)")

    invoice_restrict_storable = fields.Boolean(
        related='company_id.invoice_restrict_storable', readonly=False,
        string="Restrict Storable Products (Invoices)")
    invoice_restrict_consumable = fields.Boolean(
        related='company_id.invoice_restrict_consumable', readonly=False,
        string="Restrict Consumable Products (Invoices)")
    invoice_restrict_service = fields.Boolean(
        related='company_id.invoice_restrict_service', readonly=False,
        string="Restrict Service Products (Invoices)")
    invoice_restrict_duplicate = fields.Boolean(
        related='company_id.invoice_restrict_duplicate', readonly=False,
        string="Prevent Duplicate Lines (Invoices)")
