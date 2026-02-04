# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import secrets
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from ..utils import _display_notification


class InsuranceInformation(models.Model):
    """Insurance Information"""
    _name = 'insurance.information'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = __doc__
    _rec_name = 'insurance_number'

    insurance_number = fields.Char(string='Insurance Number', required=True, readonly=True,
                                   default=lambda self: _('New'), copy=False)
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
    policy_holder_age = fields.Char(compute="_compute_policy_holder_age_count", translate=True)
    policy_holder_gender = fields.Selection([
        ('male', "Male"),
        ('female', "Female"),
        ('others', "Others")],
        string=" Gender")

    insured_id = fields.Many2one('res.partner', string='Insured',
                                 domain="[('is_agent', '=', False)]")
    dob = fields.Date(string="Date Of Birth")
    age = fields.Char(string="Age", compute="_compute_insured_age_count", translate=True)
    gender = fields.Selection([
        ('male', "Male"),
        ('female', "Female"),
        ('others', "Others")],
        string="Gender")
    marital_status = fields.Selection([
        ('single', "Single"),
        ('married', "Married"),
        ('divorced', "Divorced"),
        ('widowed', "Widowed"),
        ('separated', "Separated"),
        ('annulled', "Annulled"),
        ('domestic', "Domestic Partnership/Civil Union"),
        ('common', "Common-Law Marriage"),
        ('other', "Other")],
        string="Marital Status")
    blood_group = fields.Selection(
        [('a_positive', "A+"),
         ('a_negative', "A-"),
         ('b_positive', "B+"),
         ('b_negative', "B-"),
         ('ab_positive', "AB+"),
         ('ab_negative', "AB-"),
         ('o_positive', "O+"),
         ('o_negative', "O-")],
        string="Blood Group")
    insured_height = fields.Char(string="Height(cm)")
    insured_weight = fields.Char(string="Weight(kg)")
    insured_birthmark = fields.Char(string="Birthmark")

    insured_details_ids = fields.One2many(comodel_name='insured.details',
                                          inverse_name='insurance_information_id',
                                          string="Insured Details")

    issue_date = fields.Date(string="Issue Date")
    expiry_date = fields.Date(string="Expiry Date", compute="_compute_time_period_date", store=True)

    agent_required = fields.Boolean(string="Agent Required")
    agent_id = fields.Many2one('res.partner', string='Agent', domain=[('is_agent', '=', True)])
    agent_phone = fields.Char(related='agent_id.phone', string="Phone")
    agent_email = fields.Char(related='agent_id.email', string="Email")

    premium_type = fields.Selection([
        ('fixed', "Fixed"),
        ('installment', "Installment")],
        default='installment',
        string="Premium Type")
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

    policy_price_list_id = fields.Many2one(
        'policy.price.list', string="Policy Time Period",
        domain="[('insurance_policy_id', '=', insurance_policy_id)]")
    policy_durations = fields.Integer(related='policy_price_list_id.duration',
                                      string="Duration (Months)")

    policy_terms_and_conditions = fields.Text(string="Terms & Conditions", translate=True)

    policy_amount = fields.Monetary(string="Policy Amount")
    commission_type = fields.Selection([
        ('fixed', "Fixed"),
        ('percentage', "Percentage")],
        string="Commission Type")
    fixed_commission = fields.Monetary(string="Fixed Amount")
    percentage_commission = fields.Float(string="Commission")
    total_commission = fields.Monetary(string="Total", compute="_compute_agent_commission")
    total_policy_amount = fields.Monetary(string="Total Policy Amount",
                                          compute="_compute_total_policy_amount")

    monthly_installment = fields.Monetary(string="Monthly Installment")
    policy_provider_cmp_id = fields.Many2one('res.partner', string='Policy Provider',
                                             domain=[('is_company', '=', True),
                                                     ('is_re_insurance_company', '=', False)])
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company,
                                 string="Company")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related="company_id.currency_id")

    invoice_id = fields.Many2one('account.move')
    payment_state = fields.Selection(related="invoice_id.payment_state", string="Invoice Status")
    agent_bill_id = fields.Many2one('account.move', string="Commission Bill")

    insurance_emi_ids = fields.One2many(comodel_name='insurance.emi',
                                        inverse_name='insurance_information_id')
    instalment_complete = fields.Boolean()

    insured_document_ids = fields.One2many(comodel_name="insured.documents",
                                           inverse_name='insured_info_id', string="Document")

    document_count = fields.Integer(compute='_compute_document_count')
    nominees_count = fields.Integer(compute='_compute_nominee_count')

    claim_count = fields.Integer(compute='_compute_claim_count')

    responsible_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user, string="Manager",
        domain=lambda self: [('all_group_ids', 'in', [self.env.ref('base.group_user').id])])

    state = fields.Selection(
        [('draft', "New"),
         ('confirmed', "Confirmed"),
         ('running', "Running"),
         ('expired', "Expired"),
         ('renew', "Renew"),
         ('cancel', "Cancelled")],
        default='draft', string="Status", group_expand='_expand_groups')

    # Life Insurance:
    life_insured_age = fields.Selection(
        [('five_to_twenty', "Between 5 to 20 Years"),
         ('twenty_to_fifty', "Between 20 to 50 Years"),
         ('fifty_to_seventy', "Between 50 to 70 Years"),
         ('above_seventy', "Above 70 Years"),
         ('below_five', "Invalid age")], string=" Insured Age")
    desired_death_amount = fields.Monetary(string="Death Amount")
    life_deductible_amount = fields.Monetary()
    is_smoking_status = fields.Selection([
        ('yes', "Yes"),
        ('no', "No")],
        string="Smoking Status", default='no')
    length_of_coverage_term = fields.Text(string="Length of Coverage Terms", translate=True)
    life_health_history = fields.Text(string="Insured Health History", translate=True)
    occupation_and_hobbies = fields.Text(string="Occupation and Hobbies Insured", translate=True)
    family_medical_history = fields.Text(string="Family Medical History", translate=True)

    # Health Insurance:
    health_insured_age = fields.Selection(
        [('five_to_twenty', "Between 5 to 20 Years"),
         ('twenty_to_fifty', "Between 20 to 50 Years"),
         ('fifty_to_seventy', "Between 50 to 70 Years"),
         ('above_seventy', "Above 70 Years"),
         ('below_five', "Invalid age")], string="Insured Age")
    desired_coverage_type = fields.Selection([
        ('individual', "Individual"),
        ('family', "Family"),
        ('group', "Group")])
    health_deductible_amount = fields.Monetary()
    copay_amount = fields.Monetary(string="Co-pay Amount")
    out_of_pocket_maximum = fields.Text(string="Out-of-Pocket Maximum", translate=True)
    health_history_of_insured = fields.Text(translate=True)
    drug_coverage = fields.Text(string="Prescription Drug Coverage", translate=True)
    healthcare_provider_network = fields.Text(string="Preferred Healthcare Provider Network",
                                              translate=True)

    # Property Insurance:
    property_type = fields.Char(string="Property Type")
    property_usage = fields.Text(string="Usage")
    area_sq_ft = fields.Char(string="Area(Sq Ft)")
    construct_year = fields.Char(string="Construct Year", translate=True)
    street = fields.Char(string="Street", translate=True)
    street2 = fields.Char(string="Street 2", translate=True)
    city = fields.Char(string="City", translate=True)
    country_id = fields.Many2one("res.country", string="Country")
    state_id = fields.Many2one("res.country.state", string="State",
                               domain="[('country_id', '=?', country_id)]")
    zip = fields.Char(string="Zip")
    property_value = fields.Monetary(string="Estimated Value")
    property_damage_coverage = fields.Monetary(string="Damage Coverage")
    property_deductible_amount = fields.Monetary()
    desired_coverage_types = fields.Selection(
        [('dwelling', "Dwelling"),
         ('personal_property', "Personal Property"),
         ('liability', "Liability"),
         ('additional_living_expenses', "Additional Living Expenses")])
    property_coverage_limits = fields.Text(string="Property Coverage Limits", translate=True)
    construction_type_and_materials = fields.Text(string="Construction Type and Materials",
                                                  translate=True)
    special_features_of_the_property = fields.Text(string="Special Features of the Property",
                                                   translate=True)
    personal_property_inventory = fields.Text(string="Personal Property Inventory", translate=True)
    property_insurance_image_ids = fields.One2many(comodel_name='property.insurance.image',
                                                   inverse_name='insurance_information_id')

    # Liability Insurance:
    type_of_liability_risk = fields.Selection(
        [('auto', "Auto"),
         ('homeowner', "HomeOwner's"),
         ('business', "Business")],
        string="Liability Risk")
    liability_coverage_type = fields.Selection(
        [('general_liability', "General Liability"),
         ('professional_liability', "Professional Liability")],
        default='general_liability')
    desired_coverage_limits = fields.Text(string="Desired Coverage Limits", translate=True)
    business_type_and_operations = fields.Text(translate=True)

    # Disability Insurance:
    occupation = fields.Char(string="Occupation", translate=True)
    income = fields.Monetary(string="Income")
    disability_desired_benefit_amount = fields.Monetary(string="Desired Amount")
    insured_is_smoking = fields.Boolean(string="Insured is Smoking")
    length_coverage_disability_period = fields.Text(string="Length of Coverage Period",
                                                    translate=True)
    disability_health_history = fields.Text(translate=True)
    occupation_and_hobbies = fields.Text(string="Occupation and Hobbies", translate=True)

    # Travel Insurance:
    types_of_coverage = fields.Selection(
        [('trip_cancellation', "Trip Cancellation"),
         ('medical_emergency', "Medical Emergency"),
         ('lost_luggage', "Lost Luggage")], string="Type of Coverage")
    travel_source = fields.Char(string="Source")
    travel_destination = fields.Char(string="Destination")
    travel_purpose = fields.Text(string="Travel Purpose")
    trip_start_date = fields.Date(string="Trip Start Date")
    trip_end_date = fields.Date(string="Trip End Date")
    trip_length = fields.Integer(string="Trip Length")
    trip_coverage_amount = fields.Monetary(string="Coverage Amount")
    odometer_unit = fields.Selection([
        ('km', 'Kilometers'),
        ('mi', 'Miles')],
        'Odometer Unit', default='km')
    traveler_health_history = fields.Text(string="Traveler Health History", translate=True)

    # Pet Insurance:
    pet_name = fields.Char(string="Pet Name")
    breed_type = fields.Char(string="Breed Type")
    pet_health_history = fields.Text(string="Health History")
    age_of_breed_of_the_pet = fields.Integer(string="Age of Breed")
    pet_desired_coverage_type = fields.Selection(
        [('accident', "Accident"),
         ('illness', "Illness"),
         ('comprehensive', "Comprehensive")])
    exclusions = fields.Selection([
        ('pre_existing_conditions', "Pre-Existing Conditions"),
        ('certain_breeds', "Certain Breeds")], string="Exclusions")

    accident_coverage = fields.Monetary(string="Accident Amount")
    illness_coverage = fields.Monetary(string="Illness Amount")
    pet_deductible_amount = fields.Monetary()
    pet_coverage_limits = fields.Text(string="Coverage Limits", translate=True)

    # Business Insurance:
    business_name = fields.Char(string="Business Name")
    business_desired_coverage_type = fields.Selection(
        [('property_damage', "Property Damage"),
         ('liability', "Liability"),
         ('workers', "Workers Compensation")])
    number_of_employees = fields.Integer(string="No. of Employees")
    business_property_value = fields.Monetary(string="Property Value")
    business_deductible_amount = fields.Monetary()
    business_type_operation = fields.Text(translate=True)
    business_coverage_limits = fields.Text(string="Business Coverage Limits", translate=True)
    industry_specific_risks = fields.Text(string=" Industry-Specific Risks", translate=True)

    # Vehicle Insurance:
    vehicle_name = fields.Char(string="Vehicle", translate=True)
    model = fields.Char(string="Model", translate=True)
    year = fields.Char(string="Year of MFG", translate=True)
    vin_no = fields.Char(string="VIN No", translate=True)
    reg_no = fields.Char(string="Registration No", translate=True)
    place_of_reg = fields.Char(string="Place of Registration", translate=True)
    cubic_capacity = fields.Integer(string="Cubic Capacity")
    setting_capacity = fields.Integer(string="Seating Capacity")
    usage_of_vehicle = fields.Selection([
        ('personal', "Personal"),
        ('commercial', "Commercial")],
        string="Usage of Vehicle")
    coverage_type = fields.Selection([
        ('liability', "Liability"),
        ('collision', "Collision"),
        ('comprehensive', "Comprehensive")])

    # Policy Details
    policy_certificate_no = fields.Char(string="Policy/Certificate No", translate=True)
    previous_policy_no = fields.Char(string="Previous Policy No", translate=True)

    # Vehicle IDV
    for_the_vehicle = fields.Monetary(string="For the Vehicle")
    for_trailer = fields.Monetary(string="For Trailer")
    non_electric_accessories = fields.Monetary(string="Non Electric Accessories")
    electric_accessories = fields.Monetary(string="Electric Accessories")
    value_of_cng_lpg_kit = fields.Monetary(string="Value of CNG/LPG Kit")
    total_idv = fields.Monetary(string="Total IDV Value")

    # Own Damage
    basic_od = fields.Monetary(string="Basic OD")
    od_package_premium = fields.Monetary()
    service_tax = fields.Monetary(string="Service Tax")
    special_discount = fields.Monetary(string="Special Discount (-)")
    final_premium = fields.Monetary(string="Final Premium")

    # Liability
    basic_tp_liability = fields.Monetary(string="Basic TP Liability")
    pa_cover_for_owner_driver = fields.Monetary(string="PA Cover for Owner-Driver")
    package_premium = fields.Monetary()
    liability_service_tax = fields.Monetary(string=" Service Tax")
    total_premium = fields.Monetary(string="Total Premium")

    limitation_as_to_use = fields.Text(string="Limitations as to Use", translate=True)
    limits_of_liability = fields.Text(string="Limits of Liability", translate=True)
    deductibles_under_section = fields.Text(string="Deductibles Under Section", translate=True)
    special_conditions = fields.Text(string="Special Conditions", translate=True)
    driving_history = fields.Text(string="Driving History of the Insured", translate=True)
    vehicle_insurance_image_ids = fields.One2many(comodel_name='vehicle.insurance.image',
                                                  inverse_name='insurance_information_id',
                                                  string="Images")

    total_due_amount = fields.Monetary(string="Due Amount", compute="_compute_insurance_due_amount")
    claim_amount = fields.Monetary(string="Claim Amount")

    previous_insurance_id = fields.Many2one('insurance.information', string="Previous Insurance")
    renew_insurance_id = fields.Many2one('insurance.information', string="Renew Insurance")
    renew_insurance_count = fields.Integer(default=1)
    policy_descriptions = fields.Text(string="Policy Description")
    insurance_nominee_ids = fields.One2many(comodel_name='insurance.nominee',
                                            inverse_name='insurance_information_id',
                                            string="Insurance Nominee")
    is_auto_cancellation = fields.Boolean(string='Auto Cancellation Policy',
                                          compute='_compute_is_auto_cancellation')
    insurance_expiry_days = fields.Integer(string='Expiry Days',
                                           compute='_compute_insurance_expiry_days')
    reminder_days = fields.Integer(string="Reminder Days for Installment",
                                   compute='_compute_reminder_days')
    cancellation_date = fields.Date(string="Cancellation Date")
    crm_lead_id = fields.Many2one('crm.lead', string="Lead")

    insurance_nominee_id = fields.Many2one('insurance.nominee', string="Nominee")
    insurance_nominee_relation_id = fields.Many2one('insurance.nominee.relation',
                                                    string="Your Nominee is Your")
    nominee_dob = fields.Date(string="Date of Birth")

    is_reinsurance_required = fields.Boolean(string="Reinsurance Required")
    re_insurance_id = fields.Many2one('re.insurance', string="ReInsurance")
    re_insurance_status = fields.Selection(related='re_insurance_id.status', string=" Status")
    access_token = fields.Char()
    renew_insurance_lead_id = fields.Many2one('crm.lead', string="Renew Request")

    policy_holder_signature = fields.Binary(string="Policy Holder Signature")
    authorized_signatory = fields.Binary(string="Authorized Signatory")
    declaration = fields.Html(string="Declaration")

    @api.model
    def _expand_groups(self, states, domain):
        return ['draft', 'confirmed', 'running', 'expired', 'renew', 'cancel']

    @api.model_create_multi
    def create(self, vals_list):
        """Create insurance record"""
        records = super().create(vals_list)
        for record in records:
            if record.insurance_number == _('New'):
                record.insurance_number = self.env['ir.sequence'].next_by_code(
                    'insurance.information') or _('New')
            # Custom document generation
            record.generate_insured_documents()
            # Generate a URL-safe access token without underscores
            token = secrets.token_urlsafe(12).replace('_', '-')
            record.access_token = token
        return records

    def write(self, vals):
        """Write insurance record"""
        res = super().write(vals)
        if 'insurance_policy_id' in vals:
            for record in self:
                record.generate_insured_documents()
        return res

    def generate_insured_documents(self):
        """Generate insured documents based on the policy's document types."""
        insured_documents = self.env['insured.documents'].sudo()
        for doc_type in self.insurance_policy_id.insured_document_type_ids:
            insured_documents.create({
                'insured_document_type_id': doc_type.id,
                'insured_id': self.policy_holder_id.id,
                'insured_info_id': self.id,
            })

    def draft_to_confirmed(self):
        """Change state from draft to confirmed after validating insurance documents."""
        if not self.insured_document_ids:
            message = _display_notification(
                message='Please attach insurance documents before confirming.',
                message_type='info')
            return message
        unverified_docs = self.insured_document_ids.filtered(lambda doc: doc.state != 'verified')
        if unverified_docs:
            message = _display_notification(
                message='All insurance documents must be verified before confirming.',
                message_type='warning')
            return message
        self.state = 'confirmed'
        return True

    def confirmed_to_running(self):
        """Confirmed to running"""
        invoice_created = True
        installment = 0
        for rec in self.insurance_emi_ids:
            if not rec.invoice_id and installment == 0:
                invoice_created = False
                break
            installment += 1
        if not invoice_created:
            message = _display_notification(
                message='Please create 1st Installment',
                message_type='info')
            return message
        self.state = 'running'
        return True

    @api.depends('is_auto_cancellation')
    def _compute_is_auto_cancellation(self):
        """Auto cancellation"""
        for record in self:
            is_auto_cancellation = self.env['ir.config_parameter'].sudo().get_param(
                'tk_insurance_management.is_auto_cancellation')
            record.is_auto_cancellation = is_auto_cancellation

    @api.depends('insurance_expiry_days')
    def _compute_insurance_expiry_days(self):
        """Count insurance expiry days"""
        for record in self:
            insurance_expiry_days = self.env['ir.config_parameter'].sudo().get_param(
                'tk_insurance_management.insurance_expiry_days')
            record.insurance_expiry_days = insurance_expiry_days

    @api.depends('reminder_days')
    def _compute_reminder_days(self):
        """Count reminder days"""
        for record in self:
            reminder_days = self.env['ir.config_parameter'].sudo().get_param(
                'tk_insurance_management.reminder_days')
            record.reminder_days = reminder_days

    def running_to_expired(self):
        """Running insurances to expired and send mail"""
        config = self.env['ir.config_parameter'].sudo()
        is_auto_cancellation = config.get_param('tk_insurance_management.is_auto_cancellation')
        insurance_expiry_days = int(
            config.get_param('tk_insurance_management.insurance_expiry_days'))
        insurances = self.search([('state', '=', 'running')])
        if is_auto_cancellation:
            for insurance in insurances:
                cancellation_date = insurance.expiry_date + relativedelta(
                    days=insurance_expiry_days + 1)
                insurance.write({
                    'cancellation_date': cancellation_date,
                })
        # Send mail
        mail_template = self.env.ref(
            'tk_insurance_management.insurance_policy_expired_mail_template',
            raise_if_not_found=False
        )
        if mail_template and insurances:
            mail_template.send_mail(self.id, force_send=True)
        self.state = 'expired'

    @api.model
    def action_create_expired_policy(self):
        """Cron: Move running insurance policies to expired state."""
        today_date = fields.Date.today()
        expired_policies = self.search([
            ('state', '=', 'running'),
            ('expiry_date', '<=', today_date)
        ])
        for rec in expired_policies:
            rec.running_to_expired()

    def expired_to_renew(self):
        """Expired to renew"""
        self.state = 'renew'

    def renew_to_cancel(self):
        """Renew to cancel"""
        self.state = 'cancel'

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
    def _onchange_policy_terms_and_condition(self):
        """Policy terms and condition"""
        for rec in self:
            policy = rec.insurance_policy_id
            if policy:
                rec.claim_amount = policy.sum_assured
                rec.policy_terms_and_conditions = policy.policy_terms_and_conditions
                rec.policy_descriptions = policy.policy_descriptions
                rec.policy_provider_cmp_id = policy.policy_provider_cmp_id.id
            else:
                rec.claim_amount = ''
                rec.policy_terms_and_conditions = ''
                rec.policy_amount = ''
                rec.policy_durations = ''
                rec.policy_descriptions = ''
                rec.policy_price_list_id = False
                rec.policy_provider_cmp_id = False
                rec.desired_coverage_type = False
                rec.insurance_buying_for_id = False
                self.insured_document_ids.sudo().unlink()

    @api.onchange('insurance_category_id')
    def onchange_policy_category(self):
        """Onchange policy category"""
        for rec in self:
            rec.insurance_sub_category_id = False
            rec.insurance_policy_id = False
            rec.insurance_buying_for_id = False
            rec.issue_date = False
            rec.policy_terms_and_conditions = False
            rec.desired_coverage_type = False

    @api.onchange('insurance_policy_id')
    def onchange_insurance_policy(self):
        """Onchange insurance policy details"""
        for rec in self:
            ins_policy = rec.insurance_policy_id
            # Life Insurance:
            rec.desired_death_amount = ins_policy.desired_death_amount
            rec.life_deductible_amount = ins_policy.life_deductible_amount
            rec.length_of_coverage_term = ins_policy.length_of_coverage_term
            rec.life_health_history = ins_policy.life_health_history
            rec.occupation_and_hobbies = ins_policy.occupation_and_hobbies
            rec.family_medical_history = ins_policy.family_medical_history
            # Health Insurance:
            rec.desired_coverage_type = ins_policy.desired_coverage_type
            rec.health_deductible_amount = ins_policy.health_deductible_amount
            rec.out_of_pocket_maximum = ins_policy.out_of_pocket_maximum
            rec.health_history_of_insured = ins_policy.health_history_of_insured
            rec.drug_coverage = ins_policy.drug_coverage
            rec.healthcare_provider_network = ins_policy.healthcare_provider_network
            # Property Insurance:
            rec.property_type = ins_policy.property_type
            rec.property_usage = ins_policy.property_usage
            rec.area_sq_ft = ins_policy.area_sq_ft
            rec.construct_year = ins_policy.construct_year
            rec.property_value = ins_policy.property_value
            rec.property_damage_coverage = ins_policy.property_damage_coverage
            rec.property_coverage_limits = ins_policy.property_coverage_limits
            rec.construction_type_and_materials = ins_policy.construction_type_and_materials
            rec.special_features_of_the_property = ins_policy.special_features_of_the_property
            rec.personal_property_inventory = ins_policy.personal_property_inventory
            # Liability Insurance:
            rec.liability_coverage_type = ins_policy.liability_coverage_type
            rec.type_of_liability_risk = ins_policy.type_of_liability_risk
            rec.desired_coverage_limits = ins_policy.desired_coverage_limits
            rec.business_type_and_operations = ins_policy.business_type_and_operations
            # Disability Insurance:
            rec.income = ins_policy.income
            rec.disability_desired_benefit_amount = ins_policy.disability_deductible_amount
            rec.length_coverage_disability_period = ins_policy.length_coverage_disability_period
            rec.disability_health_history = ins_policy.disability_health_history
            rec.occupation_and_hobbies = ins_policy.occupation_and_hobbies
            # Travel Insurance:
            rec.types_of_coverage = ins_policy.types_of_coverage
            rec.trip_coverage_amount = ins_policy.trip_coverage_amount
            rec.travel_purpose = ins_policy.travel_purpose
            rec.traveler_health_history = ins_policy.traveler_health_history
            # Pet Insurance:
            rec.pet_desired_coverage_type = ins_policy.pet_desired_coverage_type
            rec.accident_coverage = ins_policy.accident_coverage
            rec.exclusions = ins_policy.exclusions
            rec.illness_coverage = ins_policy.illness_coverage
            rec.pet_health_history = ins_policy.pet_health_history
            rec.pet_coverage_limits = ins_policy.pet_coverage_limits
            # Business Insurance:
            rec.business_desired_coverage_type = ins_policy.business_desired_coverage_type
            rec.business_property_value = ins_policy.business_property_value
            rec.business_type_operation = ins_policy.business_type_operation
            rec.business_coverage_limits = ins_policy.business_coverage_limits
            rec.industry_specific_risks = ins_policy.industry_specific_risks
            # Vehicle Insurance:
            rec.coverage_type = ins_policy.coverage_type
            rec.driving_history = ins_policy.driving_history
            rec.limitation_as_to_use = ins_policy.limitation_as_to_use
            rec.limits_of_liability = ins_policy.limits_of_liability
            rec.deductibles_under_section = ins_policy.deductibles_under_section
            rec.special_conditions = ins_policy.special_conditions

    @api.onchange('insurance_sub_category_id')
    def onchange_policy_sub_category(self):
        """Onchange policy sub category"""
        for rec in self:
            rec.insurance_policy_id = False

    @api.onchange('insurance_policy_id')
    def policy_desired_coverage_type(self):
        """Policy desired coverage type"""
        for rec in self:
            if rec.insurance_policy_id.category == "health":
                if rec.insurance_policy_id:
                    rec.desired_coverage_type = rec.insurance_policy_id.desired_coverage_type
                else:
                    rec.desired_coverage_type = ''

    @api.onchange('insurance_nominee_ids')
    def _insurance_nominee_percentage(self):
        """Insurance nominee percentage"""
        for record in self:
            total_percentage = sum(record.insurance_nominee_ids.mapped('percentage'))
            if total_percentage > 100:
                raise ValidationError(_("There are more nominees than permitted"))

    @api.onchange('for_the_vehicle', 'for_trailer', 'non_electric_accessories',
                  'electric_accessories', 'value_of_cng_lpg_kit')
    def _onchange_vehicle_idv_value(self):
        """Onchange vehicle idv value"""
        for rec in self:
            rec.total_idv = (
                    rec.for_the_vehicle +
                    rec.for_trailer +
                    rec.non_electric_accessories +
                    rec.electric_accessories +
                    rec.value_of_cng_lpg_kit
            )

    @api.onchange('basic_od', 'od_package_premium', 'service_tax', 'special_discount')
    def _onchange_own_damage_value(self):
        """Onchange own damage value"""
        for record in self:
            record.final_premium = (
                    record.basic_od +
                    record.od_package_premium +
                    record.service_tax -
                    record.special_discount
            )

    @api.onchange('basic_tp_liability', 'pa_cover_for_owner_driver', 'package_premium',
                  'liability_service_tax')
    def _onchange_liability_value(self):
        """Onchange liability value"""
        for value in self:
            value.total_premium = (
                    value.basic_tp_liability +
                    value.pa_cover_for_owner_driver +
                    value.package_premium +
                    value.liability_service_tax
            )

    @api.depends('policy_holder_dob')
    def _compute_policy_holder_age_count(self):
        """Compute policyholder age count"""
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

    @api.depends('dob')
    def _compute_insured_age_count(self):
        """Compute insured age count"""
        today = fields.Date.today()
        for rec in self:
            if rec.dob:
                dob = fields.Date.from_string(rec.dob)
                if dob > today:
                    raise ValidationError(_("DOB should be earlier than today's date."))
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                rec.age = f"{max(age, 0)} Years"
            else:
                rec.age = "0 Years"

    @api.onchange('age')
    def _onchange_agg_status(self):
        """Onchange age status"""
        for record in self:
            if record.age:
                age_numeric = int(''.join(filter(str.isdigit, str(record.age))))
                if 5 <= age_numeric < 20:
                    record.health_insured_age = 'five_to_twenty'
                elif 20 <= age_numeric < 50:
                    record.health_insured_age = 'twenty_to_fifty'
                elif 50 <= age_numeric < 70:
                    record.health_insured_age = 'fifty_to_seventy'
                elif age_numeric >= 70:
                    record.health_insured_age = 'above_seventy'
                else:
                    record.health_insured_age = 'below_five'
            else:
                record.health_insured_age = 'below_five'

    @api.constrains('issue_date')
    def _check_issue_date(self):
        """Check that the issue date is not before today"""
        today = fields.Date.today()
        for record in self:
            if record.issue_date and record.issue_date < today:
                raise ValidationError(_("The issue date cannot be earlier than today."))

    @api.constrains('state', 'policy_amount', 'desired_death_amount', 'fixed_commission',
                    'percentage_commission', 'health_deductible_amount', 'copay_amount',
                    'property_value', 'property_deductible_amount', 'income',
                    'disability_desired_benefit_amount', 'trip_length', 'trip_coverage_amount',
                    'age_of_breed_of_the_pet', 'pet_deductible_amount', 'business_property_value',
                    'number_of_employees', 'business_deductible_amount', 'cubic_capacity',
                    'setting_capacity', 'for_the_vehicle', 'for_trailer',
                    'non_electric_accessories', 'electric_accessories', 'value_of_cng_lpg_kit',
                    'total_idv', 'basic_od', 'od_package_premium', 'service_tax',
                    'special_discount', 'final_premium', 'basic_tp_liability',
                    'pa_cover_for_owner_driver', 'package_premium', 'liability_service_tax',
                    'total_premium', 'is_smoking_status', 'types_of_coverage',
                    'pet_desired_coverage_type', 'business_desired_coverage_type',
                    'type_of_liability_risk', 'trip_start_date', 'trip_end_date',
                    'agent_required', 'commission_type',
                    )
    def _validate_non_positive_values(self):
        """Validate non positive values"""
        for record in self:
            if record.state != 'draft':

                # Basic common fields
                if record.policy_amount <= 0:
                    raise ValidationError(_("The policy amount must be greater than zero."))

                # Agent details
                if record.agent_required:
                    if record.commission_type == 'fixed':
                        if record.fixed_commission <= 0:
                            raise ValidationError(
                                _("The fixed commission must be greater than zero."))
                    if record.commission_type == 'percentage':
                        if record.percentage_commission <= 0 or record.percentage_commission > 100:
                            raise ValidationError(_("The commission percentage must be between 0 and 100."))
                ins_category = record.insurance_category_id.category

                # Category : Life
                if ins_category == 'life':
                    if record.desired_death_amount <= 0:
                        raise ValidationError(_("The death amount must be greater than zero."))
                    if not record.is_smoking_status:
                        raise ValidationError(_("Select smoking status for safety information."))

                # Category : health
                elif ins_category == 'health':
                    if record.health_deductible_amount <= 0:
                        raise ValidationError(_("The deductible amount must be greater than zero."))
                    if record.copay_amount <= 0:
                        raise ValidationError(_("The co-pay amount must be greater than zero."))

                # Category : property
                elif ins_category == 'property':
                    if record.property_value <= 0:
                        raise ValidationError(_("The estimated value must be greater than zero."))
                    if record.property_deductible_amount <= 0:
                        raise ValidationError(_("The deductible amount must be greater than zero."))

                # Category : Disability
                elif ins_category == 'disability':
                    if record.income <= 0:
                        raise ValidationError(_("The income must be greater than zero."))
                    if record.disability_desired_benefit_amount <= 0:
                        raise ValidationError(_("The desired amount must be greater than zero."))

                # Category : Travel
                elif ins_category == 'travel':
                    if record.trip_length <= 0:
                        raise ValidationError(_("The trip length must be greater than zero."))
                    if record.trip_coverage_amount <= 0:
                        raise ValidationError(_("The coverage amount must be greater than zero."))
                    if not record.types_of_coverage:
                        raise ValidationError(_(
                            "Select coverage type: Trip Cancellation, Medical Emergency, or Lost"
                            " Luggage for accurate details"))
                    if record.trip_end_date and record.trip_start_date:
                        if record.trip_end_date < record.trip_start_date:
                            raise ValidationError(_(
                                "Please ensure the trip end date is greater than the trip start date"))

                # Category : Pet
                elif ins_category == 'pet':
                    if record.age_of_breed_of_the_pet <= 0:
                        raise ValidationError(_("The pet age must be greater than zero."))
                    if record.pet_deductible_amount <= 0:
                        raise ValidationError(_("The deductible amount must be greater than zero."))
                    if not record.pet_desired_coverage_type:
                        raise ValidationError(_(
                            "Select coverage type: Accident, Illness, or Comprehensive for accurate"
                            " details"))

                # Category : Business
                elif ins_category == 'business':
                    if record.business_property_value <= 0:
                        raise ValidationError(_("The property value must be greater than zero."))
                    if record.number_of_employees <= 0:
                        raise ValidationError(_("The no. of employees must be greater than zero."))
                    if record.business_deductible_amount <= 0:
                        raise ValidationError(_("The deductible amount must be greater than zero."))
                    if not record.business_desired_coverage_type:
                        raise ValidationError(_(
                            "Select coverage type: Property Damage, Liability, or Workers Compensation"
                            " for accurate details"))

                # Category : Liability
                elif ins_category == 'liability':
                    if not record.type_of_liability_risk:
                        raise ValidationError(_(
                            "Select liability risk: Auto, Homeowner's, Business. Important decision."))

                # Category : Vehicle
                elif ins_category == 'vehicle':
                    if record.cubic_capacity <= 0:
                        raise ValidationError(_("The cubic capacity must be greater than zero."))
                    if record.setting_capacity <= 0:
                        raise ValidationError(_("The setting capacity must be greater than zero."))
                    if record.for_the_vehicle <= 0:
                        raise ValidationError(
                            _("The for the vehicle value must be greater than zero."))
                    if record.for_trailer <= 0:
                        raise ValidationError(_("The for trailer value must be greater than zero."))
                    if record.non_electric_accessories <= 0:
                        raise ValidationError(
                            _("The non electric accessories value must be greater than zero."))
                    if record.electric_accessories <= 0:
                        raise ValidationError(
                            _("The electric accessories value must be greater than zero."))
                    if record.value_of_cng_lpg_kit <= 0:
                        raise ValidationError(
                            _("The value of cng/lpg kit must be greater than zero."))
                    if record.total_idv <= 0:
                        raise ValidationError(_("The total idv value must be greater than zero."))
                    if record.basic_od <= 0:
                        raise ValidationError(_("The basic od value must be greater than zero."))
                    if record.od_package_premium <= 0:
                        raise ValidationError(
                            _("The package premium value must be greater than zero."))
                    if record.service_tax <= 0:
                        raise ValidationError(_("The service tax value must be greater than zero."))
                    if record.special_discount <= 0:
                        raise ValidationError(
                            _("The special discount value must be greater than zero."))
                    if record.final_premium <= 0:
                        raise ValidationError(
                            _("The final premium value must be greater than zero."))
                    if record.basic_tp_liability <= 0:
                        raise ValidationError(
                            _("The basic tp liability value must be greater than zero."))
                    if record.pa_cover_for_owner_driver <= 0:
                        raise ValidationError(
                            _("The basic tp liability value must be greater than zero."))
                    if record.package_premium <= 0:
                        raise ValidationError(
                            _("The package premium value must be greater than zero."))
                    if record.liability_service_tax <= 0:
                        raise ValidationError(
                            _("The liability service tax value must be greater than zero."))
                    if record.total_premium <= 0:
                        raise ValidationError(
                            _("The total premium value must be greater than zero."))

    @api.depends('issue_date', 'policy_durations')
    def _compute_time_period_date(self):
        """Compute time period"""
        for rec in self:
            expiry_date = fields.Date.today()
            if rec.issue_date:
                expiry_date = rec.issue_date + relativedelta(months=rec.policy_durations)
            rec.expiry_date = expiry_date

    @api.onchange('policy_price_list_id')
    def onchange_insurance_policy_amount(self):
        """Onchange insurance policy amount"""
        for rec in self:
            if rec.policy_price_list_id:
                rec.policy_amount = rec.policy_price_list_id.policy_premium

    @api.onchange('total_policy_amount', 'policy_durations')
    def _onchange_total_monthly_installment_amount(self):
        """Total monthly installment amount"""
        for rec in self:
            if rec.policy_durations > 0:
                rec.monthly_installment = rec.total_policy_amount / rec.policy_durations

    @api.depends('commission_type', 'percentage_commission', 'policy_amount')
    def _compute_agent_commission(self):
        """Compute agent commission"""
        for rec in self:
            if rec.commission_type == "percentage":
                rec.total_commission = (rec.percentage_commission * rec.policy_amount) / 100
            else:
                rec.total_commission = 0.0

    @api.depends('total_policy_amount', 'commission_type', 'total_commission', 'policy_amount',
                 'fixed_commission')
    def _compute_total_policy_amount(self):
        """Compute total policy amount"""
        for rec in self:
            if rec.commission_type == "percentage":
                rec.total_policy_amount = rec.policy_amount + rec.total_commission
            else:
                rec.total_policy_amount = rec.policy_amount + rec.fixed_commission

    @api.depends('claim_amount')
    def _compute_insurance_due_amount(self):
        """Compute the remaining due amount after approved claims and payments."""
        for rec in self:
            total_paid = 0.0
            # All claims related to this insurance
            claims = self.env['claim.information'].sudo().search([('insurance_id', '=', rec.id)])
            for claim in claims:
                if claim.is_reinsurance_required:
                    if claim.ceding_company_pays and claim.invoice_id:
                        total_paid += claim.ceding_company_pays
                    if claim.reinsurer_pays and claim.reinsurer_invoice_id:
                        total_paid += claim.reinsurer_pays
                else:
                    if (claim.state != 'not_approved' and
                            claim.invoice_id and
                            claim.policy_amount and
                            claim.amount_paid):
                        total_paid += claim.amount_paid
            rec.total_due_amount = rec.claim_amount - total_paid

    def action_remaining_amount(self):
        """Running amount"""
        return True

    def action_create_agent_bill(self):
        """Create agent bill"""
        for rec in self:
            if not rec.commission_type:
                message = _display_notification(
                    message='Please first select the commission type.',
                    message_type='info')
                return message
            insurance = " ".join(ins.insurance_number for ins in rec)
            invoice_lines = []
            if rec.commission_type == 'fixed':
                if not rec.fixed_commission:
                    message = _display_notification(
                        message='Please add the required commission fixed value before proceeding!',
                        message_type='info')
                    return message
                fixed_commission = {
                    'product_id': self.env.ref('tk_insurance_management.agent_commission_bill').id,
                    'name': insurance,
                    'quantity': 1,
                    'price_unit': rec.fixed_commission,
                }
                invoice_lines = [(0, 0, fixed_commission)]
            elif rec.commission_type == 'percentage':
                if not rec.total_commission:
                    message = _display_notification(
                        message='Please add the required commission percentage value before'
                                ' proceeding!',
                        message_type='info')
                    return message
                percentage_commission = {
                    'product_id': self.env.ref('tk_insurance_management.agent_commission_bill').id,
                    'name': insurance,
                    'quantity': 1,
                    'price_unit': rec.total_commission,
                }
                invoice_lines = [(0, 0, percentage_commission)]
            data = {
                'partner_id': rec.agent_id.id,
                'move_type': 'in_invoice',
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': invoice_lines,
                'insurance_information_id': rec.id
            }
            agent_bill_id = self.env['account.move'].sudo().create(data)
            rec.agent_bill_id = agent_bill_id.id
            return {
                'type': 'ir.actions.act_window',
                'name': _('Commission Bill'),
                'res_model': 'account.move',
                'res_id': agent_bill_id.id,
                'view_mode': 'form',
                'target': 'current'
            }
        return True

    def _compute_document_count(self):
        """Document count"""
        for rec in self:
            rec.document_count = self.env['insured.documents'].search_count(
                [('insured_info_id', '=', rec.id)])
                
    def _compute_nominee_count(self):
        """Nominee count"""
        for rec in self:
            rec.nominees_count = self.env['insurance.nominee'].search_count(
                [('insurance_information_id', '=', rec.id)])

    def action_insured_document(self):
        """Insured document"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents'),
            'res_model': 'insured.documents',
            'domain': [('insured_info_id', '=', self.id)],
            'context': {
                'default_insured_info_id': self.id,
                'default_insured_id': self.policy_holder_id.id
            },
            'view_mode': 'list',
            'target': 'current',
        }
    def action_insured_nominee(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nominees'),
            'res_model': 'insured.documents',
            'domain': [('insurance_information_id', '=', self.id)],
            'context': {
                'default_insurance_information_id': self.id,
                'default_insurance_information_id': self.policy_holder_id.id
            },
            'view_mode': 'list',
            'target': 'current',
        }

    def _compute_claim_count(self):
        """Claim count"""
        for rec in self:
            rec.claim_count = self.env['claim.information'].search_count(
                [('insurance_id', '=', rec.id)])

    def action_insured_claim(self):
        """Insured claim"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Claims'),
            'res_model': 'claim.information',
            'domain': [('insurance_id', '=', self.id)],
            'context': {
                'default_insurance_id': self.id,
                'create': False
            },
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_renew_insurance_view(self):
        """Renew insurance"""
        return {
            'name': _('Renew'),
            'type': 'ir.actions.act_window',
            'res_model': 'insurance.information',
            'view_mode': 'form',
            'res_id': self.renew_insurance_id.id,
            'target': 'current',
        }

    def action_insurance_invoice(self):
        """Insurance invoice"""
        for rec in self:
            if not rec.claim_amount:
                raise ValidationError(_("Claim amount must be greater than zero."))
        insurance_invoice = {
            'product_id': self.env.ref('tk_insurance_management.insurance_invoice').id,
            'name': self.insurance_policy_id.policy_name,
            'quantity': 1,
            'price_unit': self.total_policy_amount,
        }
        invoice_lines = [(0, 0, insurance_invoice)]
        data = {
            'partner_id': self.policy_holder_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'insurance_information_id': self.id,
        }
        invoice_id = self.env['account.move'].sudo().create(data)
        self.write({'invoice_id': invoice_id.id})
        self.instalment_complete = True
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_emi_installment(self):
        """create emi installment"""
        for rec in self:
            if not rec.claim_amount or rec.claim_amount <= 0:
                raise ValidationError(_("Claim amount must be greater than zero."))
            if rec.issue_date:
                total_installment_amount = round(rec.total_policy_amount,
                                                 2)  # Round to 2 decimal places
                monthly_installment = round(total_installment_amount / rec.policy_durations,
                                            2)  # Calculate monthly installment
                # Adjust last installment to make sure the total sum equals the total policy amount
                last_installment_amount = round(
                    total_installment_amount - (monthly_installment * (rec.policy_durations - 1)),
                    2)
                for i in range(rec.policy_durations - 1):
                    installment_date = rec.issue_date + relativedelta(months=i)
                    data = {
                        'insurance_information_id': rec.id,
                        'name': f'Installment {i + 1}',
                        'installment_date': installment_date,
                        'installment_amount': monthly_installment,
                    }
                    self.env['insurance.emi'].create(data)
                # Create the last installment with the adjusted amount
                last_installment_date = rec.issue_date + relativedelta(
                    months=rec.policy_durations - 1)
                last_installment_data = {
                    'insurance_information_id': rec.id,
                    'name': f'Installment {rec.policy_durations}',
                    'installment_date': last_installment_date,
                    'installment_amount': last_installment_amount,
                }
                self.env['insurance.emi'].create(last_installment_data)
        self.instalment_complete = True

    @api.model
    def action_create_cancellation_policy(self):
        """Automatically cancel expired insurance policies and send notification."""
        today_date = fields.Date.today()
        config = self.env['ir.config_parameter'].sudo()
        # Get config parameters
        is_auto_cancellation = config.get_param('tk_insurance_management.is_auto_cancellation')
        insurance_expiry_days = int(
            config.get_param('tk_insurance_management.insurance_expiry_days'))
        if not is_auto_cancellation:
            return
        # Find all expired insurance records
        expired_insurances = self.search([('state', '=', 'expired')])
        for insurance in expired_insurances:
            # Calculate cancellation date + insurance expiry days
            cancellation_date = insurance.expiry_date + relativedelta(
                days=insurance_expiry_days + 1)
            if today_date == cancellation_date:
                # Send cancellation email
                template = self.env.ref(
                    'tk_insurance_management.insurance_policy_cancel_mail_template',
                    raise_if_not_found=False)
                if template:
                    template.send_mail(insurance.id, force_send=True)
                # Call the cancellation method
                insurance.renew_to_cancel()

    @api.model
    def action_create_insurance_invoice(self):
        """Create insurance invoices and send reminders before due date."""
        today = fields.Date.today()
        # Fetch reminder days from system config
        reminder_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'tk_insurance_management.reminder_days'))
        # Fetch insurance records with premium type 'Installment'
        insurances = self.search([('premium_type', '=', 'installment')])
        # Load mail template once outside the loop
        mail_template = self.env.ref(
            'tk_insurance_management.upcoming_invoice_installment_mail_template',
            raise_if_not_found=False)
        for insurance in insurances:
            for emi in insurance.insurance_emi_ids:
                if not emi.invoice_id:
                    # Calculate reminder date
                    reminder_date = emi.installment_date - relativedelta(days=reminder_days)
                    if reminder_date == today:
                        # Send reminder email
                        if mail_template:
                            mail_template.send_mail(insurance.id, force_send=True)
                        # Create invoice
                        emi.action_insurance_emi_invoice()

    def _get_report_base_filename(self):
        """Return the base filename for the generated insurance report PDF."""
        return f"Insurance Report - {self.insurance_number}"

    @staticmethod
    def lighten_color(hex_color, percentage=0.85):
        """Make Lighter color of selected color"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = int(r + (255 - r) * percentage)
        g = int(g + (255 - g) * percentage)
        b = int(b + (255 - b) * percentage)

        return f"#{r:02x}{g:02x}{b:02x}"

    def get_report_color(self):
        """Fetch the report color from system settings"""
        color = self.env['ir.config_parameter'].sudo().get_param(
            'tk_insurance_management.report_color_config', '#0a9396')
        return color

    def get_report_color_lighter(self):
        """Generate lighter shade based on the configured report color"""
        base_color = self.get_report_color()
        lighter_color = self.lighten_color(base_color)
        return lighter_color

    @api.ondelete(at_uninstall=False)
    def _prevent_unlink(self):
        """Unlink Method"""
        for rec in self:
            if rec.state == 'running':
                raise ValidationError(_('You cannot delete the running insurance.'))


class InsuranceEMI(models.Model):
    """Insurance EMI"""
    _name = 'insurance.emi'
    _description = __doc__
    _rec_name = 'name'

    name = fields.Char(translate=True)
    installment_date = fields.Date(string="Installment Date")
    installment_amount = fields.Monetary(string="Installment Amount")
    premium_type = fields.Selection(related="insurance_information_id.premium_type",
                                    string="Premium Type")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related="company_id.currency_id")
    insurance_information_id = fields.Many2one('insurance.information', ondelete='cascade')
    invoice_id = fields.Many2one('account.move')
    payment_state = fields.Selection(related="invoice_id.payment_state", string="Invoice Status")

    def action_insurance_emi_invoice(self):
        """Insurance emi invoice"""
        insurance_invoice = {
            'product_id': self.env.ref('tk_insurance_management.insurance_invoice').id,
            'name': self.name,
            'quantity': 1,
            'price_unit': self.installment_amount,
        }
        invoice_lines = [(0, 0, insurance_invoice)]
        data = {
            'partner_id': self.insurance_information_id.policy_holder_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'insurance_information_id': self.insurance_information_id.id,
        }
        invoice_id = self.env['account.move'].sudo().create(data)
        self.write({'invoice_id': invoice_id.id})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # DEPRECATED
    policy_provider_id = fields.Many2one('res.company', string="Company (legacy)")
