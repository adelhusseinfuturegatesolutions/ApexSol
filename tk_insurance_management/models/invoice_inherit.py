# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class AccountMove(models.Model):
    """Account Move"""
    _inherit = 'account.move'
    _description = __doc__

    insurance_information_id = fields.Many2one('insurance.information', string="Insurance")
    claim_information_id = fields.Many2one('claim.information', string="Claim")
