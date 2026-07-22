# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import ValidationError
from odoo import fields, api, models, _


class ReInsuranceContract(models.TransientModel):
    """Re Insurance Contract"""
    _name = 're.insurance.contract'
    _description = __doc__

    # Insurance Details
    insurance_id = fields.Many2one('insurance.information', string="Insurance")
    insurance_policy_id = fields.Many2one('insurance.policy', string='Insurance Policy')
    policy_number = fields.Char(string="Policy Number")
    contract_date = fields.Date(default=fields.Date.today())
    issue_date = fields.Date()
    expiry_date = fields.Date()
    policy_amount = fields.Monetary(
        help="Total premium amount received from the policyholder for the insured risk.")
    sum_assured = fields.Monetary(string="Sum Insured",
                                  help="Total amount covered under the insurance policy.")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related="company_id.currency_id")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company,
                                 string="Company")

    # DEPRECATED
    policy_provider_id = fields.Many2one('res.company', string='Policy Ceding Company',
                                         domain=[('is_re_insurance_company', '=', False)])
    # Policy Provider (Ceding Company)
    policy_provider_cmp_id = fields.Many2one('res.partner', string='Ceding Company',
                                        domain=[('company_type', '=', 'company')])
    provider_phone = fields.Char(string="Phone")
    provider_email = fields.Char(string="Email")

    # Reinsurer Company Details
    re_insurance_type_id = fields.Many2one('re.insurance.type', string="ReInsurance Type")
    treaty_types = fields.Selection([
        ('quota_share', 'Quota Share'),
        ('surplus', 'Surplus'),
        ('excess_of_loss', 'Excess of Loss'),
        ('stop_loss', 'Stop Loss'),
        ('facultative_obligatory', 'Facultative Obligatory'),
        ('risk_attaching', 'Risk Attaching'),
        ('losses_occurring', 'Losses Occurring'),
        ('proportional', 'Proportional'),
        ('non_proportional', 'Non-Proportional'),
    ], string="Treaty Type")

    reinsurer_company_id = fields.Many2one('res.company') # DEPRECATED

    reinsurance_company_id = fields.Many2one('res.partner', string='ReInsurance Company',
                                             domain=[('is_company', '=', True), ('is_re_insurance_company', '=', True)])

    r_phone = fields.Char(string=" Phone")
    r_email = fields.Char(string=" Email")

    # Financial Details
    retention_amount = fields.Monetary(help="Max amount the ceding company retains")
    reinsured_amount = fields.Monetary()
    reinsurance_premium = fields.Monetary()
    reinsurer_percentage = fields.Float(string="Reinsurer Share (%)")

    # Coverage
    territory = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()
    risk_description = fields.Text()
    exclusions = fields.Text()
    terms_and_conditions = fields.Html(translate=True)

    # Manager Details
    responsible_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user, string="Manager",
        domain=lambda self: [('all_group_ids', 'in', [self.env.ref('base.group_user').id])])

    @api.model
    def default_get(self, fields_list):
        """Default record"""
        default_data = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            insurance = self.env['insurance.information'].browse(active_id)
            default_data.update({
                'insurance_id': insurance.id,
                'insurance_policy_id': insurance.insurance_policy_id.id,
                'policy_number': insurance.insurance_policy_id.policy_number,
                'issue_date': insurance.issue_date,
                'expiry_date': insurance.expiry_date,
                'policy_amount': insurance.policy_amount,
                'sum_assured': insurance.insurance_policy_id.sum_assured,
                'currency_id': insurance.currency_id.id,
                'company_id': insurance.company_id.id,
                'policy_provider_cmp_id': insurance.policy_provider_cmp_id.id,
                'provider_phone': insurance.policy_provider_cmp_id.phone,
                'provider_email': insurance.policy_provider_cmp_id.email,
            })
        return default_data

    @api.onchange('reinsurance_company_id')
    def _onchange_reinsurer_company(self):
        """Onchange reinsurance company details"""
        for rec in self:
            rec.r_phone = rec.reinsurance_company_id.phone
            rec.r_email = rec.reinsurance_company_id.email

    @api.constrains('start_date', 'end_date')
    def _check_coverage_dates(self):
        """Validate coverage dates."""
        today = fields.Date.today()
        for record in self:
            if record.start_date and record.start_date < today:
                raise ValidationError(_("Coverage start date cannot be in the past."))
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("Coverage end date must be after the start date."))

    def create_re_insurance(self):
        """Create re insurance"""
        insurance = self.insurance_id
        data = {
            'insurance_id': insurance.id,
            'insurance_policy_id': insurance.insurance_policy_id.id,
            'policy_number': insurance.insurance_policy_id.policy_number,
            'issue_date': insurance.issue_date,
            'expiry_date': insurance.expiry_date,
            'policy_amount': insurance.policy_amount,
            'sum_assured': insurance.insurance_policy_id.sum_assured,
            'currency_id': insurance.currency_id.id,
            'company_id': insurance.company_id.id,
            'policy_provider_cmp_id': insurance.policy_provider_cmp_id.id,
            'provider_phone': insurance.policy_provider_cmp_id.phone,
            'provider_email': insurance.policy_provider_cmp_id.email,
            're_insurance_type_id': self.re_insurance_type_id.id,
            'treaty_types': self.treaty_types,
            'reinsurance_company_id': self.reinsurance_company_id.id,
            'r_phone': self.r_phone,
            'r_email': self.r_email,
            'retention_amount': self.retention_amount,
            'reinsured_amount': self.reinsured_amount,
            'reinsurance_premium': self.reinsurance_premium,
            'reinsurer_percentage': self.reinsurer_percentage,
            'territory': self.territory,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'risk_description': self.risk_description,
            'exclusions': self.exclusions,
            'terms_and_conditions': self.terms_and_conditions,
            'contract_date': self.contract_date,
            'responsible_id': self.responsible_id.id,
        }
        re_insurance = self.env['re.insurance'].create(data)
        insurance.re_insurance_id = re_insurance.id
        mail_template = self.env.ref(
            'tk_insurance_management.reinsurance_details_submit_mail_template')
        if mail_template:
            mail_template.send_mail(re_insurance.id, force_send=True)
        return {
            'type': 'ir.actions.act_window',
            'name': _('ReInsurance'),
            'res_model': 're.insurance',
            'res_id': re_insurance.id,
            'view_mode': 'form',
            'target': 'current'
        }
