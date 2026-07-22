# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class InsuranceConfig(models.TransientModel):
    """Insurance Config"""
    _inherit = 'res.config.settings'

    insurance_expiry_days = fields.Integer(
        string=' Days', default=5,
        config_parameter='tk_insurance_management.insurance_expiry_days')
    is_auto_cancellation = fields.Boolean(
        string="Auto Cancellation", default=True,
        config_parameter='tk_insurance_management.is_auto_cancellation')
    reminder_days = fields.Integer(
        string='Days', default=5,
        config_parameter='tk_insurance_management.reminder_days')

    is_terms_and_conditions = fields.Boolean(
        string="Terms and Conditions",
        config_parameter='tk_insurance_management.is_terms_and_conditions')
    terms_condition_url = fields.Char(
        string="URL", config_parameter='tk_insurance_management.terms_condition_url',
        default='#')

    # Policy Expiry Remaining Days
    policy_expiry_remaining_days = fields.Integer(
        string='Policy Expiry Dashboard (Days)', default=30,
        config_parameter='tk_insurance_management.policy_expiry_remaining_days')

    is_insurance_company_migrated = fields.Boolean(
        default=False, string="Company Migrated",
        config_parameter='tk_insurance_management.is_insurance_company_migrated')

    report_color_config = fields.Char(config_parameter='tk_insurance_management.report_color_config',
                                      default="#0a9396", string="Report Color")

    claim_report_color_config = fields.Char(config_parameter='tk_insurance_management.claim_report_color_config',
                                            default="#0a9396", string="Claim Report Color")

    def action_reset_color(self):
        """Reset both colors and write into config parameters"""
        ICP = self.env['ir.config_parameter'].sudo()
        # update system parameters
        ICP.set_param('tk_insurance_management.report_color_config', "#0a9396")
        ICP.set_param('tk_insurance_management.claim_report_color_config', "#0a9396")

        # update the transient record values so UI shows updated values
        for rec in self:
            rec.report_color_config = "#0a9396"
            rec.claim_report_color_config = "#0a9396"
