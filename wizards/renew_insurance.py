# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import ValidationError
from odoo import fields, api, models, _


class RenewInsurance(models.TransientModel):
    """Renew Insurance"""
    _name = 'renew.insurance'
    _description = __doc__

    insurance_id = fields.Many2one('insurance.information', string="Insurance")
    issue_date = fields.Date(string="Issue Date")
    policy_holder_id = fields.Many2one('res.partner', string="Policy Holder",
                                       domain="[('is_agent', '=', False)]")
    email = fields.Char(string="Email")
    phone = fields.Char(string=" Phone")
    policy_holder_street = fields.Char(translate=True)
    policy_holder_street2 = fields.Char(translate=True)
    policy_holder_city = fields.Char(translate=True)
    policy_holder_state_id = fields.Many2one(
        "res.country.state",
        domain="[('country_id', '=?', policy_holder_country_id)]")
    policy_holder_zip = fields.Char()
    policy_holder_country_id = fields.Many2one("res.country")
    policy_holder_dob = fields.Date()
    policy_holder_age = fields.Char(compute="_compute_policy_holder_age_count",
                                    translate=True)
    policy_holder_gender = fields.Selection([
        ('male', "Male"),
        ('female', "Female"),
        ('others', "Others")],
        string=" Gender")

    insurance_category_id = fields.Many2one('insurance.category',
                                            string="Policy Category")
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
        active_model = self.env.context.get('active_model')

        insurance = None
        if active_model == 'insurance.information' and active_id:
            insurance = self.env['insurance.information'].browse(active_id)
        elif active_model == 'crm.lead' and active_id:
            lead = self.env['crm.lead'].browse(active_id)
            insurance = lead.previous_insurance_id

        if insurance:
            default_data.update({
                'insurance_id': insurance.id,
                'policy_holder_id': insurance.policy_holder_id.id,
                'policy_holder_dob': insurance.policy_holder_dob,
                'policy_holder_age': insurance.policy_holder_age,
                'policy_holder_gender': insurance.policy_holder_gender,
                'insurance_category_id': insurance.insurance_category_id.id,
                'category': insurance.category,
                'insurance_sub_category_id': insurance.insurance_sub_category_id.id,
                'insurance_policy_id': insurance.insurance_policy_id.id,
                'insurance_buying_for_id': insurance.insurance_buying_for_id.id,
                'policy_certificate_no': insurance.policy_certificate_no,
                'previous_policy_no': insurance.previous_policy_no,
                'responsible_id': insurance.responsible_id.id,
            })
        return default_data

    @api.onchange('policy_price_list_id')
    def onchange_insurance_policy_amount(self):
        """Onchange insurance policy amount"""
        for rec in self:
            rec.policy_amount = rec.policy_price_list_id.policy_premium

    @api.constrains('issue_date')
    def _check_issue_date(self):
        """Check that the issue date is not before today"""
        today = fields.Date.today()
        for record in self:
            if record.issue_date and record.issue_date < today:
                raise ValidationError(_("The issue date cannot be earlier than today."))

    @api.onchange('policy_holder_id')
    def onchange_policy_holder_details(self):
        """Onchange policy holder details"""
        for rec in self:
            rec.email = rec.policy_holder_id.email
            rec.phone = rec.policy_holder_id.phone
            rec.policy_holder_street = rec.policy_holder_id.street
            rec.policy_holder_street2 = rec.policy_holder_id.street2
            rec.policy_holder_city = rec.policy_holder_id.city
            rec.policy_holder_zip = rec.policy_holder_id.zip
            rec.policy_holder_state_id = rec.policy_holder_id.state_id.id
            rec.policy_holder_country_id = rec.policy_holder_id.country_id.id

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

    @api.onchange('policy_amount', 'policy_durations')
    def _total_monthly_installment_amount(self):
        """Monthly installment amount"""
        for rec in self:
            if rec.policy_durations > 0:
                rec.monthly_installment = rec.policy_amount / rec.policy_durations

    def create_insurance_renew(self):
        """Insurance renew"""
        insurance = self.insurance_id
        data = {
            'previous_insurance_id': insurance.id,
            'issue_date': self.issue_date,
            'policy_holder_id': self.policy_holder_id.id,
            'email': self.email,
            'phone': self.phone,
            'policy_holder_street': self.policy_holder_street,
            'policy_holder_street2': self.policy_holder_street2,
            'policy_holder_city': self.policy_holder_city,
            'policy_holder_state_id': self.policy_holder_state_id.id,
            'policy_holder_country_id': self.policy_holder_country_id.id,
            'policy_holder_zip': self.policy_holder_zip,
            'policy_holder_dob': self.policy_holder_dob,
            'policy_holder_age': self.policy_holder_age,
            'policy_holder_gender': self.policy_holder_gender,

            'insurance_policy_id': self.insurance_policy_id.id,
            'insurance_category_id': self.insurance_category_id.id,
            'insurance_sub_category_id': self.insurance_sub_category_id.id,
            'insurance_buying_for_id': self.insurance_buying_for_id.id,
            'policy_price_list_id': self.policy_price_list_id.id,
            'policy_amount': self.policy_amount,
            'monthly_installment': self.monthly_installment,
            'claim_amount': self.claim_amount,
            'policy_provider_cmp_id': self.policy_provider_cmp_id.id,
            'responsible_id': self.responsible_id.id,

            'policy_descriptions': insurance.policy_descriptions,
            'policy_terms_and_conditions': insurance.policy_terms_and_conditions,
            'life_insured_age': insurance.life_insured_age,
            'desired_death_amount': insurance.desired_death_amount,
            'is_smoking_status': insurance.is_smoking_status,
            'length_of_coverage_term': insurance.length_of_coverage_term,
            'life_health_history': insurance.life_health_history,
            'family_medical_history': insurance.family_medical_history,

            'desired_coverage_type': insurance.desired_coverage_type,
            'health_deductible_amount': insurance.health_deductible_amount,
            'copay_amount': insurance.copay_amount,
            'out_of_pocket_maximum': insurance.out_of_pocket_maximum,
            'health_history_of_insured': insurance.health_history_of_insured,
            'drug_coverage': insurance.drug_coverage,
            'healthcare_provider_network': insurance.healthcare_provider_network,

            'property_type': insurance.property_type,
            'property_usage': insurance.property_usage,
            'area_sq_ft': insurance.area_sq_ft,
            'construct_year': insurance.construct_year,
            'street': insurance.street,
            'street2': insurance.street2,
            'city': insurance.city,
            'country_id': insurance.country_id.id,
            'state_id': insurance.state_id.id,
            'zip': insurance.zip,
            'property_value': insurance.property_value,
            'property_deductible_amount': insurance.property_deductible_amount,
            'desired_coverage_types': insurance.desired_coverage_types,
            'property_coverage_limits': insurance.property_coverage_limits,
            'construction_type_and_materials': insurance.construction_type_and_materials,
            'special_features_of_the_property': insurance.special_features_of_the_property,
            'personal_property_inventory': insurance.personal_property_inventory,

            'type_of_liability_risk': insurance.type_of_liability_risk,
            'liability_coverage_type': insurance.liability_coverage_type,
            'desired_coverage_limits': insurance.desired_coverage_limits,
            'business_type_and_operations': insurance.business_type_and_operations,

            'occupation': insurance.occupation,
            'income': insurance.income,
            'disability_desired_benefit_amount': insurance.disability_desired_benefit_amount,
            'insured_is_smoking': insurance.insured_is_smoking,
            'length_coverage_disability_period': insurance.length_coverage_disability_period,
            'disability_health_history': insurance.disability_health_history,
            'occupation_and_hobbies': insurance.occupation_and_hobbies,

            'types_of_coverage': insurance.types_of_coverage,
            'travel_source': insurance.travel_source,
            'travel_destination': insurance.travel_destination,
            'travel_purpose': insurance.travel_purpose,
            'trip_start_date': insurance.trip_start_date,
            'trip_end_date': insurance.trip_end_date,
            'trip_length': insurance.trip_length,
            'trip_coverage_amount': insurance.trip_coverage_amount,
            'odometer_unit': insurance.odometer_unit,
            'traveler_health_history': insurance.traveler_health_history,

            'pet_name': insurance.pet_name,
            'breed_type': insurance.breed_type,
            'pet_health_history': insurance.pet_health_history,
            'age_of_breed_of_the_pet': insurance.age_of_breed_of_the_pet,
            'pet_desired_coverage_type': insurance.pet_desired_coverage_type,
            'exclusions': insurance.exclusions,

            'accident_coverage': insurance.accident_coverage,
            'illness_coverage': insurance.illness_coverage,
            'pet_deductible_amount': insurance.pet_deductible_amount,
            'pet_coverage_limits': insurance.pet_coverage_limits,

            'business_name': insurance.business_name,
            'business_desired_coverage_type': insurance.business_desired_coverage_type,
            'number_of_employees': insurance.number_of_employees,
            'business_property_value': insurance.business_property_value,
            'business_deductible_amount': insurance.business_deductible_amount,
            'business_type_operation': insurance.business_type_operation,
            'business_coverage_limits': insurance.business_coverage_limits,
            'industry_specific_risks': insurance.industry_specific_risks,

            'policy_certificate_no': self.policy_certificate_no,
            'previous_policy_no': self.previous_policy_no,
            'vehicle_name': insurance.vehicle_name,
            'model': insurance.model,
            'year': insurance.year,
            'vin_no': insurance.vin_no,
            'reg_no': insurance.reg_no,
            'place_of_reg': insurance.place_of_reg,
            'cubic_capacity': insurance.cubic_capacity,
            'setting_capacity': insurance.setting_capacity,
            'usage_of_vehicle': insurance.usage_of_vehicle,
            'coverage_type': insurance.coverage_type,
            'for_the_vehicle': insurance.for_the_vehicle,
            'for_trailer': insurance.for_trailer,
            'non_electric_accessories': insurance.non_electric_accessories,
            'electric_accessories': insurance.electric_accessories,
            'value_of_cng_lpg_kit': insurance.value_of_cng_lpg_kit,
            'total_idv': insurance.total_idv,
            'basic_od': insurance.basic_od,
            'od_package_premium': insurance.od_package_premium,
            'service_tax': insurance.service_tax,
            'special_discount': insurance.special_discount,
            'final_premium': insurance.final_premium,
            'basic_tp_liability': insurance.basic_tp_liability,
            'pa_cover_for_owner_driver': insurance.pa_cover_for_owner_driver,
            'package_premium': insurance.package_premium,
            'liability_service_tax': insurance.liability_service_tax,
            'total_premium': insurance.total_premium,
            'limitation_as_to_use': insurance.limitation_as_to_use,
            'limits_of_liability': insurance.limits_of_liability,
            'deductibles_under_section': insurance.deductibles_under_section,
            'special_conditions': insurance.special_conditions,
            'driving_history': insurance.driving_history,
        }
        renew_insurance = self.env['insurance.information'].create(data)
        insurance.renew_insurance_id = renew_insurance.id
        if self.env.context.get('active_model') == 'crm.lead':
            lead_id = self.env['crm.lead'].browse(self.env.context.get('active_id'))
            lead_id.insurance_id = renew_insurance.id
        if not insurance.renew_insurance_id:
            for record in insurance.insured_document_ids:
                documents = {
                    'insured_id': record.insured_id.id,
                    'file_name': record.file_name,
                    'avatar': record.avatar,
                    'state': record.state,
                    'insured_document_type_id': record.insured_document_type_id.id,
                    'insured_info_id': renew_insurance.id,
                }
                self.env['insured.documents'].create(documents)
        for rec in insurance.property_insurance_image_ids:
            property_image = {
                'name': rec.name,
                'avatar': rec.avatar,
                'insurance_information_id': renew_insurance.id,
            }
            self.env['property.insurance.image'].create(property_image)
        for img in insurance.vehicle_insurance_image_ids:
            vehicle_image = {
                'name': img.name,
                'avatar': img.avatar,
                'insurance_information_id': renew_insurance.id,
            }
            self.env['vehicle.insurance.image'].create(vehicle_image)
        for nominee in insurance.insurance_nominee_ids:
            nominee_details = {
                'partner_id': nominee.partner_id.id,
                'insurance_nominee_relation_id': nominee.insurance_nominee_relation_id.id,
                'nominee_dob': nominee.nominee_dob,
                'nominee_age': nominee.nominee_age,
                'percentage': nominee.percentage,
                'insurance_information_id': renew_insurance.id,
            }
            self.env['insurance.nominee'].create(nominee_details)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Insurance'),
            'res_model': 'insurance.information',
            'res_id': renew_insurance.id,
            'view_mode': 'form',
            'target': 'current'
        }

    # DEPRECATED
    policy_provider_id = fields.Many2one('res.company', string="Company (legacy)")