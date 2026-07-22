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

    start_date = fields.Date()
    end_date = fields.Date()

    @api.constrains('start_date', 'end_date')
    def _check_insurance_report_date_check(self):
        """Check if end date is after start date"""
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_("End date cannot be earlier than start date."))

    def print_xlsx_report(self):
        self.ensure_one()
        # Find claims within the date range
        claims = self.env['claim.information'].search([
            ('claim_date', '>=', self.start_date),
            ('claim_date', '<=', self.end_date),
        ])
        
        if not claims:
            raise UserError("No claims found for the selected period.")

        # Pass dates to the report via the 'data' dictionary
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'ids': claims.ids, # Pass the IDs of the filtered claims
        }
        # The report name must match the 'report_name' in your XML action
        return self.env.ref('tk_insurance_management.action_report_claims_xlsx').report_action(self, data=data)