# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    restrict_zero_sale = fields.Boolean("Prevent Zero Sales", default=True)
    restrict_zero_invoice = fields.Boolean("Prevent Zero Invoicing", default=True)
    restrict_zero_pos = fields.Boolean("Prevent Zero POS", default=True)
    restrict_zero_pos = fields.Boolean("Prevent Zero POS", default=True)
    # stock_restriction_type removed (Always Forecasted)

    stock_validation_policy = fields.Selection([
        ('all', 'Strict (All Products - Ordered & Delivered)'),
        ('ordered_only', 'Respect Product Policy (Ordered Qty Only)')
    ], string="Validation Policy", default='all', 
       help="Strict: Always restrict zero sales.\nRespect Policy: Only restrict products with 'Ordered Quantities' invoicing policy.")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restrict_zero_sale = fields.Boolean(
        related='company_id.restrict_zero_sale', 
        readonly=False,
        string="Prevent Sales with Zero/Negative Stock"
    )
    restrict_zero_invoice = fields.Boolean(
        related='company_id.restrict_zero_invoice', 
        readonly=False,
        string="Prevent Invoices with Zero/Negative Stock"
    )
    restrict_zero_pos = fields.Boolean(
        related='company_id.restrict_zero_pos', 
        readonly=False,
        string="Prevent POS with Zero/Negative Stock"
    )
    restrict_zero_pos = fields.Boolean(
        related='company_id.restrict_zero_pos', 
        readonly=False,
        string="Prevent POS with Zero/Negative Stock"
    )
    # stock_restriction_type removed (Always Forecasted)
    stock_validation_policy = fields.Selection(
        related='company_id.stock_validation_policy',
        readonly=False,
        string="Validation Policy"
    )
