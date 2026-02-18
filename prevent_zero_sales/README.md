# Prevent Zero Sales

## Summary

Prevents confirming Sales Orders and Customer Invoices with insufficient stock or invalid quantities.

## Description

This module adds comprehensive stock validation for Sales Orders and Customer Invoices, preventing confirmation when products have insufficient stock, zero/negative quantities, or zero/negative prices. It provides granular control over which product types to restrict and supports both strict and policy-based validation modes.

## Features

* **Sales Order Stock Validation:** Prevents confirming sales orders when products have insufficient forecasted stock.
* **Customer Invoice Stock Validation:** Prevents confirming customer invoices when products have insufficient forecasted stock (only for invoices not linked to sales orders).
* **Real-time Stock Warnings:** Visual banner alerts when line items exceed available stock.
* **Interactive Line Validation:** Automatically removes or adjusts quantities for products with zero/negative stock when adding to orders/invoices.
* **Duplicate Line Prevention:** Optional restriction to prevent adding the same product multiple times in orders or invoices.
* **Granular Product Type Restrictions:** Configure independently for:
  - Storable Products
  - Consumable Products
  - Service Products
* **Flexible Validation Modes:**
  - Strict Mode: Applies restrictions to all products regardless of invoice policy
  - Policy-Based Mode: Only restricts products with "Ordered quantities" invoice policy
* **Price and Quantity Validation:** Blocks confirmation if any product has zero/negative price or quantity.
* **Forecasted Stock (Virtual Available):** Uses `virtual_available` for accurate stock calculations including reservations and incoming stock.

## Configuration

### Sales Settings

Go to **Sales > Configuration > Settings** and locate the **Stock Restrictions** section:

1. Enable **Prevent Sales with Zero/Negative Stock**
2. Enable **Strict Stock Validation** for all products, or leave unchecked to only restrict "Ordered quantities" policy
3. Select which product types to restrict:
   - Storable Products
   - Combos
   - Services
4. Optionally enable **Prevent Duplicate Lines**

### Invoicing Settings

Go to **Accounting > Configuration > Settings** and locate the **Stock Restrictions** section:

1. Enable **Prevent Invoices with Zero/Negative Stock**
2. Select which product types to restrict:
   - Storable Products
   - Combos
   - Services
3. Optionally enable **Prevent Duplicate Lines**

## How It Works

### Sales Orders

When adding products to a sales order:
- Products with zero/negative stock are automatically removed with a warning
- Quantities exceeding available stock are automatically adjusted to the maximum available
- A visual warning banner appears if any line exceeds available stock
- Confirmation is blocked if validation fails

### Customer Invoices

When adding products to a customer invoice:
- Same behavior as sales orders for products not linked to a sales order
- Products already linked to a sales order skip validation (stock was already validated)
- Credit notes (refunds) skip stock validation as they return inventory

## Requirements

* **Dependencies:** `base`, `account`, `sale`, `sale_management`, `sale_stock`
* **Recommended:** Install `pos_stock_policies` for Point of Sale stock validation

## Installation

Install as a standard Odoo module.

## Credits

* **Author:** consultoresodoocolombia
* **Website:** [https://consultoresodoocolombia.odoo.com/](https://consultoresodoocolombia.odoo.com/)
