# -*- coding: utf-8 -*-

from odoo import models, fields, _

class HrOm(models.Model):
    _name = 'hr.om'
    _inherit = ['hr.om', 'mail.thread', 'mail.activity.mixin']

    mobile_phone = fields.Char(_('Work Mobile'), related='employee_id.mobile_phone', readonly=True)
    state = fields.Selection(
        string=_('State'), 
        selection=[
            ('draft','Brouillon'),
            ('valid','Validé'),
            ('paid','Payé'),
            ('running','En cours'),
            ('close','Terminé')
        ],
        related='mission_id.state',
        copy=False,
        tracking=True,
        store=True
    )
    payment_id = fields.Many2one('account.payment', readonly=True, ondelete='restrict')
    mobile_transaction_ids = fields.One2many('mobile_pay_cm.mobile.transaction', 'hr_om_id')

    def action_register_mobile_payment(self):
        return {
            'name': _('Register Mobile Payment'),
            'res_model': 'mobile.payment.register',
            'view_mode': 'form',
            'context': {
                'src_model': self._name,
                'active_ids': self.ids,
                'default_phone': self.mobile_phone or self.employee_id.work_phone or '',
                'default_amount': self.montant_frais,
                'default_communication': _('Mission fees - ') + self.name,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
