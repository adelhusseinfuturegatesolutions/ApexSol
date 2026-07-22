# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ExtendInsurance(models.TransientModel):
    """Extend Insurance Policy"""
    _name = 'extend.insurance'
    _description = __doc__

    insurance_id = fields.Many2one('insurance.information', required=True)
    current_expiry_date = fields.Date(
        related='insurance_id.expiry_date',
        string="Current Expiry Date")
    extension_months = fields.Integer(
        string="Extend By (Months)", default=12, required=True)
    new_expiry_date = fields.Date(
        string="New Expiry Date",
        compute='_compute_new_expiry_date',
        store=False)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'insurance.information':
            defaults['insurance_id'] = active_id
        return defaults

    @api.depends('current_expiry_date', 'extension_months')
    def _compute_new_expiry_date(self):
        for rec in self:
            base = rec.current_expiry_date or fields.Date.context_today(rec)
            rec.new_expiry_date = base + relativedelta(months=rec.extension_months or 0)

    def action_extend(self):
        self.ensure_one()
        if self.extension_months <= 0:
            raise ValidationError(_("Extension months must be greater than zero."))
        insurance = self.insurance_id.sudo()
        insurance.write({
            'expiry_date': self.new_expiry_date,
            'state': 'running',
        })
        insurance.message_post(body=_(
            "Policy extended by %s month(s). New expiry date: %s.",
            self.extension_months, self.new_expiry_date))
        return {'type': 'ir.actions.act_window_close'}
