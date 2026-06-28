# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
from datetime import timedelta


class VehicleRentalDashboard(models.Model):
    """Vehicle Rental Dashboard"""
    _name = "vehicle.rental.dashboard"
    _description = __doc__

    @api.model
    def get_vehicle_rental_dashboard(self):
        """Vehicle rental dashboard data"""
        fleet = self.env['fleet.vehicle']
        vc = self.env['vehicle.contract']
        am = self.env['account.move']
        today = fields.Date.today()
        week = today + timedelta(days=7)
        adv_admin = self.env.user.name
        adv_admin_initials = ''.join(p[0].upper() for p in adv_admin.split() if p)[:2] if adv_admin else 'VR'
        adv_admin_avatar = self.env.user.image_1920
        if adv_admin_avatar:
            # Ensure it's a string, not bytes
            if isinstance(adv_admin_avatar, bytes):
                adv_admin_avatar = adv_admin_avatar.decode('utf-8')
            # Strip any whitespace or newlines that can break base64
            adv_admin_avatar = adv_admin_avatar.strip()

        # ── Original fields (unchanged) ──
        total_vehicle = fleet.search_count([])
        available_vehicle = fleet.search_count([('status', '=', 'available')])
        under_maintenance_vehicle = fleet.search_count([('status', '=', 'in_maintenance')])
        draft_vehicle = vc.search_count([])
        in_progress_vehicle = vc.search_count([('status', '=', 'b_in_progress')])
        return_contract = vc.search_count([('status', '=', 'c_return')])
        cancel_contract = vc.search_count([('status', '=', 'd_cancel')])
        customers = self.env['res.partner'].search_count([])
        customer_invoice = am.search_count([('vehicle_contract_id', '!=', False), ('move_type', '=', 'out_invoice')])
        pending_invoices = am.search_count(
            [('vehicle_contract_id', '!=', False), ('payment_state', '!=', 'paid'), ('move_type', '=', 'out_invoice')])

        # ── New: Revenue totals ──
        paid_inv = am.search(
            [('vehicle_contract_id', '!=', False), ('payment_state', '=', 'paid'), ('move_type', '=', 'out_invoice')])
        total_revenue = sum(paid_inv.mapped('amount_total'))
        unpaid_inv = am.search([('vehicle_contract_id', '!=', False), ('payment_state', 'in', ['not_paid', 'partial']),
                                ('move_type', '=', 'out_invoice'), ('state', '=', 'posted')])
        total_receivables = sum(unpaid_inv.mapped('amount_residual'))

        # ── New: Expiring ──
        expiring_today = vc.search_count(
            [('end_date', '>=', str(today) + ' 00:00:00'), ('end_date', '<=', str(today) + ' 23:59:59'),
             ('status', '=', 'b_in_progress')])
        expiring_week = vc.search_count([('end_date', '>=', str(today)), ('end_date', '<=', str(week) + ' 23:59:59'),
                                         ('status', '=', 'b_in_progress')])

        # ── New: Ending soon list ──
        ending_soon = vc.search([('end_date', '>=', str(today)), ('end_date', '<=', str(week) + ' 23:59:59'),
                                 ('status', '=', 'b_in_progress')])
        ending_soon_data = [{'id': c.id, 'reference': c.reference_no or '', 'customer': c.customer_id.name or '',
                             'vehicle': c.vehicle_id.name or '',
                             'end_date': str(c.end_date.date()) if c.end_date else '', 'status': c.status,
                             'rent': c.total_vehicle_rent or 0} for c in ending_soon[:10]]

        # ── New: Overdue invoices ──
        overdue_inv_count = am.search_count(
            [('vehicle_contract_id', '!=', False), ('payment_state', 'in', ['not_paid', 'partial']),
             ('invoice_date_due', '<', str(today)), ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])

        # ── New: Theme color ──
        theme_color = self.env['ir.config_parameter'].sudo().get_param('vehicle_rental.dashboard_theme_color',
                                                                       '#2563eb')

        # ── Company currency symbol ──
        company = self.env.company
        currency_symbol = company.currency_id.symbol if company.currency_id else '₹'
        currency_position = company.currency_id.position if company.currency_id else 'before'
        company_name = company.name or 'Vehicle Rental'

        data = {
            # Original
            'total_vehicle': total_vehicle, 'available_vehicle': available_vehicle,
            'under_maintenance_vehicle': under_maintenance_vehicle, 'draft_vehicle': draft_vehicle,
            'in_progress_vehicle': in_progress_vehicle, 'return_contract': return_contract,
            'cancel_contract': cancel_contract, 'customers': customers,
            'customer_invoice': customer_invoice, 'pending_invoices': pending_invoices,
            'rent_duration': self.get_rent_contract(),
            'rent_invoice_month': self.get_rent_invoice_month(),
            # New
            'total_revenue': total_revenue, 'total_receivables': total_receivables,
            'expiring_today': expiring_today, 'expiring_week': expiring_week,
            'ending_soon': ending_soon_data, 'overdue_invoices': overdue_inv_count,
            'theme_color': theme_color,
            'currency_symbol': currency_symbol,
            'currency_position': currency_position,
            'company_name': company_name,
            'gantt_data': self._get_gantt_data(),
            'revenue_chart': self._get_revenue_by_month(),
            'revenue_chart_q': self._get_revenue_by_quarter(),
            'fleet_comp': self._get_fleet_composition(),
            'rental_type_split': self._get_rental_type_split(),
            'top_vehicles': self._get_top_vehicles_by_revenue(),
            'aging': self._get_receivables_aging(),
            'crm_data': self._get_crm_data(),
            'alerts': self._get_alerts(today, week, overdue_inv_count),
            'right_panel': self._get_right_panel_data(today, week),
            'vehicle_avail_gantt': self._get_vehicle_availability_gantt(),
            'adv_admin': adv_admin,
            'adv_admin_initials': adv_admin_initials,
            'adv_admin_avatar': adv_admin_avatar,
        }
        return data

    # ── Original (unchanged) ──
    def get_rent_contract(self):
        data = []
        for c in self.env['vehicle.contract'].search([('status', '=', 'b_in_progress')]):
            data.append({'name': c.reference_no, 'start_date': str(c.start_date), 'end_date': str(c.end_date)})
        return data

    def get_rent_invoice_month(self):
        year = fields.Date.today().year
        d = {m: 0 for m in
             ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
              'November', 'December']}
        for inv in self.env['account.move'].search(
                [('vehicle_contract_id', '!=', False), ('move_type', '=', 'out_invoice')]):
            if inv.invoice_date and inv.invoice_date.year == year and inv.vehicle_contract_id.status == 'c_return':
                d[inv.invoice_date.strftime('%B')] = d.get(inv.invoice_date.strftime('%B'), 0) + inv.amount_total
        return [list(d.keys()), list(d.values())]

    # ── New helpers ──
    def _get_gantt_data(self):
        contracts = self.env['vehicle.contract'].search([('start_date', '!=', False), ('end_date', '!=', False)],
                                                        limit=100, order='start_date asc')
        smap = {'a_draft': 'upcoming', 'b_in_progress': 'active', 'c_return': 'completed', 'd_cancel': 'cancelled'}
        slbl = {'a_draft': 'New', 'b_in_progress': 'In Progress', 'c_return': 'Returned', 'd_cancel': 'Cancelled'}
        return [{'id': c.id, 'text': c.reference_no or 'Contract #%d' % c.id, 'vehicle': c.vehicle_id.name or '—',
                 'customer': c.customer_id.name or '—',
                 'start_date': str(c.start_date.date()), 'end_date': str(c.end_date.date()),
                 'status': smap.get(c.status, 'upcoming'), 'status_label': slbl.get(c.status, ''),
                 'rent': c.total_vehicle_rent or 0} for c in contracts]

    def _get_revenue_by_month(self):
        year = fields.Date.today().year
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        rev = [0.0] * 12
        maint = [0.0] * 12
        new_contracts = [0] * 12
        active_contracts = [0] * 12
        closed_contracts = [0] * 12
        for inv in self.env['account.move'].search(
                [('vehicle_contract_id', '!=', False), ('move_type', '=', 'out_invoice'),
                 ('payment_state', '=', 'paid')]):
            if inv.invoice_date and inv.invoice_date.year == year:
                rev[inv.invoice_date.month - 1] += inv.amount_total
        billed_mr = {}
        for bill in self.env['account.move'].search(
                [('maintenance_request_id', '!=', False), ('move_type', '=', 'in_invoice'),
                 ('state', '=', 'posted')]):
            if bill.invoice_date and bill.invoice_date.year == year:
                billed_mr[bill.maintenance_request_id.id] = True
                maint[bill.invoice_date.month - 1] += bill.amount_total
        for mr in self.env['maintenance.request'].search([]):
            if mr.id in billed_mr:
                continue
            dt = getattr(mr, 'schedule_date', False) or getattr(mr, 'request_date', False)
            if dt and dt.year == year:
                cost = getattr(mr, 'sub_total', 0) or (
                            getattr(mr, 'part_price', 0) + getattr(mr, 'service_charge', 0)) or getattr(mr, 'cost',
                                                                                                        0) or 0
                if cost:
                    maint[dt.month - 1] += cost
        for c in self.env['vehicle.contract'].search([]):
            if c.start_date and c.start_date.year == year:
                m = c.start_date.month - 1
                if c.status == 'a_draft':
                    new_contracts[m] += 1
                elif c.status == 'b_in_progress':
                    active_contracts[m] += 1
                elif c.status in ('c_return', 'd_cancel'):
                    closed_contracts[m] += 1
        return {
            'labels': months,
            'values': [round(v, 2) for v in rev],
            'maint': [round(m, 2) for m in maint],
            'new_contracts': new_contracts,
            'active_contracts': active_contracts,
            'closed_contracts': closed_contracts,
        }

    def _get_revenue_by_quarter(self):
        year = fields.Date.today().year
        qs = ['Q1', 'Q2', 'Q3', 'Q4']
        rev = [0.0] * 4
        maint = [0.0] * 4
        for inv in self.env['account.move'].search(
                [('vehicle_contract_id', '!=', False), ('move_type', '=', 'out_invoice'),
                 ('payment_state', '=', 'paid')]):
            if inv.invoice_date and inv.invoice_date.year == year:
                rev[(inv.invoice_date.month - 1) // 3] += inv.amount_total
        billed_mr = {}
        for bill in self.env['account.move'].search(
                [('maintenance_request_id', '!=', False), ('move_type', '=', 'in_invoice'),
                 ('state', '=', 'posted')]):
            if bill.invoice_date and bill.invoice_date.year == year:
                billed_mr[bill.maintenance_request_id.id] = True
                maint[(bill.invoice_date.month - 1) // 3] += bill.amount_total
        for mr in self.env['maintenance.request'].search([]):
            if mr.id in billed_mr:
                continue
            dt = getattr(mr, 'schedule_date', False) or getattr(mr, 'request_date', False)
            if dt and dt.year == year:
                cost = getattr(mr, 'sub_total', 0) or (
                            getattr(mr, 'part_price', 0) + getattr(mr, 'service_charge', 0)) or getattr(mr, 'cost',
                                                                                                        0) or 0
                if cost:
                    maint[(dt.month - 1) // 3] += cost
        return {'labels': [q + ' FY' + str(year)[-2:] for q in qs], 'values': [round(v, 2) for v in rev],
                'maint': [round(m, 2) for m in maint]}

    def _get_fleet_composition(self):
        comp = {}
        for v in self.env['fleet.vehicle'].search([]):
            name = (v.tag_ids[0].name if v.tag_ids else (
                v.model_id.brand_id.name if v.model_id and v.model_id.brand_id else 'Other'))
            comp[name] = comp.get(name, 0) + 1
        items = sorted(comp.items(), key=lambda x: x[1], reverse=True)[:8]
        return {'labels': [x[0] for x in items], 'values': [x[1] for x in items]}

    def _get_rental_type_split(self):
        tmap = {'hour': 'Hourly', 'days': 'Daily', 'week': 'Weekly', 'month': 'Monthly', 'year': 'Yearly',
                'km': 'Per KM', 'mi': 'Per Mile'}
        split = {}
        for c in self.env['vehicle.contract'].search([('rent_type', '!=', False)]):
            l = tmap.get(c.rent_type, c.rent_type)
            split[l] = split.get(l, 0) + 1
        items = sorted(split.items(), key=lambda x: x[1], reverse=True)
        return {'labels': [x[0] for x in items], 'values': [x[1] for x in items]}

    def _get_top_vehicles_by_revenue(self):
        vrev = {}
        for inv in self.env['account.move'].search(
                [('vehicle_contract_id', '!=', False), ('move_type', '=', 'out_invoice'),
                 ('payment_state', '=', 'paid')]):
            n = inv.vehicle_contract_id.vehicle_id.name or 'Unknown'
            vrev[n] = vrev.get(n, 0) + inv.amount_total
        items = sorted(vrev.items(), key=lambda x: x[1], reverse=True)[:8]
        return {'labels': [x[0] for x in items], 'values': [round(x[1], 2) for x in items]}

    def _get_receivables_aging(self):
        today = fields.Date.today()
        buckets = {'0-30': 0, '31-60': 0, '61-90': 0, '90+': 0}
        for inv in self.env['account.move'].search(
                [('vehicle_contract_id', '!=', False), ('payment_state', 'in', ['not_paid', 'partial']),
                 ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')]):
            if not inv.invoice_date_due: continue
            days = (today - inv.invoice_date_due).days
            amt = inv.amount_residual
            if days <= 30:
                buckets['0-30'] += amt
            elif days <= 60:
                buckets['31-60'] += amt
            elif days <= 90:
                buckets['61-90'] += amt
            else:
                buckets['90+'] += amt
        return {'labels': ['0–30 days', '31–60 days', '61–90 days', '90+ days'],
                'values': [round(v, 2) for v in buckets.values()]}

    def _get_crm_data(self):
        leads = self.env['crm.lead'].search([], limit=200)
        stage_counts = {}
        for l in leads:
            s = l.stage_id.name or 'Unknown'
            stage_counts[s] = stage_counts.get(s, 0) + 1
        funnel = [{'stage': s, 'count': c} for s, c in sorted(stage_counts.items(), key=lambda x: x[1], reverse=True)]
        return {'total_leads': len(leads), 'won_leads': self.env['crm.lead'].search_count([('probability', '=', 100)]),
                'funnel': funnel[:6]}

    def _get_alerts(self, today, week, overdue_count):
        vc = self.env['vehicle.contract']
        return {
            'expiring_today': vc.search_count(
                [('end_date', '>=', str(today) + ' 00:00:00'), ('end_date', '<=', str(today) + ' 23:59:59'),
                 ('status', '=', 'b_in_progress')]),
            'expiring_week': vc.search_count(
                [('end_date', '>=', str(today)), ('end_date', '<=', str(week) + ' 23:59:59'),
                 ('status', '=', 'b_in_progress')]),
            'overdue_invoices': overdue_count,
            'under_maintenance': self.env['fleet.vehicle'].search_count([('status', '=', 'in_maintenance')]),
            'cancelled_contracts': vc.search_count([('status', '=', 'd_cancel')]),
        }

    def _get_right_panel_data(self, today, week):
        vc = self.env['vehicle.contract']
        am = self.env['account.move']
        tomorrow = today + timedelta(days=1)
        # Contracts ending critical
        exp_today = vc.search_count(
            [('end_date', '>=', str(today) + ' 00:00:00'), ('end_date', '<=', str(today) + ' 23:59:59'),
             ('status', '=', 'b_in_progress')])
        exp_tomorrow = vc.search_count(
            [('end_date', '>=', str(tomorrow) + ' 00:00:00'), ('end_date', '<=', str(tomorrow) + ' 23:59:59'),
             ('status', '=', 'b_in_progress')])
        exp_week = vc.search_count([('end_date', '>=', str(today)), ('end_date', '<=', str(week) + ' 23:59:59'),
                                    ('status', '=', 'b_in_progress')])
        # Receivables aging buckets (quick version)
        aging_30 = aging_60 = aging_90p = 0.0
        for inv in am.search([('vehicle_contract_id', '!=', False), ('payment_state', 'in', ['not_paid', 'partial']),
                              ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')]):
            if not inv.invoice_date_due: continue
            days = (today - inv.invoice_date_due).days
            amt = inv.amount_residual
            if days <= 30:
                aging_30 += amt
            elif days <= 60:
                aging_60 += amt
            else:
                aging_90p += amt
        total_recv = aging_30 + aging_60 + aging_90p
        # Maintenance queue
        maint_overdue = self.env['maintenance.request'].search_count(
            [('schedule_date', '<', str(today)), ('stage_id.done', '=', False)])
        maint_upcoming = self.env['maintenance.request'].search_count(
            [('schedule_date', '>=', str(today)), ('schedule_date', '<=', str(week))])
        return {
            'exp_today': exp_today, 'exp_tomorrow': exp_tomorrow, 'exp_week': exp_week,
            'aging_30': round(aging_30, 2), 'aging_60': round(aging_60, 2), 'aging_90p': round(aging_90p, 2),
            'total_recv': round(total_recv, 2),
            'maint_overdue': maint_overdue, 'maint_upcoming': maint_upcoming,
            'active_contracts': vc.search_count([('status', '=', 'b_in_progress')]),
            'pending_renewals': exp_week,
        }

    def _get_vehicle_availability_gantt(self):
        """Vehicle availability timeline for Gantt — shows booked vs free periods"""
        today = fields.Date.today()
        from datetime import timedelta
        start = today - timedelta(days=15)
        end = today + timedelta(days=45)

        vehicles = self.env['fleet.vehicle'].search([], limit=40, order='name asc')
        contracts = self.env['vehicle.contract'].search([
            ('start_date', '!=', False),
            ('end_date', '!=', False),
            ('status', 'in', ['a_draft', 'b_in_progress']),
            ('end_date', '>=', str(start)),
            ('start_date', '<=', str(end) + ' 23:59:59'),
        ])

        # Group contracts by vehicle
        veh_contracts = {}
        for c in contracts:
            vid = c.vehicle_id.id
            if vid not in veh_contracts:
                veh_contracts[vid] = []
            veh_contracts[vid].append(c)

        tasks = []
        task_id = 1
        for veh in vehicles:
            veh_tasks = veh_contracts.get(veh.id, [])
            if not veh_tasks:
                # Vehicle is fully free in range — show one free bar
                tasks.append({
                    'id': task_id,
                    'text': veh.name or veh.license_plate or f'Vehicle {veh.id}',
                    'start_date': str(start),
                    'end_date': str(end),
                    'type': 'free',
                    'vehicle_id': veh.id,
                    'license': veh.license_plate or '',
                    'db_id': None,
                    'customer': '',
                    'contract_ref': '',
                })
                task_id += 1
            else:
                # Show booked segments
                for c in veh_tasks:
                    sd = max(c.start_date.date(), start)
                    ed = min(c.end_date.date(), end)
                    if sd > ed:
                        continue
                    tasks.append({
                        'id': task_id,
                        'text': veh.name or veh.license_plate or '',
                        'start_date': str(sd),
                        'end_date': str(ed),
                        'type': 'booked',
                        'vehicle_id': veh.id,
                        'license': veh.license_plate or '',
                        'db_id': c.id,
                        'customer': c.customer_id.name or '',
                        'contract_ref': c.reference_no or '',
                        'status': c.status,
                    })
                    task_id += 1

        return {
            'tasks': tasks,
            'range_start': str(start),
            'range_end': str(end),
        }
