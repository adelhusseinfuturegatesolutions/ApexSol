/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { getDefaultConfig } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { useDebounced } from "@web/core/utils/timing";
import { session } from "@web/session";
import { Domain } from "@web/core/domain";
import { sprintf } from "@web/core/utils/strings";

const { Component, useSubEnv, useState, onMounted, onWillStart, useRef } = owl;
import { loadJS, loadCSS } from "@web/core/assets"

class InsuranceDashboard extends Component {
  setup() {
    this.action = useService("action");
    this.orm = useService("orm");

    this.state = useState({
      totalInsurances: {
        'draft_insurance': 0,
        'total_insurance': 0,
        'running_insurance': 0,
        'expired_insurance': 0,
        'policy_expiry_remaining_days': 0,
      },
      totalClaims: {
        'total_claim': 0,
        'submit_claim': 0,
        'under_review_claim': 0,
        'approved_claim': 0,
        'not_approved_claim': 0,
        'closed_claim': 0,
      },
      insuranceAgents: { 'res_partner_agent': 0 },
      insuranceCategory: { 'insurance_category': 0 },
      topAgents: { 'x-axis': [], 'y-axis': [] },
      genderCounts: { 'x-axis': [], 'y-axis': [] },
      invoiceByMonth: { 'x-axis': [], 'y-axis': [], 'symbol': '' },
    });

    this.state = useState({
      insuranceList: [],
    });

    useSubEnv({
      config: {
        ...getDefaultConfig(),
        ...this.env.config,
      },
    });

    this.topAgents = useRef('insurance_top_agent');
    this.genderCounts = useRef('customer_gender');
    this.invoiceByMonth = useRef('invoice_month_graph');

    onWillStart(async () => {
      let insuranceData = await this.orm.call('insurance.dashboard', 'get_insurance_dashboard', []);
      if (insuranceData) {
        this.state.totalInsurances = insuranceData;
        this.state.totalClaims = insuranceData;
        this.state.insuranceAgents = insuranceData;
        this.state.insuranceCategory = insuranceData;
        this.state.topAgents = {
          'x-axis': insuranceData['top_agents'][0],
          'y-axis': insuranceData['top_agents'][1]
        };
        this.state.genderCounts = {
          'x-axis': insuranceData['gender_count'][0],
          'y-axis': insuranceData['gender_count'][1]
        };
        this.state.invoiceByMonth = {
          'x-axis': insuranceData['invoice_by_month'][0],
          'y-axis': insuranceData['invoice_by_month'][1],
          'symbol': insuranceData['invoice_by_month'][2]
        };
        this.state.expiringInsurance = insuranceData.expiring_insurance;
      }
    });

    onMounted(() => {
      this.renderTopFiveAgentsGraph();
      this.renderGenderCountsGraph();
      this.renderInvoiceGraph();
    })
  }

  viewInsurances(type) {
    let domain, context;
    let name = this.getInsuranceStatus(type);
    if (type === 'all') {
      domain = []
    } else {
      domain = [['state', '=', type]]
    }
    context = { 'create': false }
    this.action.doAction({
      type: 'ir.actions.act_window',
      name: name,
      res_model: 'insurance.information',
      view_mode: 'kanban',
      views: [[false, 'list'], [false, 'form'], [false, 'calendar'], [false, 'search'], [false, 'activity']],
      target: 'current',
      context: context,
      domain: domain,
    });
  }
  getInsuranceStatus(type) {
    let name;
    if (type === 'all') {
      name = 'Total Insurances'
    } else if (type === 'draft') {
      name = 'New Insurances'
    } else if (type === 'running') {
      name = 'Running Insurances'
    } else if (type === 'expired') {
      name = 'Expired Insurances'
    }
    return name;
  }

  viewClaims(type) {
    let domain, context;
    let name = this.getClaimStatus(type);
    if (type === 'all') {
      domain = []
    } else {
      domain = [['state', '=', type]]
    }
    context = { 'create': false }
    this.action.doAction({
      type: 'ir.actions.act_window',
      name: name,
      res_model: 'claim.information',
      view_mode: 'kanban',
      views: [[false, 'list'], [false, 'form'], [false, 'search'], [false, 'activity']],
      target: 'current',
      context: context,
      domain: domain,
    });
  }
  getClaimStatus(type) {
    let name;
    if (type === 'all') {
      name = 'Total Claims'
    } else if (type === 'submit') {
      name = 'Registered Claims'
    } else if (type === 'under_review') {
      name = 'Under Review Claims'
    } else if (type === 'approved') {
      name = 'Approved Claims'
    } else if (type === 'not_approved') {
      name = 'Rejected Claims'
    } else if (type === 'closed') {
      name = 'Closed Claims'
    }
    return name;
  }

  viewInsuranceAgents() {
    let domain = [['is_agent', '=', true]];
    let context = { 'create': false }
    this.action.doAction({
      type: 'ir.actions.act_window',
      name: 'Agents',
      res_model: 'res.partner',
      domain: domain,
      view_mode: 'kanban',
      views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
      target: 'current',
      context: context,
    });
  }

  viewInsuranceCategory() {
    let context = { 'create': false }
    this.action.doAction({
      type: 'ir.actions.act_window',
      name: 'Insurance Categories',
      res_model: 'insurance.category',
      view_mode: 'kanban',
      views: [[false, 'list'], [false, 'form']],
      target: 'current',
      context: context,
    });
  }

  viewInsurance(ins) {
    this.env.services.action.doAction({
      type: 'ir.actions.act_window',
      name: "Insurance",
      res_model: 'insurance.information',
      res_id: ins,
      views: [[false, 'form']],
      target: 'current',
      context: { create: false },
    });
  }

  renderGraph(el, options) {
    const graphData = new ApexCharts(el, options);
    graphData.render();
  }

  renderTopFiveAgentsGraph() {
    const options = {
      series: [{
        name: 'Insurances',
        data: this.state.topAgents['y-axis'],
      }],
      chart: {
        height: 430,
        type: 'bar',
      },
      plotOptions: {
        bar: {
          columnWidth: '50%',
          distributed: true,
        }
      },
      colors: ['#4abeff', '#5d87ff', '#ffae1f', '#fd4755', '#17deba'],
      dataLabels: {
        enabled: false
      },
      legend: {
        show: false
      },
      xaxis: {
        categories: this.state.topAgents['x-axis'],
        labels: {
          style: {
            fontSize: '10px'
          }
        }
      }
    };
    this.renderGraph(this.topAgents.el, options);
  }

  renderGenderCountsGraph(div, insuranceData) {
    const options = {
      series: this.state.genderCounts['y-axis'],
      chart: {
        width: 430,
        height: 430,
        type: 'pie',
      },
      colors: ['#4abeff', '#5d87ff', '#17deba'],
      labels: this.state.genderCounts['x-axis'],
      legend: {
        position: 'bottom'
      },
      responsive: [{
        breakpoint: 480,
        options: {
          chart: {
            width: 200
          },
          legend: {
            position: 'bottom'
          }
        }
      }]
    };
    this.renderGraph(this.genderCounts.el, options);
  }

  renderInvoiceGraph() {
    const currencySymbol = this.state.invoiceByMonth['symbol'];
    const options = {
      series: [
        {
          name: "Total Amounts: ",
          data: this.state.invoiceByMonth['y-axis'],
        }
      ],
      chart: {
        height: 440,
        type: 'bar',
      },
      plotOptions: {
        bar: {
          columnWidth: '40%',
          distributed: true,
        }
      },
      dataLabels: {
        enabled: false
      },
      legend: {
        show: false
      },
      yaxis: {
        labels: {
          formatter: function (val) {
            if (typeof val === 'number') {
              return currencySymbol + " " + val.toFixed(2);
            } else {
              return currencySymbol + val;
            }
          }
        }
      },
      xaxis: {
        categories: this.state.invoiceByMonth['x-axis'],
        labels: {
          style: {
            fontSize: '13px'
          }
        }
      }
    };
    this.renderGraph(this.invoiceByMonth.el, options);
  }

}
InsuranceDashboard.template = "tk_insurance_management.ins_dashboard";
registry.category("actions").add("insurance_dashboard", InsuranceDashboard);