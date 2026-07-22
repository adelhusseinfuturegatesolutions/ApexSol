# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import secrets
from odoo.exceptions import ValidationError
from odoo import fields, api, models, _
from ..utils import _display_notification


class QuoteLeadTracking(models.Model):
    """Quote Lead Tracking"""
    _name = 'quote.lead.tracking'
    _description = __doc__

    tracking_date = fields.Date(string="Date")
    tracking_description = fields.Char(string="Description")
    crm_lead_id = fields.Many2one('crm.lead', ondelete='cascade')


class CrmLead(models.Model):
    """Crm lead"""
    _inherit = 'crm.lead'
    _description = __doc__

    website_ref_number = fields.Char(string='Website Ref No', readonly=True,
                                     default=lambda self: '', copy=False)

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
    policy_provider_cmp_id = fields.Many2one('res.partner', string='Policy Provider',
                                             domain=[('is_company', '=', True),
                                                     ('is_re_insurance_company', '=', False)])
    policy_holder_dob = fields.Date(string="Birth Date")
    policy_holder_age = fields.Char(compute="_compute_policy_holder_age_count",
                                    translate=True)
    policy_holder_gender = fields.Selection([
        ('male', "Male"),
        ('female', "Female"),
        ('others', "Others")],
        string="Gender")

    quote_lead_tracking_ids = fields.One2many(comodel_name='quote.lead.tracking',
                                              inverse_name='crm_lead_id', string="Lead Tracking")
    is_won = fields.Boolean(related='stage_id.is_won', string="Is Won")
    file_name = fields.Char(string="filename", translate=True)
    attachment = fields.Binary(string="Attachment")

    insurance_id = fields.Many2one('insurance.information', string="Insurance")
    previous_insurance_id = fields.Many2one('insurance.information', string="Previous Insurance")

    website_tracking_status = fields.Selection([
        ('a_draft', "Draft"),
        ('b_in_progress', "In Progress"),
        ('c_complete', "Completed"),
        ('d_cancel', "Cancelled")],
        default='a_draft', string="Tracking Status")

    @api.model_create_multi
    def create(self, vals_list):
        """Create record"""
        for vals in vals_list:
            if vals.get('website_ref_number', '') == '':
                vals['website_ref_number'] = secrets.token_urlsafe(8)
        res = super().create(vals_list)
        data = {
            'tracking_date': fields.Date.today(),
            'tracking_description': 'Quotation request for ' + res.name + ' successfully submitted',
            'crm_lead_id': res.id,
        }
        self.env['quote.lead.tracking'].create(data)
        return res

    def a_draft_to_b_in_progress(self):
        """Draft to in progress"""
        self.website_tracking_status = 'b_in_progress'

    def b_in_progress_to_c_complete(self):
        """In progress to complete"""
        if not self.is_won:
            message = _display_notification(
                message='Lead is won then after you can complete the process',
                message_type='warning')
            return message
        self.website_tracking_status = 'c_complete'
        return True

    def c_complete_to_d_cancel(self):
        """Complete to cancel"""
        self.website_tracking_status = 'd_cancel'

    @api.constrains('policy_holder_gender')
    def _check_policy_holder_gender(self):
        """Check policy holder gender"""
        for record in self:
            if not record.policy_holder_gender:
                raise ValidationError(_("Please select a gender: Male, Female or Others"))

    @api.onchange('insurance_category_id')
    def onchange_policy_category(self):
        """Onchange policy category"""
        for rec in self:
            rec.insurance_sub_category_id = False
            rec.policy_provider_cmp_id = False
            rec.insurance_policy_id = False
            rec.insurance_buying_for_id = False

    @api.onchange('insurance_sub_category_id')
    def onchange_policy_insurance_sub_category(self):
        """Onchange policy insurance sub category"""
        for rec in self:
            rec.policy_provider_cmp_id = False

    @api.constrains('policy_holder_dob')
    def _check_policy_holder_dob(self):
        """Check policy holder dob"""
        today = fields.Date.today()
        for record in self:
            if record.policy_holder_dob > today:
                raise ValidationError(_("Policy holder dob should be earlier than today's date."))

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

    # DEPRECATED
    policy_provider_id = fields.Many2one('res.company', string="Company (legacy)")
