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
from odoo import api, models, fields
from odoo.exceptions import UserError


class AssetPlanning(models.Model):
    _name = "asset.planning"
    _description = "Asset Planning"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    name = fields.Char(
        string="Name",
        copy=False,
        readonly=True
    )

    project_id = fields.Many2one(
        'project.project',
        required=True,
        tracking=True
    )

    planner_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        tracking=True
    )

    planning_date = fields.Date(
        default=fields.Date.today
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', tracking=True)

    line_ids = fields.One2many(
        'asset.planning.line',
        'planning_id',
        string="Planning Lines"
    )

    def action_plan(self):
        self.state = 'planned'

    def action_approve(self):
        self.state = 'approved'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def action_reset(self):
        self.state = 'draft'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for spt in res:
            sequence_code = self.env['ir.sequence'].next_by_code(
                'asset.planning.sequence')
            spt.name = str(spt.project_id.name) + ' -' + sequence_code
        return res



class AssetPlanningLine(models.Model):
    _name = "asset.planning.line"
    _description = "Asset Planning Line"
    _order = "start_date"

    planning_id = fields.Many2one(
        "asset.planning",
        required=True,
        ondelete="cascade"
    )

    project_id = fields.Many2one(
        related="planning_id.project_id",
        store=True,
        readonly=True
    )

    asset_id = fields.Many2one(
        "product.product",
        string="Asset",
        required=True,
        domain="[('product_tmpl_id.is_asset_product','=',True)]",
    )

    start_date = fields.Date(
        string="Start Date",
        required=True
    )

    end_date = fields.Date(
        string="End Date",
        required=True
    )

    qty = fields.Float(
        string="Quantity",
        default=1.0
    )

    remarks = fields.Char()

    days = fields.Integer(
        compute="_compute_days",
        store=True
    )

    estimated_cost = fields.Float(
        string="Estimated Cost",
        compute="_compute_cost",
        store=True
    )

    has_conflict = fields.Boolean(
        string="Conflict",
        compute="_compute_conflict"
    )

    conflict_message = fields.Text(
        string="Conflict Details",
        compute="_compute_conflict"
    )

    conflict_count = fields.Integer(
        compute="_compute_conflict"
    )

    # ---------------------------------------------------------
    # COMPUTE DAYS
    # ---------------------------------------------------------

    @api.depends("start_date", "end_date")
    def _compute_days(self):
        for rec in self:
            rec.days = 0
            if rec.start_date and rec.end_date:
                rec.days = (rec.end_date - rec.start_date).days + 1

    # ---------------------------------------------------------
    # COMPUTE COST
    # ---------------------------------------------------------

    @api.depends(
        "days",
        "qty",
        "asset_id.product_tmpl_id.cost_per_day"
    )
    def _compute_cost(self):
        for rec in self:
            rec.estimated_cost = (
                rec.days
                * rec.qty
                * rec.asset_id.product_tmpl_id.cost_per_day
            )

    # ---------------------------------------------------------
    # CHECK DATE
    # ---------------------------------------------------------

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.end_date < rec.start_date:
                    raise models.UserError(
                        "End Date must be greater than Start Date."
                    )

    # ---------------------------------------------------------
    # CONFLICT CHECK
    # ---------------------------------------------------------

    @api.depends("asset_id", "start_date", "end_date")
    def _compute_conflict(self):
        for rec in self:

            rec.has_conflict = False
            rec.conflict_message = False
            rec.conflict_count = 0

            if not rec.asset_id:
                continue

            if not rec.start_date or not rec.end_date:
                continue

            overlaps = self.search([
                ("id", "!=", rec.id),
                ("asset_id", "=", rec.asset_id.id),
                ("planning_id.state", "!=", "cancel"),
                ("start_date", "<=", rec.end_date),
                ("end_date", ">=", rec.start_date),
            ])

            if overlaps:
                rec.has_conflict = True
                rec.conflict_count = len(overlaps)

                lines = []

                for line in overlaps:
                    lines.append(
                        "Project : %s\n"
                        "From    : %s\n"
                        "To      : %s"
                        % (
                            line.project_id.name,
                            line.start_date,
                            line.end_date,
                        )
                    )

                rec.conflict_message = "\n\n".join(lines)