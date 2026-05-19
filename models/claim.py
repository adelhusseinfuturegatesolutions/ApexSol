# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import secrets
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from ..utils import _display_notification
from odoo.exceptions import ValidationError


class ClaimImage(models.Model):
    """Claim Image"""
    _name = 'claim.image'
    _description = __doc__
    _rec_name = 'name'

    avatar = fields.Binary(string="Image")
    name = fields.Char(string="Name", translate=True, size=36)
    claim_information_id = fields.Many2one('claim.information', ondelete='cascade')


class ClaimInformation(models.Model):
    """Claim Information"""
    _name = "claim.information"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = __doc__
    _rec_name = 'claim_number'

    claim_number = fields.Char(string='Claim', required=True, readonly=True,
                               default=lambda self: _('New'), copy=False)
    insurance_id = fields.Many2one('insurance.information', string="Insurance",
                                   ondelete='cascade', domain="[('state', '=', 'running')]")
    nominee_id = fields.Char(string="ID", related='insurance_nominee_id.nominee_id')

    claim_date = fields.Date(string='Date')

    policy_holder_id = fields.Many2one('res.partner', string="Policy Holder")
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

    insured_id = fields.Many2one('res.partner', string='Insured')
    dob = fields.Date()
    age = fields.Char(string="Age", compute="_compute_insured_age_count", translate=True)
    gender = fields.Selection([
        ('male', "Male"),
        ('female', "Female"),
        ('others', "Others")], string="Gender")
    marital_status = fields.Selection([
        ('single', "Single"),
        ('married', "Married"),
        ('divorced', "Divorced"),
        ('widowed', "Widowed"),
        ('separated', "Separated"),
        ('annulled', "Annulled"),
        ('domestic', "Domestic Partnership/Civil Union"),
        ('common', "Common-Law Marriage"),
        ('other', "Other")], string="Marital Status")
    blood_group = fields.Selection(
        [('a_positive', "A+"),
         ('a_negative', "A-"),
         ('b_positive', "B+"),
         ('b_negative', "B-"),
         ('ab_positive', "AB+"),
         ('ab_negative', "AB-"),
         ('o_positive', "O+"),
         ('o_negative', "O-")], string="Blood Group")
    insured_height = fields.Char(string="Height(cm)")
    insured_weight = fields.Char(string="Weight(kg)")
    insured_birthmark = fields.Char(string="Birthmark")

    insurance_policy_id = fields.Many2one(
        'insurance.policy', string='Insurance Policy',
        domain="[('insurance_sub_category_id', '=', insurance_sub_category_id)]")
    policy_price_list_id = fields.Many2one(
        'policy.price.list', string="Policy Time Period",
        domain="[('insurance_policy_id', '=', insurance_policy_id)]")
    policy_durations = fields.Integer(related='policy_price_list_id.duration',
                                      string="Duration (Months)")

    insurance_category_id = fields.Many2one('insurance.category', string="Policy Category")
    category = fields.Selection(related="insurance_category_id.category")
    insurance_sub_category_id = fields.Many2one(
        'insurance.sub.category', string="Sub Category",
        domain="[('insurance_category_id', '=', insurance_category_id)]")

    desired_coverage_type = fields.Selection(related='insurance_id.desired_coverage_type',
                                             string="Coverage Type")

    agent_required = fields.Boolean(string="Agent Required")
    agent_id = fields.Many2one('res.partner', string='Agent', domain=[('is_agent', '=', True)])
    policy_amount = fields.Monetary(string="Policy Amount")
    amount_paid = fields.Monetary(string="Claim Amount",compute="_compute_total_amount", store=True)
    due_amount = fields.Monetary(string="Remaining Amount")

    policy_provider_cmp_id = fields.Many2one('res.partner', string='Service Provider',
                                             domain=[('is_company', '=', True),
                                                     ('is_service_provider', '=', True)])
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company,
                                 string="Company")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related="company_id.currency_id")
    policy_terms_and_conditions = fields.Text(string="Terms & Conditions", translate=True)

    invoice_id = fields.Many2one('account.move', string="Claim Bill")

    claim_documents_ids = fields.One2many(comodel_name='claim.documents',
                                          inverse_name='claim_information_id',
                                          string="Claim Documents")
    claim_reasons_ids = fields.Many2many('claim.reasons', string="Claim Reasons")

    claim_nominee_ids = fields.One2many(comodel_name='insurance.nominee',
                                        inverse_name='claim_information_id',
                                        string="Insurance Nominee")
    claim_insured_details_ids = fields.One2many(comodel_name='insured.details',
                                                inverse_name='claim_information_id',
                                                string="Insured Details")
    claim_image_ids = fields.One2many(comodel_name='claim.image',
                                      inverse_name='claim_information_id',
                                      string="Claim Images")

    responsible_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user, string="Manager",
        domain=lambda self: [('all_group_ids', 'in', [self.env.ref('base.group_user').id])])
    total_due_amount = fields.Monetary(related='insurance_id.total_due_amount', string="Due Amount")

    claim_fee_amount = fields.Monetary(string="Claim Fee Charges")
    fee_invoice_id = fields.Many2one('account.move', string="Claim Fee Invoice")
    fee_status = fields.Selection(related='fee_invoice_id.payment_state', string=" Status")

    is_reinsurance_required = fields.Boolean(string="Reinsurance Required")
    re_insurance_id = fields.Many2one('re.insurance', string="ReInsurance")
    reinsurance_company_id = fields.Many2one('res.partner', string='ReInsurance Company',
                                             domain=[('is_company', '=', True),
                                                     ('is_re_insurance_company', '=', True)])
    ceding_company_pays = fields.Monetary()
    reinsurer_pays = fields.Monetary()
    claim_bills = fields.Integer(compute='_compute_claim_bill')
    reinsurer_invoice_id = fields.Many2one('account.move', string="Reinsurer Bill")

    state = fields.Selection(
        [('draft', "New"),
         ('submit', "Registered"),
         ('document_submitted', "Document Submitted"),
         ('under_review', "Under Review"),
         ('approved', "Approved"),
         ('not_approved', "Rejected"),
         ('settled', "Settled"),
         ('closed', "Closed"),
         ], string="Status", default='draft')

    # DEPRECATED
    your_nominee_is_your = fields.Selection([
        ('grand_daughter', "Grand Daughter"),
        ('grand_mother', "Grand Mother"),
        ('niece', "Niece"),
        ('sister', "Sister"),
        ('aunt', "Aunt"),
        ('daughter', "Daughter"),
        ('mother', "Mother")],
        string=" Your Nominee is Your")
    maturity_of_the_policy = fields.Boolean(string="Maturity of the Policy")
    surrender_of_the_policy = fields.Boolean(string="Surrender of the Policy")
    discounted_value_in_policy = fields.Boolean(string="Discounted Value in Policy")
    death_of_the_insured = fields.Boolean(string="Death of the Insured")
    paid_up_of_lapsed_policy = fields.Boolean(string="Paid up of Lapsed Policy")
    other = fields.Boolean(string="Other")
    furnish_date_of_death = fields.Date(string="Date of Death")
    insurance_time_period = fields.Char(string=" Policy Time Period", translate=True)
    insurance_nominee_id = fields.Many2one('insurance.nominee', string="Nominee")

    @api.constrains('insurance_nominee_id')
    def _check_nominee_active(self):
        for rec in self:
            nominee = rec.insurance_nominee_id.sudo().with_context(active_test=False)
            if nominee and not nominee.active:
                raise ValidationError(_(
                    "Nominee '%s' is inactive. Claims cannot be created for an inactive nominee.",
                    nominee.name))
    insurance_nominee_relation_id = fields.Many2one('insurance.nominee.relation',
                                                    string="Your Nominee is Your")
    nominee_dob = fields.Date()
    payment_status = fields.Selection(related='invoice_id.payment_state', string="Payment Status")
    access_token = fields.Char()
    claim_service_ids = fields.One2many('claim.services', 'claim_information_id', string="Services")
    claim_service_ceiling_ids = fields.One2many('claim.services.ceiling', 'claim_information_id', string="Services")

    allowed_service_ids = fields.Many2many('product.template', compute='_compute_allowed_services')

    @api.depends('insurance_policy_id.policy_service_ids.product_service_id')
    def _compute_allowed_services(self):
        for record in self:
            # Collect all product_service_id IDs from the policy
            services = record.insurance_policy_id.policy_service_ids.mapped('product_service_id')
            record.allowed_service_ids = services

    @api.model_create_multi
    def create(self, vals_list):
        """Create claim record"""
        records = super().create(vals_list)
        for record in records:
            if record.claim_number == _('New'):
                record.claim_number = self.env['ir.sequence'].next_by_code(
                    'claim.information') or _('New')
            # Generate a URL-safe access token without underscores
            token = secrets.token_urlsafe(12).replace('_', '-')
            record.access_token = token
        return records

    @api.depends('claim_service_ids.service_price', 'claim_service_ceiling_ids.service_price')
    def _compute_total_amount(self):
        for rec in self:
            # 1. Sum service_price from the first One2many
            total_services = sum(rec.claim_service_ids.mapped('service_price'))
            
            # 2. Sum service_price from the second One2many (ceiling lines)
            total_ceilings = sum(rec.claim_service_ceiling_ids.mapped('provider_service_amount'))
            
            # 3. Combine both for the final paid amount
            rec.amount_paid = total_services + total_ceilings


    def draft_to_submit(self):
        """Draft to submit"""
        self.state = 'submit'

    def submit_to_document_submitted(self):
        """Submit to document submitted"""
        if not self.claim_documents_ids:
            for rec in self.insurance_policy_id.claim_document_type_ids:
                data = {
                    'claim_document_type_id': rec.id,
                    'claim_information_id': self.id,
                }
                self.env['claim.documents'].sudo().create(data)
        self.state = 'document_submitted'
        return True

    def document_submitted_to_under_review(self):
        """Document submitted to under review"""
        if not self.claim_documents_ids:
            message = _display_notification(
                message='Claim documents are required to proceed. Please upload them.',
                message_type='info')
            return message
        self.state = 'under_review'
        return True

    def under_review_to_approved(self):
        """Under review to approved"""
        documents_verified = all(rec.state == 'verified' for rec in self.claim_documents_ids)
        if not documents_verified:
            message = _display_notification(
                message='Please ensure the pending claim documents are verified.',
                message_type='info')
            return message
        self.state = 'approved'
        return True

    def approved_to_settled(self):
        """Approved to settled"""
        self.state = 'settled'

    def claim_reset_to_draft(self):
        """Claim reset to new"""
        for rec in self:
            if rec.claim_documents_ids:
                rec.claim_documents_ids.unlink()
            rec.claim_reasons_ids = False
            rec.state = 'draft'

    def settled_to_closed(self):
        """Settled to closed"""
        mail_template = self.env.ref(
            'tk_insurance_management.insurance_policy_approved_mail_template')
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)
        self.state = 'closed'

    def claim_not_approved(self):
        """Claim not approved"""
        self.state = 'not_approved'

    @api.depends('policy_holder_dob')
    def _compute_policy_holder_age_count(self):
        """Policyholder agg count"""
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

    @api.constrains('ceding_company_pays', 'reinsurer_pays', 'amount_paid')
    def _check_total_paid_amount(self):
        """Check total paid amount"""
        for record in self:
            total_paid = record.ceding_company_pays + record.reinsurer_pays
            if total_paid > record.amount_paid:
                raise ValidationError(
                    _("The sum of 'Ceding Company Pays' and 'Reinsurer Pays' must not be greater"
                      " than 'Claim Amount'."))

    @api.constrains('claim_date', 'insurance_id')
    def _check_claim_date(self):
        """Check claim date"""
        for rec in self:
            if rec.claim_date and rec.insurance_id:
                if (
                        rec.claim_date < rec.insurance_id.issue_date
                        or rec.claim_date > rec.insurance_id.expiry_date
                ):
                    raise ValidationError(
                        _("Claim date must be within the insurance coverage period!"))

    @api.constrains('furnish_date_of_death')
    def _check_furnish_date_of_death(self):
        """Check furnish date of death"""
        today = fields.Date.today()
        for record in self:
            if record.furnish_date_of_death:
                if record.furnish_date_of_death > today:
                    raise ValidationError(_("Date of death cannot exceed current date"))

    @api.constrains('state', 'amount_paid', 'is_reinsurance_required', 'ceding_company_pays',
                    'reinsurer_pays', 'claim_fee_amount')
    def _validate_claim_non_positive_values(self):
        """Validate claim non positive values"""
        for record in self:
            if record.state != 'draft':
                if record.amount_paid <= 0:
                    raise ValidationError(_("Claim amount must be greater than zero."))
                if record.amount_paid > record.due_amount:
                    raise ValidationError(_("Claim amount cannot exceed the Due Amount."))

                if record.is_reinsurance_required:
                    if record.ceding_company_pays <= 0:
                        raise ValidationError(_("Ceding company pays must be greater than zero."))
                    if record.reinsurer_pays <= 0:
                        raise ValidationError(_("Reinsurer pays must be greater than zero."))

                # if record.claim_fee_amount <= 0 or record.claim_fee_amount > record.amount_paid:
                #     raise ValidationError(
                #         _("Claim fee amount must be greater than zero and not exceed the claim amount."))

    @api.depends('dob')
    def _compute_insured_age_count(self):
        """Insured age count"""
        today = fields.Date.today()
        for rec in self:
            if rec.dob:
                if rec.dob > today:
                    raise ValidationError(_("DOB should be earlier than today's date."))
                age = today.year - rec.dob.year - (
                        (today.month, today.day) < (rec.dob.month, rec.dob.day))
                rec.age = str(max(age, 0)) + ' Years'
            else:
                rec.age = str(0) + ' Years'

    def create_ceding_company_bill(self):
        """Create a bill for the ceding company."""
        for record in self:
            # Validate claim amount
            if not record.amount_paid:
                message = _display_notification(
                    message='Please enter a valid claim amount.',
                    message_type='info')
                return message
            # Determine payable amount
            if record.is_reinsurance_required:
                if not record.ceding_company_pays:
                    message = _display_notification(
                        message='Please enter the amount paid by the ceding company.',
                        message_type='info')
                    return message
                amount = record.ceding_company_pays
            else:
                if record.amount_paid > record.total_due_amount:
                    message = _display_notification(
                        message='The claim amount cannot be greater than the total due. Please'
                                ' correct it.',
                        message_type='warning')
                    return message
                amount = record.amount_paid
            # Prepare invoice line
            invoice_lines = [(0, 0, {
                'name': 'Claim Amount Paid by Ceding Company',
                'quantity': 1,
                'price_unit': amount,
                'tax_ids': False,
            })]
            # Prepare invoice values
            invoice_vals = {
                'partner_id': record.policy_provider_cmp_id.id,
                'move_type': 'in_invoice',
                'invoice_date': fields.Datetime.now(),
                'invoice_line_ids': invoice_lines,
                'claim_information_id': record.id,
            }
            # Create invoice
            invoice = self.env['account.move'].sudo().create(invoice_vals)
            record.invoice_id = invoice.id
            # Return invoice form view
            return {
                'type': 'ir.actions.act_window',
                'name': 'Ceding Claim Bill',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return True

    def create_reinsurance_company_bill(self):
        """Create a bill for the reinsurance company."""
        for record in self:
            # Validate claim amount
            if not record.amount_paid:
                message = _display_notification(
                    message='Please enter a valid claim amount.',
                    message_type='info')
                return message
            if not record.reinsurer_pays:
                message = _display_notification(
                    message='Please enter the amount paid by the reinsurer.',
                    message_type='info')
                return message
            if record.reinsurer_pays > record.total_due_amount:
                message = _display_notification(
                    message='The amount paid by the reinsurer cannot exceed the due amount. Please'
                            ' enter a valid amount.',
                    message_type='warning')
                return message
            # Prepare invoice line
            invoice_lines = [(0, 0, {
                'name': 'Claim Amount Paid by Reinsurer',
                'quantity': 1,
                'price_unit': record.reinsurer_pays,
                'tax_ids': False,
            })]
            # Prepare invoice values
            invoice_vals = {
                'partner_id': record.reinsurance_company_id.id,
                'move_type': 'in_invoice',
                'invoice_date': fields.Datetime.now(),
                'invoice_line_ids': invoice_lines,
                'claim_information_id': record.id,
            }
            # Create invoice
            invoice = self.env['account.move'].sudo().create(invoice_vals)
            record.reinsurer_invoice_id = invoice.id
            # Return invoice form view
            return {
                'type': 'ir.actions.act_window',
                'name': 'Reinsurer Claim Bill',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return True

    def create_invoice_claim_fees(self):
        """Create settlement bill"""
        for record in self:
            if not record.claim_fee_amount:
                message = _display_notification(
                    message='Please add the claim fee charges',
                    message_type='info')
                return message
            claim_fee = {
                'name': 'Claim Fee Charges',
                'quantity': 1,
                'price_unit': record.claim_fee_amount,
                'tax_ids': False,
            }
            invoice_lines = [(0, 0, claim_fee)]
            data = {
                'partner_id': record.policy_holder_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Datetime.now(),
                'invoice_line_ids': invoice_lines,
                'claim_information_id': record.id
            }
            fee_invoice_id = self.env['account.move'].sudo().create(data)
            record.fee_invoice_id = fee_invoice_id.id
            return {
                'type': 'ir.actions.act_window',
                'name': 'Claim Fee Invoice',
                'res_model': 'account.move',
                'res_id': fee_invoice_id.id,
                'view_mode': 'form',
                'target': 'current'
            }
        return True

    def _compute_claim_bill(self):
        """Compute claim bills count"""
        for rec in self:
            rec.claim_bills = self.env['account.move'].search_count(
                [('claim_information_id', '=', rec.id), ('move_type', '=', 'in_invoice')])

    def view_insurance_claim_bills(self):
        """Insurance claim bills views"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Claim Bills'),
            'view_mode': 'list,form',
            'res_model': "account.move",
            'domain': [('claim_information_id', '=', self.id), ('move_type', '=', 'in_invoice')],
            'context': {
                'create': False
            }
        }

    def _get_report_base_filename(self):
        """Return the base filename for the generated claim report PDF."""
        return f"Claim Report - {self.claim_number}"

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
            'tk_insurance_management.claim_report_color_config', '#0a9396')
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
            if rec.state == 'approved':
                raise ValidationError(_('You cannot delete the approved claims.'))

    # DEPRECATED
    policy_provider_id = fields.Many2one('res.company', string="Company (legacy)")
    reinsurer_company_id = fields.Many2one('res.company', string=" Company (legacy)")


class ClaimServices(models.Model):
    _name = 'claim.services'
    _description = __doc__
    _rec_name = 'product_service_id'

    product_service_id = fields.Many2one('product.template', string="Service", domain=[('type', '=', 'service')])
    service_ceiling = fields.Float(string="Service Ceiling")
    service_price = fields.Float(string="Service Amount", readonly=False)
    remaining = fields.Float(string="Remaining", compute="_compute_remaining")
    claim_information_id = fields.Many2one('claim.information')

    @api.onchange('product_service_id')
    def _onchange_product_service_id(self):
        """ Fetch the ceiling from the Policy Line matching this service """
        if self.product_service_id and self.claim_information_id.insurance_policy_id:
            policy = self.claim_information_id.insurance_policy_id
            
            # Find the specific line that matches the selected service
            policy_line = policy.policy_service_ids.filtered(
                lambda l: l.product_service_id == self.product_service_id)
            
            if policy_line:
                # Set the ceiling from the first match found (take the first if multiple)
                self.service_ceiling = policy_line[0].service_ceiling
            else:
                self.service_ceiling = 0.0
        else:
            self.service_ceiling = 0.0

    @api.depends('service_ceiling','service_price')
    def _compute_remaining(self):
        for rec in self:
            rec.remaining = rec.service_ceiling - rec.service_price

    @api.constrains('service_ceiling', 'service_price')
    def _check_ceiling_amount(self):
        for record in self:
            if record.service_ceiling < record.service_price:
                raise ValidationError(_(
                    "Error! The 'Service Price ' (%s) cannot be greater than the 'Service Ceiling' (%s)."
                ) % (record.service_price, record.service_ceiling))

class ClaimServicesCeiling(models.Model):
    _name = 'claim.services.ceiling'
    _description = __doc__
    _rec_name = 'product_service_id'

    product_service_id = fields.Many2one('product.template', string="Service", domain=[('type', '=', 'service')])
    service_price = fields.Float(string="Service Amount", readonly=False)
    provider_service_amount = fields.Float(string="Service Amount By Provider")
    difference_amount = fields.Float(string="Difference Amount", compute="_compute_difference")
    claim_information_id = fields.Many2one('claim.information')

    @api.depends('provider_service_amount','service_price')
    def _compute_difference(self):
        for rec in self:
            rec.difference_amount = rec.service_price - rec.provider_service_amount

    # @api.constrains('provider_service_amount', 'service_price')
    # def _check_provider_amount(self):
    #     for record in self:
    #         if record.provider_service_amount > record.service_price:
    #             raise ValidationError(_(
    #                 "Error! The 'Service Amount By Provider' (%s) cannot be greater than the 'Service Price' (%s)."
    #             ) % (record.provider_service_amount, record.service_price))

    @api.onchange('product_service_id')
    def _onchange_product_service_id(self):
        """Fetch price from the Provider's Pricelist"""
        if self.product_service_id and self.claim_information_id.policy_provider_cmp_id:
            # 1. Get the Provider and their Pricelist
            provider = self.claim_information_id.policy_provider_cmp_id
            pricelist = provider.property_product_pricelist

            if pricelist:
                # 2. Get the first variant of the template (required for pricelist logic)
                product_variant = self.product_service_id.product_variant_id
                
                if product_variant:
                   
                    price = pricelist._get_product_price(
                        product_variant, 
                        quantity=1.0, 
                        partner=provider
                    )
                    self.service_price = price


class ServicesProvider(models.Model):
    _name = 'services.provider'
    _description = __doc__
    _rec_name = 'name'

    name = fields.Char(string="Service Provider")
    

