# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _


class InsuranceTimePeriod(models.Model):
    """Insurance Time Period"""
    _name = 'insurance.time.period'
    _description = __doc__
    _rec_name = 't_period'

    t_period = fields.Char(string="Policy Time Period", translate=True)
    duration = fields.Integer(string="Duration (Months)")

    @api.constrains('duration')
    def _check_duration(self):
        """Check duration"""
        for record in self:
            if record.duration <= 0:
                raise ValidationError(_("Please add an Duration (Months) greater than zero."))


class InsuranceBuyingFor(models.Model):
    """Insurance For"""
    _name = 'insurance.buying.for'
    _description = __doc__
    _rec_name = 'buying_for'

    buying_for = fields.Char(string="Buying For", translate=True)
    insurance_category_id = fields.Many2one('insurance.category', string="Policy Category")

    policy_provider_cmp_id = fields.Many2one('res.partner', string='Policy Provider',
                                             domain=[('is_company', '=', True),
                                                     ('is_re_insurance_company', '=', False)])
    # DEPRECATED
    policy_provider_id = fields.Many2one('res.company', string="Company (legacy)")


class InsurancePolicy(models.Model):
    """Insurance Policy"""
    _name = 'insurance.policy'
    _description = __doc__
    _rec_name = 'policy_name'

    policy_name = fields.Char(translate=True)
    policy_number = fields.Char(string="Policy Number")
    insurance_category_id = fields.Many2one('insurance.category', string="Policy Category")
    category = fields.Selection(related="insurance_category_id.category", string='Category')
    insurance_sub_category_id = fields.Many2one(
        'insurance.sub.category', string="Sub Category",
        domain="[('insurance_category_id', '=', insurance_category_id)]")

    insured_document_type_ids = fields.Many2many('insured.document.type',
                                                 string="Policy Documents")
    claim_document_type_ids = fields.Many2many('claim.document.type',
                                               string="Claim Documents")

    policy_terms_and_conditions = fields.Text(string="Terms & Conditions", translate=True)
    policy_provider_cmp_id = fields.Many2one('res.partner', string='Policy Provider',
                                             domain=[('is_company', '=', True),
                                                     ('is_re_insurance_company', '=', False)], required=False)
    phone = fields.Char(related='policy_provider_cmp_id.phone', string="Phone", translate=True)
    street = fields.Char(related="policy_provider_cmp_id.street", string="Street", translate=True)
    street2 = fields.Char(related="policy_provider_cmp_id.street2", string="Street 2", translate=True)
    city = fields.Char(related="policy_provider_cmp_id.city", string="City", translate=True)
    state_id = fields.Many2one(related="policy_provider_cmp_id.state_id", string="State")
    country_id = fields.Many2one(related="policy_provider_cmp_id.country_id", string="Country")
    zip = fields.Char(related="policy_provider_cmp_id.zip", string="Zip")
    sum_assured = fields.Monetary(string="Sum Insured")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related="company_id.currency_id")
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env.company)
    policy_descriptions = fields.Text(string="Policy Description")

    policy_price_list_ids = fields.One2many(comodel_name='policy.price.list',
                                            inverse_name='insurance_policy_id',
                                            string="Policy Price list")
    policy_service_ids = fields.One2many('policy.services', 'insurance_policy_id', string="Policy Services")
    family_member_ids = fields.One2many('family.member.insurance', 'insurance_policy_id', string="Family Members")



    # Life Insurance:
    desired_death_amount = fields.Monetary(string="Death Amount")
    life_deductible_amount = fields.Monetary()
    length_of_coverage_term = fields.Text(string="Length of Coverage Terms", translate=True)
    life_health_history = fields.Text(string="Insured Health History", translate=True)
    occupation_and_hobbies = fields.Text(string="Occupation and Hobbies", translate=True)
    family_medical_history = fields.Text(string="Family Medical History", translate=True)

    # Health Insurance:
    desired_coverage_type = fields.Selection([
        ('individual', "Individual"),
        ('family', "Family"),
        ('group', "Group")])
    health_deductible_amount = fields.Monetary()
    out_of_pocket_maximum = fields.Text(string="Out-of-Pocket Maximum", translate=True)
    health_history_of_insured = fields.Text(translate=True)
    drug_coverage = fields.Text(string="Prescription Drug Coverage", translate=True)
    healthcare_provider_network = fields.Text(string="Preferred Healthcare Provider Network",
                                              translate=True)

    # Property Insurance:
    property_type = fields.Char(string="Property Type")
    property_usage = fields.Text(string="Usage")
    area_sq_ft = fields.Char(string="Area(Sq Ft)")
    construct_year = fields.Integer(string="Construct Year")
    property_value = fields.Monetary()
    property_damage_coverage = fields.Monetary(string="Damage Coverage")
    property_coverage_limits = fields.Text(string="Property Coverage Limits", translate=True)
    construction_type_and_materials = fields.Text(string="Construction Type and Materials",
                                                  translate=True)
    special_features_of_the_property = fields.Text(string="Special Features of the Property",
                                                   translate=True)
    personal_property_inventory = fields.Text(string="Personal Property Inventory", translate=True)

    # Liability Insurance:
    type_of_liability_risk = fields.Selection(
        [('auto', "Auto"),
         ('homeowner', "HomeOwner's"),
         ('business', "Business")], string="Liability Risk")
    liability_coverage_type = fields.Selection(
        [('general_liability', "General Liability"),
         ('professional_liability', "Professional Liability")])
    desired_coverage_limits = fields.Text(string="Desired Coverage Limits", translate=True)
    business_type_and_operations = fields.Text(translate=True)

    # Disability Insurance:
    income = fields.Monetary(string="Income")
    disability_deductible_amount = fields.Monetary()
    length_coverage_disability_period = fields.Text(string="Length of Coverage Period",
                                                    translate=True)
    disability_health_history = fields.Text(translate=True)
    occupation_and_hobbies = fields.Text(string="Occupation and Hobbies", translate=True)

    # Travel Insurance:
    types_of_coverage = fields.Selection(
        [('trip_cancellation', "Trip Cancellation"),
         ('medical_emergency', "Medical Emergency"),
         ('lost_luggage', "Lost Luggage")],
        string="Type of Coverage")
    trip_coverage_amount = fields.Monetary(string="Coverage Amount")
    travel_purpose = fields.Text(string="Travel Purpose")
    traveler_health_history = fields.Text(string="Traveler Health History", translate=True)

    # Pet Insurance:
    pet_desired_coverage_type = fields.Selection(
        [('accident', "Accident"),
         ('illness', "Illness"),
         ('comprehensive', "Comprehensive")],
        string="Coverage Type ")
    exclusions = fields.Selection(
        [('pre_existing_conditions', "Pre-Existing Conditions"),
         ('certain_breeds', "Certain Breeds")],
        string="Exclusions")
    accident_coverage = fields.Monetary(string="Accident Amount")
    illness_coverage = fields.Monetary(string="Illness Amount")
    pet_health_history = fields.Text(string="Health History")
    pet_coverage_limits = fields.Text(string="Coverage Limits", translate=True)

    # Business Insurance:
    business_desired_coverage_type = fields.Selection(
        [('property_damage', "Property Damage"),
         ('liability', "Liability"),
         ('workers', "Workers Compensation")])
    business_property_value = fields.Monetary()
    business_type_operation = fields.Text(translate=True)
    business_coverage_limits = fields.Text(string="Business Coverage Limits", translate=True)
    industry_specific_risks = fields.Text(string=" Industry-Specific Risks", translate=True)

    # Vehicle Insurance:
    coverage_type = fields.Selection(
        [('liability', "Liability"),
         ('collision', "Collision"),
         ('comprehensive', "Comprehensive")])
    driving_history = fields.Text(string="Driving History of the Insured", translate=True)
    limitation_as_to_use = fields.Text(string="Limitation as to Use", translate=True)
    limits_of_liability = fields.Text(string="Limits of Liability", translate=True)
    deductibles_under_section = fields.Text(string="Deductibles under Section", translate=True)
    special_conditions = fields.Text(string="Special Conditions", translate=True)

    @api.constrains('desired_coverage_type')
    def _check_desired_coverage_type(self):
        """Check desired coverage type"""
        for record in self:
            if record.category == 'health':
                if not record.desired_coverage_type:
                    raise ValidationError(_("Select coverage type like: individual, family, group"))

    @api.constrains('trip_start_date', 'trip_end_date')
    def _check_trip_period(self):
        """Check trip period"""
        for record in self:
            if record.category == 'travel':
                if record.trip_end_date and record.trip_start_date:
                    if record.trip_end_date < record.trip_start_date:
                        raise ValidationError(_(
                            "Please ensure the trip end date is greater than the trip start date"))

    @api.constrains('policy_price_list_ids')
    def _check_policy_price_lists(self):
        """Policy price list"""
        for record in self:
            if not record.policy_price_list_ids:
                raise ValidationError(_("Add information to policy price list tab"))

    @api.constrains('sum_assured')
    def _check_sum_assured_amount(self):
        """Check that the sum assured is greater than zero."""
        for record in self:
            if record.sum_assured <= 0:
                raise ValidationError(_("The Sum Insured amount must be greater than zero."))

    @api.onchange('insurance_category_id')
    def _onchange_insurance_policy(self):
        """Onchange insurance policy"""
        for rec in self:
            # Reset insurance_sub_category_id to False
            rec.insurance_sub_category_id = False
            category = rec.insurance_category_id
            # Life Insurance:
            rec.length_of_coverage_term = category.length_of_coverage_term
            rec.life_health_history = category.life_health_history
            rec.occupation_and_hobbies = category.occupation_and_hobbies
            rec.family_medical_history = category.family_medical_history
            # Health Insurance:
            rec.out_of_pocket_maximum = category.out_of_pocket_maximum
            rec.health_history_of_insured = category.health_history_of_insured
            rec.drug_coverage = category.drug_coverage
            rec.healthcare_provider_network = category.healthcare_provider_network
            # Property Insurance:
            rec.property_coverage_limits = category.property_coverage_limits
            rec.construction_type_and_materials = category.construction_type_and_materials
            rec.special_features_of_the_property = category.special_features_of_the_property
            rec.personal_property_inventory = category.personal_property_inventory
            # Liability Insurance:
            rec.desired_coverage_limits = category.desired_coverage_limits
            rec.business_type_and_operations = category.business_type_and_operations
            # Disability Insurance:
            rec.length_coverage_disability_period = category.length_coverage_disability_period
            rec.disability_health_history = category.disability_health_history
            rec.occupation_and_hobbies = category.occupation_and_hobbies
            # Travel Insurance:
            rec.travel_purpose = category.travel_purpose
            rec.traveler_health_history = category.traveler_health_history
            # Pet Insurance:
            rec.pet_health_history = category.pet_health_history
            rec.pet_coverage_limits = category.pet_coverage_limits
            # Business Insurance:
            rec.business_type_operation = category.business_type_operation
            rec.business_coverage_limits = category.business_coverage_limits
            rec.industry_specific_risks = category.industry_specific_risks
            # Vehicle Insurance:
            rec.driving_history = category.driving_history
            rec.limitation_as_to_use = category.limitation_as_to_use
            rec.limits_of_liability = category.limits_of_liability
            rec.deductibles_under_section = category.deductibles_under_section
            rec.special_conditions = category.special_conditions

    # DEPRECATED
    life_insured_age = fields.Selection(
        [('five_to_twenty', "Between 5 to 20 Years"),
         ('twenty_to_fifty', "Between 20 to 50 Years"),
         ('fifty_to_seventy', "Between 50 to 70 Years"),
         ('above_seventy', "Above 70 Years")])
    health_insured_age = fields.Selection(
        [('five_to_twenty', "Between 5 to 20 Years"),
         ('twenty_to_fifty', "Between 20 to 50 Years"),
         ('fifty_to_seventy', "Between 50 to 70 Years"),
         ('above_seventy', "Above 70 Years")])
    business_name = fields.Char()
    travel_source = fields.Char()
    travel_destination = fields.Char()
    trip_start_date = fields.Date()
    trip_end_date = fields.Date()
    pet_name = fields.Char()
    breed_type = fields.Char()
    property_insurance_image_ids = fields.One2many(comodel_name='property.insurance.image',
                                                   inverse_name='insurance_policy_id')
    vehicle_insurance_image_ids = fields.One2many(comodel_name='vehicle.insurance.image',
                                                  inverse_name='insurance_policy_id')
    policy_provider_id = fields.Many2one('res.company', string="Company (legacy)")

    @api.ondelete(at_uninstall=False)
    def _unlink_service_record(self):
        """Prevent deletion if record is linked to insurances"""
        for record in self:
            insurance = self.env['insurance.information'].search(domain=[('insurance_policy_id', '=', record.id)],
                                                                 limit=1)
            if insurance:
                raise ValidationError(_('You cannot delete policy because it is linked to insurance.'))

class PolicyServices(models.Model):
    _name = 'policy.services'
    _description = __doc__
    _rec_name = 'product_service_id'

    product_service_id = fields.Many2one('product.template', string="Service", domain=[('type', '=', 'service')])
    service_ceiling = fields.Float(string="Service Ceiling", readonly=False)
    insurance_policy_id = fields.Many2one('insurance.policy')

class FamilyMemberAmounts(models.Model):
    _name = 'family.member.insurance'
    _description = __doc__
    _rec_name = 'relation_type'

    relation_type = fields.Selection([('spouse','Spouse'),('wife','Wife'),('husband','Husband'),('son','Son'),('daughter','Daughter'),('father','Father'),('mother','Mother')],string="Family Member")
    insurance_amount = fields.Float(string="Insurance Amount", readonly=False)
    insurance_policy_id = fields.Many2one('insurance.policy')


