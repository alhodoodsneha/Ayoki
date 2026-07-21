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
from odoo.exceptions import UserError


class ConsumedMaterial(models.Model):
    _name = 'consumed.material'
    _description = 'Consumed Material'
    _rec_name = 'item_id'

    item_id = fields.Many2one('product.product', string="Item")
    qty = fields.Float(string="Quantity")
    maintenance_id = fields.Many2one('maintenance.request', string="maintenance")


class MaintenanceRequest(models.Model):
    _name = 'maintenance.request'
    _description = 'Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence_code'

    sequence_code = fields.Char(string="sequence", tracking=True)
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    project_id = fields.Many2one('project.project', string='Project', required=True)
    asset_id = fields.Many2one('product.product', string='Asset', required=True,
                               domain="[('is_asset_product', '=', True)]")
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    available_quantity = fields.Float(string='Available Quantity', required=True)
    location_id = fields.Many2one('stock.location', string='From Location', required=True)
    stage = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
    ], string='Stage', default='draft')
    stage_type = fields.Selection(
        [('start', 'Start'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('scrap', 'Scrap')],
        string="Type")
    date_today = fields.Date(string="Date", default=fields.Date.today)
    uom_id = fields.Many2one('uom.uom', string="Uom",related='asset_id.uom_id')
    consumed_ids = fields.One2many('consumed.material', 'maintenance_id', string="Consumed Material")
    scrap_qty = fields.Float(string="Scrap qty")

    @api.model
    def create(self, vals):
        res = super(MaintenanceRequest, self).create(vals)
        res.sequence_code = self.env['ir.sequence'].next_by_code('property.maintenance')
        return res

    def action_approve(self):
        self.stage = 'approve'

    def action_start(self):
        main_loc = self.env['stock.location'].search([('is_maintenance_loc', '=', True)], limit=1)
        if not main_loc:
            raise UserError(_("Please Configure a Maintenance Location!!"))
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', self.project_id.warehouse_id.id)
        ], limit=1)
        move_lines = []
        move_lines.append((0, 0, {
            'product_id': self.asset_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.uom_id.id,
        }))
        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type.id,
            'location_id': self.location_id.id,
            'location_dest_id': main_loc.id,
            'partner_id': self.project_id.partner_id.id,
            'scheduled_date': self.date_today,
            'move_ids': move_lines,
        })
        picking.action_confirm()
        picking.button_validate()
        self.stage_type = 'start'

    def action_in_progress(self):
        self.stage_type = 'in_progress'

    def action_scrap(self):
        return {
            'name': 'Scrap',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            "view_type": "form",
            'res_model': 'maintenance.scrap.wizard',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_maintenance_id': self.id,
            }
        }

    def action_completed(self):
        qty = self.quantity
        if self.scrap_qty:
            if self.scrap_qty < self.quantity:
                qty = self.quantity - self.scrap_qty
            else:
                qty = self.scrap_qty - self.quantity
        main_loc = self.env['stock.location'].search([('is_maintenance_loc', '=', True)], limit=1)
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', self.project_id.warehouse_id.id)
        ], limit=1)
        move_lines = []
        move_lines.append((0, 0, {
            'product_id': self.asset_id.id,
            'product_uom_qty': qty,
            'product_uom': self.uom_id.id
        }))
        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type.id,
            'location_id': main_loc.id,
            'location_dest_id': self.location_id.id,
            'partner_id': self.project_id.partner_id.id,
            'scheduled_date': fields.Date.today(),
            'move_ids': move_lines,
        })
        picking.action_confirm()
        picking.button_validate()
        self.stage_type = 'completed'
