# Prevent Zero Sales

## Summary
Prevents confirming invoices (Customer/Vendor), credit notes, and POS orders with zero amount.

## Description
This module adds strict validation to prevent processing customer and vendor invoices (`account.move`), as well as credit notes and point of sale orders (`pos.order`) with a total amount of 0.

## Features
*   **Invoice and Credit Note Validation:** Prevents confirmation of invoices (Customer/Vendor) and credit notes if the total amount is 0.
*   **Stock Validation (Sales):** Prevents confirming Sale Orders if there is not enough stock on hand (qty_available).
*   **POS Validation:** Prevents creation of point of sale orders if the total amount is 0.

## Installation
Install as a standard Odoo module.

## Credits
*   **Author:** consultoresodoocolombia
*   **Website:** [https://consultoresodoocolombia.odoo.com/](https://consultoresodoocolombia.odoo.com/)
