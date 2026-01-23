# -*- coding: utf-8 -*-
{
    'name': "Prevent Zero Sales",

    'summary': "Prevents confirming invoices and POS orders with zero amount.",

    'description': """
        This module adds strict validation to prevent processing
        customer invoices (account.move) and point of sale orders (pos.order)
        with a total amount of 0.
    """,

    'author': "consultoresodoocolombia",
    'website': "https://consultoresodoocolombia.odoo.com/",

    'category': 'Accounting',
    'version': '18.0.1.0.0',
    'license': 'OPL-1',

    # Dependencias necesarias para heredar de account y sale
    'depends': ['base', 'account', 'sale', 'sale_management', 'sale_stock'],

    'assets': {
        'web.assets_backend': [
             'prevent_zero_sales/static/src/js/stock_restricted_list_renderer.js',
             'prevent_zero_sales/static/src/xml/stock_restricted_list_renderer.xml',
             'prevent_zero_sales/static/src/js/stock_restricted_section_and_note_field.js',
        ],
    },

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/account_views.xml',
        'views/sale_views.xml',
    ],

    'installable': True,
    'application': False,
}

