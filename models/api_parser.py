# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

API_TOKEN_ERROR_CODE = "token_not_valid"
API_MSG_ERROR_CODE = "MG000"
API_ERROR = _('An error occured, please contact your administrator if it persist')
API_TOKEN_EXPIRE_MSG = _("We tried to get a new token. You can try a new request.\n If the problem persists, please contact your administrator")
TRANSACTION_SUCCESS_MSG = _("Transaction executed successfully")

class ApiParser(models.AbstractModel):
    _name = "mobile_pay_cm.api.parser"
    _description = "API Parser"

    def get_response(self, response):
        if self.is_success(response):
            api_response = self.env['mobile_pay_cm.api.response'].create({
                'msg_code': response['msg_code'],
                'success': response['success'],
                'results': response['results']
            })

            return api_response

        return None

    def get_results(self, response):
        return response['results'][0]


    def get_error(self, response):
        if self.is_error(response):
            api_error = self.env['mobile_pay_cm.api.error'].create({
                'msg_code': response['msg_code'],
                'success':  response['success']
            })

            for error in response['errors']:
                self.env['mobile_pay_cm.api.base.error'].create({
                    'error_code': error['error_code'],
                    'error_msg': error['error_msg'],
                    'error_id': api_error.id
                })

            return api_error

        return None


    def get_token_error(self, response):
        if self.is_token_error(response):
            token_error = self.env['mobile_pay_cm.api.token.error'].create({
                'code': response['code'], 
                'detail': response['detail']
            })

            for msg in response['messages']:
                self.env['mobile_pay_cm.api..base.token.error'].create({
                    'token_class': msg['token_class'],
                    'token_type': msg['token_type'],
                    'message': msg['message'],
                    'error_id': token_error.id
                })

            return token_error

        return None

    def is_success(self, response):
        return not self.is_error(response) and not self.is_token_error(response)

    def is_error(self, response):
        return response.get('success', 0) != 1 or response.get('msg_code', '') == API_MSG_ERROR_CODE

    def is_token_error(self, response):
        return response.get('code', False) and response.get('code', '') == API_TOKEN_ERROR_CODE


class ApiResponse(models.TransientModel):
    _name = "mobile_pay_cm.api.response"
    _description = "API response"

    msg_code = fields.Char()
    success = fields.Integer()
    results = fields.Text()


class ApiTokenBaseError(models.TransientModel):
    _name = "mobile_pay_cm.api.base.token.error"
    _description = "API base token error"

    token_class = fields.Char()
    token_type = fields.Char()
    message = fields.Char()
    error_id = fields.Many2one("mobile_pay_cm.api.token.error")


class ApiTokenError(models.TransientModel):
    _name = "mobile_pay_cm.api.token.error"
    _description = "API token error"

    code = fields.Char()
    detail = fields.Text()
    messages = fields.One2many("mobile_pay_cm.api.base.token.error", "error_id")

    @api.model
    def get_text_message(self):
        return ''.join(_('Message: ') + error.message + ' \n' + _('Details: ') + error.detail + '\n' for error in self.messages)


class ApiError(models.TransientModel):
    _name = "mobile_pay_cm.api.error"
    _description = "API error"

    msg_code = fields.Char()
    success = fields.Integer()
    errors = fields.One2many('mobile_pay_cm.api.base.error', 'error_id')

    @api.model
    def get_text_message(self):
        return ''.join(error.error_msg + ' \n' for error in self.errors)


class ApiBaseError(models.TransientModel):
    _name = "mobile_pay_cm.api.base.error"
    _description = "API base error"

    error_code = fields.Char()
    error_msg = fields.Char()
    error_id = fields.Many2one('mobile_pay_cm.api.error')
