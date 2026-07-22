# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from ..utils import _display_notification


class ReInsuranceType(models.Model):
    """Re Insurance Type"""
    _name = 're.insurance.type'
    _description = __doc__
    _rec_name = 'name'

    name = fields.Char(string="Name", translate=True)


class ReInsuranceDocument(models.Model):
    """Re Insurance Documents"""
    _name = 're.insurance.document'
    _description = __doc__
    _rec_name = 'file_name'

    file_name = fields.Char(string="File Name", translate=True)
    avatar = fields.Binary(string="Document")
    description = fields.Char(string="Description", translate=True)
    re_insurance_id = fields.Many2one('re.insurance', ondelete='cascade')
    status = fields.Selection([
        ('draft', "Draft"),
        ('verified', "Verified"),
        ('rejected', "Rejected")],
        default='draft')

    def re_insurance_document_resubmit(self):
        """ReInsurance document resubmit"""
        self.status = 'draft'
        self.avatar = ''

    def verified_re_insurance_document(self):
        """Verified re insurance document"""
        if not self.avatar:
            raise ValidationError(_("Please upload the document, then proceed with verification."))
        self.status = 'verified'

    def rejected_re_insurance_document(self):
        """Rejected re insurance document"""
        self.status = 'rejected'

    def action_delete_document(self):
        """Deletes the current document record"""
        return self.unlink()


class ReInsurance(models.Model):
    """Re Insurance Details"""
    _name = 're.insurance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = __doc__
    _rec_name = 'sequence_number'

    sequence_number = fields.Char(readonly=True, default=lambda self: _('New'), copy=False)

    # Insurance Details
    insurance_id = fields.Many2one(
        'insurance.information', string="Insurance",
        domain=[('state', '=', 'running'), ('is_reinsurance_required', '=', True)])
    insurance_policy_id = fields.Many2one('insurance.policy', string='Insurance Policy')
    policy_number = fields.Char(string="Policy Number")
    contract_date = fields.Date(default=fields.Date.today())
    issue_date = fields.Date()
    expiry_date = fields.Date()
    policy_amount = fields.Monetary(
        help="Total premium amount received from the policyholder for the insured risk.")
    sum_assured = fields.Monetary(string="Sum Insured",
                                  help="Total amount covered under the insurance policy.")
    # Policy Provider (Ceding Company)
    policy_provider_cmp_id = fields.Many2one('res.partner', string='Policy Provider',
                                             domain=[('is_company', '=', True),
                                                     ('is_re_insurance_company', '=', False)])
    provider_phone = fields.Char(string="Phone")
    provider_email = fields.Char(string="Email")

    # Reinsurer Company Details
    re_insurance_type_id = fields.Many2one('re.insurance.type', string="ReInsurance Type")
    treaty_types = fields.Selection([
        ('quota_share', 'Quota Share'),
        ('surplus', 'Surplus'),
        ('excess_of_loss', 'Excess of Loss'),
        ('stop_loss', 'Stop Loss'),
        ('facultative_obligatory', 'Facultative Obligatory'),
        ('risk_attaching', 'Risk Attaching'),
        ('losses_occurring', 'Losses Occurring'),
        ('proportional', 'Proportional'),
        ('non_proportional', 'Non-Proportional'),
    ], string="Treaty Type")

    reinsurance_company_id = fields.Many2one('res.partner', string='ReInsurance Company',
                                             domain=[('is_company', '=', True),
                                                     ('is_re_insurance_company', '=', True)])
    r_phone = fields.Char(string=" Phone")
    r_email = fields.Char(string=" Email")

    # Financial Details
    retention_amount = fields.Monetary(help="Max amount the ceding company retains")
    reinsured_amount = fields.Monetary()
    reinsurance_premium = fields.Monetary()
    reinsurer_percentage = fields.Float(string="Reinsurer Share (%)")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related="company_id.currency_id")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company,
                                 string="Company")

    # Coverage
    territory = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()

    # Manager Details
    responsible_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user, string="Manager",
        domain=lambda self: [('all_group_ids', 'in', [self.env.ref('base.group_user').id])])

    # Signatures
    risk_description = fields.Html()
    exclusions = fields.Html()
    terms_and_conditions = fields.Html(translate=True)
    ceding_company_date = fields.Date(string="Ceding Company Sign Date")
    ceding_company_signature = fields.Binary()
    reinsurer_company_date = fields.Date(string="Reinsurance Company Sign Date")
    reinsurer_company_signature = fields.Binary()
    rejection_reason = fields.Html()

    # Status and Other Details
    document_count = fields.Integer(compute='_compute_document_count')
    re_insurance_document_ids = fields.One2many(comodel_name='re.insurance.document',
                                                inverse_name='re_insurance_id')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('active', 'Active'),
        ('running', 'Running'),
        ('expired', 'Expired'),
        ('reject', 'Rejected'),
    ], string='Status', default='draft')

    @api.model_create_multi
    def create(self, vals_list):
        """Create re insurance record"""
        records = super().create(vals_list)
        for record in records:
            if record.sequence_number == _('New'):
                record.sequence_number = self.env['ir.sequence'].next_by_code('re.insurance') or _(
                    'New')
        return records

    @api.constrains('ceding_company_date', 'reinsurer_company_date')
    def _check_contract_sign_date(self):
        """Check contract sign date"""
        today = fields.Date.today()
        for record in self:
            if record.ceding_company_date and record.ceding_company_date < today:
                raise ValidationError(
                    _("Authorized Signatory (Insurer) Date cannot be in the past."))
            if record.reinsurer_company_date and record.reinsurer_company_date < today:
                raise ValidationError(
                    _("Authorized Signatory (Reinsurer) Date cannot be in the past."))

    @api.constrains('retention_amount', 'reinsured_amount', 'reinsurance_premium',
                    'reinsurer_percentage')
    def _validate_re_insurance_values(self):
        """Validate re insurance values"""
        for record in self:
            if record.retention_amount <= 0:
                raise ValidationError(_("Retention amount must be greater than zero."))
            if record.reinsured_amount <= 0:
                raise ValidationError(_("Reinsured amount must be greater than zero."))
            if record.reinsurance_premium <= 0:
                raise ValidationError(_("Reinsurance premium amount must be greater than zero."))
            if record.reinsurer_percentage <= 0:
                raise ValidationError(_("Reinsurance percentage must be greater than zero."))

    @api.constrains('start_date', 'end_date')
    def _check_invalid_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError("The end date must be later than the start date.")

    def draft_to_approve(self):
        """Draft to approve"""
        if not self.re_insurance_document_ids:
            message = _display_notification(
                message='Reinsurance documents are required to proceed. Please upload them.',
                message_type='info')
            return message

        documents_verified = all(rec.status == 'verified' for rec in self.re_insurance_document_ids)
        if not documents_verified:
            message = _display_notification(
                message='Please verify all pending reinsurance documents before proceeding.',
                message_type='warning')
            return message
        self.status = 'approve'
        return True

    def approve_to_active(self):
        """Approve to active"""
        self.status = 'active'

    def active_to_running(self):
        """Active to running"""
        self.status = 'running'

    def running_to_expired(self):
        """Running to expired"""
        self.status = 'expired'

    def reinsurance_reset_to_draft(self):
        """Reinsurance reset to draft"""
        for rec in self.re_insurance_document_ids:
            rec.unlink()
        self.status = 'draft'

    def _compute_document_count(self):
        """Document count"""
        for rec in self:
            rec.document_count = self.env['re.insurance.document'].search_count(
                [('re_insurance_id', '=', rec.id)])

    def action_re_insurance_document_view(self):
        """Action view insurance document"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents'),
            'res_model': 're.insurance.document',
            'domain': [('re_insurance_id', '=', self.id)],
            'view_mode': 'list',
            'target': 'current',
            'context': {
                'default_re_insurance_id': self.id,
            },
        }

    @api.model
    def action_auto_expire_reinsurance_policies(self):
        """Auto expire policies end date is today"""
        today = fields.Date.today()
        policies = self.search([('end_date', '=', today), ('status', '=', 'running')])
        for policy in policies:
            policy.running_to_expired()

    @api.constrains('reinsurer_percentage')
    def _constrain_reinsurer_percentage(self):
        """Check Reinsurance Percentage"""
        for record in self:
            if record.reinsurer_percentage > 100:
                raise ValidationError(_("Maximum reinsurer percentage: 100 %"))

    # DEPRECATED
    policy_provider_id = fields.Many2one('res.company', string="Company (legacy)")
    reinsurer_company_id = fields.Many2one('res.company', string=" R Company (legacy)")
