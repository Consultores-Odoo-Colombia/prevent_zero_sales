# -*- coding: utf-8 -*-

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase


@tagged('post_install', '-at_install')
class TestPreventZeroSales(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'restrict_zero_sale': True,
            'restrict_zero_invoice': True,
            'strict_stock_validation': True,
            'sale_restrict_storable': True,
            'sale_restrict_consumable': False,
            'sale_restrict_service': False,
            'sale_restrict_duplicate': False,
            'invoice_restrict_storable': True,
            'invoice_restrict_consumable': False,
            'invoice_restrict_service': False,
            'invoice_restrict_duplicate': False,
        })

        cls.partner = cls.env['res.partner'].create({'name': 'PZS Test Partner'})
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1)

        cls.storable = cls.env['product.product'].create({
            'name': 'PZS Storable',
            'type': 'consu',
            'is_storable': True,
            'list_price': 100.0,
            'invoice_policy': 'order',
        })
        cls.service = cls.env['product.product'].create({
            'name': 'PZS Service',
            'type': 'service',
            'list_price': 50.0,
            'invoice_policy': 'order',
        })

    def _set_stock(self, product, qty):
        self.env['stock.quant']._update_available_quantity(
            product, self.warehouse.lot_stock_id, qty)

    def _make_order(self, lines):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create(vals) for vals in lines],
        })

    def _make_invoice(self, lines):
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [Command.create(vals) for vals in lines],
        })

    # ------------------------------------------------------------------
    # Sales orders
    # ------------------------------------------------------------------

    def test_sale_zero_stock_opens_wizard(self):
        # Producto sin stock CON cantidad: al confirmar no se confirma, se abre el
        # diálogo Sí/No para decidir si se eliminan esas líneas.
        order = self._make_order([{
            'product_id': self.storable.id,
            'product_uom_qty': 5,
            'price_unit': 100.0,
        }])
        action = order.action_confirm()
        self.assertEqual(order.state, 'draft',
                         "Con producto sin stock no debe confirmarse: abre el diálogo")
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('res_model'), 'pzs.zero.stock.wizard')

    def test_sale_confirmed_with_stock(self):
        self._set_stock(self.storable, 10)
        order = self._make_order([{
            'product_id': self.storable.id,
            'product_uom_qty': 5,
            'price_unit': 100.0,
        }])
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_sale_blocked_zero_price(self):
        self._set_stock(self.storable, 10)
        order = self._make_order([{
            'product_id': self.storable.id,
            'product_uom_qty': 1,
            'price_unit': 0.0,
        }])
        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_sale_service_not_restricted_by_default(self):
        order = self._make_order([{
            'product_id': self.service.id,
            'product_uom_qty': 3,
            'price_unit': 50.0,
        }])
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_sale_duplicate_lines_blocked(self):
        self.company.sale_restrict_duplicate = True
        self._set_stock(self.storable, 10)
        order = self._make_order([
            {'product_id': self.storable.id, 'product_uom_qty': 1, 'price_unit': 100.0},
            {'product_id': self.storable.id, 'product_uom_qty': 2, 'price_unit': 100.0},
        ])
        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_sale_disabled_master_switch(self):
        self.company.restrict_zero_sale = False
        order = self._make_order([{
            'product_id': self.storable.id,
            'product_uom_qty': 5,
            'price_unit': 100.0,
        }])
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_sale_policy_based_mode_skips_delivery_products(self):
        self.company.strict_stock_validation = False
        self.storable.invoice_policy = 'delivery'
        order = self._make_order([{
            'product_id': self.storable.id,
            'product_uom_qty': 5,
            'price_unit': 100.0,
        }])
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_sale_banner_warns_on_insufficient_stock(self):
        order = self._make_order([{
            'product_id': self.storable.id,
            'product_uom_qty': 5,
            'price_unit': 100.0,
        }])
        self.assertTrue(order.stock_warning_banner)

    def test_sale_confirm_yes_drops_zero_stock_lines(self):
        # Una línea válida (con stock) y otra sin stock: al confirmar se abre el
        # diálogo; al responder «Sí» en el asistente la línea sin stock se elimina
        # y la orden se confirma solo con la primera.
        self._set_stock(self.storable, 10)
        no_stock = self.env['product.product'].create({
            'name': 'PZS No Stock',
            'type': 'consu',
            'is_storable': True,
            'list_price': 20.0,
            'invoice_policy': 'order',
        })
        order = self._make_order([
            {'product_id': self.storable.id, 'product_uom_qty': 2, 'price_unit': 100.0},
            {'product_id': no_stock.id, 'product_uom_qty': 0, 'price_unit': 20.0},
        ])
        action = order.action_confirm()
        self.assertEqual(order.state, 'draft')
        self.assertEqual(action.get('res_model'), 'pzs.zero.stock.wizard')

        # Responder «Sí, eliminar y confirmar» en el asistente.
        wizard = self.env['pzs.zero.stock.wizard'].browse(action['res_id'])
        wizard.action_confirm_remove()

        self.assertEqual(order.state, 'sale')
        self.assertEqual(len(order.order_line), 1,
                         "La línea sin stock debe eliminarse al confirmar con «Sí»")
        self.assertEqual(order.order_line.product_id, self.storable)

    # ------------------------------------------------------------------
    # Sales orders — onchange auto-adjust (the product is never removed)
    # ------------------------------------------------------------------

    def test_sale_onchange_zero_qty_becomes_one(self):
        self._set_stock(self.storable, 10)
        with Form(self.env['sale.order']) as form:
            form.partner_id = self.partner
            with form.order_line.new() as line:
                line.product_id = self.storable
                line.product_uom_qty = 0
                self.assertEqual(line.product_id, self.storable,
                                 "El producto no debe perderse de la línea")
                self.assertEqual(line.product_uom_qty, 1,
                                 "La cantidad 0 debe ajustarse a 1")

    def test_sale_onchange_negative_qty_becomes_one(self):
        self._set_stock(self.storable, 10)
        with Form(self.env['sale.order']) as form:
            form.partner_id = self.partner
            with form.order_line.new() as line:
                line.product_id = self.storable
                line.product_uom_qty = -1
                self.assertEqual(line.product_id, self.storable)
                self.assertEqual(line.product_uom_qty, 1,
                                 "La cantidad negativa debe ajustarse a 1")

    def test_sale_onchange_excess_capped_to_available(self):
        self._set_stock(self.storable, 3)
        with Form(self.env['sale.order']) as form:
            form.partner_id = self.partner
            with form.order_line.new() as line:
                line.product_id = self.storable
                line.product_uom_qty = 10
                self.assertEqual(line.product_id, self.storable)
                self.assertEqual(line.product_uom_qty, 3,
                                 "El exceso debe capearse al máximo disponible")

    def test_sale_onchange_no_stock_keeps_product_qty_zero(self):
        # storable sin stock: virtual_available = 0
        with Form(self.env['sale.order']) as form:
            form.partner_id = self.partner
            with form.order_line.new() as line:
                line.product_id = self.storable
                line.product_uom_qty = 5
                self.assertEqual(line.product_id, self.storable,
                                 "Sin stock, el producto debe permanecer en la línea")
                self.assertEqual(line.product_uom_qty, 0,
                                 "Sin stock, la cantidad debe quedar en 0")

    # ------------------------------------------------------------------
    # Customer invoices
    # ------------------------------------------------------------------

    def test_invoice_blocked_without_stock(self):
        invoice = self._make_invoice([{
            'product_id': self.storable.id,
            'quantity': 5,
            'price_unit': 100.0,
        }])
        with self.assertRaises(ValidationError):
            invoice.action_post()

    def test_invoice_posted_with_stock(self):
        self._set_stock(self.storable, 10)
        invoice = self._make_invoice([{
            'product_id': self.storable.id,
            'quantity': 5,
            'price_unit': 100.0,
        }])
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_invoice_blocked_zero_price(self):
        self._set_stock(self.storable, 10)
        invoice = self._make_invoice([{
            'product_id': self.storable.id,
            'quantity': 1,
            'price_unit': 0.0,
        }])
        with self.assertRaises(ValidationError):
            invoice.action_post()

    def test_credit_note_not_restricted(self):
        refund = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.storable.id,
                'quantity': 5,
                'price_unit': 100.0,
            })],
        })
        refund.action_post()
        self.assertEqual(refund.state, 'posted')

    def test_invoice_duplicate_lines_blocked(self):
        self.company.invoice_restrict_duplicate = True
        self._set_stock(self.storable, 10)
        invoice = self._make_invoice([
            {'product_id': self.storable.id, 'quantity': 1, 'price_unit': 100.0},
            {'product_id': self.storable.id, 'quantity': 2, 'price_unit': 100.0},
        ])
        with self.assertRaises(ValidationError):
            invoice.action_post()

    def test_invoice_from_sale_order_skips_stock_check(self):
        self._set_stock(self.storable, 5)
        order = self._make_order([{
            'product_id': self.storable.id,
            'product_uom_qty': 5,
            'price_unit': 100.0,
        }])
        order.action_confirm()
        # Consume the stock so the invoice would fail a fresh stock check.
        self._set_stock(self.storable, -5)
        invoice = order._create_invoices()
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    # ------------------------------------------------------------------
    # Customer invoices — onchange auto-adjust (the product is never removed)
    # ------------------------------------------------------------------

    def _invoice_form_line(self, qty):
        """Crea una factura de cliente vía Form con una línea de producto
        storable a la cantidad dada y devuelve (product_id, quantity) tras
        el onchange."""
        move_form = Form(self.env['account.move'].with_context(
            default_move_type='out_invoice'))
        move_form.partner_id = self.partner
        with move_form.invoice_line_ids.new() as line:
            line.product_id = self.storable
            line.quantity = qty
            return line.product_id, line.quantity

    def test_invoice_onchange_zero_qty_becomes_one(self):
        self._set_stock(self.storable, 10)
        product, quantity = self._invoice_form_line(0)
        self.assertEqual(product, self.storable)
        self.assertEqual(quantity, 1, "La cantidad 0 debe ajustarse a 1")

    def test_invoice_onchange_excess_capped_to_available(self):
        self._set_stock(self.storable, 3)
        product, quantity = self._invoice_form_line(10)
        self.assertEqual(product, self.storable)
        self.assertEqual(quantity, 3, "El exceso debe capearse al máximo disponible")

    def test_invoice_onchange_no_stock_keeps_product_qty_zero(self):
        product, quantity = self._invoice_form_line(5)
        self.assertEqual(product, self.storable,
                         "Sin stock, el producto debe permanecer en la línea")
        self.assertEqual(quantity, 0, "Sin stock, la cantidad debe quedar en 0")

    def test_invoice_post_drops_zero_qty_zero_stock_lines(self):
        # Réplica del borrado de la cotización: al contabilizar, la línea en
        # cantidad 0 sin stock se elimina y la factura se contabiliza con el resto.
        self._set_stock(self.storable, 10)
        no_stock = self.env['product.product'].create({
            'name': 'PZS Inv No Stock',
            'type': 'consu',
            'is_storable': True,
            'list_price': 20.0,
            'invoice_policy': 'order',
        })
        invoice = self._make_invoice([
            {'product_id': self.storable.id, 'quantity': 2, 'price_unit': 100.0},
            {'product_id': no_stock.id, 'quantity': 0, 'price_unit': 20.0},
        ])
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')
        product_lines = invoice.invoice_line_ids.filtered(
            lambda l: l.display_type == 'product')
        self.assertEqual(len(product_lines), 1,
                         "La línea en cantidad 0 sin stock debe eliminarse al contabilizar")
        self.assertEqual(product_lines.product_id, self.storable)

    def test_invoice_post_blocked_when_all_product_lines_zero_stock(self):
        # Trazabilidad fiscal: si todas las líneas de producto se borran por falta
        # de stock, NO se contabiliza una factura vacía (numeración sin contenido).
        no_stock = self.env['product.product'].create({
            'name': 'PZS Inv No Stock 2',
            'type': 'consu',
            'is_storable': True,
            'list_price': 20.0,
            'invoice_policy': 'order',
        })
        invoice = self._make_invoice([
            {'product_id': no_stock.id, 'quantity': 0, 'price_unit': 20.0},
        ])
        with self.assertRaises(ValidationError):
            invoice.action_post()
