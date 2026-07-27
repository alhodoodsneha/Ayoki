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


class AllotAssetLine(models.Model):
    _name = 'allot.asset.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'product_id'
    _description = 'Asset Lines'

    product_id = fields.Many2one('product.product', string="Asset",
                                 domain="[('is_asset_product', '=',True),('type','=','consu')]")
    available_qty = fields.Float(string="Available Qty", compute='_compute_available_qty')
    qty = fields.Float(string="Required Qty")
    approved_qty = fields.Float(string="Approved Qty")
    asset_allot_id = fields.Many2one('allot.asset', string="Allot asset")
    uom_id = fields.Many2one('uom.uom', string="Uom",related='product_id.uom_id')

    is_asset_modifier = fields.Boolean(
        string="Milestone Modifier",
        compute='compute_project_modifier'
    )

    @api.depends('available_qty', 'product_id', 'asset_allot_id')
    def compute_project_modifier(self):
        for rec in self:
            if self.env.user.has_group(
                    'asset_managemnet_customization.group_approve_asset_request'):
                rec.is_asset_modifier = True
            else:
                rec.is_asset_modifier = False

    @api.depends('product_id', 'qty', 'asset_allot_id.from_loc_id')
    def _compute_available_qty(self):
        for rec in self:
            if rec.product_id and rec.asset_allot_id.from_loc_id:
                qty = sum(self.env['stock.quant'].sudo().search([('product_id', '=', rec.product_id.id), (
                    'location_id', '=', rec.asset_allot_id.from_loc_id.id)]).mapped('inventory_quantity_auto_apply'))
                rec.available_qty = qty
            else:
                rec.available_qty = 0.0

    @api.onchange('qty')
    def _onchange_qty(self):
        if self.available_qty < self.qty:
            raise UserError(_("Required Quantity Is Not Available In Stock!!"))

    @api.onchange('approved_qty')
    def _onchange_approved_qty(self):
        if self.available_qty < self.approved_qty:
            raise UserError(_("Approved Quantity Is Not Available In Stock!!"))


class AllotAsset(models.Model):
    _name = 'allot.asset'
    _description = 'Allocate asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'from_loc_id'

    name = fields.Char(
        string="Name",
        tracking=True
    )

    project_id = fields.Many2one('project.project', string="Project", tracking=True)
    from_loc_id = fields.Many2one('stock.location', string="From Location", required=True, tracking=True)
    to_loc_id = fields.Many2one('stock.location', string="To Location", tracking=True)
    asset_lot_ids = fields.One2many('allot.asset.line', 'asset_allot_id', string="Allot Assets", tracking=True)
    stage = fields.Selection(
        [('new', 'New'), ('waiting_for_approval', 'Waiting For Approval'),
         ('approved', 'Approved'),('rejected', 'Rejected')], string="Stage",
        default='new',
        tracking=True)
    date_today = fields.Date(string="Requested Deadline", default=fields.Date.today)
    requested_by = fields.Many2one(
        'res.users',
        string="Requested By",
        default=lambda self: self.env.user,
        tracking=True
    )
    requested_on = fields.Date(
        string="Requested On",
        tracking=True,
        default=lambda self: fields.Date.today(),
    )


    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for spt in res:
            sequence_code = self.env['ir.sequence'].next_by_code(
                'allot.asset.sequence')
            spt.name = str(spt.project_id.name) + ' -'+sequence_code
        return res

    def action_submit(self):
        self.stage = 'waiting_for_approval'
        groups = [
            'asset_managemnet_customization.group_approve_asset_request',
        ]
        users = self.env['res.users'].sudo().search([
            ('group_ids', 'in', [
                self.env.ref(group).id for group in groups
            ])
        ])
        for user in users:
            if user.partner_id.email:
                base_url = self.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url')
                record_url = f"{base_url}/web#id={self.id}&model={self._name}&view_type=form"
                body_html = f"""
                                       <p>Dear {user.name},</p>
                                      <p>
                                        New  Asset Allocation request is submitted.
                                      </p>
                                         Kindly review the Request details and proceed with the approval at your earliest convenience.
                                         <p>
                                           Please let us know if any additional documents or clarification are required from our side.
                                           </p>
                                         <p>
                                          Thank you for your support.
                                         </p>
                                         <p>
                                              <a href="{record_url}"
                                                 style="
                                                     background-color:#0a6ebd;
                                                     color:#ffffff;
                                                     padding:8px 14px;
                                                     text-decoration:none;
                                                     border-radius:4px;
                                                     display:inline-block;
                                                 ">
                                                 View Request
                                              </a>
                                          </p>
                                          <p>
                                              Best regards,<br/>
                                              {self.env.user.name}
                                          </p>
                                   """
                subject = _(
                    'New Asset Allocation Request  - %s Submitted !!') % (
                              self.name)
                main_content = {
                    'subject': subject,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': body_html,
                    'email_to': user.partner_id.email,
                }
                self.env['mail.mail'].sudo().create(main_content).send()

    def action_approve(self):
        if not self.asset_lot_ids:
            raise UserError(_("No assets selected for transfer.!!"))
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', self.project_id.warehouse_id.id)
        ], limit=1)
        move_lines = []
        for line in self.asset_lot_ids:
            if line.approved_qty > 0:
                move_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.approved_qty,
                    'product_uom': line.uom_id.id
                }))

        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': picking_type.id,
            'location_id': self.from_loc_id.id,
            'location_dest_id': self.to_loc_id.id,
            'partner_id': self.project_id.partner_id.id,
            'project_id': self.project_id.id,
            'allot_asset_id': self.id,
            'scheduled_date': self.date_today,
            'move_ids': move_lines
        })
        picking.action_confirm()
        picking.button_validate()
        self.stage = 'approved'
        if self.requested_by.partner_id.email:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            record_url = f"{base_url}/web#id={self.id}&model={self._name}&view_type=form"
            body_html = f"""
                                   <p>Dear {self.requested_by.name},</p>
                                  <p>
                                    The Asset Allocation request {self.name} for {self.project_id.name} is Approved.
                                  </p>
                                     Kindly check the request.
                                     <p>
                                       Please let us know if any additional documents or clarification are required from our side.
                                       </p>
                                     <p>
                                      Thank you for your support.
                                     </p>
                                     <p>
                                          <a href="{record_url}"
                                             style="
                                                 background-color:#0a6ebd;
                                                 color:#ffffff;
                                                 padding:8px 14px;
                                                 text-decoration:none;
                                                 border-radius:4px;
                                                 display:inline-block;
                                             ">
                                             View Request
                                          </a>
                                      </p>
                                      <p>
                                          Best regards,<br/>
                                          {self.env.user.name}
                                      </p>
                               """
            subject = _(
                'Asset Allocation Request  - %s Approved !!') % (
                          self.name)
            main_content = {
                'subject': subject,
                'author_id': self.env.user.partner_id.id,
                'body_html': body_html,
                'email_to': self.requested_by.partner_id.email,
            }
            self.env['mail.mail'].sudo().create(main_content).send()


    def action_reject(self):
        self.stage = 'rejected'
        if self.requested_by.partner_id.email:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            record_url = f"{base_url}/web#id={self.id}&model={self._name}&view_type=form"
            body_html = f"""
                                           <p>Dear {self.requested_by.name},</p>
                                          <p>
                                            The Asset Allocation request {self.name} for {self.project_id.name} is Rejected.
                                          </p>
                                             Kindly check the request.
                                             <p>
                                               Please let us know if any additional documents or clarification are required from our side.
                                               </p>
                                             <p>
                                              Thank you for your support.
                                             </p>
                                             <p>
                                                  <a href="{record_url}"
                                                     style="
                                                         background-color:#0a6ebd;
                                                         color:#ffffff;
                                                         padding:8px 14px;
                                                         text-decoration:none;
                                                         border-radius:4px;
                                                         display:inline-block;
                                                     ">
                                                     View Request
                                                  </a>
                                              </p>
                                              <p>
                                                  Best regards,<br/>
                                                  {self.env.user.name}
                                              </p>
                                       """
            subject = _(
                'Asset Allocation Request  - %s Is Rejected !!') % (
                          self.name)
            main_content = {
                'subject': subject,
                'author_id': self.env.user.partner_id.id,
                'body_html': body_html,
                'email_to': self.requested_by.partner_id.email,
            }
            self.env['mail.mail'].sudo().create(main_content).send()


    def action_view_allocated_asset(self):
        return {
            'name': 'Internal Transfer',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('allot_asset_id', '=', self.id)],
            'target': 'current',
        }
