# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_mobile_pay_journal = fields.Boolean(default=False, help=_("Allow to use this journal as payment method for mobile electronic payments"))