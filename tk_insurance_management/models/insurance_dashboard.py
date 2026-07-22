# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from datetime import timedelta
from odoo import models, fields, api


class InsuranceDashboard(models.Model):
    """Insurance Dashboard"""
    _name = "insurance.dashboard"
    _description = __doc__

    @api.model
    def get_insurance_dashboard(self):
        """Insurance dashboard"""
        insurance_information = self.env['insurance.information'].sudo()
        claims = self.env['claim.information'].sudo()

        insurance_category = self.env['insurance.category'].sudo().search_count([])
        total_insurance = insurance_information.search_count([])
        draft_insurance = insurance_information.search_count([('state', '=', 'draft')])
        running_insurance = insurance_information.search_count([('state', '=', 'running')])
        expired_insurance = insurance_information.search_count([('state', '=', 'expired')])

        total_claim = claims.search_count([])
        submit_claim = claims.search_count([('state', '=', 'submit')])
        under_review_claim = claims.search_count([('state', '=', 'under_review')])
        approved_claim = claims.search_count([('state', '=', 'approved')])
        not_approved_claim = claims.search_count([('state', '=', 'not_approved')])
        closed_claim = claims.search_count([('state', '=', 'closed')])

        res_partner_agent = self.env['res.partner'].sudo().search_count([('is_agent', '=', True)])
        male_count = insurance_information.search_count([('policy_holder_gender', '=', 'male')])
        female_count = insurance_information.search_count([('policy_holder_gender', '=', 'female')])
        others_count = insurance_information.search_count([('policy_holder_gender', '=', 'others')])
        gender_count = [['Male', 'Female', 'Other'], [male_count, female_count, others_count]]

        total_claim_count_graph = [['Registered', 'Approved', 'Rejected'],
                                   [submit_claim, approved_claim, not_approved_claim]]
        insurance_state_graph = [['Running', 'Expired'], [running_insurance, expired_insurance]]

        policy_expiry_remaining_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'tk_insurance_management.policy_expiry_remaining_days'))

        data = {
            'insurance_category': insurance_category,
            'total_insurance': total_insurance,
            'draft_insurance': draft_insurance,
            'running_insurance': running_insurance,
            'expired_insurance': expired_insurance,
            'total_claim': total_claim,
            'submit_claim': submit_claim,
            'under_review_claim': under_review_claim,
            'approved_claim': approved_claim,
            'not_approved_claim': not_approved_claim,
            'closed_claim': closed_claim,
            'res_partner_agent': res_partner_agent,
            'total_claim_count_graph': total_claim_count_graph,
            'insurance_state_graph': insurance_state_graph,
            'top_agents': self.get_top_agents(),
            'gender_count': gender_count,
            'invoice_by_month': self.get_insurance_invoice_by_month(),
            'expiring_insurance': self.get_expiring_insurance(),
            'policy_expiry_remaining_days': policy_expiry_remaining_days,
        }
        return data

    def get_top_agents(self):
        """Top five agents"""
        agent_data = {}
        groups = self.env['insurance.information']._read_group(
            [('agent_bill_id', '!=', False)],
            ['agent_id'],
            ['agent_id:count'],
            order="agent_id DESC",
            limit=5
        )
        for group in groups:
            agent_id = group[0]
            if agent_id:
                agent_name = agent_id.name
                agent_data[agent_name] = group[1]
        # Sort the dictionary by count in descending order
        sorted_medium = dict(sorted(agent_data.items(), key=lambda item: item[1], reverse=True))
        return [list(sorted_medium.keys()), list(sorted_medium.values())]

    def get_insurance_invoice_by_month(self):
        """Insurance invoice by month"""
        currency_symbol = self.env.company.currency_id.symbol
        year = fields.Date.today().year
        year_str = str(year)
        data_dict = {
            '01/' + year_str: 0,
            '02/' + year_str: 0,
            '03/' + year_str: 0,
            '04/' + year_str: 0,
            '05/' + year_str: 0,
            '06/' + year_str: 0,
            '07/' + year_str: 0,
            '08/' + year_str: 0,
            '09/' + year_str: 0,
            '10/' + year_str: 0,
            '11/' + year_str: 0,
            '12/' + year_str: 0,
        }
        # Fetch invoices related to insurance for the current year
        insurance_invoices = self.env['account.move'].search(
            [('insurance_information_id', '!=', False)])
        # Aggregate invoice amounts by month
        for invoice in insurance_invoices:
            if invoice.invoice_date and invoice.invoice_date.year == year:
                month_year = invoice.invoice_date.strftime("%m/%Y")
                data_dict[month_year] += invoice.amount_total
        return [list(data_dict.keys()), list(data_dict.values()), currency_symbol]

    def get_expiring_insurance(self):
        """Get Expiring Insurance"""
        policy_expiry_remaining_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'tk_insurance_management.policy_expiry_remaining_days'))
        today = fields.Date.today()
        expiry_limit_date = today + timedelta(days=policy_expiry_remaining_days)

        ins_info = self.env['insurance.information'].sudo().search([
            ('expiry_date', '>=', today),
            ('expiry_date', '<=', expiry_limit_date),
            ('state', '=', 'running')
        ])
        insurance_information = []
        for ins in ins_info:
            remaining_days = (ins.expiry_date - today).days
            insurance_information.append({
                'id': ins.id,
                'insurance_number': ins.insurance_number,
                'policy_holder': ins.policy_holder_id.name,
                'category': ins.insurance_category_id.name,
                'sub_category': ins.insurance_sub_category_id.name,
                'insurance_policy': ins.insurance_policy_id.policy_name,
                'time_period': ins.policy_price_list_id.insurance_time_period_id.t_period,
                'expiry_date': ins.expiry_date,
                'remaining_days': remaining_days,
            })
        return insurance_information
