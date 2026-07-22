# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import base64
from io import BytesIO
import xlwt
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class InsuranceExpiryReport(models.TransientModel):
    """Generate Excel report of upcoming insurance expirations"""
    _name = 'insurance.expiry.report'
    _description = __doc__

    start_date = fields.Date()
    end_date = fields.Date()

    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        """Check if end date is after start date"""
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_("End date cannot be earlier than start date."))

    def action_generate_insurance_expiry_excel(self):
        """Generate and return Excel file for upcoming expiring insurance policies"""
        records = self.env['insurance.information'].search([
            ('expiry_date', '>=', self.start_date),
            ('expiry_date', '<=', self.end_date),
            ('state', '=', 'running')
        ])

        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('Insurance Policies', cell_overwrite_ok=True)

        # Styles
        main_heading = xlwt.easyxf(
            'align: horiz center, vert center; font: bold True, height 320;')
        heading = xlwt.easyxf('align: vert center; font: bold True, height 220;')
        content_format = xlwt.easyxf('align: vert center; font: height 220;')

        # Define styles
        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'

        # Set row widths
        sheet.row(0).height = 500
        sheet.row(1).height = 400

        # Set column widths
        sheet.col(0).width = 2800
        sheet.col(1).width = 4800
        sheet.col(2).width = 8000
        sheet.col(3).width = 8000
        sheet.col(4).width = 8000
        sheet.col(5).width = 8000
        sheet.col(6).width = 5100
        sheet.col(7).width = 3100
        sheet.col(8).width = 4400

        # Write header
        sheet.write_merge(0, 0, 0, 8, 'Running Insurance Policies Nearing Expiry', main_heading)
        sheet.write(1, 0, "Serial No.", heading)
        sheet.write(1, 1, "Insurance Number", heading)
        sheet.write(1, 2, "Policy Holder", heading)
        sheet.write(1, 3, "Policy Category", heading)
        sheet.write(1, 4, "Sub Category", heading)
        sheet.write(1, 5, "Insurance Policy", heading)
        sheet.write(1, 6, "Policy Time Period", heading)
        sheet.write(1, 7, "Expiry Date", heading)
        sheet.write(1, 8, "Remaining Days", heading)
        # Write data rows
        row = 2

        today = fields.Date.today()
        for rec in records:
            sheet.row(row).height = 400
            sheet.write(row, 0, row - 1, content_format)
            sheet.write(row, 1, rec.insurance_number, content_format)
            sheet.write(row, 2, rec.policy_holder_id.name, content_format)
            sheet.write(row, 3, rec.insurance_category_id.name, content_format)
            sheet.write(row, 4, rec.insurance_sub_category_id.name, content_format)
            sheet.write(row, 5, rec.insurance_policy_id.policy_name, content_format)
            sheet.write(row, 6, rec.policy_price_list_id.insurance_time_period_id.t_period,
                        content_format)
            sheet.write(row, 7, rec.expiry_date.strftime('%d/%m/%Y'), content_format)
            # Add "Days Remaining"
            days_remaining = max((rec.expiry_date - today).days, 0)
            sheet.write(row, 8, f"{days_remaining} Days", content_format)
            row += 1
        # Save to stream and encode
        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())

        # Create attachment
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Upcoming Insurance Expiry Report.xls',
            'type': 'binary',
            'public': False,
            'datas': out,
        })
        # Return download action
        if attachment:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'new',
            }
        return True
