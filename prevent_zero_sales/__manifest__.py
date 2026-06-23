# -*- coding: utf-8 -*-
{
    'name': "Prevent Zero Sales",

    'summary': "Block sales orders and customer invoices with zero quantities, "
               "zero prices, duplicate lines or insufficient stock.",

    'description': """
Adds a configurable validation layer on Sales Orders and Customer Invoices:

- Blocks confirmation when a product line has a zero or negative quantity or price.
- Blocks confirmation when the forecasted stock is not enough to cover the line.
- Optionally prevents duplicate product lines.
- Real-time warning banner and interactive line validation while editing.
- Granular configuration per company and per product type (storable, consumable/combo, service).
    """,

    'author': "consultoresodoocolombia",
    'website': "https://consultoresodoocolombia.odoo.com/",
    'support': "jacal2211@gmail.com",

    'category': 'Sales',
    'version': '18.0.1.6.1',
    'license': 'OPL-1',
    'price': 20.00,
    'currency': 'USD',
    'images': ['static/description/main_screenshot.png'],

    'depends': ['account', 'sale_management', 'sale_stock'],

    'assets': {
        'web.assets_backend': [
            'prevent_zero_sales/static/src/js/stock_restricted_list_renderer.js',
            'prevent_zero_sales/static/src/xml/stock_restricted_list_renderer.xml',
            'prevent_zero_sales/static/src/js/stock_restricted_section_and_note_field.js',
        ],
    },

    'data': [
        'security/ir.model.access.csv',
        'wizards/pzs_zero_stock_wizard_views.xml',
        'views/res_config_settings_views.xml',
        'views/account_views.xml',
        'views/sale_views.xml',
    ],

    'installable': True,
    'application': False,
}
