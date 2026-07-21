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


class ProjectTaskProductLine(models.Model):
    _name = 'project.task.product.line'

    task_id = fields.Many2one('project.task', string='Task')
    product_id = fields.Many2one('product.product', string='Product')
    location = fields.Many2one('stock.location', string='Location')
    quantity = fields.Float(string='Quantity')
    cost = fields.Float(string='Cost')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    is_asset_task = fields.Boolean(string="IS Asset Task", default=False)

    product_line_ids = fields.One2many(
        'project.task.product.line',
        'task_id',
        string='Product Lines'
    )

    def action_schedule_asset(self):
        tasks = self.env['project.task'].search([('is_asset_task', '=', True)])
        for rec in tasks:
            rec.product_line_ids.unlink()
            quants =  self.env['stock.quant'].search([('project_id','=',rec.project_id.id)])
            for quant in quants:
                if quant.product_id.is_asset_product:
                    self.env['project.task.product.line'].sudo().create({
                        'task_id':rec.id,
                        'product_id':quant.product_id.id,
                        'location':quant.location_id.id,
                        'quantity':quant.inventory_quantity_auto_apply,
                        'cost':quant.product_id.cost_per_day,
                    })