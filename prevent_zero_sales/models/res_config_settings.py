# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    restrict_zero_sale = fields.Boolean("Prevent Zero Sales", default=True)
    restrict_zero_invoice = fields.Boolean("Prevent Zero Invoicing", default=True)
    restrict_zero_pos = fields.Boolean("Prevent Zero POS", default=True)
    
    # New Restrictions
    strict_stock_validation = fields.Boolean("Strict Stock Validation", default=True, help="If checked, restrictions apply to both Ordered and Delivered quantities. If unchecked, only Ordered quantities are restricted.")
    
    sale_restrict_storable = fields.Boolean("Restrict Storable (Sales)", default=True)
    sale_restrict_consumable = fields.Boolean("Restrict Consumables (Sales)", default=False)
    sale_restrict_service = fields.Boolean("Restrict Services (Sales)", default=False)
    sale_restrict_duplicate = fields.Boolean("Restrict Duplicate Lines (Sales)", default=False)

    invoice_restrict_storable = fields.Boolean("Restrict Storable (Invoices)", default=True)
    invoice_restrict_consumable = fields.Boolean("Restrict Consumables (Invoices)", default=False)
    invoice_restrict_service = fields.Boolean("Restrict Services (Invoices)", default=False)
    invoice_restrict_duplicate = fields.Boolean("Restrict Duplicate Lines (Invoices)", default=False)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restrict_zero_sale = fields.Boolean(related='company_id.restrict_zero_sale', readonly=False, string="Prevent Sales with Zero/Negative Stock")
    restrict_zero_invoice = fields.Boolean(related='company_id.restrict_zero_invoice', readonly=False, string="Prevent Invoices with Zero/Negative Stock")
    restrict_zero_pos = fields.Boolean(related='company_id.restrict_zero_pos', readonly=False, string="Prevent POS with Zero/Negative Stock")

    strict_stock_validation = fields.Boolean(related='company_id.strict_stock_validation', readonly=False, string="Strict Stock Validation (Ordered and Delivered)")

    sale_restrict_storable = fields.Boolean(related='company_id.sale_restrict_storable', readonly=False, string="Restrict Storable Products")
    sale_restrict_consumable = fields.Boolean(related='company_id.sale_restrict_consumable', readonly=False, string="Restrict Consumable Products")
    sale_restrict_service = fields.Boolean(related='company_id.sale_restrict_service', readonly=False, string="Restrict Service Products")
    sale_restrict_duplicate = fields.Boolean(related='company_id.sale_restrict_duplicate', readonly=False, string="Prevent Duplicate Lines")

    invoice_restrict_storable = fields.Boolean(related='company_id.invoice_restrict_storable', readonly=False, string="Restrict Storable Products")
    invoice_restrict_consumable = fields.Boolean(related='company_id.invoice_restrict_consumable', readonly=False, string="Restrict Consumable Products")
    invoice_restrict_service = fields.Boolean(related='company_id.invoice_restrict_service', readonly=False, string="Restrict Service Products")
    invoice_restrict_duplicate = fields.Boolean(related='company_id.invoice_restrict_duplicate', readonly=False, string="Prevent Duplicate Lines")
