# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResConfigSetting(models.TransientModel):
    """Inherits res.config.settings"""
    _inherit = 'res.config.settings'

    terms_conditions_link = fields.Char(config_parameter='vehicle_rental.terms_conditions_link')
    privacy_policy_link = fields.Char(config_parameter='vehicle_rental.privacy_policy_link')
    pagination_item_per_page = fields.Integer(
        string="Records Per Page",
        config_parameter="vehicle_rental.pagination_item_per_page", default=5)
    salesperson_id = fields.Many2one(
        comodel_name='res.users', string='Default Salesperson',
        domain="[('share', '=', False)]",
        config_parameter='vehicle_rental.salesperson_id')
    sale_team_id = fields.Many2one(
        comodel_name='crm.team', string="Default Sales Team",
        config_parameter='vehicle_rental.sale_team_id')
    maintenance_reminder_days = fields.Integer(
        string="Maintenance Reminder Before (Days)", default=5,
        config_parameter="vehicle_rental.maintenance_reminder_days")

    # Dashboard theme — stored as Char ir.config_parameter, shown as color swatch radio
    dashboard_theme_color = fields.Char(
        string="Dashboard Theme Color",
        config_parameter='vehicle_rental.dashboard_theme_color',
        default='#2563eb')

    def set_values(self):
        super().set_values()

    def get_values(self):
        res = super().get_values()
        color = self.env['ir.config_parameter'].sudo().get_param(
            'vehicle_rental.dashboard_theme_color', '#2563eb')
        res['dashboard_theme_color'] = color
        return res
