# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class ResInsuranceCompany(models.Model):
    """Res Insurance Company"""
    _inherit = 'res.company'
    _description = __doc__

    # DEPRECATED
    is_displayed_on_ins_website = fields.Boolean(string="Display on website insurance form",
                                                 default=True)
    is_re_insurance_company = fields.Boolean(string="ReInsurance Company")
