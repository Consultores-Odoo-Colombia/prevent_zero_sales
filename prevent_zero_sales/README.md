# Prevent Zero Sales

## Summary

Blocks confirmation of Sales Orders and Customer Invoices that contain lines with
zero/negative quantities or prices, duplicate products, or insufficient stock.

## Description

This module adds a configurable validation layer on Sales Orders and Customer
Invoices. It prevents confirmation when products have insufficient forecasted
stock, zero/negative quantities, or zero/negative prices, and can optionally
forbid duplicate product lines. Restrictions are configurable per company and
per product type, with strict and policy-based validation modes.

## Features

* **Sales Order Stock Validation:** blocks confirmation when a line exceeds the
  forecasted stock of the product.
* **Customer Invoice Stock Validation:** same check on customer invoices, only
  for lines not linked to a sales order (those were already validated at SO level).
* **Real-time Stock Warnings:** a banner appears on the form as soon as a line
  exceeds the available stock, and the line editor blocks adding new rows until
  the violation is fixed.
* **Interactive Line Validation:** products with zero/negative stock are removed
  on the fly; quantities above the available stock are capped automatically.
* **Duplicate Line Prevention (optional):** forbids the same product on several
  lines of the same order/invoice.
* **Granular Product Type Restrictions**, configured independently for Sales and
  Invoicing:
  - Storable products (`is_storable`)
  - Consumables / Combos
  - Services
* **Validation Modes:**
  - *Strict:* restrictions apply regardless of the product invoicing policy.
  - *Policy-based:* products invoiced on delivered quantities are not restricted.
* **Zero Price/Quantity Validation:** confirmation is blocked if any product line
  has a zero or negative price or quantity.
* **Forecasted Stock:** all checks use `virtual_available` (on hand + incoming −
  outgoing), with proper unit-of-measure conversion and rounding.

## Configuration

### Sales

**Sales → Configuration → Settings → Stock Restrictions**

1. Enable **Prevent Sales with Zero/Negative Stock** (master switch).
2. Choose **Strict Stock Validation**, or leave it unchecked for policy-based mode.
3. Tick the product types to restrict (Storable / Consumables / Services).
4. Optionally enable **Prevent Duplicate Lines**.

### Invoicing

**Accounting → Configuration → Settings → Stock Restrictions**

1. Enable **Prevent Invoices with Zero/Negative Stock** (master switch).
2. Tick the product types to restrict.
3. Optionally enable **Prevent Duplicate Lines**.

## How It Works

### Sales Orders

While editing a quotation:

* Adding a product with zero/negative stock removes the line with a warning.
* Quantities above the available stock are capped to the maximum available.
* A red banner shows up while any line exceeds the available stock.

On confirmation, the order is blocked if any line has zero/negative quantity or
price, exceeds the forecasted stock, or duplicates another line (when enabled).
Confirmed orders are no longer restricted (stock is already reserved).

### Customer Invoices

Same behaviour for invoice lines **not** linked to a sales order. Lines invoiced
from a sales order skip the stock check, and credit notes are never restricted
(they return inventory).

## Requirements

* **Dependencies:** `account`, `sale_management`, `sale_stock`
* **Odoo version:** 18.0 (Community / Enterprise)

## Installation

Install as a standard Odoo module.

## Credits

* **Author:** consultoresodoocolombia
* **Website:** [https://consultoresodoocolombia.odoo.com/](https://consultoresodoocolombia.odoo.com/)
