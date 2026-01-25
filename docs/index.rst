Prevent Zero Sales (Sales & Invoicing)
======================================

.. toctree::
   :maxdepth: 2
   :caption: Content:

Summary
-------
Prevents checking out orders or confirming invoices with invalid quantities or insufficient stock.

Description
-----------
This module adds strict validations to Sales Orders and Customer Invoices. It ensures that businesses do not sell items that are out of stock (based on Forecasted Quantity) or process empty lines.

Features
--------
* **Forecasted Stock Check:** Validation is strictly based on `virtual_available` (Forecasted Stock), respecting reservations.
* **Smart Handling:**
    * **Quantity < 0:** Line is automatically deleted.
    * **Stock <= 0:** Line is automatically deleted.
    * **Insufficient Stock:** Quantity is automatically limited to the available forecasted amount.
    * **Quantity = 0:** Allowed initially (standard Odoo behavior) but prevents confirmation.
* **Multi-Policy Support:** Works for both 'Ordered Quantities' and 'Delivered Quantities' invoicing policies.
* **Strict Server-Side Validation:** Prevents bypassing UI checks on Confirmation/Post.
* **Duplicate Line Prevention:** Configurable option to prevent adding the same product multiple times in an order or invoice.

Installation
------------
Requires ``sale``, ``sale_management``, ``account``, ``sale_stock``.

Credits
-------
* **Author:** consultoresodoocolombia
* **Website:** https://consultoresodoocolombia.odoo.com/
