# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _


class InsuranceNomineeRelation(models.Model):
    """Insurance Nominee Relation"""
    _name = 'insurance.nominee.relation'
    _description = __doc__
    _rec_name = 'name'

    name = fields.Char(translate=True)


class InsuranceNominee(models.Model):
    """Insurance Nominee"""
    _name = 'insurance.nominee'
    _description = __doc__
    _rec_name = 'name'

    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    name = fields.Char(string="Name")
    nominee_id = fields.Char(string="ID")
    nominee_dob = fields.Date(string="Date of Birth")
    nominee_age = fields.Char(string="Age", compute="_compute_nominee_age_count", translate=True)
    insured_gender = fields.Selection([
        ('male', "Male"),
        ('female', "Female"),
        ('others', "Others")],
        string=" Gender")
    insured_blood_group = fields.Selection(
        [('a_positive', "A+"),
         ('a_negative', "A-"),
         ('b_positive', "B+"),
         ('b_negative', "B-"),
         ('ab_positive', "AB+"),
         ('ab_negative', "AB-"),
         ('o_positive', "O+"),
         ('o_negative', "O-")],
        string="Blood Group")
    insured_heights = fields.Char(string="Height(cm)")
    insured_weights = fields.Char(string="Weight(kg)")
    insured_birthmarks = fields.Char(string="Birthmark")
    insured_marital_status = fields.Selection([
        ('single', "Single"),
        ('married', "Married"),
        ('divorced', "Divorced"),
        ('widowed', "Widowed"),
        ('separated', "Separated"),
        ('annulled', "Annulled"),
        ('domestic', "Domestic Partnership/Civil Union"),
        ('common', "Common-Law Marriage"),
        ('other', "Other")], string="Marital Status")
    insurance_information_id = fields.Many2one('insurance.information', ondelete='cascade')
    claim_information_id = fields.Many2one('claim.information', ondelete='cascade')
    policy_holder_id = fields.Many2one('res.partner', string='Policy Holder')
    active = fields.Boolean(default=True)
    medical_history_ids = fields.One2many('medical.history', 'insure_nominee_id',string="Medical History")
    parent_nominee_id = fields.Many2one(
        'insurance.nominee', 
        string="Main Nominee (Employee)", 
        index=True, 
        ondelete='cascade'
    )
    
    family_member_ids = fields.One2many(
        'insurance.nominee', 
        'parent_nominee_id', 
        string="Family Members"
    )

    relation_type = fields.Selection([('spouse','Spouse'),('son','Son'),('daughter','Daughter'),('father','Father'),('mother','Mother')],string="Relationship.")
    amount_factor = fields.Float(string='Amount Factor')
    claims_count = fields.Integer(compute='_compute_claim_count')


    # policy details
    insurance_category_id = fields.Many2one('insurance.category', string="Policy Category" , related='insurance_information_id.insurance_category_id')
    insurance_sub_category_id = fields.Many2one('insurance.sub.category', string="Sub Category",related='insurance_information_id.insurance_sub_category_id')
    insurance_policy_id = fields.Many2one('insurance.policy', string='Insurance Policy',related='insurance_information_id.insurance_policy_id')
    policy_price_list_id = fields.Many2one('policy.price.list', string="Policy Time Period",related='insurance_information_id.policy_price_list_id')
    policy_provider_cmp_id = fields.Many2one('res.partner', string='Policy Provider',related='insurance_information_id.policy_provider_cmp_id')
    issue_date = fields.Date(string="Issue Date", related='insurance_information_id.issue_date')
    expiry_date = fields.Date(string="Expiry Date", related='insurance_information_id.expiry_date')


    @api.constrains('nominee_dob')
    def _check_nominee_dob(self):
        """Check nominee dob"""
        today = fields.Date.today()
        for record in self:
            if record.nominee_dob and record.nominee_dob > today:
                raise ValidationError(_("Nominee must be born before today's date."))

    @api.depends('nominee_dob')
    def _compute_nominee_age_count(self):
        """Nominee age count"""
        today = fields.Date.today()
        for rec in self:
            if rec.nominee_dob:
                nominee_dob = fields.Date.from_string(rec.nominee_dob)
                if nominee_dob > today:
                    raise ValidationError(_("DOB should be earlier than today's date."))
                nominee_age = today.year - nominee_dob.year - (
                        (today.month, today.day) < (nominee_dob.month, nominee_dob.day))
                rec.nominee_age = f"{max(nominee_age, 0)} Years"
            else:
                rec.nominee_age = "0 Years"

    def _compute_claim_count(self):
        """Claim count"""
        for rec in self:
            rec.claims_count = self.env['claim.information'].search_count(
                [('insurance_nominee_id', '=', rec.id)])

    def action_insured_nominee_claim(self):
        """Insured claim"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Claims'),
            'res_model': 'claim.information',
            'domain': [('insurance_nominee_id', '=', self.id)],
            'context': {
                'default_insurance_nominee_id': self.id,
            },
            'view_mode': 'list,form',
            'target': 'current',
        }

class MedicalHistory(models.Model):
    _name = 'medical.history'
    _description = __doc__
    _rec_name = 'name'

    name = fields.Char(translate=True, string="Disease")
    disease_year = fields.Char(string="Year of Disease")
    notes = fields.Text(string="Medical Notes")
    insure_nominee_id = fields.Many2one('insurance.nominee')
