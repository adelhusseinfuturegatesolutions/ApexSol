# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ReInsuranceRejectReason(models.TransientModel):
    """ReInsurance Reject Reason"""
    _name = 'reinsurance.reject.reason'
    _description = __doc__

    reinsurance_id = fields.Many2one('re.insurance', string="ReInsurance",
                                     default=lambda self: self.env.context.get('active_id'))
    rejection_reason = fields.Html()

    def action_submit_reject_reason(self):
        """Submit the rejection reason to the linked reinsurance record"""
        reinsurance = self.reinsurance_id
        if reinsurance:
            reinsurance.write({
                'rejection_reason': self.rejection_reason,
                'status': 'reject',
            })
