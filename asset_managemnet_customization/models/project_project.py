# -*- coding: utf-8 -*-
#############################################################################

#    Alhodood Technologies.
#
#    Copyright (C) 2024-TODAY Alhodood Technologies(<https://www.alhodood.com>)
#    Author: Alhodood Technologies(<https://www.alhodood.com>)
#
#    You can modify it under the terms of the GNU Affero General Public License (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License (AGPL v3) for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models, fields, _


class Project(models.Model):
    _inherit = 'project.project'

    _is_asset = fields.Boolean(
        string="Is asset")
    # stage_type = fields.Selection(
    #     [('new', "New"), ('running', 'Running'), ('closed', 'Closed')], related='stage_id.stage_type')
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Warehouse")
    location_id = fields.Many2one(
        'stock.location',
        string="Location")
    project_qty_ids = fields.One2many(
        'stock.quant',
        'project_id',
        string="Assets",
        domain="[('product_id.is_asset_product', '=', True)]")
    total_expense = fields.Float(
        string="Total Expense",
        compute='_compute_total_expense')

    is_project_asset_modifier = fields.Boolean(
        string="Asset Modifier",
        compute='compute_project_asset_modifier'
    )

    is_loc_allocate = fields.Boolean(
        string="Location Allocated",
        default=False
    )

    @api.depends('name', 'user_id')
    def compute_project_asset_modifier(self):
        for rec in self:
            if self.env.user.has_group(
                    'asset_managemnet_customization.group_project_asset_modifier'):
                rec.is_project_asset_modifier = True
            else:
                rec.is_project_asset_modifier = False

    def _compute_total_expense(self):
        for rec in self:
            total_amount = 0.0
            task = self.env['project.task'].sudo().search([('project_id', '=', rec.id), ('is_asset_task', '=', True)],
                                                          limit=1)
            if task:
                if task.product_line_ids:
                    total_amount = total_amount + sum(task.product_line_ids.mapped('cost'))
                if task.timesheet_ids:
                    total_amount = total_amount + sum(task.timesheet_ids.mapped('labour_cost'))
            rec.total_expense = total_amount

    def action_run_project(self):
        project_task = self.env['project.task'].sudo().create({
            'name': self.name,
            'user_ids': [(6, 0, [self.user_id.id])],
            'partner_id': self.partner_id.id,
            'date_deadline': self.date,
            'description': self.description,
            'project_id': self.id,
            'is_asset_task': True,
        })
        base_code = self.name[:2].upper() if self.name else 'WH'
        existing_codes = self.env['stock.warehouse'].sudo().search([('code', '=like', base_code + '%')]).mapped('code')
        new_code = base_code
        counter = 1
        while new_code in existing_codes:
            new_code = f"{base_code}{counter}"
            counter += 1
        warehouse_id = self.env['stock.warehouse'].sudo().create({
            'name': self.name,
            'project_id': self.id,
            'code': new_code
        })
        self.warehouse_id = warehouse_id.id
        self.location_id = warehouse_id.lot_stock_id.id
        self.is_loc_allocate = True
        # task_stage_id = self.env['project.project.stage'].search([('stage_type', '=', 'running')], limit=1)
        # self.stage_id = task_stage_id.id

    def action_open_stock(self):
        current_stock = self.env['stock.quant'].sudo().search([('location_id', '=', self.location_id.id)])
        return {
            'name': 'Current Stock',
            'view_type': 'list',
            'view_mode': 'list,form',
            'res_model': 'stock.quant',
            'domain': [('id', 'in', current_stock.ids)],
            'type': 'ir.actions.act_window',
        }

    def action_maintenance_request(self):
        return {
            'name': 'Maintenance',
            'view_type': 'list',
            'view_mode': 'list,form',
            'res_model': 'maintenance.request',
            'domain': [('project_id', '=', self.id)],
            'type': 'ir.actions.act_window',
        }

    def action_allot_asset(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Allocate Asset',
            'res_model': 'allot.asset',
            'view_mode': 'form',
            'view_id': self.env.ref('asset_managemnet_customization.view_form_allot_asset').id,
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'default_to_loc_id': self.location_id.id
            }
        }

    def action_view_allot_asset(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Allocated Asset',
            'res_model': 'allot.asset',
            'view_type': 'list',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'default_to_loc_id': self.location_id.id
            }
        }

    def action_view_allocated_asset(self):
        return {
            'name': 'Internal Transfer',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'target': 'current',
        }

    def action_view_open_asset_planning(self):
        return {
            'name': 'Asset Planning',
            'type': 'ir.actions.act_window',
            'res_model': 'asset.planning',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'target': 'current',
            'context': {
                'default_project_id': self.id,
            }
        }


class ProjectProjectStage(models.Model):
    _inherit = 'project.project.stage'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    # stage_type = fields.Selection(
    #     [('new', "New"), ('running', 'Running'), ('closed', 'Closed')], string="Stage Type")
