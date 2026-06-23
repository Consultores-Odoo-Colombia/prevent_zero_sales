# -*- coding: utf-8 -*-
"""Lógica compartida de restricción de stock entre líneas de venta y de factura.

`sale.order.line` y `account.move.line` validan exactamente igual, pero exponen
sus datos con nombres de campo distintos (``product_uom_qty``/``quantity``,
``product_uom``/``product_uom_id``). En vez de duplicar la regla de negocio o
forzar una jerarquía de clases/AbstractModel (que en Odoo colisiona con campos
Many2many heredados y con el *layout* de la metaclase), se centraliza aquí en
**funciones de módulo** que reciben el recordset. Cada modelo concreto solo
implementa unos *accessors* (`_pzs_get_qty`, `_pzs_set_qty`, `_pzs_get_uom`,
`_pzs_company`, `_pzs_stock_limit`) y delega en estas funciones.

Comportamiento del auto-ajuste (sin perder nunca el producto de la línea):
  * sin stock disponible (límite <= 0) → cantidad = 0, se mantiene el producto;
  * cantidad <= 0                       → cantidad = mínimo vendible (1, acotado al límite);
  * cantidad > disponible               → cantidad = máximo disponible (capping);
  * en rango válido                     → sin cambios.
"""

from odoo import _
from odoo.tools import float_compare

from .res_company import UNLIMITED_QTY


def qty_in_product_uom(line):
    """Cantidad de la línea expresada en la UoM de referencia del producto."""
    uom = line._pzs_get_uom()
    if uom and uom != line.product_id.uom_id:
        return uom._compute_quantity(line._pzs_get_qty(), line.product_id.uom_id)
    return line._pzs_get_qty()


def limit_in_line_uom(line, limit):
    """Convierte un límite (en UoM del producto) a la UoM de la línea."""
    uom = line._pzs_get_uom()
    if uom and uom != line.product_id.uom_id:
        return line.product_id.uom_id._compute_quantity(limit, uom)
    return limit


def compute_qty_on_hand_check(lines):
    """Calcula la cota cliente ``qty_on_hand_check`` por línea."""
    for line in lines:
        limit = line._pzs_stock_limit()
        if limit is None:
            line.qty_on_hand_check = UNLIMITED_QTY if line.product_id else 0.0
            continue
        line.qty_on_hand_check = limit_in_line_uom(line, limit)


def check_stock_adjust(lines):
    """Auto-ajusta la cantidad sin borrar el producto. Devuelve el primer dict
    de ``warning`` para el onchange (o ``None``)."""
    for line in lines:
        warning = _adjust_one(line)
        if warning:
            return warning
    return None


def _adjust_one(line):
    limit = line._pzs_stock_limit()
    if limit is None:
        return None

    rounding = line.product_id.uom_id.rounding
    qty = line._pzs_get_qty()

    # Sin stock disponible: mantener el producto, dejar la cantidad en 0.
    if float_compare(limit, 0.0, precision_rounding=rounding) <= 0:
        if float_compare(qty, 0.0, precision_rounding=rounding) != 0:
            line._pzs_set_qty(0.0)
        return {
            'warning': {
                'title': _("Product Not Available"),
                'message': _("There is no available stock for this product. The "
                             "quantity has been set to 0; please review the line."),
            }
        }

    limit_line = limit_in_line_uom(line, limit)

    # Cantidad <= 0 → mínimo vendible (1, acotado al disponible).
    if float_compare(qty, 0.0, precision_rounding=rounding) <= 0:
        new_qty = min(1.0, limit_line)
        line._pzs_set_qty(new_qty)
        return {
            'warning': {
                'title': _("Invalid Quantity"),
                'message': _("Quantity must be greater than 0. It has been "
                             "adjusted to %s.", new_qty),
            }
        }

    # Cantidad > disponible → capar al máximo disponible.
    if float_compare(qty_in_product_uom(line), limit,
                     precision_rounding=rounding) > 0:
        line._pzs_set_qty(limit_line)
        return {
            'warning': {
                'title': _("Insufficient Stock"),
                'message': _("The requested quantity exceeds the available stock. "
                             "It has been adjusted to the maximum available (%s).",
                             limit_line),
            }
        }

    return None
