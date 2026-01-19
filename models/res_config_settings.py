# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    restrict_zero_sale = fields.Boolean("Prevent Zero Sales", default=True)
    restrict_zero_invoice = fields.Boolean("Prevent Zero Invoicing", default=True)
    restrict_zero_pos = fields.Boolean("Prevent Zero POS", default=True)
    stock_restriction_type = fields.Selection([
        ('forecast', 'Forecasted Stock (Virtual)'),
        ('on_hand', 'On Hand Stock (Physical)')
    ], string="Restriction Type", default='forecast')

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
    stock_restriction_type = fields.Selection(
        related='company_id.stock_restriction_type',
        readonly=False,
        string="Stock Restriction Type"
    )
