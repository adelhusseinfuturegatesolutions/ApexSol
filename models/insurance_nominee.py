# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _


class InsuranceNomineeRelation(models.Model):
    """Insurance Nominee Relation"""
    _name = 'insurance.nominee.relation'
    _description = __doc__
    _rec_name = 'name'

    name = fields.Char(translate=True)


class InsuranceNominee(models.Model):
    """Insurance Nominee"""
    _name = 'insurance.nominee'
    _description = __doc__
    _rec_name = 'name'

    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    name = fields.Char(string="Name")
    nominee_id = fields.Char(string="ID")
    nominee_dob = fields.Date(string="Date of Birth")
    nominee_age = fields.Char(string="Age", compute="_compute_nominee_age_count", translate=True)
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
        ('Employee-Male', "Employee-Male"),
        ('Employee-Female', "Employee-Female"), 
        ('other', "Other")], string="Status")
    insurance_information_id = fields.Many2one('insurance.information', ondelete='cascade')
    claim_information_id = fields.Many2one('claim.information', ondelete='cascade')
    policy_holder_id = fields.Many2one('res.partner', string='Policy Holder')
    active = fields.Boolean(default=True)
    medical_history_ids = fields.One2many('medical.history', 'insure_nominee_id',string="Medical History")
    parent_nominee_id = fields.Many2one(
        'insurance.nominee', 
        string="Main Nominee (Employee)", 
        index=True, 
        ondelete='cascade'
    )
    
    family_member_ids = fields.One2many(
        'insurance.nominee', 
        'parent_nominee_id', 
        string="Family Members"
    )

    relation_type = fields.Selection([('Employee-Male','Employee-Male'),('Employee-Female','Employee-Female'),('Wife','Wife'),('son','Son'),('daughter','Daughter'),('father','Father'),('mother','Mother'),('Husband','Husband')],string="Relationship.")
    amount_factor = fields.Float(string='Amount Factor')
    claims_count = fields.Integer(compute='_compute_claim_count')

    nominee_status = fields.Selection(
        [('active', 'Active'),
         ('inactive', 'Inactive')],
        string="Status",
        compute='_compute_nominee_status',
        inverse='_inverse_nominee_status',
        search='_search_nominee_status')

    @api.depends('active')
    def _compute_nominee_status(self):
        for rec in self:
            rec.nominee_status = 'active' if rec.active else 'inactive'

    def _inverse_nominee_status(self):
        for rec in self:
            rec.active = (rec.nominee_status != 'inactive')

    def write(self, vals):
        """When a main employee is (de)activated, cascade to family members."""
        result = super().write(vals)
        if 'active' in vals:
            self._cascade_active_to_family(vals['active'])
        return result

    def toggle_active(self):
        """Force cascade also when toggled via the standard Archive action."""
        result = super().toggle_active()
        for rec in self.with_context(active_test=False):
            rec._cascade_active_to_family(rec.active)
        return result

    def action_set_inactive(self):
        self.with_context(active_test=False).write({'active': False})
        return True

    def action_set_active(self):
        self.with_context(active_test=False).write({'active': True})
        return True

    def _cascade_active_to_family(self, new_active):
        """Apply the given active state to all family members of any main
        employee in self. Posts a message on the employee chatter."""
        for rec in self.with_context(active_test=False):
            if rec.parent_nominee_id:
                continue
            members = rec.family_member_ids.with_context(active_test=False).filtered(
                lambda m: m.active != new_active)
            if not members:
                continue
            members.write({'active': new_active})

    def _search_nominee_status(self, operator, value):
        if operator not in ('=', '!=', 'in', 'not in'):
            return []
        if isinstance(value, str):
            value = [value]
        wants_inactive = ('inactive' in value)
        wants_active = ('active' in value)
        if operator in ('!=', 'not in'):
            wants_inactive, wants_active = not wants_inactive, not wants_active
        if wants_active and not wants_inactive:
            return [('active', '=', True)]
        if wants_inactive and not wants_active:
            return [('active', '=', False)]
        return []

    family_head_name = fields.Char(
        string="Family",
        compute='_compute_family_head_name')

    @api.depends('parent_nominee_id.name', 'name')
    def _compute_family_head_name(self):
        """Group key: own name for employees, parent's name for family members."""
        for rec in self:
            rec.family_head_name = rec.parent_nominee_id.name or rec.name

    sum_assured = fields.Monetary(
        string="Sum Insured",
        related='insurance_policy_id.sum_assured',
        currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        related='insurance_information_id.currency_id')
    total_claimed = fields.Monetary(
        string="Total Claimed",
        compute='_compute_claim_summary',
        currency_field='currency_id')
    remaining_consumption = fields.Monetary(
        string="Remaining Coverage",
        compute='_compute_claim_summary',
        currency_field='currency_id')
    approved_claims_count = fields.Integer(
        string="Approved Claims",
        compute='_compute_claim_summary')
    last_claim_amount = fields.Monetary(
        string="Last Claim Amount",
        compute='_compute_claim_summary',
        currency_field='currency_id')

    def _compute_claim_summary(self):
        approved_states = ('approved', 'settled', 'closed')
        Claim = self.env['claim.information']
        for rec in self:
            claims = Claim.search([
                ('insurance_nominee_id', '=', rec.id),
                ('state', 'in', approved_states),
            ])
            rec.total_claimed = sum(claims.mapped('amount_paid'))
            rec.approved_claims_count = len(claims)
            rec.remaining_consumption = (rec.sum_assured or 0.0) - rec.total_claimed
            last_claim = Claim.search(
                [('insurance_nominee_id', '=', rec.id)],
                order='claim_date desc, id desc',
                limit=1,
            )
            rec.last_claim_amount = last_claim.amount_paid if last_claim else 0.0


    # policy details
    insurance_category_id = fields.Many2one('insurance.category', string="Policy Category" , related='insurance_information_id.insurance_category_id')
    insurance_sub_category_id = fields.Many2one('insurance.sub.category', string="Sub Category",related='insurance_information_id.insurance_sub_category_id')
    insurance_policy_id = fields.Many2one('insurance.policy', string='Insurance Policy',related='insurance_information_id.insurance_policy_id')
    policy_price_list_id = fields.Many2one('policy.price.list', string="Policy Time Period",related='insurance_information_id.policy_price_list_id')
    policy_provider_cmp_id = fields.Many2one('res.partner', string='Policy Provider',related='insurance_information_id.policy_provider_cmp_id')
    issue_date = fields.Date(string="Issue Date", related='insurance_information_id.issue_date')
    expiry_date = fields.Date(string="Expiry Date", related='insurance_information_id.expiry_date')
    insurance_number = fields.Char(
        string="Policy Number",
        related='insurance_information_id.insurance_number')
    insurance_state = fields.Selection(
        string="Policy Status",
        related='insurance_information_id.state')
    addition_date = fields.Date(
        string="Addition Date",
        compute='_compute_addition_date',
        inverse='_inverse_addition_date',
        help="Date this nominee was added to the policy; drives pro-rated premium.")

    @api.depends('create_date')
    def _compute_addition_date(self):
        ICP = self.env['ir.config_parameter'].sudo()
        for rec in self:
            stored = ICP.get_param(f'tk_insurance.nominee.addition_date.{rec.id}')
            if stored:
                rec.addition_date = fields.Date.from_string(stored)
            elif rec.create_date:
                rec.addition_date = rec.create_date.date()
            else:
                rec.addition_date = fields.Date.context_today(rec)

    def _inverse_addition_date(self):
        ICP = self.env['ir.config_parameter'].sudo()
        for rec in self:
            key = f'tk_insurance.nominee.addition_date.{rec.id}'
            if rec.addition_date:
                ICP.set_param(key, fields.Date.to_string(rec.addition_date))
            else:
                existing = ICP.search([('key', '=', key)], limit=1)
                if existing:
                    existing.unlink()
        insurances = self.mapped('insurance_information_id')
        if insurances:
            insurances.invalidate_recordset(['total_policy_amount'])
        for rec in self:
            if rec.insurance_information_id.state == 'running':
                rec._update_subscription_invoice()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        ICP = self.env['ir.config_parameter'].sudo()
        today_str = fields.Date.to_string(fields.Date.context_today(self))
        for rec in records:
            insurance = rec.insurance_information_id \
                or rec.parent_nominee_id.insurance_information_id
            if insurance and insurance.state == 'running':
                # Stamp today as the addition date so quarter pro-rating kicks in.
                ICP.set_param(
                    f'tk_insurance.nominee.addition_date.{rec.id}', today_str)
                rec._update_subscription_invoice()
        return records

    def _get_main_nominee(self):
        self.ensure_one()
        return self.parent_nominee_id or self

    def _subscription_invoice_key(self):
        return f'tk_insurance.subscription_invoice.{self._get_main_nominee().id}'

    def _get_existing_subscription_invoice(self):
        ICP = self.env['ir.config_parameter'].sudo()
        invoice_id = ICP.get_param(self._subscription_invoice_key())
        if not invoice_id:
            return False
        try:
            move = self.env['account.move'].sudo().browse(int(invoice_id))
        except (TypeError, ValueError):
            return False
        return move if move.exists() else False

    def _subscription_invoice_lines(self):
        """Return invoice line vals for the employee + their family members."""
        main = self._get_main_nominee()
        insurance = main.insurance_information_id
        if not insurance:
            return []
        unit = main.with_context(active_test=False) \
                   | main.family_member_ids.with_context(active_test=False)
        lines = []
        for nominee in unit:
            if not nominee.active:
                continue
            amount = insurance._nominee_prorated_amount(nominee)
            if not amount or amount <= 0:
                continue
            label = _("Subscription — %s (%s)",
                      nominee.name or _("Nominee"),
                      nominee.relation_type or nominee.insured_gender or '')
            lines.append({
                'name': label,
                'quantity': 1,
                'price_unit': amount,
                'tax_ids': False,
            })
        return lines

    def _update_subscription_invoice(self):
        """Create or refresh a single invoice that covers the employee and
        all their family members. If an existing invoice is still in draft
        it is updated in place; otherwise a new invoice is created."""
        self.ensure_one()
        main = self._get_main_nominee()
        insurance = main.insurance_information_id
        if not insurance or not insurance.policy_holder_id:
            return False
        lines = main._subscription_invoice_lines()
        if not lines:
            return False
        existing = main._get_existing_subscription_invoice()
        if existing and existing.state == 'draft':
            existing.invoice_line_ids.unlink()
            existing.write({
                'invoice_line_ids': [(0, 0, l) for l in lines],
            })
            return existing
        move = self.env['account.move'].sudo().create({
            'partner_id': insurance.policy_holder_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': [(0, 0, l) for l in lines],
        })
        self.env['ir.config_parameter'].sudo().set_param(
            main._subscription_invoice_key(), str(move.id))
        return move

    def action_create_subscription_invoice(self):
        """Manually refresh / create the subscription invoice for the unit."""
        for rec in self:
            move = rec._update_subscription_invoice()
            if move:
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Subscription Invoice'),
                    'res_model': 'account.move',
                    'res_id': move.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        return True


    @api.constrains('nominee_dob')
    def _check_nominee_dob(self):
        """Check nominee dob"""
        today = fields.Date.today()
        for record in self:
            if record.nominee_dob and record.nominee_dob > today:
                raise ValidationError(_("Nominee must be born before today's date."))

    @api.depends('nominee_dob')
    def _compute_nominee_age_count(self):
        """Nominee age count"""
        today = fields.Date.today()
        for rec in self:
            if rec.nominee_dob:
                nominee_dob = fields.Date.from_string(rec.nominee_dob)
                if nominee_dob > today:
                    raise ValidationError(_("DOB should be earlier than today's date."))
                nominee_age = today.year - nominee_dob.year - (
                        (today.month, today.day) < (nominee_dob.month, nominee_dob.day))
                rec.nominee_age = f"{max(nominee_age, 0)} Years"
            else:
                rec.nominee_age = "0 Years"

    def _compute_claim_count(self):
        """Claim count"""
        for rec in self:
            rec.claims_count = self.env['claim.information'].search_count(
                [('insurance_nominee_id', '=', rec.id)])

    def action_insured_nominee_claim(self):
        """Insured claim"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Claims'),
            'res_model': 'claim.information',
            'domain': [('insurance_nominee_id', '=', self.id)],
            'context': {
                'default_insurance_nominee_id': self.id,
            },
            'view_mode': 'list,form',
            'target': 'current',
        }

class MedicalHistory(models.Model):
    _name = 'medical.history'
    _description = __doc__
    _rec_name = 'name'

    name = fields.Char(translate=True, string="Disease")
    disease_year = fields.Char(string="Year of Disease")
    notes = fields.Text(string="Medical Notes")
    insure_nominee_id = fields.Many2one('insurance.nominee')
