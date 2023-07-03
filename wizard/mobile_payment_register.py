# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

MOBILE_PAY_OPERATORS = [('ORANGE', 'Orange'), ('MTN', 'MTN')]

class MobilePaymentRegister(models.TransientModel):
    _name = 'mobile.payment.register'
    _description = 'Mobile Payment Register'

    amount = fields.Monetary(currency_field='currency_id', required=True)
    payment_date = fields.Date(string="Payment Date", required=True, default=fields.Date.context_today)
    communication = fields.Char(string="Memo")
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, 
                                  compute='_compute_currency_id',
                                  help="The payment's currency."
                                  )
    journal_id = fields.Many2one('account.journal', 
                                 required=True, 
                                 string=_('Payment Method'),
                                 domain="[('company_id', '=', company_id), ('is_mobile_pay_journal', '=', True)]", 
                                 help=_("The mobile payment's method.") 
                                 )
    company_id = fields.Many2one('res.company', store=True, copy=False, 
                                 default=lambda self: self.env.company, 
                                 groups='base.group_multi_company'
                                 )
    phone = fields.Char('Phone', 
                                 required=True,
                                 help=_("This phone number will receive money. \n Format: 6xxxxxxxx or 2376xxxxxxxx")
                                 )
    operateur_envoie = fields.Selection(string=_('Sending Operator'), required=True, selection=MOBILE_PAY_OPERATORS, default='ORANGE')
    operateur_recu = fields.Selection(string=_('Receiving Operator'), related="operateur_envoie", store=True, invisible=True)
    type_operation = fields.Char(invisible=True, readonly=True, compute="_get_type_operation")
    

    def _get_type_operation(self):
        if self.operateur_envoie == 'ORANGE':
            self.type_operation = 'ORANGE_MONEY_CM'
        elif self.operateur_envoie == 'MTN':
            self.type_operation = 'MTN_MONEY_CM'
        else:
            self.type_operation = 'OTHER'

    @api.depends('journal_id', 'company_id')
    def _compute_currency_id(self):
        for wizard in self:
            wizard.currency_id = wizard.journal_id.currency_id or wizard.company_id.currency_id

    def action_hr_om_create_payments(self):
        hr_oms = self.env['hr.om'].browse(self.env.context.get('active_ids'))
        
        for record in self:
            for om in hr_oms:
                if record.journal_id.is_mobile_pay_journal:
                    if not om.employee_id.salary_account_id:
                        raise UserError(_('No salary account found for the employee %s'%(om.employee_id.name)))

                    mobile_transaction_data = {
                            'montant': record.amount,
                            'client_nom': om.employee_id.name,
                            'client_prenom': om.employee_id.name,
                            'operateur_envoie': record.operateur_envoie,
                            'operateur_recu': record.operateur_recu,
                            'numero_beneficiaire': record.phone,
                            'type_operation': record.type_operation,
                            'hr_om_id': om.id
                        }
                    mobile_transaction = self.env['mobile_pay_cm.mobile.transaction'].create(mobile_transaction_data)
                    mobile_transaction.execute(mobile_transaction_data)

                    payment_data = {
                            'payment_type': 'outbound',
                            'destination_account_id': om.employee_id.salary_account_id.id,
                            'journal_id': record.journal_id.id,
                            'amount': record.amount,
                            'currency_id': record.currency_id.id,
                            'ref': record.communication
                        }

                    payment = self.env['account.payment'].create(payment_data)
                    mobile_transaction.payment_id = payment


    def action_vendor_bill_create_payments(self):
        invoices = self.env['account.move'].browse(self.env.context.get('active_ids'))
        
        for record in self:
            for invoice in invoices:
                if invoice.is_purchase_document(include_receipts=True) and record.journal_id.is_mobile_pay_journal:
                    mobile_transaction_data = {
                            'montant': record.amount,
                            'client_nom': invoice.partner_id.display_name,
                            'client_prenom': invoice.partner_id.display_name,
                            'operateur_envoie': record.operateur_envoie,
                            'operateur_recu': record.operateur_recu,
                            'numero_beneficiaire': record.phone,
                            'type_operation': record.type_operation,
                            'invoice_id': invoice.id
                        }
                    mobile_transaction = self.env['mobile_pay_cm.mobile.transaction'].create(mobile_transaction_data)
                    mobile_transaction.execute(mobile_transaction_data)

                    payment_data = {
                            'payment_type': 'outbound',
                            'partner_type': 'supplier',
                            'partner_id': invoice.partner_id.id,
                            'journal_id': record.journal_id.id,
                            'amount': record.amount,
                            'currency_id': record.currency_id.id,
                            'ref': record.communication
                        }

                    payment = self.env['account.payment'].create(payment_data)
                    mobile_transaction.payment_id = payment
                else:
                    raise UserError(_('Unable to continue operation for this document type.'))