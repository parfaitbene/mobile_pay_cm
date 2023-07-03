# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError

class HrMission(models.Model):
    _inherit = 'hr.mission'

    state = fields.Selection(
        string=_('State'), 
        default='draft', 
        selection=[
            ('draft','Brouillon'),
            ('valid','Validé'),
            ('paid','Payé'),
            ('running','En cours'),
            ('close','Terminé')
        ],
        copy=False,
        tracking=True
    )

    def set_to_paid(self):
        self.state='paid'
