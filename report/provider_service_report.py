import io
import base64
from odoo import models

class ProviderService(models.AbstractModel):
    _name = 'report.tk_insurance_management.provider_service_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, claims):
        # 1. Define Formats
        company_name_format = workbook.add_format({
            'bold': True, 'align': 'center', 'font_size': 14
        })
        invoice_title_format = workbook.add_format({
            'bold': True, 'align': 'center', 'font_size': 18, 'font_color': '#2c3e50'
        })
        header_format = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#2c3e50', 'font_color': 'white', 'border': 1
        })
        cell_format = workbook.add_format({'border': 1, 'align': 'left'})
        num_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})

        sheet = workbook.add_worksheet('Service Provider Report')
        
        # Set Column Widths
        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 25)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 15)

        # 2. Company Logo (Rows 1 to 6)
        company = claims[0].company_id
        if company.logo:
            # Decode the base64 logo
            image_data = io.BytesIO(base64.b64decode(company.logo))
            
            sheet.insert_image('B1', 'logo.png', {
                'image_data': image_data,
                'x_scale': 0.7,   # Increase/decrease to fit width of B, C, D
                'y_scale': 0.7,   # Maintain aspect ratio
                'x_offset': 5,    # Slight padding from the left of Column B
                'y_offset': 5,    # Slight padding from the top of Row 1
                'object_position': 1 # Ensures the image moves/sizes with cells
            })

       
        sheet.merge_range(6, 1, 6, 3, company.name, company_name_format)
        
        sheet.merge_range(7, 1, 7, 3, "Hospitals Medical Services Entitlement", invoice_title_format)

        # 5. Data Headers (Starting at Row 10)
        row = 9
        headers = ['#','إسم مزود الخدمة', 'المنطقة','المبلغ', 'الشهر', 'رقم الحساب', ' رقم الحساب بإسم']
        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)
        
        row += 1

        # 6. Populate Data
        serial_no = 1

        for claim in claims:
            provider_name = claim.policy_provider_cmp_id.name
            location = claim.policy_provider_cmp_id.street 
            amount = claim.amount_paid 
            date = claim.claim_date.strftime('%B') if claim.claim_date else ''
            account_number = claim.policy_provider_cmp_id.bank_ids[0].acc_number if claim.partner_id.bank_ids else ''
            account_name = claim.policy_provider_cmp_id.bank_ids[0].partner_id.name if claim.partner_id.bank_ids else ''


            sheet.write(row, 0, serial_no, cell_format)
            sheet.write(row, 1, provider_name, cell_format)
            sheet.write(row, 2, location, cell_format)
            sheet.write(row, 3, amount, num_format)
            sheet.write(row, 4, date, cell_format)
            sheet.write(row, 5, location, cell_format)
            sheet.write(row, 6, account_number, cell_format)
            sheet.write(row, 7, account_name, cell_format)
            

            row += 1
            serial_no += 1
