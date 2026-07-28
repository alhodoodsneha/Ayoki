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
from odoo import api, models, fields,_
from odoo.exceptions import UserError


class ProjectManpowerPlanning(models.Model):
    _name = "project.manpower.planning"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "ProjectManpowerPlanning"
    _rec_name = 'project_id'

    project_id = fields.Many2one(
        "project.project",
        string="Project",
        tracking=True
    )

    partner_id = fields.Many2one(
        related="project_id.partner_id",
        string="Customer",
    )

    project_start_date = fields.Date(
        related="project_id.date_start",
        string="Project Start Date",
        tracking=True
    )

    project_end_date = fields.Date(
        related="project_id.date",
        string="Project End Date",
        tracking=True
    )

    create_user_id = fields.Many2one(
        "res.users",
        string="Created By",
        readonly=True,
        default=lambda self: self.env.user,
        tracking=True
    )

    create_on_date = fields.Datetime(
        string="Created On",
        readonly=True,
        default=fields.Datetime.now,
        tracking=True
    )

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        string="Company",
        tracking=True

    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
    ], default='draft', tracking=True)


    line_ids = fields.One2many(
        "project.manpower.planning.line",
        "planning_id",
        string="Planning Lines",
    )


    def action_approve(self):
        self.state = 'approved'

class ProjectManpowerPlanningLine(models.Model):
    _name = "project.manpower.planning.line"
    _description = "Project Manpower Planning Line"

    planning_id = fields.Many2one(
        "project.manpower.planning",
        required=True,
        ondelete="cascade",
    )

    employee_id = fields.Many2one(
        "hr.employee",
        required=True,
        string="Employee"
    )

    planned_start = fields.Datetime(
        string="Planned Start",
        required=True,
    )

    planned_end = fields.Datetime(
        string="Planned End",
        required=True,
    )


    @api.constrains('employee_id', 'planned_start', 'planned_end')
    def _check_employee_planning_overlap(self):
        for rec in self:
            if not rec.employee_id or not rec.planned_start or not rec.planned_end:
                continue

            if rec.planned_end <= rec.planned_start:
                raise UserError(_("Planned End must be greater than Planned Start."))

            overlap = self.search([
                ('id', '!=', rec.id),
                ('employee_id', '=', rec.employee_id.id),
                ('planned_start', '<', rec.planned_end),
                ('planned_end', '>', rec.planned_start),
            ], limit=1)

            if overlap:
                raise UserError(_(
                    "Employee '%s' is already allocated.\n\n"
                    "Project : %s\n"
                    "From : %s\n"
                    "To : %s"
                ) % (
                    rec.employee_id.name,
                    overlap.planning_id.project_id.display_name,
                    fields.Datetime.to_string(overlap.planned_start),
                    fields.Datetime.to_string(overlap.planned_end),
                ))

