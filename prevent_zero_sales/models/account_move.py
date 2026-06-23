# -*- coding: utf-8 -*-

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare

from . import pzs_stock_mixin as pzs

# Campos de "contenido" de la factura que el bloqueo en borrador protege. Una
# escritura de usuario que toque cualquiera de estos sobre una factura bloqueada
# se rechaza; las transiciones de estado (contabilizar) y los recálculos internos
# (totales, etc.) no están aquí, por lo que siguen funcionando.
PZS_LOCKED_PROTECTED_FIELDS = frozenset({
    'invoice_line_ids', 'line_ids',
    'partner_id', 'partner_shipping_id', 'partner_bank_id',
    'invoice_date', 'invoice_date_due', 'date',
    'currency_id', 'invoice_payment_term_id', 'journal_id',
    'fiscal_position_id', 'invoice_origin', 'ref',
    'payment_reference', 'narration',
})


class AccountMove(models.Model):
    _inherit = 'account.move'

    stock_warning_banner = fields.Html(compute='_compute_stock_warning_banner')

    pzs_draft_locked = fields.Boolean(
        "Draft Locked", default=False, copy=False,
        help="When set, this draft customer invoice (generated from a sales "
             "order) is locked against changes until posted or unlocked by an "
             "authorized user.")

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        # Marcar como bloqueadas las facturas de cliente en borrador que nacen de
        # un pedido de venta cuando la compañía activa la opción.
        for move in moves:
            if move.move_type != 'out_invoice' or move.state != 'draft':
                continue
            company = move.company_id or self.env.company
            if company.lock_draft_invoice_from_sale and move._pzs_is_from_sale():
                move.pzs_draft_locked = True
        return moves

    def write(self, vals):
        # Bloqueo duro: rechazar ediciones de usuario sobre facturas bloqueadas en
        # borrador. Se permiten siempre: escrituras del sistema (`env.su`, p.ej. la
        # creación de la factura desde el pedido se hace en sudo), la transición de
        # estado (contabilizar/restablecer) y el desbloqueo (`pzs_force_unlock`).
        if (not self.env.su
                and 'state' not in vals
                and not self.env.context.get('pzs_force_unlock')
                and PZS_LOCKED_PROTECTED_FIELDS.intersection(vals)):
            locked = self.filtered(lambda m: (
                m.pzs_draft_locked and m.state == 'draft'
                and (m.company_id or self.env.company).lock_draft_invoice_from_sale))
            if locked:
                raise UserError(_(
                    "This draft invoice was generated from a sales order and is "
                    "locked against changes. An authorized user must unlock it "
                    "before editing: %s.",
                    ", ".join(locked.mapped('display_name'))))
        return super().write(vals)

    def action_pzs_unlock_draft(self):
        """Botón «Unlock»: reabre la edición del borrador. Solo para usuarios con
        permiso de gestión contable."""
        if not self.env.user.has_group('account.group_account_manager'):
            raise AccessError(_(
                "Only users with accounting management rights can unlock a "
                "locked draft invoice."))
        for move in self:
            if not move.pzs_draft_locked:
                continue
            move.with_context(pzs_force_unlock=True).pzs_draft_locked = False
            move.message_post(body=_(
                "Locked draft invoice unlocked for editing by %s.",
                self.env.user.name))
        return True

    def _pzs_is_from_sale(self):
        """True si la factura proviene de un pedido de venta (alguna línea con
        ``sale_line_ids``)."""
        self.ensure_one()
        return bool(self.invoice_line_ids.sale_line_ids)

    @api.depends('move_type', 'invoice_line_ids.quantity',
                 'invoice_line_ids.product_id',
                 'invoice_line_ids.product_id.virtual_available')
    def _compute_stock_warning_banner(self):
        for move in self:
            move.stock_warning_banner = False
            if move.move_type != 'out_invoice':
                continue
            zero_stock = move._pzs_zero_stock_lines()
            if zero_stock:
                names = ", ".join(zero_stock.mapped('product_id.display_name'))
                move.stock_warning_banner = Markup(
                    '<div class="alert alert-danger" role="alert">⚠️ '
                    '<b>%s</b> %s</div>'
                ) % (
                    _("No Stock:"),
                    _("These products have no available stock and will be excluded "
                      "when posting: %s.", names),
                )
                continue
            for line in move.invoice_line_ids:
                limit = line._pzs_stock_limit()
                if limit is None:
                    continue
                rounding = line.product_id.uom_id.rounding
                if float_compare(line._pzs_qty_in_product_uom(), limit,
                                 precision_rounding=rounding) > 0:
                    move.stock_warning_banner = Markup(
                        '<div class="alert alert-danger" role="alert">⚠️ '
                        '<b>%s</b> %s</div>'
                    ) % (
                        _("Stock Alert:"),
                        _("Requested quantity exceeds available stock (%s).", limit),
                    )
                    break

    def _pzs_zero_stock_lines(self):
        """Líneas de producto sin stock disponible (límite 0 o menos) que son
        candidatas a BORRARSE al contabilizar. Excluye siempre las que provienen
        de un pedido de venta: esas nunca se borran (rompería la conciliación
        pedido↔factura↔entrega); si la compañía activó la validación de líneas de
        pedido, el stock insuficiente las bloquea con error en _pzs_validate_invoice."""
        lines = self.env['account.move.line']
        for move in self:
            for line in move.invoice_line_ids:
                if line.sale_line_ids:
                    continue
                limit = line._pzs_stock_limit()
                if limit is None:
                    continue
                rounding = line.product_id.uom_id.rounding
                if float_compare(limit, 0.0, precision_rounding=rounding) <= 0:
                    lines |= line
        return lines

    def action_post(self):
        # Diálogo Sí/No al contabilizar facturas de cliente con productos sin
        # stock disponible (equivalente a la confirmación del pedido). Se omite
        # en flujos automáticos —ya respondido «Sí» (`pzs_drop_zero_stock`) o
        # asientos con `auto_post`— para no dejar la factura sin contabilizar al
        # devolver una acción de ventana. El cron de auto-post llama a `_post()`,
        # no a `action_post()`, así que ese camino nunca abre el diálogo.
        if not self.env.context.get('pzs_drop_zero_stock'):
            zero_stock = self.filtered(
                lambda m: m.move_type == 'out_invoice'
                and m.auto_post == 'no'
                and (m.company_id or m.env.company).restrict_zero_invoice
            )._pzs_zero_stock_lines()
            if zero_stock:
                return self._pzs_open_zero_stock_wizard(zero_stock)
        for move in self:
            move._pzs_validate_invoice()
        return super().action_post()

    def _pzs_open_zero_stock_wizard(self, lines):
        """Abre el diálogo Sí/No listando los productos sin stock."""
        names = "\n".join(
            "• %s" % name
            for name in sorted(set(lines.mapped('product_id.display_name')))
        )
        wizard = self.env['pzs.zero.stock.wizard'].create({
            'res_model': 'account.move',
            'res_ids_str': ','.join(str(i) for i in self.ids),
            'product_names': names,
            'message': _("The following products have no available stock. Do you "
                         "want to remove them and post the invoice anyway? "
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

    def _pzs_validate_invoice(self):
        self.ensure_one()
        # Only customer invoices are validated. Credit notes are returns: they
        # increase inventory and must not be blocked by stock restrictions.
        if self.move_type != 'out_invoice':
            return
        company = self.company_id or self.env.company
        if not company.restrict_zero_invoice:
            return

        # Al contabilizar, descartar las líneas de productos sin stock disponible
        # para que no se facturen productos que no hay en almacén. Ver
        # salvaguardas de trazabilidad fiscal en _pzs_drop_zero_stock_lines.
        self._pzs_drop_zero_stock_lines()

        seen_products = set()
        for line in self.invoice_line_ids:
            if line.display_type != 'product' or not line.product_id:
                continue

            # Líneas provenientes de un pedido de venta: solo se validan si la
            # compañía activó "Also Validate Invoice Lines from Sales Orders".
            if line.sale_line_ids and not company.invoice_validate_from_sale:
                continue

            if company.invoice_restrict_qty and line.quantity <= 0:
                raise ValidationError(_(
                    "Cannot confirm: Quantity for product %s is 0 or negative.",
                    line.product_id.display_name))
            if company.invoice_restrict_price and line.price_unit <= 0:
                raise ValidationError(_(
                    "Cannot confirm: Price for product %s is 0 or negative.",
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

            if company.invoice_restrict_duplicate:
                if line.product_id.id in seen_products:
                    raise ValidationError(_(
                        "Duplicate Lines Restriction: Product %s appears multiple "
                        "times in the invoice.", line.product_id.display_name))
                seen_products.add(line.product_id.id)

    def _pzs_drop_zero_stock_lines(self):
        """Elimina, antes de contabilizar, las líneas de productos sin stock
        disponible (límite 0), tengan o no cantidad, para que no se facturen.
        Salvaguardas propias de la trazabilidad fiscal de la factura:

        * Solo se ejecuta en borrador (action_post lo llama antes de validar el
          asiento), nunca sobre una factura ya contabilizada e inmutable.
        * `_pzs_zero_stock_lines` excluye las líneas enlazadas a un pedido de venta
          (``sale_line_ids``); esas líneas NUNCA se borran, preservando la
          conciliación pedido↔factura↔entrega. Si la compañía activó la validación
          de líneas de pedido, su stock insuficiente bloquea con error en
          ``_pzs_validate_invoice`` en lugar de borrarse.
        * Solo afecta facturas de cliente (`out_invoice`); las notas de crédito
          y los apuntes contables (impuestos/contrapartida) quedan intactos.
        * Si se eliminaran todas las líneas de producto, se bloquea: no se debe
          contabilizar un documento fiscal numerado pero vacío.
        * Deja un rastro en el chatter con los productos retirados y el porqué.
        """
        self.ensure_one()
        to_drop = self._pzs_zero_stock_lines()
        if not to_drop:
            return
        remaining = (self.invoice_line_ids - to_drop).filtered(
            lambda l: l.display_type == 'product')
        if not remaining:
            # No contabilizar una factura sin líneas de producto: generaría un
            # documento fiscal con numeración secuencial pero sin contenido.
            raise ValidationError(_(
                "Cannot post this invoice: all product lines were removed because "
                "they had no available stock. Add at least one product with stock."))
        names = ", ".join(sorted(set(to_drop.mapped('product_id.display_name'))))
        to_drop.unlink()
        self.message_post(body=_(
            "Lines removed on posting for having no available stock: %s.", names))


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    qty_on_hand_check = fields.Float(compute='_compute_qty_on_hand_check')

    # --- Accessors usados por la lógica compartida (pzs_stock_mixin) ---
    def _pzs_get_qty(self):
        return self.quantity

    def _pzs_set_qty(self, value):
        self.quantity = value

    def _pzs_get_uom(self):
        return self.product_uom_id

    def _pzs_qty_in_product_uom(self):
        return pzs.qty_in_product_uom(self)

    def _pzs_company(self):
        self.ensure_one()
        return self.company_id or self.move_id.company_id or self.env.company

    def _pzs_stock_limit(self):
        """Return the maximum invoiceable quantity (in the product reference
        UoM) for this line, or None when the line is not restricted."""
        self.ensure_one()
        product = self.product_id
        if self.display_type != 'product' or not product:
            return None
        if self.move_id.move_type != 'out_invoice':
            return None
        company = self._pzs_company()
        if not company.restrict_zero_invoice or not company.invoice_restrict_stock:
            return None
        # Lines coming from a sales order are skipped unless the company opted in
        # to re-validate them at the invoice (stock may have changed since the
        # order was confirmed).
        if self.sale_line_ids and not company.invoice_validate_from_sale:
            return None
        if not company._pzs_is_product_restricted(product, 'invoice'):
            return None
        return product.virtual_available

    @api.depends('product_id', 'product_uom_id', 'move_id.move_type',
                 'move_id.company_id', 'company_id', 'sale_line_ids',
                 'product_id.virtual_available')
    def _compute_qty_on_hand_check(self):
        pzs.compute_qty_on_hand_check(self)

    @api.onchange('product_id')
    def _onchange_product_id_duplicate_check(self):
        for line in self:
            if not line.product_id or line.move_id.move_type != 'out_invoice':
                continue
            company = line._pzs_company()
            if not (company.restrict_zero_invoice and company.invoice_restrict_duplicate):
                continue
            duplicates = line.move_id.invoice_line_ids.filtered(
                lambda l: l.product_id == line.product_id)
            if len(duplicates) > 1:
                line.product_id = False
                return {
                    'warning': {
                        'title': _("Duplicate Product"),
                        'message': _("This product is already present in the invoice. "
                                     "Duplicate lines are not allowed."),
                    }
                }

    @api.onchange('product_id', 'quantity')
    def _onchange_product_id_check_stock(self):
        # Auto-ajusta la cantidad sin perder el producto (lógica compartida).
        return pzs.check_stock_adjust(self)
