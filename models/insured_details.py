# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _


class InsuredDetails(models.Model):
    """Insured Details"""
    _name = 'insured.details'
    _description = __doc__
    _rec_name = 'partner_id'

    partner_id = fields.Many2one("res.partner", string="Insured",
                                 domain="[('is_agent', '=', False)]")
    insured_dob = fields.Date(string="Date of Birth")
    insured_ages = fields.Char(compute="_compute_insured_ages_count", translate=True, string="Age")
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

    currency_id = fields.Many2one(
        'res.currency',
        related='insurance_information_id.currency_id',
        string='Currency')
    gender_premium = fields.Monetary(
        string="Premium",
        compute="_compute_gender_premium",
        store=True,
        currency_field='currency_id')

    @api.depends('insured_gender',
                 'insurance_information_id.policy_price_list_id.male_premium',
                 'insurance_information_id.policy_price_list_id.female_premium',
                 'insurance_information_id.policy_price_list_id.policy_premium')
    def _compute_gender_premium(self):
        """Premium per insured driven by gender pricing on the policy pricelist."""
        for rec in self:
            pricelist = rec.insurance_information_id.policy_price_list_id
            if rec.insured_gender == 'male':
                rec.gender_premium = pricelist.male_premium or pricelist.policy_premium
            elif rec.insured_gender == 'female':
                rec.gender_premium = pricelist.female_premium or pricelist.policy_premium
            else:
                rec.gender_premium = pricelist.policy_premium

    @api.depends('insured_dob')
    def _compute_insured_ages_count(self):
        """Insured age count"""
        today = fields.Date.today()
        for rec in self:
            if rec.insured_dob:
                insured_dob = fields.Date.from_string(rec.insured_dob)
                if insured_dob > today:
                    raise ValidationError(_("DOB should be earlier than today's date."))
                insured_ages = today.year - insured_dob.year - (
                        (today.month, today.day) < (insured_dob.month, insured_dob.day))
                rec.insured_ages = f"{max(insured_ages, 0)} Years"
            else:
                rec.insured_ages = "0 Years"
