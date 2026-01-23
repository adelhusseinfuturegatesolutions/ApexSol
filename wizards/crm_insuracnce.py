# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import ValidationError
from odoo import fields, api, models, _


class CrmInsurance(models.TransientModel):
    """Crm Insurance"""
    _name = 'crm.insurance'
    _description = __doc__

    crm_lead_id = fields.Many2one('crm.lead', string="Lead")
    issue_date = fields.Date(string="Issue Date")
    policy_holder_id = fields.Many2one('res.partner', string="Policy Holder",
                                       domain="[('is_agent', '=', False)]")
    email = fields.Char(string="Email")
    phone = fields.Char(string=" Phone")
    policy_holder_dob = fields.Date()
    policy_holder_age = fields.Char(compute="_compute_policy_holder_age_count", translate=True)
    policy_holder_gender = fields.Selection([
        ('male', "Male"),
        ('female', "Female"),
        ('others', "Others")], string=" Gender")

    insurance_category_id = fields.Many2one('insurance.category', string="Policy Category")
    category = fields.Selection(related="insurance_category_id.category")
    insurance_sub_category_id = fields.Many2one(
        'insurance.sub.category', string="Sub Category",
        domain="[('insurance_category_id', '=', insurance_category_id)]")
    insurance_policy_id = fields.Many2one(
        'insurance.policy', string='Insurance Policy',
        domain="[('insurance_sub_category_id', '=', insurance_sub_category_id)]")
    insurance_buying_for_id = fields.Many2one(
        'insurance.buying.for', string="Buying For",
        domain="[('insurance_category_id', '=', insurance_category_id)]")
    policy_certificate_no = fields.Char(string="Policy/Certificate No", translate=True)
    previous_policy_no = fields.Char(string="Previous Policy No", translate=True)
    policy_price_list_id = fields.Many2one(
        'policy.price.list', string="Policy Time Period",
        domain="[('insurance_policy_id', '=', insurance_policy_id)]")
    policy_durations = fields.Integer(related='policy_price_list_id.duration',
                                      string="Duration (Months)")
    policy_amount = fields.Monetary(string="Policy Amount")
    claim_amount = fields.Monetary(string="Claim Amount")

    policy_provider_cmp_id = fields.Many2one('res.partner', string='Policy Provider',
                                             domain=[('is_company', '=', True),
                                                     ('is_re_insurance_company', '=', False)])
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company,
                                 string="Company")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related="company_id.currency_id")
    responsible_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user, string="Manager",
        domain=lambda self: [('all_group_ids', 'in', [self.env.ref('base.group_user').id])])
    monthly_installment = fields.Monetary(string="Monthly Installment")

    @api.model
    def default_get(self, fields_list):
        """Default record"""
        default_data = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            leads = self.env['crm.lead'].browse(active_id)
            default_data.update({
                'crm_lead_id': leads.id,
                'policy_holder_id': leads.partner_id.id,
                'email': leads.email_from,
                'phone': leads.phone,
                'policy_holder_dob': leads.policy_holder_dob,
                'policy_holder_gender': leads.policy_holder_gender,
                'insurance_category_id': leads.insurance_category_id.id,
                'category': leads.category,
                'insurance_sub_category_id': leads.insurance_sub_category_id.id,
                'insurance_policy_id': leads.insurance_policy_id.id,
                'insurance_buying_for_id': leads.insurance_buying_for_id.id,
                'responsible_id': leads.user_id,
            })
        return default_data

    @api.constrains('policy_holder_gender')
    def _check_policy_holder_gender(self):
        """Check policy holder gender"""
        for record in self:
            if not record.policy_holder_gender:
                raise ValidationError(_("Please select a gender: Male, Female or Others"))

    @api.constrains('issue_date')
    def _check_issue_date(self):
        """Check that the issue date is not before today"""
        today = fields.Date.today()
        for record in self:
            if record.issue_date and record.issue_date < today:
                raise ValidationError(_("The issue date cannot be earlier than today."))

    @api.depends('policy_holder_dob')
    def _compute_policy_holder_age_count(self):
        """Policyholder age count"""
        today = fields.Date.today()
        for rec in self:
            if rec.policy_holder_dob:
                policy_holder_dob = fields.Date.from_string(rec.policy_holder_dob)
                if policy_holder_dob > today:
                    raise ValidationError(_("DOB should be earlier than today's date."))
                policy_holder_age = today.year - policy_holder_dob.year - (
                        (today.month, today.day) < (policy_holder_dob.month, policy_holder_dob.day))
                rec.policy_holder_age = f"{max(policy_holder_age, 0)} Years"
            else:
                rec.policy_holder_age = "0 Years"

    @api.onchange('policy_price_list_id')
    def onchange_insurance_policy_amount(self):
        """Onchange insurance policy amount"""
        for rec in self:
            if rec.policy_price_list_id:
                rec.policy_amount = rec.policy_price_list_id.policy_premium

    @api.onchange('policy_holder_id')
    def onchange_policy_holder_details(self):
        """Onchange policy holder details"""
        for rec in self:
            rec.email = rec.policy_holder_id.email
            rec.phone = rec.policy_holder_id.phone

    @api.onchange('insurance_policy_id')
    def _onchange_policy_details(self):
        """Onchange policy details"""
        for rec in self:
            if rec.insurance_policy_id:
                rec.claim_amount = rec.insurance_policy_id.sum_assured
                rec.policy_provider_cmp_id = rec.insurance_policy_id.policy_provider_cmp_id.id
            else:
                rec.claim_amount = ''
                rec.policy_price_list_id = False
                rec.policy_amount = ''
                rec.policy_provider_cmp_id = False
                rec.insurance_buying_for_id = False

    @api.onchange('policy_amount', 'policy_durations')
    def _total_monthly_installment_amount(self):
        """Monthly installment amount"""
        for rec in self:
            if rec.policy_durations > 0:
                rec.monthly_installment = rec.policy_amount / rec.policy_durations

    def action_create_crm_insurance(self):
        """Create crm lead to insurance"""
        data = {
            'crm_lead_id': self.crm_lead_id.id,
            'issue_date': self.issue_date,
            'policy_holder_id': self.policy_holder_id.id,
            'email': self.email,
            'phone': self.phone,
            'policy_holder_dob': self.policy_holder_dob,
            'policy_holder_age': self.policy_holder_age,
            'policy_holder_gender': self.policy_holder_gender,
            'policy_holder_street': self.crm_lead_id.partner_id.street,
            'policy_holder_street2': self.crm_lead_id.partner_id.street2,
            'policy_holder_city': self.crm_lead_id.partner_id.city,
            'policy_holder_state_id': self.crm_lead_id.partner_id.state_id.id,
            'policy_holder_zip': self.crm_lead_id.partner_id.zip,
            'policy_holder_country_id': self.crm_lead_id.partner_id.country_id.id,

            'insurance_policy_id': self.insurance_policy_id.id,
            'insurance_category_id': self.insurance_category_id.id,
            'insurance_sub_category_id': self.insurance_sub_category_id.id,
            'insurance_buying_for_id': self.insurance_buying_for_id.id,
            'policy_price_list_id': self.policy_price_list_id.id,
            'policy_amount': self.policy_amount,
            'monthly_installment': self.monthly_installment,
            'claim_amount': self.claim_amount,
            'policy_provider_cmp_id': self.policy_provider_cmp_id.id,
            'policy_certificate_no': self.policy_certificate_no,
            'previous_policy_no': self.previous_policy_no,
            'responsible_id': self.responsible_id.id,
            'policy_descriptions': self.insurance_policy_id.policy_descriptions,
            'policy_terms_and_conditions': self.insurance_policy_id.policy_terms_and_conditions,
        }
        insurance_id = self.env['insurance.information'].create(data)
        self.crm_lead_id.insurance_id = insurance_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Insurance'),
            'res_model': 'insurance.information',
            'res_id': insurance_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    # DEPRECATED
    policy_provider_id = fields.Many2one('res.company', string="Company (legacy)")