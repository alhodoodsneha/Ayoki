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

class ReturnWizard(models.TransientModel):
    _name = 'asset.return.wizard'
    _description = "Return Asset"


    project_id = fields.Many2one('project.project', string="Project", tracking=True)
    from_loc_id = fields.Many2one('stock.location', string="From Location", required=True, tracking=True)
    to_loc_id = fields.Many2one('stock.location', string="To Location", tracking=True)
    product_id = fields.Many2one('product.product', string="Asset",
                                 domain="[('is_asset_product', '=',True),('detailed_type','=','product')]")
    uom_id = fields.Many2one('uom.uom', string="Uom",related='product_id.uom_id')
    available_qty = fields.Float(string="Available Qty")
    qty = fields.Float(string="Returned Qty")
    date_today = fields.Date(string="Date", default=fields.Date.today)

    @api.onchange('qty')
    def _onchange_qty(self):
        if self.available_qty < self.qty:
            raise UserError(_("Return Quantity Is Not Available In Stock!!"))

    def action_return_asset(self):
        if self.qty <= 0:
            raise UserError(_("Quantity must be greater than zero."))
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', self.project_id.warehouse_id.id)
        ], limit=1)
        move_lines = []
        move_lines.append((0, 0, {
            'product_id': self.product_id.id,
            'product_uom_qty': self.qty,
            'product_uom': self.uom_id.id
        }))
        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type.id,
            'location_id': self.from_loc_id.id,
            'location_dest_id': self.to_loc_id.id,
            'partner_id': self.project_id.partner_id.id,
            'scheduled_date': self.date_today,
            'project_id': self.project_id.id,
            'move_ids': move_lines,
        })
        picking.action_confirm()