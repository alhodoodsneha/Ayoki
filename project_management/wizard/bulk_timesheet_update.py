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
from odoo import fields, models, api,_
from odoo.exceptions import UserError


class BulkTimesheetWizard(models.TransientModel):
    _name = "bulk.timesheet.wizard"
    _description = "Bulk Timesheet Wizard"

    project_id = fields.Many2one(
        "project.project",
        string="Project",
        required=True,
    )

    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.today,
    )

    description = fields.Char(
        string="Description",
        required=True,
    )

    line_ids = fields.One2many(
        "bulk.timesheet.wizard.line",
        "wizard_id",
        string="Employees",
    )

    @api.onchange("project_id")
    def _onchange_project_id(self):
        self.line_ids = [(5, 0, 0)]
        if self.project_id:
            lines = []
            for employee in self.project_id.employee_ids:
                lines.append((0, 0, {
                    "employee_id": employee.id,
                    "hours": 8.0,
                }))
            self.line_ids = lines


    def action_create_timesheets(self):
        AnalyticLine = self.env["account.analytic.line"]
        for line in self.line_ids:
            if line.hours:
                if not line.task_id:
                    raise UserError(
                        _("Please select a task for employee %s.") %
                        line.employee_id.name
                    )
                AnalyticLine.create({
                    "name": self.description,
                    "date": self.date,
                    "project_id": self.project_id.id,
                    "task_id": line.task_id.id,
                    "employee_id": line.employee_id.id,
                    "unit_amount": line.hours,
                })



class BulkTimesheetWizardLine(models.TransientModel):
    _name = "bulk.timesheet.wizard.line"
    _description = "Bulk Timesheet Wizard Line"

    wizard_id = fields.Many2one(
        "bulk.timesheet.wizard",
        ondelete="cascade",
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        readonly=True,
    )

    task_id = fields.Many2one(
        "project.task",
        string="Task",
        domain="[('project_id','=',parent.project_id)]",
    )

    hours = fields.Float(
        string="Hours",
        default=8.0,
    )