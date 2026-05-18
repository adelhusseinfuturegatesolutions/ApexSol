# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _


class PolicyPriceList(models.Model):
    """Policy PriceList"""
    _name = 'policy.price.list'
    _description = __doc__
    _rec_name = 'insurance_time_period_id'

    insurance_time_period_id = fields.Many2one('insurance.time.period', string="Policy Time Period")
    duration = fields.Integer(related="insurance_time_period_id.duration",
                              string="Duration (Months)")
    policy_premium = fields.Monetary(string="Premium")
    male_premium = fields.Monetary(string="Male Premium")
    female_premium = fields.Monetary(string="Female Premium")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related="company_id.currency_id")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company,
                                 string="Company")
    insurance_policy_id = fields.Many2one('insurance.policy', string="Insurance Policy",
                                          ondelete='cascade')

    @api.constrains('policy_premium')
    def _check_premium_amount(self):
        """Check premium amount"""
        for record in self:
            if not record.policy_premium:
                raise ValidationError(
                    _("Include valid policy premium amounts in the policy price list tab"))
