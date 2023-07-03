# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    salary_account_id = fields.Many2one('account.account', _('Salary account'))