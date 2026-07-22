# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import base64
from io import BytesIO
import xlwt
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class InsuranceReport(models.TransientModel):
    """Generate Excel report of insurances"""
    _name = 'insurance.report'
    _description = __doc__

    start_date = fields.Date()
    end_date = fields.Date()

    @api.constrains('start_date', 'end_date')
    def _check_insurance_report_date_check(self):
        """Check if end date is after start date"""
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_("End date cannot be earlier than start date."))

    def action_generate_insurance_excel(self):
        """Generate and return Excel file for insurances"""
        records = self.env['insurance.information'].search([
            ('issue_date', '>=', self.start_date),
            ('issue_date', '<=', self.end_date),
        ])

        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('Insurances', cell_overwrite_ok=True)

        # Styles
        main_heading = xlwt.easyxf('align: horiz center, vert center; font: bold True, height 320;')
        heading = xlwt.easyxf('align: vert center; font: bold True, height 220;')
        content_format = xlwt.easyxf('align: vert center; font: height 220;')

        gray_text = xlwt.easyxf(
            "align:horz center, vert center;"
            "font:name Century Gothic, color_index gray80, bold on;"
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")

        blue_text = xlwt.easyxf(
            "align:horz center, vert center;"
            "font:name Century Gothic, color_index dark_blue, bold on;"
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")

        yellow_text = xlwt.easyxf(
            "align:horz center, vert center;"
            "font:name Century Gothic, color_index olive_ega, bold on;"
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")

        green_text = xlwt.easyxf(
            "align:horz center, vert center;"
            "font:name Century Gothic, color_index sea_green, bold on;"
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")

        red_text = xlwt.easyxf(
            "align:horz center, vert center;"
            "font:name Century Gothic, color_index dark_red, bold on;"
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")

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
        sheet.col(8).width = 3100
        sheet.col(9).width = 3500

        # Write header
        sheet.write_merge(0, 0, 0, 9, 'History of Insurance Policies', main_heading)
        sheet.write(1, 0, "Serial No.", heading)
        sheet.write(1, 1, "Insurance Number", heading)
        sheet.write(1, 2, "Policy Holder", heading)
        sheet.write(1, 3, "Policy Category", heading)
        sheet.write(1, 4, "Sub Category", heading)
        sheet.write(1, 5, "Insurance Policy", heading)
        sheet.write(1, 6, "Policy Time Period", heading)
        sheet.write(1, 7, "Issue Date", heading)
        sheet.write(1, 8, "Expiry Date", heading)
        sheet.write(1, 9, "Status", heading)
        # Write data rows
        row = 2

        for rec in records:
            status = ""
            style = gray_text
            if rec.state == 'draft':
                status = "New"
                style = gray_text
            elif rec.state == 'confirmed':
                status = "Confirmed"
                style = blue_text
            elif rec.state == 'running':
                status = "Running"
                style = green_text
            elif rec.state == 'expired':
                status = "Expired"
                style = red_text
            elif rec.state == 'renew':
                status = 'Renew'
                style = yellow_text
            elif rec.state == 'cancel':
                status = 'Cancelled'
                style = red_text

            sheet.row(row).height = 400
            sheet.write(row, 0, row - 1, content_format)
            sheet.write(row, 1, rec.insurance_number, content_format)
            sheet.write(row, 2, rec.policy_holder_id.name, content_format)
            sheet.write(row, 3, rec.insurance_category_id.name, content_format)
            sheet.write(row, 4, rec.insurance_sub_category_id.name, content_format)
            sheet.write(row, 5, rec.insurance_policy_id.policy_name, content_format)
            sheet.write(row, 6, rec.policy_price_list_id.insurance_time_period_id.t_period,
                        content_format)
            sheet.write(row, 7, rec.issue_date.strftime('%d/%m/%Y'), content_format)
            sheet.write(row, 8, rec.expiry_date.strftime('%d/%m/%Y'), content_format)
            sheet.write(row, 9, status, style)
            row += 1
        # Save to stream and encode
        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())

        # Create attachment
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Insurance Policies Report.xls',
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
