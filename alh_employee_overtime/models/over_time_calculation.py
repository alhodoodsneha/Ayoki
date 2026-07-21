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
import calendar
from odoo import api, models, fields,_
from odoo.exceptions import UserError
from collections import defaultdict

class OvertimeCalculation(models.Model):
    _name = "overtime.calculation"
    _description = "Overtime Calculation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"
    _rec_name = "name"

    name = fields.Char(
        string="Sequence",
        copy=False,
        tracking=True
    )

    date_from = fields.Date(
        string="Date From",
        required=True,
        tracking=True
    )

    date_to = fields.Date(
        string="Date To",
        required=True,
        tracking=True
    )

    all_employee = fields.Boolean(
        string="All Employees",
        default=True,
        tracking=True
    )

    employee_id = fields.Many2many(
        "hr.employee",
        string="Employee",
        tracking=True
    )

    line_ids = fields.One2many(
        "overtime.calculation.line",
        "calculation_id",
        string="Over Time Lines"
    )

    state = fields.Selection([
        ("draft", "Draft"),
        ("generated", "Generated"),
        ("approved", "Approved"),
    ], default="draft", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for spt in res:
            sequence_code = self.env['ir.sequence'].next_by_code(
                'over.time.calculation')
            spt.name = sequence_code
        return res

    @api.constrains("date_from", "date_to")
    def _check_month(self):
        for rec in self:
            if not rec.date_from or not rec.date_to:
                continue

            if rec.date_from.month != rec.date_to.month:
                raise UserError(
                    _("Please select dates from the same month.")
                )

            if rec.date_from.year != rec.date_to.year:
                raise UserError(
                    _("Please select dates from the same year.")
                )

            if rec.date_from.day != 1:
                raise UserError(
                    _("Date From must be the first day of the month.")
                )

            last_day = calendar.monthrange(
                rec.date_to.year,
                rec.date_to.month
            )[1]

            if rec.date_to.day != last_day:
                raise UserError(
                    _("Date To must be the last day of the month.")
                )

    def action_generate(self):
        self.ensure_one()
        self.line_ids.unlink()
        if self.all_employee:
            employees = self.env['hr.employee'].search([])
        else:
            if not self.employee_id:
                raise UserError(_("Please select an employee."))
            employees = self.employee_id
        Holiday = self.env['resource.calendar.leaves']
        for employee in employees:
            normal_ot = 0.0
            public_ot = 0.0
            calendar = employee.resource_calendar_id
            standard_hours = calendar.hours_per_day if calendar else 0.0

            timesheets = self.env['account.analytic.line'].search([
                ('employee_id', '=', employee.id),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('project_id.is_internal_project', '=', False),
            ], order='date')

            worked_per_day = defaultdict(float)

            for ts in timesheets:
                worked_per_day[ts.date] += ts.unit_amount or 0.0

            for work_date, worked_hours in worked_per_day.items():

                holiday = Holiday.search([
                    ('calendar_id', 'in',
                     [False, calendar.id if calendar else False]),
                    ('date_from', '<=',
                     fields.Datetime.to_datetime(work_date)),
                    ('date_to', '>=', fields.Datetime.to_datetime(work_date)),
                ], limit=1)

                weekday = str(fields.Date.to_date(work_date).weekday())

                working_day = False
                if calendar:
                    working_day = bool(calendar.attendance_ids.filtered(
                        lambda a: a.dayofweek == weekday
                    ))

                if holiday or not working_day:
                    public_ot += worked_hours
                else:
                    if worked_hours > standard_hours:
                        normal_ot += worked_hours - standard_hours
            self.env['overtime.calculation.line'].create({
                'calculation_id': self.id,
                'employee_id': employee.id,
                'normal_ot': normal_ot,
                'public_ot': public_ot,
                'approved_normal_ot': normal_ot,
                'approved_public_ot': public_ot,
            })

        self.state = 'generated'

    def action_approve(self):
        self.state = "approved"

    def action_reset(self):
        self.state = "draft"


class OvertimeCalculationLine(models.Model):
    _name = "overtime.calculation.line"
    _description = "Overtime Calculation Line"

    calculation_id = fields.Many2one(
        "overtime.calculation",
        ondelete="cascade"
    )

    employee_id = fields.Many2one(
        "hr.employee",
        required=True
    )

    department_id = fields.Many2one(
        'hr.department',
        related="employee_id.department_id",
        store=True
    )

    job_id = fields.Many2one(
        'hr.job',
        related="employee_id.job_id",
        store=True
    )

    normal_ot = fields.Float(
        string="Normal OT"
    )

    public_ot = fields.Float(
        string="Public Holiday OT"
    )

    approved_normal_ot = fields.Float(
        string="Approved Normal OT"
    )

    approved_public_ot = fields.Float(
        string="Approved Public OT"
    )

    total_ot = fields.Float(
        compute="_compute_total",
        store=True
    )

    @api.depends(
        "approved_normal_ot",
        "approved_public_ot"
    )
    def _compute_total(self):
        for rec in self:
            rec.total_ot = (
                rec.approved_normal_ot +
                rec.approved_public_ot
            )