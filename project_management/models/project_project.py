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
from odoo.exceptions import UserError
from odoo import api, models, fields,_
from datetime import timedelta


class Project(models.Model):
    _inherit = 'project.project'

    weightage_progress = fields.Float(
        string="Progress (%)",
        compute="_compute_weightage_progress",
        store=True,
    )
    bill_created = fields.Boolean(
        string="Bill created",
        default=False
    )

    project_total_amount = fields.Float(
        string="Total Project Amount",
        tracking=True
    )

    bill_percentage = fields.Float(
        string='Percentage Invoiced',
        default=0.0
    )

    lpo_reference = fields.Char(
        string="Lpo Reference No"
    )

    employee_ids = fields.Many2many(
        "hr.employee",
        "project_employee_rel",
        "project_id",
        "employee_id",
        string="Allocated Employees",
    )

    done_project = fields.Boolean(
        string="Done",
        related='stage_id.done_project',
    )


    @api.depends(
        'milestone_ids.weightage_progress',
        'milestone_ids.weightage'
    )
    def _compute_weightage_progress(self):
        for project in self:
            total_weight = sum(project.milestone_ids.mapped('weightage'))
            if total_weight:
                project.weightage_progress = (
                        sum(
                            milestone.weightage * milestone.weightage_progress
                            for milestone in project.milestone_ids
                        ) / total_weight
                )
            else:
                project.weightage_progress = 0.0

    def action_allocate_employee(self):
        return {
            "name": "Allocate Employee",
            "type": "ir.actions.act_window",
            "res_model": "project.employee.allocate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_project_id": self.id,
                "default_action": "allocate",
            },
        }

    def action_view_project_manpower_planing(self):
        return {
            "name": "Manpower Planning",
            'view_type': 'list',
            'view_mode': 'list,form',
            "res_model": "project.manpower.planning",
            'domain': [('project_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_project_id': self.id}
        }

    def action_view_absent_employee(self):
        return {
            "name": "Absent Employee",
            'view_type': 'list',
            'view_mode': 'list,form',
            "res_model": "project.absent.employee",
            'domain': [('project_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_project_id': self.id}
        }


    def action_create_payment_certificate(self):
        requested_percentage = 100 - self.bill_percentage
        return {
            'name': _('Payment Certificate'),
            'type': 'ir.actions.act_window',
            'res_model': 'payment.certificate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_project_id': self.id,
                        'default_requested_percentage': requested_percentage,
                        }
        }


    def action_view_payment_certificate(self):
        return {
            'name': 'Payment Certificate',
            'type': 'ir.actions.act_window',
            'res_model': 'payment.certificate',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'target': 'current',
            'context': {'create': False,
                        'delete': False,
                        }
        }

    @api.model
    def cron_check_project_absent_employees(self):
        yesterday = fields.Date.today() - timedelta(days=1)
        projects = self.search([
            ('employee_ids', '!=', False),('done_project','!=',True)
        ])
        AnalyticLine = self.env['account.analytic.line']
        Absent = self.env['project.absent.employee']

        for project in projects:
            for employee in project.employee_ids:
                timesheet = AnalyticLine.search_count([
                    ('employee_id', '=', employee.id),
                    ('project_id', '=', project.id),
                    ('date', '=', yesterday),
                ])
                if not timesheet:
                    exists = Absent.search_count([
                        ('employee_id', '=', employee.id),
                        ('project_id', '=', project.id),
                        ('date', '=', yesterday),
                    ])
                    if not exists:
                        Absent.create({
                            'employee_id': employee.id,
                            'project_id': project.id,
                            'date': yesterday,
                        })


class ProjectProjectStage(models.Model):
    _inherit = 'project.project.stage'

    done_project = fields.Boolean(string="Closed Stage",default=False)