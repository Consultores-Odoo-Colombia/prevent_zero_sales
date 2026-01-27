# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    stock_warning_banner = fields.Html(compute='_compute_stock_warning_banner')

    @api.depends('invoice_line_ids.quantity', 'invoice_line_ids.product_id', 'invoice_line_ids.product_id.virtual_available')
    def _compute_stock_warning_banner(self):
        for move in self:
            move.stock_warning_banner = False
            # Check Config
            if not move.company_id.restrict_zero_invoice:
                continue

            if move.move_type in ['out_invoice', 'out_refund']:
                for line in move.invoice_line_ids:
                    if line.display_type == 'product' or (not line.display_type and line.product_id):
                        # Config check: only warn if restricted
                        product_type = line.product_id.type
                        is_restricted = False
                        if product_type == 'product' and move.company_id.invoice_restrict_storable:
                            is_restricted = True
                        elif product_type == 'consu' and move.company_id.invoice_restrict_consumable:
                            is_restricted = True
                        elif product_type == 'service' and move.company_id.invoice_restrict_service:
                            is_restricted = True
                        
                        if not is_restricted:
                            continue

                        # Check Policy
                        if not move.company_id.strict_stock_validation:
                            if line.product_id.invoice_policy == 'delivery':
                                continue

                        # Always use Forecasted Stock
                        stock_qty = line.product_id.virtual_available
                        
                        if line.quantity > stock_qty:
                            move.stock_warning_banner = _('<div class="alert alert-danger" role="alert">⚠️ <b>Stock Alert:</b> Requested quantity exceeds available stock (%s).</div>') % stock_qty
                            break

    def action_post(self):
        # Strict Validation on Post (Invoice Confirmation)
        _logger.info(">>>>>>>>> VALIDATE INVOICE (action_post) <<<<<<<<<<")
        for move in self:
            if not move.company_id.restrict_zero_invoice:
                continue

            if move.move_type in ['out_invoice', 'out_refund']:
                for line in move.invoice_line_ids:
                    # Validate product lines
                    if line.display_type == 'product' or (not line.display_type and line.product_id):
                        # Basic quantity/price set checks
                        if line.quantity <= 0:
                            raise ValidationError(_("Cannot confirm: The quantity for product line %s is 0 or negative.") % line.product_id.name)
                        if line.price_unit <= 0:
                            raise ValidationError(_("Cannot confirm: The price for product %s is 0 or negative.") % line.product_id.name)
                        
                        # Stock Check
                        product_type = line.product_id.type
                        is_restricted = False
                        if product_type == 'product' and move.company_id.invoice_restrict_storable:
                            is_restricted = True
                        elif product_type == 'consu' and move.company_id.invoice_restrict_consumable:
                            is_restricted = True
                        elif product_type == 'service' and move.company_id.invoice_restrict_service:
                            is_restricted = True
                        
                        if not is_restricted:
                            continue

                        # Check Policy
                        if not move.company_id.strict_stock_validation:
                            if line.product_id.invoice_policy == 'delivery':
                                continue

                        # Always use Forecasted Stock
                        stock_qty = line.product_id.virtual_available
                        
                        if line.quantity > stock_qty:
                            raise ValidationError(_("Restriction Active: Not enough stock for product %s. (Requested: %s, Available: %s)") % (line.product_id.name, line.quantity, stock_qty))
            
            # Check for Duplicate Lines (Configurable)
            if move.company_id.invoice_restrict_duplicate:
                product_counts = {}
                for line in move.invoice_line_ids:
                    if not line.product_id:
                        continue
                    if line.product_id.id in product_counts:
                        raise ValidationError(_("Duplicate Line Restriction: Product %s is present multiple times in the invoice.") % line.product_id.name)
                    product_counts[line.product_id.id] = True
        
        return super(AccountMove, self).action_post()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    stock_warning_banner = fields.Html(compute='_compute_stock_warning_banner')

    @api.depends('order_line.product_uom_qty', 'order_line.product_id', 'order_line.product_id.virtual_available')
    def _compute_stock_warning_banner(self):
        for order in self:
            order.stock_warning_banner = False
            if not order.company_id.restrict_zero_sale:
                continue

            for line in order.order_line:
                product_type = line.product_id.type
                is_restricted = False
                if product_type == 'product' and order.company_id.sale_restrict_storable:
                    is_restricted = True
                elif product_type == 'consu' and order.company_id.sale_restrict_consumable:
                    is_restricted = True
                elif product_type == 'service' and order.company_id.sale_restrict_service:
                    is_restricted = True
                
                if not is_restricted:
                    continue

                if not order.company_id.strict_stock_validation:
                    if line.product_id.invoice_policy == 'delivery':
                        continue

                # Always use Forecasted Stock
                stock_qty = line.product_id.virtual_available
                
                if line.product_uom_qty > stock_qty:
                    order.stock_warning_banner = _('<div class="alert alert-danger" role="alert">⚠️ <b>Stock Alert (Sales):</b> Quantity exceeds available stock (%s).</div>') % stock_qty
                    break

    def action_confirm(self):
        _logger.info(">>>>>>>>> VALIDATE SALE (action_confirm) - START <<<<<<<<<<")
        for order in self:
            if not order.company_id.restrict_zero_sale:
                _logger.info("StockRestriction: Skipping validation (Setting Disabled)")
                continue

            if not order.order_line:
                raise ValidationError(_("Cannot confirm an empty sale order."))

            for line in order.order_line:
                if line.product_uom_qty <= 0:
                    raise ValidationError(_("Cannot confirm sale: The quantity for product %s is 0 or negative.") % line.product_id.name)
                if line.price_unit <= 0:
                    raise ValidationError(_("Cannot confirm sale: The price for product %s is 0 or negative.") % line.product_id.name)

                product_type = line.product_id.type
                is_restricted = False
                if product_type == 'product' and order.company_id.sale_restrict_storable:
                    is_restricted = True
                elif product_type == 'consu' and order.company_id.sale_restrict_consumable:
                    is_restricted = True
                elif product_type == 'service' and order.company_id.sale_restrict_service:
                    is_restricted = True
                
                if not is_restricted:
                    continue

                if not order.company_id.strict_stock_validation:
                    if line.product_id.invoice_policy == 'delivery':
                        continue

                # Always use Forecasted Stock
                stock_qty = line.product_id.virtual_available
                
                if line.product_uom_qty > stock_qty:
                    raise ValidationError(_("Restriction Active: Not enough stock for product %s. (Requested: %s, Available: %s)") % (line.product_id.name, line.product_uom_qty, stock_qty))

            # Check for Duplicate Lines (Configurable)
            if order.company_id.sale_restrict_duplicate:
                product_counts = {}
                for line in order.order_line:
                    if not line.product_id:
                        continue
                    if line.product_id.id in product_counts:
                        raise ValidationError(_("Duplicate Line Restriction: Product %s is present multiple times in the sale order.") % line.product_id.name)
                    product_counts[line.product_id.id] = True
        
        return super(SaleOrder, self).action_confirm()



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_on_hand_check = fields.Float(compute='_compute_qty_on_hand_check', store=False)

    @api.depends('product_id', 'order_id.company_id', 'company_id')
    def _compute_qty_on_hand_check(self):
        for line in self:
            if not line.product_id:
                line.qty_on_hand_check = 0.0
                continue

            # Default to Forecasted Stock
            stock_qty = line.product_id.virtual_available
            
            # Check Config to see if we should enforce restriction (return real stock) or bypass (return Infinity)
            company = line.company_id or line.order_id.company_id or self.env.company
            
            if not company.restrict_zero_sale:
                line.qty_on_hand_check = 999999999.0
                continue

            product_type = line.product_id.type
            is_restricted = False
            if product_type == 'product' and company.sale_restrict_storable:
                is_restricted = True
            elif product_type == 'consu' and company.sale_restrict_consumable:
                is_restricted = True
            elif product_type == 'service' and company.sale_restrict_service:
                is_restricted = True
            
            if not is_restricted:
                line.qty_on_hand_check = 999999999.0
                continue

            if not company.strict_stock_validation:
                if line.product_id.invoice_policy == 'delivery':
                    line.qty_on_hand_check = 999999999.0
                    continue

            # If restricted, return actual Forecasted Stock
            line.qty_on_hand_check = stock_qty

    @api.onchange('product_id')
    def _onchange_product_id_duplicate_check(self):
        for line in self:
            if not line.product_id:
                continue
            
            # Check Config - Use company_id directly if possible or env user company as fallback context
            company = line.company_id or line.order_id.company_id or self.env.company

            # 0. Live Duplicate Check (Memory/Compute)
            # Must also respect the main "Prevent Zero Sales" toggle
            if company.restrict_zero_sale and company.sale_restrict_duplicate:
                # Check if product exists in other lines (excluding self if possible, though new line ID might be NewId)
                # In onchange, we iterate over the virtual records in order_id.order_line
                duplicate_count = 0
                for other_line in line.order_id.order_line:
                    if other_line.product_id == line.product_id:
                        duplicate_count += 1
                
                # If count > 1, it means we have the current line plus at least one more
                if duplicate_count > 1:
                    line.product_id = False
                    return {
                        'warning': {
                            'title': _("Duplicate Product"),
                            'message': _("This product is already present in the order. Duplicate lines are not allowed.")
                        }
                    }

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id_check_stock(self):
        for line in self:
            if not line.product_id or line.product_id.type == 'service':
                continue
            
            # Check Config - Use company_id directly if possible or env user company as fallback context
            company = line.company_id or line.order_id.company_id or self.env.company

            # Duplicate Check REMOVED from here to allow quantity updates

            if not company.restrict_zero_sale:
                return

            product_type = line.product_id.type
            is_restricted = False
            if product_type == 'product' and company.sale_restrict_storable:
                is_restricted = True
            elif product_type == 'consu' and company.sale_restrict_consumable:
                is_restricted = True
            elif product_type == 'service' and company.sale_restrict_service:
                is_restricted = True
            
            if not is_restricted:
                return

            if not company.strict_stock_validation:
                if line.product_id.invoice_policy == 'delivery':
                    return

            # Always use Forecasted Stock
            stock_on_hand = line.product_id.virtual_available
            
            # 1. Check Negative Quantity (User Requirement: Delete line if negative)
            # Allow 0 initially (Odoo default), invalid 0 will be blocked on confirm.
            if line.product_uom_qty < 0:
                 line.product_id = False
                 line.product_uom_qty = 0
                 return {
                    'warning': {
                        'title': _("Invalid Quantity"),
                        'message': _("Quantity cannot be negative. The product has been removed.")
                    }
                }

            # 2. Check Zero/Negative Stock (User Requirement: Delete line)
            # We ONLY check this if the user is adding the product (or changing the product), 
            # NOT necessarily if they are just changing quantity, but the requirement implies strictness.
            # However, standard behavior is to check on any relevant change.
            if stock_on_hand <= 0:
                 # Clear line
                 line.product_id = False
                 line.product_uom_qty = 0
                 return {
                    'warning': {
                        'title': _("Product Not Available"),
                        'message': _("The product has been removed because there is no available stock (%s).") % stock_on_hand
                    }
                }
            
            # 3. Check Insufficient Stock (User Requirement: Limit Quantity)
            if line.product_uom_qty > stock_on_hand:
                 line.product_uom_qty = stock_on_hand
                 return {
                    'warning': {
                        'title': _("Insufficient Stock"),
                        'message': _("You cannot add more quantity because there is not enough stock. (Available: %s)") % stock_on_hand
                    }
                }

    @api.constrains('product_uom_qty', 'price_unit', 'product_id')
    def _check_strict_values_and_stock(self):
         # Validations delegated to action_confirm
         pass

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    qty_on_hand_check = fields.Float(compute='_compute_qty_on_hand_check', store=False)

    @api.depends('product_id', 'move_id.company_id', 'company_id')
    def _compute_qty_on_hand_check(self):
        for line in self:
            if not line.product_id:
                line.qty_on_hand_check = 0.0
                continue

            # Default to Forecasted Stock
            stock_qty = line.product_id.virtual_available

            if line.move_id.move_type not in ('out_invoice', 'out_refund'):
                 line.qty_on_hand_check = 999999999.0
                 continue

            # Check Config
            company = line.company_id or line.move_id.company_id or self.env.company
            if not company.restrict_zero_invoice:
                line.qty_on_hand_check = 999999999.0
                continue

            product_type = line.product_id.type
            is_restricted = False
            if product_type == 'product' and company.invoice_restrict_storable:
                is_restricted = True
            elif product_type == 'consu' and company.invoice_restrict_consumable:
                is_restricted = True
            elif product_type == 'service' and company.invoice_restrict_service:
                is_restricted = True
            
            if not is_restricted:
                line.qty_on_hand_check = 999999999.0
                continue
            
            if not company.strict_stock_validation:
                if line.product_id.invoice_policy == 'delivery':
                    line.qty_on_hand_check = 999999999.0
                    continue

            # If restricted, return actual Forecasted Stock
            line.qty_on_hand_check = stock_qty

    @api.onchange('product_id')
    def _onchange_product_id_duplicate_check(self):
        for line in self:
            if not line.product_id:
                continue
            if line.move_id.move_type not in ('out_invoice', 'out_refund'):
                continue
            
            # Check Config
            company = line.company_id or line.move_id.company_id or self.env.company

            # Must also respect the main "Prevent Zero Invoicing" toggle
            if company.restrict_zero_invoice and company.invoice_restrict_duplicate:
                duplicate_count = 0
                for other_line in line.move_id.invoice_line_ids:
                    if other_line.product_id == line.product_id:
                        duplicate_count += 1
                
                # If count > 1, it means we have the current line plus at least one more
                if duplicate_count > 1:
                    line.product_id = False
                    return {
                        'warning': {
                            'title': _("Duplicate Product"),
                            'message': _("This product is already present in the invoice. Duplicate lines are not allowed.")
                        }
                    }

    @api.onchange('product_id', 'quantity')
    def _onchange_product_id_check_stock(self):
        for line in self:
            if not line.product_id or line.product_id.type == 'service':
                continue
            
            if line.move_id.move_type not in ('out_invoice', 'out_refund'):
                continue
            
            # Check Config
            company = line.company_id or line.move_id.company_id or self.env.company

            # Duplicate Check REMOVED from here

            if not company.restrict_zero_invoice:
                return

            product_type = line.product_id.type
            is_restricted = False
            if product_type == 'product' and company.invoice_restrict_storable:
                is_restricted = True
            elif product_type == 'consu' and company.invoice_restrict_consumable:
                is_restricted = True
            elif product_type == 'service' and company.invoice_restrict_service:
                is_restricted = True
            
            if not is_restricted:
                return

            if not company.strict_stock_validation:
                if line.product_id.invoice_policy == 'delivery':
                    return

            # Always use Forecasted Stock
            stock_on_hand = line.product_id.virtual_available
            
            # 1. Check Negative Quantity (User Requirement: Delete line if negative)
            # Allow 0 initially (Odoo default), invalid 0 will be blocked on confirm.
            if line.quantity < 0:
                 line.product_id = False
                 line.quantity = 0
                 return {
                    'warning': {
                        'title': _("Invalid Quantity"),
                        'message': _("Quantity cannot be negative. The product has been removed.")
                    }
                }

            # 2. Check Zero/Negative Stock (User Requirement: Delete line)
            if stock_on_hand <= 0:
                 line.product_id = False
                 line.quantity = 0
                 return {
                    'warning': {
                        'title': _("Product Not Available"),
                        'message': _("The product has been removed because there is no available stock (%s).") % stock_on_hand
                    }
                }

            # 3. Check Insufficient Stock (User Requirement: Limit Quantity)
            if line.quantity > stock_on_hand:
                 line.quantity = stock_on_hand
                 return {
                    'warning': {
                        'title': _("Insufficient Stock"),
                        'message': _("You cannot add more quantity because there is not enough stock. (Available: %s)") % stock_on_hand
                    }
                }

    @api.constrains('quantity', 'price_unit', 'product_id')
    def _check_strict_values_and_stock_invoice(self):
         pass



