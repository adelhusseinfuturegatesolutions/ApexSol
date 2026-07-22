# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _


class VehicleInsuranceImage(models.Model):
    """Vehicle Insurance Image"""
    _name = 'vehicle.insurance.image'
    _description = __doc__
    _rec_name = 'name'

    avatar = fields.Binary(string="Image")
    name = fields.Char(string="Name", translate=True, size=23)
    insurance_information_id = fields.Many2one('insurance.information', ondelete='cascade')

    # DEPRECATED
    insurance_category_id = fields.Many2one('insurance.category', ondelete='cascade')
    insurance_policy_id = fields.Many2one('insurance.policy', ondelete='cascade')


class PropertyInsuranceImage(models.Model):
    """Property Insurance Image"""
    _name = 'property.insurance.image'
    _description = __doc__
    _rec_name = 'name'

    avatar = fields.Binary(string="Image")
    name = fields.Char(string="Name", translate=True, size=23)
    insurance_information_id = fields.Many2one('insurance.information', ondelete='cascade')

    # DEPRECATED
    insurance_category_id = fields.Many2one('insurance.category', ondelete='cascade')
    insurance_policy_id = fields.Many2one('insurance.policy', ondelete='cascade')


class InsuranceSubCategory(models.Model):
    """Insurance Sub Category"""
    _name = 'insurance.sub.category'
    _description = __doc__
    _rec_name = 'name'

    insurance_category_id = fields.Many2one('insurance.category', string="Category")
    name = fields.Char(translate=True)
    policy_provider_cmp_id = fields.Many2one('res.partner', string='Policy Provider',
                                             domain=[('is_company', '=', True),
                                                     ('is_re_insurance_company', '=', False)])
    # DEPRECATED
    policy_provider_id = fields.Many2one('res.company', string="Company (legacy)")


class InsuranceCategory(models.Model):
    """Insurance Category"""
    _name = 'insurance.category'
    _description = __doc__
    _rec_name = 'name'

    name = fields.Char(translate=True)
    category = fields.Selection(
        [('life', "Life Insurance"),
         ('health', "Health Insurance"),
         ('property', "Property Insurance"),
         ('liability', "Liability Insurance"),
         ('disability', "Disability Insurance"),
         ('travel', "Travel Insurance"),
         ('pet', "Pet Insurance"),
         ('business', "Business Insurance"),
         ('vehicle', "Vehicle Insurance")])
    category_code = fields.Char(string="Code")
    policy_provider_cmp_id = fields.Many2one('res.partner', string='Policy Provider',
                                             domain=[('is_company', '=', True),
                                                     ('is_re_insurance_company', '=', False)])
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related="company_id.currency_id")
    is_displayed_on_website = fields.Boolean(string="Displayed on Website", default=True)

    # Per-role premium amounts driving Total Policy Amount
    employee_male_amount = fields.Monetary(string="Employee (Male) Amount")
    employee_female_amount = fields.Monetary(string="Employee (Female) Amount")
    wife_amount = fields.Monetary(string="Wife Amount")
    husband_amount = fields.Monetary(string="Husband Amount")
    son_amount = fields.Monetary(string="Son Amount")
    daughter_amount = fields.Monetary(string="Daughter Amount")
    father_amount = fields.Monetary(string="Father Amount")
    mother_amount = fields.Monetary(string="Mother Amount")

    # Life Insurance:
    length_of_coverage_term = fields.Text(string="Length of Coverage Terms", translate=True)
    life_health_history = fields.Text(string="Insured Health History", translate=True)
    occupation_and_hobbies = fields.Text(string="Occupation and Hobbies", translate=True)
    family_medical_history = fields.Text(string="Family Medical History", translate=True)

    # Health Insurance:
    out_of_pocket_maximum = fields.Text(string="Out-of-Pocket Maximum", translate=True)
    health_history_of_insured = fields.Text(translate=True)
    drug_coverage = fields.Text(string="Prescription Drug Coverage", translate=True)
    healthcare_provider_network = fields.Text(string="Preferred Healthcare Provider Network",
                                              translate=True)

    # Property Insurance:
    property_coverage_limits = fields.Text(string="Property Coverage Limits", translate=True)
    construction_type_and_materials = fields.Text(string="Construction Type and Materials",
                                                  translate=True)
    special_features_of_the_property = fields.Text(string="Special Features of the Property",
                                                   translate=True)
    personal_property_inventory = fields.Text(string="Personal Property Inventory", translate=True)

    # Liability Insurance:
    desired_coverage_limits = fields.Text(string="Desired Coverage Limits", translate=True)
    business_type_and_operations = fields.Text(translate=True)

    # Disability Insurance:
    length_coverage_disability_period = fields.Text(string="Length of Coverage Period",
                                                    translate=True)
    disability_health_history = fields.Text(translate=True)
    occupation_and_hobbies = fields.Text(string="Occupation and Hobbies", translate=True)

    # Travel Insurance:
    travel_purpose = fields.Text(string="Travel Purpose")
    traveler_health_history = fields.Text(string="Traveler Health History", translate=True)

    # Pet Insurance:
    pet_health_history = fields.Text(string="Health History")
    pet_coverage_limits = fields.Text(string="Coverage Limits", translate=True)

    # Business Insurance:
    business_type_operation = fields.Text(translate=True)
    business_coverage_limits = fields.Text(string="Business Coverage Limits", translate=True)
    industry_specific_risks = fields.Text(string=" Industry-Specific Risks", translate=True)

    # Vehicle Insurance:
    driving_history = fields.Text(string="Driving History of the Insured", translate=True)
    limitation_as_to_use = fields.Text(string="Limitations as to Use", translate=True)
    limits_of_liability = fields.Text(string="Limits of Liability", translate=True)
    deductibles_under_section = fields.Text(string="Deductibles under Section", translate=True)
    special_conditions = fields.Text(string="Special Conditions", translate=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Check if a category already exists before creating a new record."""
        for vals in vals_list:
            category = vals.get('category_code')
            if category:
                existing_record = self.search([('category_code', '=', category)], limit=1)
                if existing_record:
                    raise ValidationError(
                        _("Code %s is already in use. Please try a different one.", category))
        return super().create(vals_list)

    def write(self, vals):
        """Check if a category already exists before updating a record."""
        if 'category_code' in vals:
            new_category = vals['category_code']
            if new_category:
                for record in self:
                    existing_record = self.search(
                        [('category_code', '=', new_category), ('id', '!=', record.id)], limit=1)
                    if existing_record:
                        raise ValidationError(
                            _("Code %s is already in use. Please try a different one.",
                              new_category))
        return super().write(vals)

    @api.constrains('trip_start_date', 'trip_end_date')
    def _check_trip_period(self):
        """Check time period"""
        for record in self:
            if record.category == 'travel':
                if record.trip_end_date and record.trip_start_date:
                    if record.trip_end_date < record.trip_start_date:
                        raise ValidationError(_(
                            "Please ensure the trip end date is greater than the trip start date"))

    # DEPRECATED
    life_insured_age = fields.Selection(
        [('five_to_twenty', "Between 5 to 20 Years"),
         ('twenty_to_fifty', "Between 20 to 50 Years"),
         ('fifty_to_seventy', "Between 50 to 70 Years"),
         ('above_seventy', "Above 70 Years"),
         ('below_five', "Invalid age")])
    desired_death_amount = fields.Monetary()
    life_deductible_amount = fields.Monetary()
    liife_co_payment = fields.Monetary()

    health_insured_age = fields.Selection(
        [('five_to_twenty', "Between 5 to 20 Years"),
         ('twenty_to_fifty', "Between 20 to 50 Years"),
         ('fifty_to_seventy', "Between 50 to 70 Years"),
         ('above_seventy', "Above 70 Years"),
         ('below_five', "Invalid age")])
    desired_coverage_type = fields.Selection([
        ('individual', "Individual"),
        ('family', "Family"),
        ('group', "Group")])
    health_deductible_amount = fields.Monetary()

    property_type = fields.Char()
    property_usage = fields.Text()
    area_sq_ft = fields.Char()
    construct_year = fields.Integer()
    property_value = fields.Monetary()
    property_damage_coverage = fields.Monetary()
    property_insurance_image_ids = fields.One2many(comodel_name='property.insurance.image',
                                                   inverse_name='insurance_category_id')

    type_of_liability_risk = fields.Selection(
        [('auto', "Auto"),
         ('homeowner', "HomeOwner's"),
         ('business', "Business")])
    liability_coverage_type = fields.Selection(
        [('general_liability', "General Liability"),
         ('professional_liability', "Professional Liability")])

    income = fields.Monetary()
    disability_deductible_amount = fields.Monetary()

    types_of_coverage = fields.Selection(
        [('trip_cancellation', "Trip Cancellation"),
         ('medical_emergency', "Medical Emergency"),
         ('lost_luggage', "Lost Luggage")])
    travel_source = fields.Char()
    travel_destination = fields.Char()
    trip_start_date = fields.Date()
    trip_end_date = fields.Date()
    trip_coverage_amount = fields.Monetary()

    pet_name = fields.Char()
    breed_type = fields.Char()
    pet_desired_coverage_type = fields.Selection(
        [('accident', "Accident"),
         ('illness', "Illness"),
         ('comprehensive', "Comprehensive")])
    exclusions = fields.Selection([
        ('pre_existing_conditions', "Pre-Existing Conditions"),
        ('certain_breeds', "Certain Breeds")])
    accident_coverage = fields.Monetary()
    illness_coverage = fields.Monetary()

    business_name = fields.Char()
    business_desired_coverage_type = fields.Selection(
        [('property_damage', "Property Damage"),
         ('liability', "Liability"),
         ('workers', "Workers Compensation")])
    business_property_value = fields.Monetary()

    coverage_type = fields.Selection([
        ('liability', "Liability"),
        ('collision', "Collision"),
        ('comprehensive', "Comprehensive")])
    vehicle_insurance_image_ids = fields.One2many(comodel_name='vehicle.insurance.image',
                                                  inverse_name='insurance_category_id')
    policy_provider_id = fields.Many2one('res.company', string="Company (legacy)")

    @api.model
    def action_scheduler_create_company_to_partner(self):
        """Create or update partner from insurance company if not migrated"""
        config = self.env['ir.config_parameter'].sudo()
        is_insurance_company_migrated = config.get_param('tk_insurance_management.is_insurance_company_migrated')

        if is_insurance_company_migrated == 'True':
            return  # skip scheduler

        insurance_categories = self.search([('policy_provider_id', '!=', False)])
        for category in insurance_categories:
            company = category.policy_provider_id

            existing_partner = self.env['res.partner'].search([
                '|',
                ('name', '=', company.name),
                ('email', '=', company.email)
            ], limit=1)

            if not existing_partner:
                existing_partner = self.env['res.partner'].create({
                    'name': company.name,
                    'email': company.email,
                    'phone': company.phone,
                    'is_company': True,
                    'company_type': 'company',
                })

            # Update category
            category.write({
                'policy_provider_cmp_id': existing_partner.id,
                'policy_provider_id': False,
            })

            # Update Sub Categories
            sub_categories = self.env['insurance.sub.category'].search([
                ('insurance_category_id', '=', category.id)
            ])
            for sub_cat in sub_categories:
                sub_cat.write({
                    'policy_provider_cmp_id': existing_partner.id,
                    'policy_provider_id': False,
                })

            # Update Insurance Policy
            ins_policy = self.env['insurance.policy'].search([
                ('insurance_category_id', '=', category.id)
            ])
            for policy in ins_policy:
                policy.write({
                    'policy_provider_cmp_id': existing_partner.id,
                    'policy_provider_id': False,
                })

            # Update Insurance Buying For
            ins_buying_for = self.env['insurance.buying.for'].search([
                ('insurance_category_id', '=', category.id)
            ])
            for buying_for in ins_buying_for:
                buying_for.write({
                    'policy_provider_cmp_id': existing_partner.id,
                    'policy_provider_id': False,
                })
        config.set_param('tk_insurance_management.is_insurance_company_migrated', 'True')
