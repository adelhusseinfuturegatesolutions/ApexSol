/** @odoo-module **/
import {registry} from "@web/core/registry";
import {getDefaultConfig} from "@web/views/view";
import {useService} from "@web/core/utils/hooks";
import {loadJS} from "@web/core/assets";

const {Component, useSubEnv, useState, onMounted, onWillStart, useRef} = owl;

/* ────────────────────────────────────────────────
   THEME PRESETS  (10 predefined)
──────────────────────────────────────────────── */
const THEMES = {
    '#2563eb': {rgb: '37,99,235', dark: '#1d4ed8'},
    '#7c3aed': {rgb: '124,58,237', dark: '#6d28d9'},
    '#0891b2': {rgb: '8,145,178', dark: '#0e7490'},
    '#059669': {rgb: '5,150,105', dark: '#047857'},
    '#dc2626': {rgb: '220,38,38', dark: '#b91c1c'},
    '#ea580c': {rgb: '234,88,12', dark: '#c2410c'},
    '#d97706': {rgb: '217,119,6', dark: '#b45309'},
    '#db2777': {rgb: '219,39,119', dark: '#be185d'},
    '#0f172a': {rgb: '15,23,42', dark: '#020617'},
    '#374151': {rgb: '55,65,81', dark: '#1f2937'},
};

class VehicleRentalDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        useSubEnv({config: {...getDefaultConfig(), ...this.env.config}});

        this.state = useState({
            data: null, loading: true,
            sec: "overview",
            ganttZoom: "month",
            availZoom: "week",
            revMode: "monthly",
        });

        this._charts = {};
        this._contractGanttInited = false;
        this._availGanttInited = false;
        this._ganttEvt = null;
        this._availEvt = null;

        this.contractDurations = useRef('rent_contract_duration');
        this.invoiceStatusGraph = useRef('invoice_status_graph');

        onWillStart(async () => {
            const d = await this.orm.call('vehicle.rental.dashboard', 'get_vehicle_rental_dashboard', []);
            if (d) {
                this.state.data = d;
                this.state.loading = false;
                // Store currency for use in _fmt()
                this._currencySymbol = d.currency_symbol || '₹';
                this._currencyPosition = d.currency_position || 'before';
            }
        });

        onMounted(() => {
            if (!this.state.data) return;
            // Apply theme here (DOM is ready), not in onWillStart
            this._applyTheme(this.state.data.theme_color || '#2563eb');
            setTimeout(() => {
                this._buildCharts();
                this._buildContractGantt();
            }, 80);
        });
    }

    /* ── Theme ──────────────────────────────────── */
    _applyTheme(hex) {
        const preset = THEMES[hex] || THEMES['#2563eb'];
        const el = document.querySelector('.vr-dashboard');
        if (!el) return;
        el.style.setProperty('--vrd-brand', hex);
        el.style.setProperty('--vrd-brand-d', preset.dark);
        el.style.setProperty('--vrd-brand-rgb', preset.rgb);
        el.style.setProperty('--vrd-t05', `rgba(${preset.rgb},0.05)`);
        el.style.setProperty('--vrd-t10', `rgba(${preset.rgb},0.10)`);
        el.style.setProperty('--vrd-t15', `rgba(${preset.rgb},0.15)`);
        el.style.setProperty('--vrd-t25', `rgba(${preset.rgb},0.25)`);
        el.style.setProperty('--vrd-t40', `rgba(${preset.rgb},0.40)`);
        el.style.setProperty('--vrd-grad-brand', `linear-gradient(135deg,rgba(${preset.rgb},0.05) 0%,rgba(${preset.rgb},0.12) 100%)`);
    }

    _brand() {
        const el = document.querySelector('.vr-dashboard');
        return el ? el.style.getPropertyValue('--vrd-brand') || '#2563eb' : '#2563eb';
    }

    /* ── Palette ────────────────────────────────── */
    _pal(n) {
        const b = this._brand();
        const pr = THEMES[b] || THEMES['#2563eb'];
        const [r, g, bl] = pr.rgb.split(',').map(Number);
        const steps = ['dd', 'bb', '99', '77', '55', '44', '33', '22'];
        return Array.from({length: n}, (_, i) => {
            const shift = i * 16;
            const nr = Math.min(255, r + shift), ng = Math.min(255, g + shift * 0.6), nb = Math.min(255, bl);
            return `rgba(${nr},${ng},${nb},${0.65 + (i % 4) * 0.08})`;
        });
    }

    /* ── Section switch ─────────────────────────── */
    switchSection(sec) {
        this.state.sec = sec;
        setTimeout(() => {
            this._destroyCharts();
            this._buildCharts();
            if (sec === 'contracts') {
                this._buildContractGantt();
                this._buildAvailGantt();
            }
            if (sec === 'gantt') {
                this._buildGanttSection();
            }
            if (sec === 'availability') {
                this._buildAvailabilitySection();
            }
        }, 60);
    }

    /* ── Charts ─────────────────────────────────── */
    _destroyCharts() {
        Object.values(this._charts).forEach(c => {
            try {
                c.destroy();
            } catch (_) {
            }
        });
        this._charts = {};
    }

    _tip() {
        return {
            backgroundColor: '#fff',
            borderColor: '#e4eaf5',
            borderWidth: 1.5,
            padding: 10,
            titleColor: '#111827',
            bodyColor: '#4b5563',
            cornerRadius: 8,
            displayColors: true
        };
    }

    _base() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        padding: 12,
                        usePointStyle: true,
                        pointStyleWidth: 8,
                        color: '#6b7280',
                        font: {size: 10}
                    }
                }, tooltip: this._tip()
            }
        };
    }

    _buildCharts() {
        if (!this.state.data || typeof Chart === 'undefined') return;
        const d = this.state.data;
        Chart.defaults.color = '#9ca3af';
        Chart.defaults.borderColor = '#e4eaf5';
        Chart.defaults.font.size = 11;

        const rv = this.state.revMode === 'quarterly' ? d.revenue_chart_q : d.revenue_chart;

        // Revenue
        const revEl = document.getElementById('vr-revenueChart');
        if (revEl) {
            const brand = this._brand(), pr = THEMES[brand] || THEMES['#2563eb'], rgb = pr.rgb;
            this._charts.rev = new Chart(revEl, {
                type: 'line',

                data: {
                    labels: rv.labels, datasets: [
                        {
                            label: 'Revenue',
                            data: rv.values,
                            borderColor: brand,
                            backgroundColor: `rgba(${rgb},0.08)`,
                            borderWidth: 2,
                            fill: true,
                            tension: .4,
                            pointBackgroundColor: brand,
                            pointRadius: 3,
                            pointHoverRadius: 6
                        },
                        {
                            label: 'Maintenance',
                            data: rv.maint || rv.values.map(() => 0),
                            borderColor: '#f59e0b',
                            backgroundColor: 'rgba(245,158,11,0.06)',
                            borderWidth: 2,
                            fill: true,
                            tension: .4,
                            pointBackgroundColor: '#f59e0b',
                            pointRadius: 3,
                            pointHoverRadius: 6
                        },
                    ]
                },
                options: {
                    ...(this._base()),
                    scales: {
                        x: {grid: {color: '#f1f5fb'}},
                        y: {grid: {color: '#f1f5fb'}, ticks: {callback: v => this._fmt(v)}}
                    },
                    onClick: () => this._open('account.move',
                        [['vehicle_contract_id', '!=', false], ['payment_state', '=', 'paid'], ['move_type', '=', 'out_invoice']],
                        'Invoices')
                }
            });
        }
        // Fleet donut
        const fdEl = document.getElementById('vr-fleetDonut');
        if (fdEl && d.fleet_comp?.labels?.length) {
            this._charts.fd = new Chart(fdEl, {
                type: 'doughnut',
                data: {
                    labels: d.fleet_comp.labels,
                    datasets: [{
                        data: d.fleet_comp.values,
                        backgroundColor: this._pal(d.fleet_comp.labels.length),
                        borderColor: '#fff',
                        borderWidth: 3,
                        hoverOffset: 8
                    }]
                },
                options: {
                    ...(this._base()), cutout: '64%', onClick: () => this._open('fleet.vehicle',
                        [],
                        'Vehicles')
                }
            });
        }
        // Rental pie
        const rpEl = document.getElementById('vr-rentalPie');
        if (rpEl && d.rental_type_split?.labels?.length) {
            this._charts.rp = new Chart(rpEl, {
                type: 'pie',
                data: {
                    labels: d.rental_type_split.labels,
                    datasets: [{
                        data: d.rental_type_split.values,
                        backgroundColor: this._pal(d.rental_type_split.labels.length),
                        borderColor: '#fff',
                        borderWidth: 3
                    }]
                },
                options: {
                    ...(this._base()), onClick: () => this._open('vehicle.contract',
                        [],
                        'Contracts')
                }
            });
        }
        // Top vehicles
        const vbEl = document.getElementById('vr-vehicleBar');
        if (vbEl && d.top_vehicles?.labels?.length) {
            this._charts.vb = new Chart(vbEl, {
                type: 'bar',
                data: {
                    labels: d.top_vehicles.labels,
                    datasets: [{
                        label: 'Revenue',
                        data: d.top_vehicles.values,
                        backgroundColor: this._pal(d.top_vehicles.labels.length),
                        borderRadius: 5,
                        borderSkipped: false
                    }]
                },
                options: {
                    ...(this._base()), indexAxis: 'y',
                    plugins: {...(this._base()).plugins, legend: {display: false}},
                    scales: {
                        x: {grid: {color: '#f1f5fb'}, ticks: {callback: v => this._fmt(v)}},
                        y: {grid: {display: false}}
                    },
                    onClick: () => this._open('fleet.vehicle',
                        [],
                        'Vehicles')
                }
            });
        }
        // Contract activity timeline (stacked bar)
        const ctEl = document.getElementById('vr-contractTimeline');
        if (ctEl && d.revenue_chart) {
            const brand = this._brand(), pr = THEMES[brand] || THEMES['#2563eb'], rgb = pr.rgb;
            this._charts.ct = new Chart(ctEl, {
                type: 'bar',
                data: {
                    labels: d.revenue_chart.labels, datasets: [
                        {
                            label: 'New',
                            data: d.revenue_chart.new_contracts || d.revenue_chart.values.map(() => 0),
                            backgroundColor: `rgba(${rgb},0.75)`,
                            borderRadius: {topLeft: 4, topRight: 4},
                            stack: 's'
                        },
                        {
                            label: 'Active',
                            data: d.revenue_chart.active_contracts || d.revenue_chart.values.map(() => 0),
                            backgroundColor: 'rgba(16,185,129,0.75)',
                            borderRadius: {topLeft: 4, topRight: 4},
                            stack: 's'
                        },
                        {
                            label: 'Closed',
                            data: d.revenue_chart.closed_contracts || d.revenue_chart.values.map(() => 0),
                            backgroundColor: 'rgba(107,114,128,0.55)',
                            borderRadius: {topLeft: 4, topRight: 4},
                            stack: 's'
                        },
                    ]
                },
                options: {
                    ...(this._base()),
                    scales: {x: {grid: {display: false}, stacked: true}, y: {grid: {color: '#f1f5fb'}, stacked: true}},
                    plugins: {
                        ...(this._base()).plugins,
                        legend: {position: 'bottom', labels: {font: {size: 10}, padding: 10}}
                    }
                }
            });
        }
        // CRM funnel
        const crmEl = document.getElementById('vr-crmFunnel');
        if (crmEl && d.crm_data?.funnel?.length) {
            this._charts.crm = new Chart(crmEl, {
                type: 'bar',
                data: {
                    labels: d.crm_data.funnel.map(f => f.stage),
                    datasets: [{
                        label: 'Leads',
                        data: d.crm_data.funnel.map(f => f.count),
                        backgroundColor: this._pal(d.crm_data.funnel.length),
                        borderRadius: 5
                    }]
                },
                options: {
                    ...(this._base()), plugins: {...(this._base()).plugins, legend: {display: false}},
                    scales: {
                        y: {grid: {color: '#f1f5fb'}},
                        x: {grid: {display: false}, ticks: {maxRotation: 30, font: {size: 10}}}
                    },
                    onClick: () => this._open('crm.lead', [], 'Leads')
                }
            });
        }
        // Aging
        const agEl = document.getElementById('vr-agingChart');
        if (agEl && d.aging) {
            this._charts.ag = new Chart(agEl, {
                type: 'bar',
                data: {
                    labels: d.aging.labels,
                    datasets: [{
                        label: 'Amount',
                        data: d.aging.values,
                        backgroundColor: ['#3b82f6', '#f59e0b', '#f97316', '#e11d48'],
                        borderRadius: 5,
                        borderSkipped: false
                    }]
                },
                options: {
                    ...(this._base()), plugins: {...(this._base()).plugins, legend: {display: false}},
                    scales: {
                        x: {grid: {display: false}},
                        y: {grid: {color: '#f1f5fb'}, ticks: {callback: v => this._fmt(v)}}
                    }
                }
            });
        }
    }

    /* ── Contract Gantt ─────────────────────────── */
    _buildContractGantt() {
        if (typeof gantt === 'undefined') return;
        const elId = 'vr-ganttChart';
        const el = document.getElementById(elId);
        if (!el || !this.state.data?.gantt_data?.length) return;
        const brand = this._brand();

        try {
            gantt.clearAll();
        } catch (_) {
        }
        this._configGantt(this.state.ganttZoom);
        gantt.config.columns = [
            {name: 'text', label: 'Contract', width: 125, resize: true},
            {name: 'vehicle', label: 'Vehicle', width: 100, resize: true, template: t => t.vehicle || '—'},
            {name: 'customer', label: 'Customer', width: 100, resize: true, template: t => t.customer || '—'},
            {
                name: 'status_label', label: 'Status', width: 85, resize: true,
                template: t => {
                    const clr = {
                        active: '#10b981',
                        cancelled: '#e11d48',
                        completed: '#6b7280',
                        upcoming: brand
                    }[t.status] || brand;
                    const bg = {
                        active: '#ecfdf5',
                        cancelled: '#fff1f2',
                        completed: '#f9fafb',
                        upcoming: `rgba(${(THEMES[brand] || THEMES['#2563eb']).rgb},0.08)`
                    }[t.status] || '#f0f9ff';
                    return `<span style="font-size:9px;font-weight:700;padding:2px 7px;border-radius:20px;background:${bg};color:${clr}">${t.status_label || ''}</span>`;
                }
            },
        ];
        gantt.templates.task_class = (s, e, t) => ({
            active: 'gantt-active',
            completed: 'gantt-completed',
            cancelled: 'gantt-cancelled',
            upcoming: 'gantt-upcoming'
        }[t.status] || 'gantt-upcoming');
        gantt.templates.tooltip_text = (s, e, t) => {
            const days = Math.round((e - s) / 864e5),
                fmt = d => d.toLocaleDateString('en-IN', {day: '2-digit', month: 'short', year: 'numeric'});
            return `<b style="font-size:12px">${t.text}</b><br><span style="color:#9ca3af">Vehicle:</span> <b>${t.vehicle || '—'}</b><br><span style="color:#9ca3af">Customer:</span> <b>${t.customer || '—'}</b><br><span style="color:#9ca3af">Duration:</span> <b>${days} day${days !== 1 ? 's' : ''}</b><br><span style="color:#9ca3af">Status:</span> <b>${t.status_label}</b>${t.rent ? `<br><span style="color:#9ca3af">Value:</span> <b>${this._fmt(t.rent)}</b>` : ''}`;
        };

        if (this._ganttEvt) {
            try {
                gantt.detachEvent(this._ganttEvt);
            } catch (_) {
            }
        }
        this._ganttEvt = gantt.attachEvent('onTaskClick', (id) => {
            const task = gantt.getTask(id);
            if (task?.db_id) this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'vehicle.contract',
                res_id: parseInt(task.db_id),
                views: [[false, 'form']],
                target: 'current'
            });
            return true;
        });

        if (!this._contractGanttInited) {
            gantt.init(elId);
            this._contractGanttInited = true;
        } else {
            try {
                gantt.render();
            } catch (_) {
            }
        }

        const tasks = {data: [], links: []};
        this.state.data.gantt_data.forEach((c, i) => {
            if (!c.start_date || !c.end_date) return;
            const sd = new Date(c.start_date), ed = new Date(c.end_date);
            if (isNaN(sd.getTime()) || isNaN(ed.getTime())) return;
            const safeEd = ed <= sd ? new Date(sd.getTime() + 86400000) : ed;
            tasks.data.push({
                id: i + 1,
                db_id: c.id,
                text: c.text,
                vehicle: c.vehicle,
                customer: c.customer,
                start_date: c.start_date,
                end_date: safeEd.toISOString().slice(0, 10),
                status: c.status,
                status_label: c.status_label,
                rent: c.rent,
                progress: c.status === 'completed' ? 1 : c.status === 'active' ? 0.5 : 0
            });
        });
        gantt.parse(tasks);
    }

    /* ── Availability Gantt ─────────────────────── */
    _buildAvailGantt() {
        if (typeof gantt === 'undefined') return;
        // We need a second gantt container — dhtmlxGantt is a singleton,
        // so we render vehicle availability as a separate styled table instead.
        // Build it as HTML for correctness.
        const container = document.getElementById('vr-availChart');
        if (!container || !this.state.data?.vehicle_avail_gantt) return;

        const avData = this.state.data.vehicle_avail_gantt;
        const today = new Date().toISOString().slice(0, 10);
        const start = new Date(avData.range_start);
        const end = new Date(avData.range_end);
        const totalDays = Math.round((end - start) / 864e5) + 1;

        // Group tasks by vehicle_id
        const byVeh = {};
        for (const t of (avData.tasks || [])) {
            if (!byVeh[t.vehicle_id]) byVeh[t.vehicle_id] = {name: t.text, license: t.license, tasks: []};
            byVeh[t.vehicle_id].tasks.push(t);
        }

        const brand = this._brand();
        const pr = THEMES[brand] || THEMES['#2563eb'];

        // Build header dates
        let hdHtml = '<div class="vra-header"><div class="vra-label">Vehicle</div><div class="vra-bar-area">';
        // Show week labels
        let d = new Date(start);
        while (d <= end) {
            const pct = ((d - start) / 864e5 / totalDays * 100).toFixed(2);
            hdHtml += `<div class="vra-wk-label" style="left:${pct}%">${d.toLocaleDateString('en-IN', {
                day: '2-digit',
                month: 'short'
            })}</div>`;
            d = new Date(d.getTime() + 7 * 864e5);
        }
        // Today marker
        const todayPct = ((new Date(today) - start) / 864e5 / totalDays * 100).toFixed(2);
        hdHtml += `<div class="vra-today-line" style="left:${todayPct}%"></div>`;
        hdHtml += '</div></div>';

        // Build rows
        let rowsHtml = '';
        for (const [vid, veh] of Object.entries(byVeh)) {
            let barsHtml = `<div class="vra-today-line" style="left:${todayPct}%"></div>`;
            for (const t of veh.tasks) {
                const ts = Math.max(new Date(t.start_date), start);
                const te = Math.min(new Date(t.end_date), end);
                if (ts > te) continue;
                const left = ((ts - start) / 864e5 / totalDays * 100).toFixed(2);
                const width = ((te - ts) / 864e5 / totalDays * 100).toFixed(2);
                const isBooked = t.type === 'booked';
                const cls = isBooked ? 'avail-booked' : 'avail-free';
                const label = isBooked ? (t.customer || t.contract_ref || 'Booked') : 'Available';
                const tip = isBooked
                    ? `title="Booked: ${t.contract_ref || ''} · ${t.customer || ''} · ${t.start_date} → ${t.end_date}"`
                    : `title="Available · ${t.start_date} → ${t.end_date}"`;
                barsHtml += `<div class="vra-bar ${cls}" style="left:${left}%;width:${width}%" ${tip} data-vid="${vid}" data-dbid="${t.db_id || ''}">${width > 5 ? label : ''}</div>`;
            }
            rowsHtml += `<div class="vra-row"><div class="vra-label"><span class="vra-vname">${veh.name}</span><span class="vra-lplate">${veh.license}</span></div><div class="vra-bar-area">${barsHtml}</div></div>`;
        }

        if (!rowsHtml) {
            container.innerHTML = '<div class="vr-empty" style="padding:28px"><div class="vr-empty-icon">🚗</div><div class="vr-empty-text">No vehicle data available</div></div>';
            return;
        }

        container.innerHTML = `
<style>
.vra-header,.vra-row{display:flex;align-items:center;border-bottom:1px solid var(--vrd-bdr);}
.vra-header{background:var(--vrd-sf2);font-size:9.5px;font-weight:700;color:var(--vrd-tx3);text-transform:uppercase;letter-spacing:.4px;position:sticky;top:0;z-index:2;}
.vra-label{width:160px;min-width:160px;padding:6px 12px;border-right:1px solid var(--vrd-bdr);display:flex;flex-direction:column;gap:1px;}
.vra-vname{font-size:11px;font-weight:600;color:var(--vrd-tx);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.vra-lplate{font-size:9px;color:var(--vrd-tx3);}
.vra-bar-area{flex:1;height:36px;position:relative;background:var(--vrd-sf3);}
.vra-header .vra-bar-area{height:28px;}
.vra-row:hover .vra-bar-area{background:var(--vrd-t05);}
.vra-bar{position:absolute;top:5px;height:26px;border-radius:6px;font-size:9.5px;font-weight:600;color:#fff;display:flex;align-items:center;padding:0 7px;cursor:pointer;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;transition:opacity .15s,transform .15s;}
.vra-bar:hover{opacity:.85;transform:scaleY(1.06);}
.avail-booked{background:linear-gradient(90deg,#f59e0b,#fbbf24);box-shadow:0 2px 6px rgba(245,158,11,.25);}
.avail-free{background:linear-gradient(90deg,#10b981,#6ee7b7);opacity:.6;}
.avail-free:hover{opacity:.8;}
.vra-wk-label{position:absolute;top:6px;font-size:8.5px;color:var(--vrd-tx3);transform:translateX(-50%);white-space:nowrap;}
.vra-today-line{position:absolute;top:0;bottom:0;width:2px;background:var(--vrd-danger);opacity:.7;pointer-events:none;z-index:1;}
</style>
${hdHtml}
<div style="overflow-y:auto;max-height:340px;">${rowsHtml}</div>`;

        // Click handler for booked bars
        container.querySelectorAll('.avail-booked[data-dbid]').forEach(bar => {
            bar.addEventListener('click', () => {
                const dbId = bar.getAttribute('data-dbid');
                if (dbId) this.action.doAction({
                    type: 'ir.actions.act_window',
                    res_model: 'vehicle.contract',
                    res_id: parseInt(dbId),
                    views: [[false, 'form']],
                    target: 'current'
                });
            });
        });
    }

    /* ── Contract Gantt Section (dedicated full-page nav) ── */
    _buildGanttSection() {
        if (typeof gantt === 'undefined') return;
        const elId2 = 'vr-ganttChart2';
        const el2 = document.getElementById(elId2);
        if (!el2 || !this.state.data?.gantt_data?.length) return;

        // Set full-page height before init so dhtmlxGantt reads a pixel height
        const contentEl = document.querySelector('.vr-content-full');
        const secEl = el2.closest('.vr-gantt-fill');
        const headerEl = secEl?.querySelector('.vr-gantt-header');
        const legendEl = secEl?.querySelector('.vr-gantt-legend');
        const availH = (contentEl?.clientHeight || window.innerHeight - 100)
            - (headerEl?.offsetHeight || 55)
            - (legendEl?.offsetHeight || 36)
            - 2;
        el2.style.height = Math.max(280, availH) + 'px';

        const brand = this._brand();
        try { gantt.clearAll(); } catch (_) {}
        this._configGantt(this.state.ganttZoom);
        gantt.config.columns = [
            {name: 'text', label: 'Contract', width: 125, resize: true},
            {name: 'vehicle', label: 'Vehicle', width: 100, resize: true, template: t => t.vehicle || '—'},
            {name: 'customer', label: 'Customer', width: 100, resize: true, template: t => t.customer || '—'},
            {
                name: 'status_label', label: 'Status', width: 85, resize: true,
                template: t => {
                    const clr = {active:'#10b981',cancelled:'#e11d48',completed:'#6b7280',upcoming:brand}[t.status] || brand;
                    const bg  = {active:'#ecfdf5',cancelled:'#fff1f2',completed:'#f9fafb',upcoming:`rgba(${(THEMES[brand]||THEMES['#2563eb']).rgb},0.08)`}[t.status] || '#f0f9ff';
                    return `<span style="font-size:9px;font-weight:700;padding:2px 7px;border-radius:20px;background:${bg};color:${clr}">${t.status_label||''}</span>`;
                }
            },
        ];
        gantt.templates.task_class = (s, e, t) =>
            ({active:'gantt-active',completed:'gantt-completed',cancelled:'gantt-cancelled',upcoming:'gantt-upcoming'}[t.status] || 'gantt-upcoming');
        gantt.templates.tooltip_text = (s, e, t) => {
            const days = Math.round((e - s) / 864e5);
            return `<b style="font-size:12px">${t.text}</b><br><span style="color:#9ca3af">Vehicle:</span> <b>${t.vehicle||'—'}</b><br><span style="color:#9ca3af">Customer:</span> <b>${t.customer||'—'}</b><br><span style="color:#9ca3af">Duration:</span> <b>${days} day${days!==1?'s':''}</b><br><span style="color:#9ca3af">Status:</span> <b>${t.status_label}</b>${t.rent?`<br><span style="color:#9ca3af">Value:</span> <b>${this._fmt(t.rent)}</b>`:''}`;
        };
        if (this._ganttEvt) { try { gantt.detachEvent(this._ganttEvt); } catch(_){} }
        this._ganttEvt = gantt.attachEvent('onTaskClick', (id) => {
            const task = gantt.getTask(id);
            if (task?.db_id) this.action.doAction({
                type: 'ir.actions.act_window', res_model: 'vehicle.contract',
                res_id: parseInt(task.db_id), views: [[false, 'form']], target: 'current'
            });
            return true;
        });
        this._contractGanttInited = false;
        gantt.init(elId2);
        this._contractGanttInited = true;
        const tasks = {data: [], links: []};
        this.state.data.gantt_data.forEach((c, i) => {
            if (!c.start_date || !c.end_date) return;
            const sd = new Date(c.start_date), ed = new Date(c.end_date);
            if (isNaN(sd.getTime()) || isNaN(ed.getTime())) return;
            const safeEd = ed <= sd ? new Date(sd.getTime() + 86400000) : ed;
            tasks.data.push({
                id: i + 1, db_id: c.id, text: c.text, vehicle: c.vehicle, customer: c.customer,
                start_date: c.start_date, end_date: safeEd.toISOString().slice(0, 10),
                status: c.status, status_label: c.status_label, rent: c.rent,
                progress: c.status === 'completed' ? 1 : c.status === 'active' ? 0.5 : 0
            });
        });
        gantt.parse(tasks);
    }

    /* ── Vehicle Availability Section (dedicated full-page nav) ── */
    _buildAvailabilitySection() {
        const container = document.getElementById('vr-availChart2');
        if (!container || !this.state.data?.vehicle_avail_gantt) return;

        const avData = this.state.data.vehicle_avail_gantt;
        const today  = new Date().toISOString().slice(0, 10);
        const start  = new Date(avData.range_start);
        const end    = new Date(avData.range_end);
        const totalDays = Math.round((end - start) / 864e5) + 1;

        // Set full-page height for the container
        const contentEl = document.querySelector('.vr-content-full');
        const secEl = container.closest('.vr-gantt-fill');
        const headerEl = secEl?.querySelector('.vr-gantt-header');
        const legendEl = secEl?.querySelector('.vr-gantt-legend');
        const availH = (contentEl?.clientHeight || window.innerHeight - 100)
            - (headerEl?.offsetHeight || 55)
            - (legendEl?.offsetHeight || 36)
            - 2;
        container.style.height = Math.max(280, availH) + 'px';
        container.style.overflowY = 'auto';

        const byVeh = {};
        for (const t of (avData.tasks || [])) {
            if (!byVeh[t.vehicle_id]) byVeh[t.vehicle_id] = {name: t.text, license: t.license, tasks: []};
            byVeh[t.vehicle_id].tasks.push(t);
        }

        const todayPct = ((new Date(today) - start) / 864e5 / totalDays * 100).toFixed(2);
        let hdHtml = '<div class="vra-header"><div class="vra-label">Vehicle</div><div class="vra-bar-area">';
        let d = new Date(start);
        while (d <= end) {
            const pct = ((d - start) / 864e5 / totalDays * 100).toFixed(2);
            hdHtml += `<div class="vra-wk-label" style="left:${pct}%">${d.toLocaleDateString('en-IN',{day:'2-digit',month:'short'})}</div>`;
            d = new Date(d.getTime() + 7 * 864e5);
        }
        hdHtml += `<div class="vra-today-line" style="left:${todayPct}%"></div></div></div>`;

        let rowsHtml = '';
        for (const [vid, veh] of Object.entries(byVeh)) {
            let barsHtml = `<div class="vra-today-line" style="left:${todayPct}%"></div>`;
            for (const t of veh.tasks) {
                const ts = Math.max(new Date(t.start_date), start);
                const te = Math.min(new Date(t.end_date), end);
                if (ts > te) continue;
                const left  = ((ts - start) / 864e5 / totalDays * 100).toFixed(2);
                const width = ((te - ts) / 864e5 / totalDays * 100).toFixed(2);
                const isBooked = t.type === 'booked';
                const cls   = isBooked ? 'avail-booked' : 'avail-free';
                const label = isBooked ? (t.customer || t.contract_ref || 'Booked') : 'Available';
                const tip   = isBooked
                    ? `title="Booked: ${t.contract_ref||''} · ${t.customer||''} · ${t.start_date} → ${t.end_date}"`
                    : `title="Available · ${t.start_date} → ${t.end_date}"`;
                barsHtml += `<div class="vra-bar ${cls}" style="left:${left}%;width:${width}%" ${tip} data-vid="${vid}" data-dbid="${t.db_id||''}">${parseFloat(width) > 5 ? label : ''}</div>`;
            }
            rowsHtml += `<div class="vra-row"><div class="vra-label"><span class="vra-vname">${veh.name}</span><span class="vra-lplate">${veh.license}</span></div><div class="vra-bar-area">${barsHtml}</div></div>`;
        }

        if (!rowsHtml) {
            container.innerHTML = '<div class="vr-empty" style="padding:40px;height:100%;justify-content:center;"><div class="vr-empty-icon">🚗</div><div class="vr-empty-text">No vehicle availability data found.</div></div>';
            return;
        }

        container.innerHTML = `
<style>
.vra-header,.vra-row{display:flex;align-items:center;border-bottom:1px solid var(--vrd-bdr);}
.vra-header{background:var(--vrd-sf2);font-size:9.5px;font-weight:700;color:var(--vrd-tx3);text-transform:uppercase;letter-spacing:.4px;position:sticky;top:0;z-index:2;}
.vra-label{width:160px;min-width:160px;padding:6px 12px;border-right:1px solid var(--vrd-bdr);display:flex;flex-direction:column;gap:1px;}
.vra-vname{font-size:11px;font-weight:600;color:var(--vrd-tx);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.vra-lplate{font-size:9px;color:var(--vrd-tx3);}
.vra-bar-area{flex:1;height:40px;position:relative;background:var(--vrd-sf3);}
.vra-header .vra-bar-area{height:28px;}
.vra-row:hover .vra-bar-area{background:var(--vrd-t05);}
.vra-bar{position:absolute;top:6px;height:28px;border-radius:6px;font-size:9.5px;font-weight:600;color:#fff;display:flex;align-items:center;padding:0 7px;cursor:pointer;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;transition:opacity .15s,transform .15s;}
.vra-bar:hover{opacity:.85;transform:scaleY(1.06);}
.avail-booked{background:linear-gradient(90deg,#f59e0b,#fbbf24);box-shadow:0 2px 6px rgba(245,158,11,.25);}
.avail-free{background:linear-gradient(90deg,#10b981,#6ee7b7);opacity:.6;}
.avail-free:hover{opacity:.8;}
.vra-wk-label{position:absolute;top:6px;font-size:8.5px;color:var(--vrd-tx3);transform:translateX(-50%);white-space:nowrap;}
.vra-today-line{position:absolute;top:0;bottom:0;width:2px;background:var(--vrd-danger);opacity:.7;pointer-events:none;z-index:1;}
</style>
${hdHtml}
${rowsHtml}`;

        container.querySelectorAll('.avail-booked[data-dbid]').forEach(bar => {
            bar.addEventListener('click', () => {
                const dbId = bar.getAttribute('data-dbid');
                if (dbId) this.action.doAction({
                    type: 'ir.actions.act_window', res_model: 'vehicle.contract',
                    res_id: parseInt(dbId), views: [[false, 'form']], target: 'current'
                });
            });
        });
    }

    _configGantt(zoom) {
        gantt.config.xml_date = '%Y-%m-%d';
        gantt.config.readonly = true;
        gantt.config.show_grid = true;
        gantt.config.row_height = 38;
        gantt.config.bar_height = 24;
        gantt.config.fit_tasks = true;
        gantt.config.show_today_line = true;
        gantt.config.scale_unit = zoom;
        gantt.config.date_scale = zoom === 'day' ? '%d %M' : zoom === 'week' ? 'Week %W' : ' %F %Y';
        gantt.config.subscales = zoom === 'month' ? [{unit: 'week', step: 1, date: 'W%W'}] : [];
        gantt.config.tooltip_timeout = 30;
        gantt.config.tooltip_hide_timeout = 2500;
        gantt.config.tooltip_offset_x = 12;
        gantt.config.tooltip_offset_y = 16;
        try { if (gantt.plugins) gantt.plugins({tooltip: true}); } catch (_) {}
        gantt.templates.task_text = (s, e, t) => t.text || '';
    }

    setGanttZoom(zoom) {
        this.state.ganttZoom = zoom;
        if (typeof gantt !== 'undefined') {
            gantt.config.scale_unit = zoom;
            gantt.config.date_scale = zoom === 'day' ? '%d %M' : zoom === 'week' ? 'Week %W' : '%F %Y';
            gantt.config.subscales = zoom === 'month' ? [{unit: 'week', step: 1, date: 'W%W'}] : [];
            try { gantt.render(); } catch (_) {}
        }
        // Re-build whichever Gantt section is active
        if (this.state.sec === 'gantt') {
            setTimeout(() => this._buildGanttSection(), 30);
        }
    }

    toggleRevMode(m) {
        this.state.revMode = m;
        setTimeout(() => {
            this._destroyCharts();
            this._buildCharts();
        }, 30);
    }

    /* ── Actions ────────────────────────────────── */
    viewFleetVehicleDetails(s) {
        this._open('fleet.vehicle', s === 'all' ? [] : [['status', '=', s]], 'Vehicles');
    }

    viewVehicleContractStatus(s) {
        this._open('vehicle.contract', s === 'all' ? [] : [['status', '=', s]], 'Contracts');
    }

    viewVehicleCustomers() {
        this._open('res.partner', [], 'Customers');
    }

    viewCustomerInvoices() {
        this._open('account.move',
            [['vehicle_contract_id', '!=', false], ['move_type', '=', 'out_invoice']],
            'Invoices');
    }

    viewPendingInvoices() {
        this._open('account.move',
            [['payment_state', '!=', 'paid'], ['vehicle_contract_id', '!=', false], ['move_type', '=', 'out_invoice']],
            'Pending Invoices');
    }

    openExpiringToday() {
        const t = new Date().toISOString().slice(0, 10);
        this._open('vehicle.contract',
            [['end_date', '>=', t + ' 00:00:00'], ['end_date', '<=', t + ' 23:59:59'], ['status', '=', 'b_in_progress']],
            'Today Expiry Contracts');
    }

    openContractRecord(id) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'vehicle.contract',
            res_id: id,
            views: [[false, 'form']],
            target: 'current'
        });
    }

    openLeads() {
        this._open('crm.lead', [], 'Leads');
    }

    openMaintenance() {
        this._open('maintenance.request', [], 'Maintenance Request');
    }

    createNewContract() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'vehicle.contract',
            views: [[false, 'form']],
            target: 'current'
        });
    }

    _open(model, domain, tname) {
        this.action.doAction({
            name: tname,
            type: 'ir.actions.act_window',
            res_model: model,
            domain: domain,
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    refresh() {
        this._destroyCharts();
        this._contractGanttInited = false;
        if (typeof gantt !== 'undefined') {
            try {
                gantt.clearAll();
            } catch (_) {
            }
        }
        this.orm.call('vehicle.rental.dashboard', 'get_vehicle_rental_dashboard', []).then(d => {
            this.state.data = d;
            this._currencySymbol = d.currency_symbol || '₹';
            this._currencyPosition = d.currency_position || 'before';
            this._applyTheme(d.theme_color || '#2563eb');
            setTimeout(() => {
                this._buildCharts();
                this._buildContractGantt();
                if (this.state.sec === 'contracts') this._buildAvailGantt();
                if (this.state.sec === 'gantt') this._buildGanttSection();
                if (this.state.sec === 'availability') this._buildAvailabilitySection();
            }, 60);
        });
    }

    /* ── Helpers ────────────────────────────────── */
    _fmt(v) {
        const n = Number(v) || 0;
        const sym = this._currencySymbol || '₹';
        const pos = this._currencyPosition || 'before';
        const fmt = (num, suffix) => pos === 'after' ? num + suffix + sym : sym + num + suffix;
        if (n >= 10000000) return fmt((n / 10000000).toFixed(1), 'Cr');
        if (n >= 100000) return fmt((n / 100000).toFixed(1), 'L');
        if (n >= 1000) return fmt((n / 1000).toFixed(1), 'K');
        return pos === 'after' ? Math.round(n).toLocaleString() + sym : sym + Math.round(n).toLocaleString();
    }

    formatCurrency(v) {
        return this._fmt(v);
    }

    currentMonthYear() {
        const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
        const now = new Date();
        return months[now.getMonth()] + ' ' + now.getFullYear();
    }

    statusBadgeClass(s) {
        return {
            a_draft: 'badge-draft',
            b_in_progress: 'badge-active',
            c_return: 'badge-return',
            d_cancel: 'badge-cancel'
        }[s] || 'badge-draft';
    }

    statusLabel(s) {
        return {a_draft: 'New', b_in_progress: 'Active', c_return: 'Returned', d_cancel: 'Cancelled'}[s] || s;
    }

    /* Legacy chart methods */
    renderGraph(el, opts) {
        if (typeof ApexCharts !== 'undefined') {
            new ApexCharts(el, opts).render();
        }
    }

    renderContractDurationsGraph() {
        if (!this.state.data || !this.contractDurations.el) return;
        const cd = [];
        for (const ss of (this.state.data.rent_duration || [])) {
            cd.push({
                name: ss.name,
                data: [{x: 'Duration', y: [new Date(ss.start_date).getTime(), new Date(ss.end_date).getTime()]}]
            });
        }
        this.renderGraph(this.contractDurations.el, {
            series: cd,
            chart: {height: 390, type: 'rangeBar'},
            plotOptions: {bar: {horizontal: true}},
            colors: ['#1e3a8a', '#1d4ed8', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd'],
            dataLabels: {
                enabled: true, formatter: (v) => {
                    const a = moment(v[0]), b = moment(v[1]), d = b.diff(a, 'days');
                    return d + (d > 1 ? ' days' : ' day')
                }, style: {colors: ['#273029']}
            },
            fill: {
                type: 'gradient',
                gradient: {
                    shade: 'white',
                    type: 'horizontal',
                    inverseColors: false,
                    opacityFrom: 1,
                    opacityTo: 1,
                    stops: [0, 50, 100]
                }
            },
            yaxis: {title: {text: 'Contract Duration'}, labels: {show: false}},
            xaxis: {type: 'datetime'},
            legend: {position: 'bottom'}
        });
    }

    renderInvoiceStatusGraph(div, data) {
        if (typeof am5 === 'undefined' || !div) return;
        const cD = [], root = am5.Root.new(div);
        root.setThemes([am5themes_Animated.new(root)]);
        const chart = root.container.children.push(am5xy.XYChart.new(root, {
            panX: true,
            panY: true,
            wheelX: 'panX',
            wheelY: 'zoomX',
            pinchZoomX: true,
            paddingLeft: 0,
            paddingRight: 1
        }));
        const cursor = chart.set('cursor', am5xy.XYCursor.new(root, {}));
        cursor.lineY.set('visible', false);
        const xR = am5xy.AxisRendererX.new(root, {minGridDistance: 30, minorGridEnabled: true});
        xR.labels.template.setAll({centerY: am5.p50, centerX: am5.p50, paddingRight: 15});
        xR.grid.template.setAll({location: 1});
        const xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
            maxDeviation: 0.3,
            categoryField: 'category',
            renderer: xR,
            tooltip: am5.Tooltip.new(root, {})
        }));
        const yR = am5xy.AxisRendererY.new(root, {strokeOpacity: 0.1});
        const yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {maxDeviation: 0.3, renderer: yR}));
        const series = chart.series.push(am5xy.ColumnSeries.new(root, {
            name: 'Series 1',
            xAxis,
            yAxis,
            valueYField: 'value',
            sequencedInterpolation: true,
            categoryXField: 'category',
            tooltip: am5.Tooltip.new(root, {labelText: '{valueY}'})
        }));
        series.columns.template.setAll({cornerRadiusTL: 5, cornerRadiusTR: 5, strokeOpacity: 0});
        series.columns.template.adapters.add('fill', (f, t) => chart.get('colors').getIndex(series.columns.indexOf(t)));
        series.columns.template.adapters.add('stroke', (s, t) => chart.get('colors').getIndex(series.columns.indexOf(t)));
        for (let i = 0; i < data['x-axis'].length; i++) {
            cD.push({value: data['y-axis'][i], category: data['x-axis'][i]});
        }
        xAxis.data.setAll(cD);
        series.data.setAll(cD);
        series.appear(1000);
        chart.appear(1000, 100);
    }
}

VehicleRentalDashboard.template = 'vehicle_rental.rental_dashboard';
registry.category('actions').add('vehicle_rental_dashboard', VehicleRentalDashboard);
