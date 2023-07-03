
# -*- coding: utf-8 -*-
{
    'name': "Paiement Mobile",

    'summary': """
        Use local electronic payments providers like Orange Money (OM) or MTN Mobile Money (MoMo) to execute payments.
        Modules : 
        * Supplier Invoicing 
        * Mission fees of Human Resources 
        """,

    'description': """
    """,

    'author': "Parfait BENE",
    'website': "https://parfaitbene.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'hr_mission_cm'],

    # always loaded
    'data': [
        'data/ir_cron_data.xml',
        'security/mobile_pay_cm_groups.xml',
        'security/ir.model.access.csv',
        'views/mobile_pay_cm_views.xml',
        'views/account_journal_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_mission_views.xml',
        'views/hr_om_views.xml',
        'views/account_move_views.xml',
        'wizard/mobile_payment_register_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
