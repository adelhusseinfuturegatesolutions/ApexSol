# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ClaimReasons(models.Model):
    """Claim Reasons"""
    _name = 'claim.reasons'
    _description = __doc__
    _rec_name = 'name'

    color = fields.Integer(default=1)
    name = fields.Char(translate=True)
