# -*- coding: utf-8 -*-

import json
import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from .api_parser import API_ERROR, API_TOKEN_EXPIRE_MSG, TRANSACTION_SUCCESS_MSG
from ..exceptions import ApiException

class MobilePayCmCconfig(models.Model):
    _name = 'mobile_pay_cm.config'
    _description = 'Mobile Payment Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([("draft", _("Disabled")), ("done", _("Enabled"))], default="draft", tracking=True, copy=False)
    name = fields.Char(default=_('Unknow'))
    api_login_url = fields.Char(required=True,tracking=True)
    api_pay_out_url = fields.Char(required=True,tracking=True)
    api_check_status_url = fields.Char(required=True,tracking=True)
    login = fields.Char(required=True,tracking=True)
    password = fields.Char(required=True,tracking=True)
    token = fields.Char(readonly=True,tracking=True)
    active = fields.Boolean(_('Visible ?'), default=True, copy=False, help=_("Indicate if this configuration is archive or not."))
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, groups='base.group_multi_company')

    def action_enable(self):
        active_config = self.search([('state', '=', 'done'), ('company_id', '=', self.env.company.id)])

        if active_config.exists():
            raise UserError(_("We found an already active configuration."))
            
        self.state = 'done'

    def action_disable(self):
        self.state = 'draft'

    def get_api_login_url(self):
        return self.api_login_url.strip().endswith('/') and self.api_login_url.strip() or self.self.api_login_url.strip() + '/'

    def get_api_pay_out_url(self):
        return self.api_pay_out_url.strip().endswith('/') and self.api_pay_out_url.strip() or self.self.api_pay_out_url.strip() + '/'
    
    def get_api_check_status_url(self):
        return self.api_check_status_url.strip().endswith('/') and self.api_check_status_url.strip() or self.self.api_check_status_url.strip() + '/'

    @api.model
    def get_active_config(self):
        config = self.search([('state', '=', 'done'), ('company_id', '=', self.env.company.id)], limit=1)

        if not config:
            raise UserError(_('We have not found any active configuration for mobile payment.\n Please create one and active it.'))

        return config

    def login_user(self):
        config = self.get_active_config()
        data = { 'email': config.login, 'password': config.password }
        parser = self.env['mobile_pay_cm.api.parser']

        try:
            response = requests.post(
                    url=config.get_api_login_url(), 
                    data=data
                ).json()[0]

            if parser.is_success(response): 
                config.token = response.get('results')[0].get('token')
                return config.token

            elif parser.is_error(response):
                raise ApiException(parser.get_error(response).get_text_message())
        except ApiException as e:
            raise UserError(e)
        except:
            raise UserError(API_ERROR)

    def get_token(self):
        token = self.get_active_config().token

        if token:
            return token
        else:
            return self.login_user()


class MobilePayCmTransaction(models.Model):
    _name = 'mobile_pay_cm.mobile.transaction'
    _description = 'Mobile Payment Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    ## odoo logic fields ##
    name = fields.Char(string=_('Name'), related='reference', store=True, readonly=True)
    state = fields.Selection(string=_('State'), related="statut", store=True, tracking=True)
    hr_om_id = fields.Many2one('hr.om', ondelete='restrict', readonly=True)
    payment_id = fields.Many2one('account.payment', readonly=True, ondelete='restrict')
    invoice_id = fields.Many2one('account.move', readonly=True, ondelete='restrict')

    ## api request fields ##
    montant = fields.Float(readonly=True, required=True)
    client_nom = fields.Char(readonly=True, required=True)
    client_prenom = fields.Char(readonly=True)
    operateur_envoie = fields.Char(string=_('Sending Operator'), readonly=True, required=True)
    operateur_recu = fields.Char(string=_('Receiving Operator'), readonly=True, required=True)
    numero_beneficiaire = fields.Char(readonly=True, required=True)

    ## api response fields ##
    pk = fields.Integer(readonly=True)
    reference = fields.Char(string=_('Reference'), readonly=True)
    statut = fields.Selection(string=_('Status'), tracking=True, copy=False, readonly=True, 
                              selection=[("WAIT", _("Pending")), 
                                        ("PROGRESS", _("In progress")), 
                                        ("FINISH", _("Done"))], 
                              default="WAIT")
    code = fields.Integer(readonly=True)
    type_operation = fields.Char(readonly=True)
    charge = fields.Float(readonly=True)
    price_transaction = fields.Float(readonly=True)
    charge_plateforme = fields.Float(readonly=True)
    compte_virtuel_id = fields.Integer(readonly=True)
    id_produit_psi = fields.Integer(readonly=True)
    message_id = fields.Char(readonly=True)
    payment_url = fields.Char(readonly=True)
    pay_token = fields.Char(readonly=True)
    notif_token = fields.Char(readonly=True)

    def execute(self, data):
        config = self.env['mobile_pay_cm.config'].get_active_config()
        parser = self.env['mobile_pay_cm.api.parser']
        headers = {
          'Content-Type': 'application/json',
          'Authorization': 'Token '+ config.get_token(),
        }

        for record in self:
            try:
                response = requests.post(
                    url=config.get_api_pay_out_url(), 
                    headers=headers,
                    data=json.dumps(data)
                ).json()[0]

                if parser.is_success(response):
                    results = parser.get_results(response)
                    record.pk = results.get('pk')
                    record.reference = results.get('reference')
                    record.statut = results.get('statut')
                    record.pk = results.get('pk')
                    record.code = results.get('code')
                    record.charge = results.get('charge')
                    record.operateur_envoie = results.get('operateur_envoie')
                    record.operateur_recu = results.get('operateur_recu')
                    record.price_transaction = results.get('price_transaction')
                    record.charge_plateforme = results.get('charge_plateforme')
                    record.compte_virtuel_id = results.get('compteVirtuel_id')
                    record.id_produit_psi = results.get('id_produitPSI')
                    record.message_id = results.get('messageId')
                    record.payment_url = results.get('payment_url')
                    record.pay_token = results.get('pay_token')
                    record.notif_token = results.get('notif_token')
                    record.create_log(TRANSACTION_SUCCESS_MSG)

                elif parser.is_error(response):
                    raise ApiException(parser.get_error(response).get_text_message())

                elif parser.is_token_error(response):
                    self.env['mobile_pay_cm.config'].get_token() #In case of token expiration, trying to get a new one
                    message = parser.get_token_error(response).get_text_message() + '\n' + API_TOKEN_EXPIRE_MSG
                    raise ApiException(message)
            except ApiException as e:
                record.create_log(e)
                raise UserError(e)
            except:
                record.create_log(API_ERROR)
                raise UserError(API_ERROR)

    def update_status(self):
        """ 
        Checks and updates the status of a previously initiated mobile transaction, 
        then posts the payment if everything was successful. Optionally, marks the work order as paid.
        """

        config = self.env['mobile_pay_cm.config'].get_active_config()
        parser = self.env['mobile_pay_cm.api.parser']
        headers = {
          'Content-Type': 'application/json',
          'Authorization': 'Token '+ config.get_token(),
        }
        
        for record in self:
            try:
                response = requests.post(
                    url=config.get_api_check_status_url(), 
                    headers=headers,
                    data=json.dumps({'reference': record.reference})
                ).json()[0]

                if parser.is_success(response):
                    results = parser.get_results(response)
                    record.statut = results.get('statut')

                    if record.statut == 'FINISH':
                        record.payment_id.action_post()
                        if record.hr_om_id:
                            record._update_hr_om_state()
                        record.create_log(TRANSACTION_SUCCESS_MSG)
                    else:
                        pass

                elif parser.is_error(response):
                    record.create_log(parser.get_error(response).get_text_message())

                elif parser.is_token_error(response):
                    self.env['mobile_pay_cm.config'].get_token() #In case of token expiration, trying to get a new one
                    message = parser.get_token_error(response).get_text_message() + '\n' + API_TOKEN_EXPIRE_MSG
                    record.create_log(message)
            except:
                record.create_log(API_ERROR)

    
    def _update_hr_om_state(self):
        """
        Checks the status of the payments then updates that of the mission order in case of success.
        """

        for record in self:
            total_paid = sum(transaction.montant for transaction in record.hr_om_id.mobile_transaction_ids.filtered(lambda t: t.state == 'FINISH'))
            if total_paid == record.hr_om_id.montant_frais:
                 record.hr_om_id.state = 'paid'


    def create_log(self, message):
        for record in self:
            return self.env['mobile_pay_cm.mobile.transaction.log'].create({
                'reference': record.reference,
                'state': record.state,
                'message': message
            })


    def _cron_update_transactions_status(self):
        transactions = self.search([('state', 'in', ('WAIT', 'PROGRESS'))])
        transactions.update_status()


class MobilePayCmTransactionLog(models.Model):
    _name = 'mobile_pay_cm.mobile.transaction.log'
    _description = 'Mobile Payment Transaction Log'
    _order = 'id desc'

    reference = fields.Char()
    state = fields.Char()
    message = fields.Text()
