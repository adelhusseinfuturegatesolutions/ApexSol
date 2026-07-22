# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import base64
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager


def validate_mandatory_fields(mandate_fields, kw):
    """Validate mandatory fields"""
    error, data = None, {}
    for key, value in mandate_fields.items():
        if not kw.get(key):
            error = "Mandatory fields " + value + " Missing"
            break
        data[key] = kw.get(key)
    return error, data


def validate_optional_fields(opt_fields, kw):
    """Validate optional fields"""
    data = {}
    for fld in opt_fields:
        if kw.get(fld):
            data[fld] = kw.get(fld)
    return data


class InsuranceQuotationWebsite(CustomerPortal):
    """Insurance Quotation Website"""

    @staticmethod
    def _get_initial_values():
        """Get initial values"""
        insurance_category = request.env['insurance.category'].sudo().search(
            [('is_displayed_on_website', '=', True)])
        insurance_sub_category = request.env['insurance.sub.category'].sudo().search([])
        policy_providers = request.env['res.partner'].sudo().search(
            [('is_publish_on_web', '=', True), ('is_re_insurance_company', '=', False)])
        is_terms_and_conditions = request.env['ir.config_parameter'].sudo().get_param(
            'tk_insurance_management.is_terms_and_conditions')
        terms_condition_url = request.env['ir.config_parameter'].sudo().get_param(
            'tk_insurance_management.terms_condition_url')
        return {
            'insurance_category': insurance_category,
            'insurance_sub_category': insurance_sub_category,
            'policy_providers': policy_providers,
            'is_terms_and_conditions': is_terms_and_conditions,
            'terms_condition_url': terms_condition_url,
        }

    @http.route('/get_category_wise_sub_category', type='jsonrpc', auth='public')
    def get_insurance_sub_category(self, insurance_category_id):
        """Insurance sub category"""
        sub_category = {}
        if not insurance_category_id:
            return sub_category  # Consistent return type
        insurance_sub_category = request.env['insurance.sub.category'].sudo().search(
            [('insurance_category_id', '=', int(insurance_category_id))])
        for data in insurance_sub_category:
            sub_category[data.id] = data.name
        return sub_category

    @http.route('/insurance/quote/request', type='http', auth='public', website=True)
    def get_insurance_quote_request(self):
        """Get insurance quote request"""
        values = self._get_initial_values()
        return request.render('tk_insurance_management.insurance_quote_request_form', values)

    @http.route('/create/quote-request', type='http', auth='public', website=True)
    def create_web_insurance_quote(self, **kw):
        """Create web insurance quote"""
        values = self._get_initial_values()
        mandatory_fields = {'name': "Request For", 'policy_holder_gender': "Gender",
                            'policy_holder_dob': "Date of Birth",
                            'insurance_category_id': "Policy Category",
                            'policy_provider_cmp_id': "Policy Provider", 'email_from': "Email",
                            'phone': "Phone"}
        optional_fields = ['contact_name', 'insurance_sub_category_id', 'description',
                           'policy_holder_age']
        error, quotation_data = validate_mandatory_fields(mandatory_fields, kw)
        if values['is_terms_and_conditions'] and not kw.get('terms_and_conditions'):
            error = "Mandatory fields Terms & Conditions Missing"
        if error:
            values['error'] = error
            kw.update(values)
            return request.render('tk_insurance_management.insurance_quote_request_form', kw)
        # Handle document attachment
        document = kw.get('document')
        if document:
            filename = document.filename  # Simplified filename extraction
            image = base64.b64encode(document.read())
            quotation_data.update({'attachment': image, 'file_name': filename})
        opt_data = validate_optional_fields(optional_fields, kw)
        quotation_data.update(opt_data)
        quotation_data['type'] = 'lead'
        quotation_data['user_id'] = False
        quotation_details = request.env['crm.lead'].sudo().create(quotation_data)
        email_values = {
            'email_to': quotation_details.email_from,
            'email_from': request.website.company_id.sudo().email,
            'author_id': False
        }
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = base_url + "/quote/request-information/" + quotation_details.website_ref_number
        ctx = {
            "customer_url": url,
        }
        template_id = request.env.ref(
            'tk_insurance_management.quote_ref_number_mail_template').sudo()
        request.env['mail.template'].sudo().browse(template_id.id).with_context(ctx).send_mail(
            quotation_details.id,
            email_values=email_values,
            email_layout_xmlid='mail.mail_notification_light',
            force_send=True)
        return request.render('tk_insurance_management.quotation_created',
                              {'quotation_details': quotation_details})

    @http.route(['/quote/request-information/<string:ref>'], type='http', auth="public",
                website=True)
    def quote_request_information_detail(self, ref):
        """Quote request information detail"""
        quote_details = request.env['crm.lead'].sudo().search([('website_ref_number', '=', ref)],
                                                              limit=1)
        is_terms_and_conditions = request.env['ir.config_parameter'].sudo().get_param(
            'tk_insurance_management.is_terms_and_conditions')
        terms_condition_url = request.env['ir.config_parameter'].sudo().get_param(
            'tk_insurance_management.terms_condition_url')
        if not quote_details:
            return request.redirect('/')
        data = {
            'quote_details': quote_details,
            'is_terms_and_conditions': is_terms_and_conditions,
            'terms_condition_url': terms_condition_url,
        }
        return request.render('tk_insurance_management.insurance_quote_details', data)

    @http.route(['/quote/request/details'], type='http', auth="public", website=True)
    def quotation_details(self, **kw):
        """Quotation details"""
        tracking_no = "tk-ins-ref"
        if kw.get('quote_number'):
            tracking_no = kw.get('quote_number')
        invalid_ref = False
        is_error = False
        data = {
            'invalid_ref': invalid_ref,
            'is_error': is_error,
        }
        if tracking_no == 'tk-ins-ref':
            return request.render('tk_insurance_management.quotation_tracking_details', data)
        if not tracking_no:
            data['invalid_ref'] = True
            return request.render('tk_insurance_management.quotation_tracking_details', data)
        quote_leads = request.env['crm.lead'].sudo().search(
            [('website_ref_number', '=', tracking_no)], limit=1)
        if not quote_leads:
            data['is_error'] = True
        if quote_leads:
            quote_details_url = '/quote/request-information/' + str(quote_leads.website_ref_number)
            return request.redirect(quote_details_url)
        return request.render('tk_insurance_management.quotation_tracking_details', data)

    @http.route('/quote/track-details', type='http', auth="public", website=True, cache=300)
    def quote_tracks_details(self):
        """Quote tracks details"""
        tracking_no = request.params.get('quote_number')
        if not tracking_no:
            return request.redirect('/quote/request/details')
        quotations_leads = request.env['crm.lead'].sudo().search([('name', '=', tracking_no)])
        if quotations_leads:
            return request.render('tk_insurance_management.insurance_quote_details',
                                  {'quotations_leads': quotations_leads})
        return request.redirect('/quote/request/details')

    @http.route(['/my/insurance-records', '/my/insurance-records/page/<int:page>'], type='http',
                auth='user', website=True)
    def insurance_records_portal_view(self, page=1, **kw):
        """Insurance records for the logged-in user."""
        domain = [('policy_holder_id', '=', request.env.user.partner_id.id)]
        page_size = 10
        offset = (page - 1) * page_size

        search = kw.get('search')
        if search:
            domain = domain + ['|', '|', '|', '|', '|',
                               ('insurance_number', 'ilike', search),
                               ('insurance_category_id', 'ilike', search),
                               ('insurance_sub_category_id', 'ilike', search),
                               ('insurance_policy_id', 'ilike', search),
                               ('policy_price_list_id', 'ilike', search),
                               ('state', 'ilike', search)]

        filter_by = kw.get('filter_by')
        if filter_by == 'state_draft':
            domain.append(('state', '=', 'draft'))
        elif filter_by == 'state_confirmed':
            domain.append(('state', '=', 'confirmed'))
        elif filter_by == 'state_running':
            domain.append(('state', '=', 'running'))
        elif filter_by == 'state_expired':
            domain.append(('state', '=', 'expired'))
        elif filter_by == 'state_cancel':
            domain.append(('state', '=', 'cancel'))

        total_count = request.env['insurance.information'].sudo().search_count(domain)
        insurance_records = request.env['insurance.information'].sudo().search(
            domain,
            limit=page_size,
            offset=offset,
            order='insurance_number desc'
        )

        pager_details = pager(
            url="/my/insurance-records",
            total=total_count,
            page=page,
            step=page_size,
            scope=5
        )
        return request.render('tk_insurance_management.portal_insurance_record_list', {
            'insurance_records': insurance_records,
            'page_name': 'insurance_record_list',
            'pager': pager_details,
        })

    @http.route("/insurance/policy-details/<string:access_token>", type='http', auth="user",
                website=True)
    def insurance_policy_details(self, access_token):
        """Specific insurances for the logged-in user."""
        insurance_record = request.env['insurance.information'].sudo().search(
            [('access_token', '=', access_token),
             ('policy_holder_id', '=', request.env.user.partner_id.id)], limit=1)
        if not insurance_record:
            return request.redirect('/')
        # Get all insurance for the logged-in user
        user_policies = request.env['insurance.information'].sudo().search([
            ('policy_holder_id', '=', request.env.user.partner_id.id)])
        policy_ids = user_policies.ids
        current_index = policy_ids.index(
            insurance_record.id) if insurance_record.id in policy_ids else -1
        if current_index == -1:
            return request.redirect('/')
        # Previous and Next URLs
        prev_url = f"/insurance/policy-details/{user_policies[current_index - 1].access_token}" \
            if current_index > 0 else None
        next_url = f"/insurance/policy-details/{user_policies[current_index + 1].access_token}" \
            if current_index < len(policy_ids) - 1 else None
        return request.render('tk_insurance_management.web_insurance_detail_view', {
            'policy': insurance_record,
            'page_name': 'insurance_policy_form',
            'prev_record': prev_url,
            'next_record': next_url,
        })

    @http.route('/my/insurance/report/<string:access_token>', type='http', auth='user',
                website=True)
    def portal_generate_insurance_report(self, access_token):
        """Download insurance report PDF for the logged-in user"""
        if not access_token:
            return request.redirect('/my/home')
        insurance = request.env['insurance.information'].sudo().search([
            ('access_token', '=', access_token),
            ('policy_holder_id', '=', request.env.user.partner_id.id),
        ], limit=1)
        if not insurance:
            return request.redirect('/my/home')
        report_ref = 'tk_insurance_management.insurance_report_template'
        response = self._show_report(model=insurance, report_type='pdf', report_ref=report_ref,
                                     download=True)
        return response

    @http.route('/my/insurance/submit_claim', type='http', auth='user', methods=['POST'],
                website=True, csrf=True)
    def submit_insurance_claim(self, **post):
        """Submit insurance claim from website"""
        insurance_id = int(post.get('insurance_id'))
        claim_date = post.get('claim_date')

        insurance = request.env['insurance.information'].sudo().browse(insurance_id)

        if not insurance.exists():
            return request.redirect('/')
        claim = request.env['claim.information'].sudo().create({
            'insurance_id': insurance_id,
            'claim_date': claim_date,
            'policy_holder_id': insurance.policy_holder_id.id,
            'email': insurance.email,
            'phone': insurance.phone,
            'policy_holder_street': insurance.policy_holder_street,
            'policy_holder_street2': insurance.policy_holder_street2,
            'policy_holder_city': insurance.policy_holder_city,
            'policy_holder_state_id': insurance.policy_holder_state_id.id,
            'policy_holder_country_id': insurance.policy_holder_country_id.id,
            'policy_holder_zip': insurance.policy_holder_zip,
            'policy_holder_dob': insurance.policy_holder_dob,
            'policy_holder_age': insurance.policy_holder_age,
            'policy_holder_gender': insurance.policy_holder_gender,
            'insured_id': insurance.insured_id.id,
            'gender': insurance.gender,
            'dob': insurance.dob,
            'age': insurance.age,
            'marital_status': insurance.marital_status,
            'blood_group': insurance.blood_group,
            'insured_height': insurance.insured_height,
            'insured_weight': insurance.insured_weight,
            'insured_birthmark': insurance.insured_birthmark,
            'insurance_policy_id': insurance.insurance_policy_id.id,
            'insurance_category_id': insurance.insurance_category_id.id,
            'insurance_sub_category_id': insurance.insurance_sub_category_id.id,
            'desired_coverage_type': insurance.desired_coverage_type,
            'policy_provider_cmp_id': insurance.policy_provider_cmp_id.id,
            'agent_required': insurance.agent_required,
            'agent_id': insurance.agent_id.id,
            'responsible_id': insurance.responsible_id.id,
            'policy_price_list_id': insurance.policy_price_list_id.id,
            'policy_amount': insurance.policy_amount,
            'due_amount': insurance.total_due_amount,
            'policy_terms_and_conditions': insurance.policy_terms_and_conditions,
            'is_reinsurance_required': insurance.is_reinsurance_required,
            're_insurance_id': insurance.re_insurance_id.id,
            'reinsurance_company_id': insurance.re_insurance_id.reinsurance_company_id.id,
        })

        for insured_detail in insurance.insured_details_ids:
            insured_detail.claim_information_id = claim.id
        for nominee in insurance.insurance_nominee_ids:
            nominee.claim_information_id = claim.id
        return request.redirect(
            f'/my/insurance/claim-submitted?access_token={insurance.access_token}')

    @http.route('/my/insurance/claim-submitted', type='http', auth="public", website=True,
                methods=['GET'])
    def get_insurance_claim_submitted(self, **kwargs):
        """Insurance claim submitted"""
        access_token = kwargs.get('access_token')
        policy_url = f'/insurance/policy-details/{access_token}' if access_token else '/'
        return request.render('tk_insurance_management.web_insurance_claim_submitted', {
            'policy_url': policy_url
        })

    @http.route(['/my/insurance-claims/<string:access_token>',
                 '/my/insurance-claims/<string:access_token>/page/<int:page>'],
                type='http', auth='user', website=True)
    def insurance_policy_claims(self, access_token, page=1, **kw):
        """List all claims for insurance"""
        insurance = request.env['insurance.information'].sudo().search([
            ('access_token', '=', access_token),
            ('policy_holder_id', '=', request.env.user.partner_id.id)
        ], limit=1)

        if not insurance:
            return request.redirect('/')

        domain = [('insurance_id', '=', insurance.id)]
        page_size = 10
        offset = (page - 1) * page_size

        search = kw.get('search')
        if search:
            domain = domain + ['|', ('claim_number', 'ilike', search), ('state', 'ilike', search)]

        filter_by = kw.get('filter_by')
        if filter_by == 'state_draft':
            domain.append(('state', '=', 'draft'))
        elif filter_by == 'state_submit':
            domain.append(('state', '=', 'submit'))
        elif filter_by == 'state_under_review':
            domain.append(('state', '=', 'under_review'))
        elif filter_by == 'state_running':
            domain.append(('state', '=', 'approved'))
        elif filter_by == 'state_expired':
            domain.append(('state', '=', 'not_approved'))
        elif filter_by == 'state_settled':
            domain.append(('state', '=', 'settled'))
        elif filter_by == 'state_closed':
            domain.append(('state', '=', 'closed'))

        total_count = request.env['claim.information'].sudo().search_count(domain)
        claims = request.env['claim.information'].sudo().search(
            domain,
            limit=page_size,
            offset=offset,
            order='id desc'
        )
        pager_details = pager(
            url=f"/my/insurance-claims/{access_token}",
            total=total_count,
            page=page,
            step=page_size,
            scope=5
        )
        return request.render('tk_insurance_management.web_insurance_claim_list', {
            'insurance': insurance,
            'claims': claims,
            'page_name': 'page_claim_list',
            'pager': pager_details,
            'access_token': access_token,
        })

    @http.route("/insurance/claim-details/<string:access_token>", type='http', auth="user",
                website=True)
    def insurance_policy_claim_details(self, access_token):
        """insurance claim for the logged-in user."""
        claim_record = request.env['claim.information'].sudo().search(
            [('access_token', '=', access_token),
             ('policy_holder_id', '=', request.env.user.partner_id.id)], limit=1)
        if not claim_record:
            return request.redirect('/')
        # Get all insurance claims for the logged-in user
        user_claims = request.env['claim.information'].sudo().search([
            ('policy_holder_id', '=', request.env.user.partner_id.id)])
        claim_ids = user_claims.ids
        current_index = claim_ids.index(claim_record.id) if claim_record.id in claim_ids else -1
        if current_index == -1:
            return request.redirect('/')
        # Previous and Next URLs
        prev_url = f"/insurance/claim-details/{user_claims[current_index - 1].access_token}" \
            if current_index > 0 else None
        next_url = f"/insurance/claim-details/{user_claims[current_index + 1].access_token}" \
            if current_index < len(claim_ids) - 1 else None
        return request.render('tk_insurance_management.web_insurance_claim_detail_view', {
            'claim_rec': claim_record,
            'page_name': 'insurance_claim_form',
            'prev_record': prev_url,
            'next_record': next_url,
        })

    @http.route('/my/claim/report/<string:access_token>', type='http', auth='user', website=True)
    def portal_generate_claim_report(self, access_token):
        """Download claim report PDF for the logged-in user"""
        if not access_token:
            return request.redirect('/my/home')
        claims = request.env['claim.information'].sudo().search([
            ('access_token', '=', access_token),
            ('policy_holder_id', '=', request.env.user.partner_id.id),
        ], limit=1)
        if not claims:
            return request.redirect('/my/home')
        report_ref = 'tk_insurance_management.insurance_claim_report_template'
        response = self._show_report(model=claims, report_type='pdf', report_ref=report_ref,
                                     download=True)
        return response

    @http.route(['/my/insurance-managing-records',
                 '/my/insurance-managing-records/page/<int:page>'], type='http', auth='user',
                website=True)
    def agent_insurance_records_portal_view(self, page=1, **kw):
        """Agent insurance records for the logged-in user."""
        domain = [('agent_id', '=', request.env.user.partner_id.id)]
        page_size = 10
        offset = (page - 1) * page_size

        search = kw.get('search')
        if search:
            domain = domain + [('insurance_number', 'ilike', search)]

        filter_by = kw.get('filter_by')
        if filter_by == 'fixed_commission':
            domain.append(('commission_type', '=', 'fixed'))
        elif filter_by == 'percentage_commission':
            domain.append(('commission_type', '=', 'percentage'))

        total_count = request.env['insurance.information'].sudo().search_count(domain)
        agent_insurance_records = request.env['insurance.information'].sudo().search(
            domain,
            limit=page_size,
            offset=offset,
            order='insurance_number desc'
        )

        pager_details = pager(
            url="/my/insurance-managing-records",
            total=total_count,
            page=page,
            step=page_size,
            scope=5
        )
        return request.render('tk_insurance_management.portal_agent_insurance_record_list', {
            'agent_insurance_records': agent_insurance_records,
            'page_name': 'agent_insurance_list',
            'pager': pager_details,
        })

    @http.route("/my/insurance-record-details/<string:access_token>", type='http', auth="user",
                website=True)
    def agent_insurance_record_details(self, access_token):
        """Agent insurance record for the logged-in user."""
        agent_insurance_record = request.env['insurance.information'].sudo().search(
            [('access_token', '=', access_token),
             ('agent_id', '=', request.env.user.partner_id.id)], limit=1)
        if not agent_insurance_record:
            return request.redirect('/')
        # Get all agent insurance for the logged-in user
        agent_insurances = request.env['insurance.information'].sudo().search([
            ('agent_id', '=', request.env.user.partner_id.id)])
        agent_insurance_ids = agent_insurances.ids
        current_index = agent_insurance_ids.index(
            agent_insurance_record.id) if agent_insurance_record.id in agent_insurance_ids else -1
        if current_index == -1:
            return request.redirect('/')
        # Previous and Next URLs
        prev_url = f"/my/insurance-record-details/{agent_insurances[current_index - 1].access_token}" \
            if current_index > 0 else None
        next_url = f"/my/insurance-record-details/{agent_insurances[current_index + 1].access_token}" \
            if current_index < len(agent_insurance_ids) - 1 else None
        return request.render('tk_insurance_management.portal_agent_insurance_record_details', {
            'agent_ins': agent_insurance_record,
            'page_name': 'agent_insurance_form',
            'prev_record': prev_url,
            'next_record': next_url,
        })

    @http.route('/my/insurance/renewal-request', type='http', auth='user', methods=['POST'],
                website=True, csrf=True)
    def renewal_insurance_policy_request(self, **post):
        """Renewal insurance policy request"""
        insurance_id = post.get('insurance_id')
        if not insurance_id:
            return request.redirect('/')

        insurance = request.env['insurance.information'].sudo().browse(int(insurance_id))
        if not insurance.exists():
            return request.redirect('/')

        crm_lead_rec = request.env['crm.lead'].sudo().create({
            'type': 'lead',
            'previous_insurance_id': insurance.id,
            'policy_holder_dob': insurance.policy_holder_dob,
            'policy_holder_gender': insurance.policy_holder_gender,
            'insurance_category_id': insurance.insurance_category_id.id,
            'insurance_sub_category_id': insurance.insurance_sub_category_id.id,
            'policy_provider_cmp_id': insurance.policy_provider_cmp_id.id,
            'insurance_policy_id': insurance.insurance_policy_id.id,
            'insurance_buying_for_id': insurance.insurance_buying_for_id.id,
            'name': f"Renewal request for {insurance.insurance_number}",
            'partner_id': insurance.policy_holder_id.id,
            'description': f"Renewal request for Insurance Policy: {insurance.insurance_number}",
            'user_id': False,
        })
        insurance.renew_insurance_lead_id = crm_lead_rec.id
        return request.redirect(
            f"/my/insurance/renewal-request-submitted?access_token={insurance.access_token}"
        )

    @http.route('/my/insurance/renewal-request-submitted', type='http', auth="public", website=True,
                methods=['GET'])
    def get_renewal_request_submitted(self, **kwargs):
        """Insurance renewal request submitted"""
        access_token = kwargs.get('access_token')
        policy_url = f'/insurance/policy-details/{access_token}' if access_token else '/'
        return request.render('tk_insurance_management.web_renewal_insurance_submitted', {
            'policy_url': policy_url
        })


class InsurancePortal(CustomerPortal):
    """Insurance Portal"""

    def _prepare_home_portal_values(self, counters):
        """Prepare portal values including insurance counts for policyholders and agents."""
        values = super(InsurancePortal, self)._prepare_home_portal_values(counters)
        partner_id = request.env.user.partner_id.id
        counts = {}

        if 'count' in counters:
            count = request.env['insurance.information'].sudo().search_count([
                ('policy_holder_id', '=', partner_id)
            ])
            counts['count'] = count

        if 'agent_count' in counters:
            agent_count = request.env['insurance.information'].sudo().search_count([
                ('agent_id', '=', partner_id)
            ])
            counts['agent_count'] = agent_count
        values.update(counts)
        return values
