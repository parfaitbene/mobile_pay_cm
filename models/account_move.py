# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_register_mobile_payment(self):
        return {
            'name': _('Register Mobile Payment'),
            'res_model': 'mobile.payment.register',
            'view_mode': 'form',
            'context': {
                'src_model': self._name,
                'active_ids': self.ids,
                'default_phone': self.partner_id.mobile or self.partner_id.phone or '',
                'default_amount': self.amount_residual,
                'default_communication': self.name,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
