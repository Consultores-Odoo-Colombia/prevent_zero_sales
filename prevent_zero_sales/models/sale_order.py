# -*- coding: utf-8 -*-

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

from . import pzs_stock_mixin as pzs


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    stock_warning_banner = fields.Html(compute='_compute_stock_warning_banner')

    @api.depends('state', 'order_line.product_uom_qty', 'order_line.product_id',
                 'order_line.product_id.virtual_available')
    def _compute_stock_warning_banner(self):
        for order in self:
            order.stock_warning_banner = False
            zero_stock = order._pzs_zero_stock_lines()
            if zero_stock:
                names = ", ".join(zero_stock.mapped('product_id.display_name'))
                order.stock_warning_banner = Markup(
                    '<div class="alert alert-danger" role="alert">⚠️ '
                    '<b>%s</b> %s</div>'
                ) % (
                    _("No Stock:"),
                    _("These products have no available stock and will be excluded "
                      "on confirmation: %s.", names),
                )
                continue
            for line in order.order_line:
                limit = line._pzs_stock_limit()
                if limit is None:
                    continue
                rounding = line.product_id.uom_id.rounding
                if float_compare(line._pzs_qty_in_product_uom(), limit,
                                 precision_rounding=rounding) > 0:
                    order.stock_warning_banner = Markup(
                        '<div class="alert alert-danger" role="alert">⚠️ '
                        '<b>%s</b> %s</div>'
                    ) % (
                        _("Stock Alert:"),
                        _("Requested quantity exceeds available stock (%s).", limit),
                    )
                    break

    def action_confirm(self):
        # Si hay líneas de productos sin stock disponible, preguntar Sí/No antes
        # de confirmar (salvo que ya se haya respondido «Sí» en el asistente).
        if not self.env.context.get('pzs_drop_zero_stock'):
            zero_stock = self.filtered(
                lambda o: (o.company_id or o.env.company).restrict_zero_sale
            )._pzs_zero_stock_lines()
            if zero_stock:
                return self._pzs_open_zero_stock_wizard(zero_stock)
        for order in self:
            order._pzs_validate_order()
        return super().action_confirm()

    def _pzs_zero_stock_lines(self):
        """Líneas de producto restringidas cuyo stock disponible es 0 (o menos),
        tengan o no cantidad. Son las que se ofrecen eliminar al confirmar."""
        lines = self.env['sale.order.line']
        for order in self:
            for line in order.order_line:
                limit = line._pzs_stock_limit()
                if limit is None:
                    continue
                rounding = line.product_id.uom_id.rounding
                if float_compare(limit, 0.0, precision_rounding=rounding) <= 0:
                    lines |= line
        return lines

    def _pzs_open_zero_stock_wizard(self, lines):
        """Abre el diálogo Sí/No listando los productos sin stock."""
        names = "\n".join(
            "• %s" % name
            for name in sorted(set(lines.mapped('product_id.display_name')))
        )
        wizard = self.env['pzs.zero.stock.wizard'].create({
            'res_model': 'sale.order',
            'res_ids_str': ','.join(str(i) for i in self.ids),
            'product_names': names,
            'message': _("The following products have no available stock. Do you "
                         "want to remove them and confirm the order anyway? "
                         "Choosing «No» keeps them highlighted for review."),
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _("Products Without Stock"),
            'res_model': 'pzs.zero.stock.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _pzs_validate_order(self):
        self.ensure_one()
        company = self.company_id or self.env.company
        if not company.restrict_zero_sale:
            return

        # Al confirmar (tras responder «Sí» en el diálogo), eliminar todas las
        # líneas de productos sin stock disponible para que no se facturen.
        if self.env.context.get('pzs_drop_zero_stock'):
            self._pzs_drop_zero_stock_lines()
        else:
            # Salvaguarda: descartar las que quedaron en cantidad 0 sin stock.
            self._pzs_drop_zero_qty_zero_stock_lines()

        if not self.order_line:
            raise ValidationError(_("Cannot confirm an empty sales order."))

        seen_products = set()
        for line in self.order_line:
            if line.display_type or not line.product_id:
                continue

            if company.sale_restrict_qty and line.product_uom_qty <= 0:
                raise ValidationError(_(
                    "Cannot confirm sale: Quantity for product %s is 0 or negative.",
                    line.product_id.display_name))
            if company.sale_restrict_price and line.price_unit <= 0:
                raise ValidationError(_(
                    "Cannot confirm sale: Price for product %s is 0 or negative.",
                    line.product_id.display_name))

            limit = line._pzs_stock_limit()
            if limit is not None:
                rounding = line.product_id.uom_id.rounding
                qty = line._pzs_qty_in_product_uom()
                if float_compare(qty, limit, precision_rounding=rounding) > 0:
                    raise ValidationError(_(
                        "Active Restriction: Not enough stock for product %(product)s. "
                        "(Requested: %(requested)s, Available: %(available)s)",
                        product=line.product_id.display_name,
                        requested=qty, available=limit))

            if company.sale_restrict_duplicate:
                if line.product_id.id in seen_products:
                    raise ValidationError(_(
                        "Duplicate Lines Restriction: Product %s appears multiple "
                        "times in the sales order.", line.product_id.display_name))
                seen_products.add(line.product_id.id)

    def _pzs_drop_zero_qty_zero_stock_lines(self):
        """Elimina las líneas con cantidad 0 y sin stock disponible (límite 0).
        Son las que el onchange dejó en 0 por falta de stock; al confirmar la
        cotización no deben formar parte de la orden."""
        self.ensure_one()
        to_drop = self.env['sale.order.line']
        for line in self.order_line:
            if line.display_type or not line.product_id:
                continue
            limit = line._pzs_stock_limit()
            if limit is None:
                continue
            rounding = line.product_id.uom_id.rounding
            if (float_compare(line.product_uom_qty, 0.0, precision_rounding=rounding) <= 0
                    and float_compare(limit, 0.0, precision_rounding=rounding) <= 0):
                to_drop |= line
        if to_drop:
            to_drop.unlink()

    def _pzs_drop_zero_stock_lines(self):
        """Elimina TODAS las líneas de productos sin stock disponible (límite 0),
        tengan o no cantidad. Es la acción del botón «Sí» del diálogo: así esos
        productos no llegan a la factura. Deja un rastro en el chatter."""
        self.ensure_one()
        to_drop = self._pzs_zero_stock_lines()
        if not to_drop:
            return
        names = ", ".join(sorted(set(to_drop.mapped('product_id.display_name'))))
        to_drop.unlink()
        self.message_post(body=_(
            "Lines removed on confirmation for having no available stock: %s.",
            names))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_on_hand_check = fields.Float(compute='_compute_qty_on_hand_check')

    # --- Accessors usados por la lógica compartida (pzs_stock_mixin) ---
    def _pzs_get_qty(self):
        return self.product_uom_qty

    def _pzs_set_qty(self, value):
        self.product_uom_qty = value

    def _pzs_get_uom(self):
        return self.product_uom

    def _pzs_qty_in_product_uom(self):
        return pzs.qty_in_product_uom(self)

    def _pzs_company(self):
        self.ensure_one()
        return self.company_id or self.order_id.company_id or self.env.company

    def _pzs_stock_limit(self):
        """Return the maximum sellable quantity (in the product reference UoM)
        for this line, or None when the line is not restricted."""
        self.ensure_one()
        product = self.product_id
        if self.display_type or not product:
            return None
        company = self._pzs_company()
        if not company.restrict_zero_sale or not company.sale_restrict_stock:
            return None
        # Once confirmed, stock is already reserved: do not restrict.
        if self.order_id.state not in ('draft', 'sent'):
            return None
        if not company._pzs_is_product_restricted(product, 'sale'):
            return None
        return product.virtual_available

    @api.depends('product_id', 'product_uom', 'order_id.state',
                 'order_id.company_id', 'company_id',
                 'product_id.virtual_available')
    def _compute_qty_on_hand_check(self):
        pzs.compute_qty_on_hand_check(self)

    @api.onchange('product_id')
    def _onchange_product_id_duplicate_check(self):
        for line in self:
            if not line.product_id:
                continue
            company = line._pzs_company()
            if not (company.restrict_zero_sale and company.sale_restrict_duplicate):
                continue
            duplicates = line.order_id.order_line.filtered(
                lambda l: l.product_id == line.product_id)
            if len(duplicates) > 1:
                line.product_id = False
                return {
                    'warning': {
                        'title': _("Duplicate Product"),
                        'message': _("This product is already present in the order. "
                                     "Duplicate lines are not allowed."),
                    }
                }

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id_check_stock(self):
        # Auto-ajusta la cantidad sin perder el producto (lógica compartida).
        return pzs.check_stock_adjust(self)
