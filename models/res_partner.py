# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _


class ResPartner(models.Model):
    """Res Partner """
    _inherit = 'res.partner'
    _description = __doc__

    is_agent = fields.Boolean(string="Agent")
    is_re_insurance_company = fields.Boolean(string="ReInsurance Company")
    is_publish_on_web = fields.Boolean(string="Display on website insurance form",
                                                 default=True)

    insurance_information_ids = fields.One2many(comodel_name='insurance.information',
                                                inverse_name='agent_id', string="Insurance")
    total_agent_bill = fields.Monetary(string="Total",
                                       compute="_compute_total_agent_bill")
    total_insurance_count = fields.Integer(string="Insurances",
                                           compute='_compute_total_insurance_count')
    total_claim_count = fields.Integer(string="Claims",
                                       compute='_compute_total_claim_count')

    category_id = fields.Many2one('insurance.category', string="Category")

    def _compute_total_insurance_count(self):
        """Total insurance count"""
        for rec in self:
            rec.total_insurance_count = self.env['insurance.information'].search_count(
                [('policy_holder_id', '=', rec.id)])

    def action_view_insurances(self):
        """View insurance"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Insurances'),
            'res_model': 'insurance.information',
            'domain': [('policy_holder_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_policy_holder_id': self.id,
                'create': False,
            },
        }

    def _compute_total_claim_count(self):
        """Total claim count"""
        for rec in self:
            rec.total_claim_count = self.env['claim.information'].search_count(
                [('policy_holder_id', '=', rec.id)])

    def action_view_claims(self):
        """Claim view"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Claims'),
            'res_model': 'claim.information',
            'domain': [('policy_holder_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_policy_holder_id': self.id,
                'create': False,
            },
        }

    @api.depends('insurance_information_ids.agent_bill_id.amount_total')
    def _compute_total_agent_bill(self):
        """Total agent bill"""
        for rec in self:
            rec.total_agent_bill = sum(
                bill.agent_bill_id.amount_total for bill in rec.insurance_information_ids)

    def action_bill_view(self):
        """Agent commission bill"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Agent Commission Bills'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [
                ('insurance_information_id', 'in', self.insurance_information_ids.ids),
                ('partner_id', '=', self.id),
            ],
            'context': {
                'default_partner_id': self.id,
                'create': False,
            },
        }
