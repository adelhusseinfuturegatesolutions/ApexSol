import base64
from io import BytesIO
from locale import currency

import xlwt
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class ClaimReport(models.TransientModel):
    """Generate Excel report of claims"""
    _name = 'patient.contract.claim.report'
    _description = __doc__

    # start_date = fields.Date()
    # end_date = fields.Date()