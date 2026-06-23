# -*- coding: utf-8 -*-
"""Diálogo Sí/No para las líneas de productos sin stock disponible.

Cuando se confirma un pedido de venta (o se contabiliza una factura de cliente)
que contiene productos restringidos con stock disponible 0, en vez de bloquear o
borrar en silencio se abre este asistente y se pregunta al usuario:

  * **Sí, eliminar y confirmar** → se eliminan esas líneas (así no se facturan
    productos que no hay en almacén) y el documento continúa su confirmación.
  * **No** → no se confirma; las líneas afectadas quedan resaltadas en rojo en la
    lista para que el usuario las revise.

El asistente es genérico: sirve para ``sale.order`` y ``account.move`` mediante
``res_model`` + ``res_ids_str`` (lista de ids separada por comas).
"""

from odoo import _, fields, models


class PzsZeroStockWizard(models.TransientModel):
    _name = 'pzs.zero.stock.wizard'
    _description = 'Confirmación de líneas sin stock disponible'

    res_model = fields.Char(required=True)
    res_ids_str = fields.Char(required=True)
    product_names = fields.Text(readonly=True)
    message = fields.Text(readonly=True)

    def _records(self):
        """Devuelve el recordset (sale.order / account.move) afectado."""
        self.ensure_one()
        ids = [int(x) for x in (self.res_ids_str or '').split(',') if x]
        return self.env[self.res_model].browse(ids)

    def action_confirm_remove(self):
        """Botón «Sí»: elimina las líneas sin stock y continúa la confirmación."""
        self.ensure_one()
        records = self._records().with_context(pzs_drop_zero_stock=True)
        if self.res_model == 'sale.order':
            return records.action_confirm()
        return records.action_post()

    # El botón «No» usa special="cancel": cierra el diálogo sin confirmar. Las
    # líneas sin stock quedan resaltadas por la decoración de la lista.
