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
from odoo import models, fields, api
from odoo.exceptions import UserError

class MaintenanceScrapWizard(models.TransientModel):
    _name = "maintenance.scrap.wizard"
    _description = "Scrap Maintenance Product"

    maintenance_id = fields.Many2one('maintenance.request', string="Maintenance Request", required=True)
    scrap_qty = fields.Float(string="Scrap Quantity", required=True)

    @api.constrains('scrap_qty')
    def _check_scrap_qty(self):
        """Ensure scrap quantity is not greater than the available maintenance quantity"""
        for record in self:
            if record.scrap_qty > record.maintenance_id.quantity:
                raise UserError("Scrap quantity cannot be greater than the maintenance quantity.")

    def action_scrap(self):
        scrap_location = self.env['stock.location'].search([('scrap_location', '=', True)], limit=1)
        if not scrap_location:
            raise UserError("No scrap location found. Please configure one in Inventory.")
        main_loc = self.env['stock.location'].search([('is_maintenance_loc', '=', True)], limit=1)
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', self.maintenance_id.project_id.warehouse_id.id)
        ], limit=1)
        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type.id,
            'location_id': main_loc.id,
            'location_dest_id':scrap_location.id,
            'partner_id': self.maintenance_id.project_id.partner_id.id,
            'scheduled_date': fields.date.today(),
        })
        move_vals = {
            'name': self.maintenance_id.asset_id.display_name,
            'product_id': self.maintenance_id.asset_id.id,
            'product_uom_qty': self.scrap_qty,
            'location_id': main_loc.id,
            'location_dest_id': scrap_location.id,
            'picking_id': picking.id,
        }

        self.env['stock.move'].create(move_vals)
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()
        self.maintenance_id.scrap_qty = self.scrap_qty + self.maintenance_id.scrap_qty
        if self.maintenance_id.quantity == self.scrap_qty:
            self.maintenance_id.stage_type = 'Scrap'

