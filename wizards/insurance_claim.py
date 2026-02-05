# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from ..utils import _display_notification


class InsuranceClaim(models.TransientModel):
    """Insurance Claim"""
    _name = 'insurance.claim'
    _description = __doc__

    insurance_id = fields.Many2one('insurance.information', string="Insurance")
    insurance_nominee_id = fields.Many2one('insurance.nominee', string="Insurance Nominee")
    claim_date = fields.Date(string='Date')

    # @api.model
    # def default_get(self, field):
    #     """Default record"""
    #     res = super().default_get(field)
    #     res['insurance_id'] = self.env.context.get('active_id')
    #     return res
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        active_id = self.env.context.get('active_id')
        
        if active_id and self.env.context.get('active_model') == 'insurance.nominee':
            nominee = self.env['insurance.nominee'].browse(active_id)
            
            # Set the Nominee field
            res['insurance_nominee_id'] = nominee.id
            
            # Set the Insurance field from the nominee's relationship
            if nominee.insurance_information_id:
                res['insurance_id'] = nominee.insurance_information_id.id
                
        return res

    @api.constrains('claim_date', 'insurance_id')
    def _check_claim_date(self):
        """Check claim date"""
        for rec in self:
            if rec.claim_date and rec.insurance_id:
                if (rec.claim_date < rec.insurance_id.issue_date or
                        rec.claim_date > rec.insurance_id.expiry_date):
                    raise ValidationError(
                        _("Claim date must be within the insurance coverage period!"))

    def insurance_claim_create(self):
        """Create insurance claim"""
        for rec in self.insurance_id:
            nominee = self.insurance_nominee_id
            # Validate reinsurance requirement
            if rec.is_reinsurance_required:
                if not rec.re_insurance_id:
                    return _display_notification(
                        message='Please create the reinsurance record before proceeding.',
                        message_type='warning'
                    )
                if rec.re_insurance_id.status == 'draft':
                    return _display_notification(
                        message="Reinsurance status must be 'Running' before proceeding.",
                        message_type='warning'
                    )
            # Validate claim eligibility
            if rec.total_due_amount <= 0.0:
                return _display_notification(
                    message='You are not eligible to create additional claims.',
                    message_type='warning'
                )
            # Prepare claim data
            reinsurance_valid = rec.is_reinsurance_required and rec.re_insurance_id.status != 'expired'
            data = {
                'insurance_id': rec.id,
                'insurance_nominee_id': nominee.id,
                'claim_date': self.claim_date,
                'policy_holder_id': rec.policy_holder_id.id,
                'email': rec.email,
                'phone': rec.phone,
                'policy_holder_street': rec.policy_holder_street,
                'policy_holder_street2': rec.policy_holder_street2,
                'policy_holder_city': rec.policy_holder_city,
                'policy_holder_state_id': rec.policy_holder_state_id.id,
                'policy_holder_country_id': rec.policy_holder_country_id.id,
                'policy_holder_zip': rec.policy_holder_zip,
                'policy_holder_dob': nomniee.nominee_dob,
                'policy_holder_age': nomniee.nominee_age,
                'policy_holder_gender': nomniee.insured_gender,

                'insured_id': rec.insured_id.id,
                'gender': nomniee.insured_gender,
                'dob': nomniee.nominee_dob,
                'age': nomniee.nominee_age,
                'marital_status': nomniee.insured_marital_status,
                'blood_group': nomniee.insured_blood_group,
                'insured_height': nomniee.insured_heights,
                'insured_weight': nomniee.insured_weights,
                'insured_birthmark': nomniee.insured_blood_group,

                'insurance_policy_id': rec.insurance_policy_id.id,
                'insurance_category_id': rec.insurance_category_id.id,
                'insurance_sub_category_id': rec.insurance_sub_category_id.id,
                'desired_coverage_type': rec.desired_coverage_type,
                'policy_provider_cmp_id': rec.policy_provider_cmp_id.id,
                'agent_required': rec.agent_required,
                'agent_id': rec.agent_id.id,
                'responsible_id': rec.responsible_id.id,
                'policy_price_list_id': rec.policy_price_list_id.id,
                'policy_amount': rec.total_policy_amount,
                'due_amount': rec.total_due_amount,
                'policy_terms_and_conditions': rec.policy_terms_and_conditions,

                'is_reinsurance_required': reinsurance_valid,
                're_insurance_id': rec.re_insurance_id.id if reinsurance_valid else False,
                'reinsurance_company_id': rec.re_insurance_id.reinsurance_company_id.id if reinsurance_valid else False,
            }

            claim = self.env['claim.information'].create(data)
            for insured_detail in self.insurance_id.insured_details_ids:
                insured_detail.claim_information_id = claim.id
            for nominee in self.insurance_id.insurance_nominee_ids:
                nominee.claim_information_id = claim.id
            return {
                'type': 'ir.actions.act_window',
                'name': _('Claim'),
                'res_model': 'claim.information',
                'res_id': claim.id,
                'view_mode': 'form',
                'target': 'current'
            }
        return True
