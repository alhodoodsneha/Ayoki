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


class TimesheetInWizard(models.TransientModel):
    _name = 'timesheet.in.wizard'
    _description = 'Timesheet In'

    task_id = fields.Many2one('project.task', string="Task", required=True)
    employee_ids = fields.Many2many('hr.employee', string="Employees", required=True)
    start_date = fields.Datetime(string="Start Date", default=fields.Datetime.now)

    def action_create_timesheets(self):
        start_date_only = fields.Date.from_string(self.start_date)
        for employee in self.employee_ids:
            timesheet_in = self.env['account.analytic.line'].sudo().search([
                ('task_id', '=', self.task_id.id),
                ('employee_id', '=', employee.id),
                ('date', '=', start_date_only)
            ], limit=1)
            if timesheet_in:
                raise UserError(_("You cant create multiple timesheet for same employee in same task at same date!!"))
            self.env['account.analytic.line'].create({
                'task_id': self.task_id.id,
                'employee_id': employee.id,
                'date': start_date_only,
                'start_date': self.start_date,
                'unit_amount': 0.0,
                'name': f'Work on - : {self.task_id.name}',
            })


class TimesheetOutWizard(models.TransientModel):
    _name = 'timesheet.out.wizard'
    _description = 'Timesheet Out Wizard'

    task_id = fields.Many2one('project.task', string="Task", required=True)
    employee_ids = fields.Many2many('hr.employee', string="Employees", required=True)
    end_date = fields.Datetime(string="End Date", default=fields.Datetime.now)

    def action_update_timesheets(self):
        for employee in self.employee_ids:
            end_date_only = fields.Date.from_string(self.end_date)
            timesheet_in = self.env['account.analytic.line'].sudo().search([
                ('task_id', '=', self.task_id.id),
                ('employee_id', '=', employee.id),
                ('date', '=', end_date_only)
            ], limit=1)

            if timesheet_in:
                unit_amount = (self.end_date - timesheet_in.start_date).total_seconds() / 3600
                timesheet_in.sudo().write({
                    'end_date': self.end_date,
                    'unit_amount': round(unit_amount, 2)
                })
