# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import base64
from io import BytesIO
from locale import currency

import xlwt
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class ClaimReport(models.TransientModel):
    """Generate Excel report of claims"""
    _name = 'claim.report'
    _description = __doc__

    start_date = fields.Date()
    end_date = fields.Date()

    @api.constrains('start_date', 'end_date')
    def _check_claim_report_date_check(self):
        """Check if end date is after start date"""
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_("End date cannot be earlier than start date."))

    def action_generate_claim_excel(self):
        """Generate and return Excel file for claims"""
        records = self.env['claim.information'].search([
            ('claim_date', '>=', self.start_date),
            ('claim_date', '<=', self.end_date),
        ])

        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('Claims', cell_overwrite_ok=True)

        # Styles
        main_heading = xlwt.easyxf('align: horiz center, vert center; font: bold True, height 320;')
        heading = xlwt.easyxf('align: vert center; font: bold True, height 220;')
        content_format = xlwt.easyxf('align: vert center; font: height 220;')
        currency_format = xlwt.easyxf('align: horz right; font: height 220;')

        gray_text = xlwt.easyxf(
            "align:horz left, vert center;"
            "font:name Century Gothic, color_index gray80, bold on;"
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")

        blue_text = xlwt.easyxf(
            "align:horz left, vert center;"
            "font:name Century Gothic, color_index dark_blue, bold on;"
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")

        yellow_text = xlwt.easyxf(
            "align:horz left, vert center;"
            "font:name Century Gothic, color_index olive_ega, bold on;"
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")

        green_text = xlwt.easyxf(
            "align:horz left, vert center;"
            "font:name Century Gothic, color_index sea_green, bold on;"
            "border: top hair, bottom hair, left hair, right hair, "
            "top_color gray50, bottom_color gray50, left_color gray50, right_color gray50")

        red_text = xlwt.easyxf(
            "align:horz left, vert center;"
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
        sheet.col(2).width = 4800
        sheet.col(3).width = 3700
        sheet.col(4).width = 5500
        sheet.col(5).width = 5000
        sheet.col(6).width = 8000
        sheet.col(7).width = 8000
        sheet.col(8).width = 4000
        sheet.col(9).width = 5000
        sheet.col(10).width = 4000
        sheet.col(11).width = 6000

        # Write header
        sheet.write_merge(0, 0, 0, 11, 'History of Insurance Claims', main_heading)
        sheet.write(1, 0, "Serial No.", heading)
        sheet.write(1, 1, "Claim Number", heading)
        sheet.write(1, 2, "Insurance", heading)
        sheet.write(1, 3, "Claim Date", heading)
        sheet.write(1, 4, "Policy Holder", heading)
        sheet.write(1, 5, "Policy Category", heading)
        sheet.write(1, 6, "Sub Category", heading)
        sheet.write(1, 7, "Insurance Policy", heading)
        sheet.write(1, 8, "Policy Amount", heading)
        sheet.write(1, 9, "Remaining Amount", heading)
        sheet.write(1, 10, "Claim Amount", heading)
        sheet.write(1, 11, "Status", heading)
        # Write data rows
        row = 2

        for rec in records:
            status = ""
            style = gray_text
            if rec.state == 'draft':
                status = "New"
                style = gray_text
            elif rec.state == 'submit':
                status = "Registered"
                style = gray_text
            elif rec.state == 'document_submitted':
                status = "Document Submitted"
                style = yellow_text
            elif rec.state == 'under_review':
                status = "Under Review"
                style = yellow_text
            elif rec.state == 'approved':
                status = 'Approved'
                style = green_text
            elif rec.state == 'closed':
                status = 'Closed'
                style = green_text
            elif rec.state == 'not_approved':
                status = 'Rejected'
                style = red_text
            elif rec.state == 'settled':
                status = 'Settled'
                style = blue_text

            sheet.row(row).height = 400
            sheet.write(row, 0, row - 1, content_format)
            sheet.write(row, 1, rec.claim_number, content_format)
            sheet.write(row, 2, rec.insurance_id.insurance_number, content_format)
            sheet.write(row, 3, rec.claim_date.strftime('%d/%m/%Y'), content_format)
            sheet.write(row, 4, rec.policy_holder_id.name, content_format)
            sheet.write(row, 5, rec.insurance_category_id.name, content_format)
            sheet.write(row, 6, rec.insurance_sub_category_id.name, content_format)
            sheet.write(row, 7, rec.insurance_policy_id.policy_name, content_format)
            sheet.write(row, 8, f'{rec.currency_id.symbol} {rec.policy_amount}', currency_format)
            sheet.write(row, 9, f'{rec.currency_id.symbol} {rec.due_amount}', currency_format)
            sheet.write(row, 10, f'{rec.currency_id.symbol} {rec.amount_paid}', currency_format)
            sheet.write(row, 11, status, style)
            row += 1
        # Save to stream and encode
        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())

        # Create attachment
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Insurance Claims Report.xls',
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
