# -*- coding: utf-8 -*-
{
    'name': "method_linio",

    'summary': """
        Integración Linio con Method ERP""",

    'description': """
        Sincronización de:
            Producto
            Clientes
            Ordenes de Venta
            Actualiza el Stock de Method a Linio
    """,

    'author': "Method ERP",
    'website': "https://www.method.cl",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/cron.xml',        
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}