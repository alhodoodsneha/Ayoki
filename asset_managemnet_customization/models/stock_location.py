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

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    project_id = fields.Many2one('project.project', string="Project")


class StockLocation(models.Model):
    _inherit = 'stock.location'

    project_id = fields.Many2one('project.project', string="Project", related='warehouse_id.project_id')
    is_maintenance_loc = fields.Boolean(string="Is Maintenance Location",default=False)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    project_id = fields.Many2one('project.project', related='location_id.project_id', string="Project")

    def action_return(self):
        if self.inventory_quantity_auto_apply <= 0.0:
            raise UserError(_("No quantity to return!!"))
        return {
            'name': 'Return Asset',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            "view_type": "form",
            'res_model': 'asset.return.wizard',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_project_id': self.project_id.id,
                'default_from_loc_id': self.location_id.id,
                'default_product_id': self.product_id.id,
                'default_available_qty': self.inventory_quantity_auto_apply,
            }
        }

    def action_repair(self):
        if self.inventory_quantity_auto_apply <= 0.0:
            raise UserError(_("No quantity to repair!!"))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Request',
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'view_id': self.env.ref('asset_managemnet_customization.view_maintenance_request_form').id,
            'target': 'new',
            'context': {
                'default_project_id': self.project_id.id,
                'default_asset_id': self.product_id.id,
                'default_location_id': self.location_id.id,
                'default_available_quantity': self.inventory_quantity_auto_apply,
            }
        }


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    allot_asset_id = fields.Many2one(
        'allot.asset',
        string="Allot Asset Request",
        tracking=True
    )