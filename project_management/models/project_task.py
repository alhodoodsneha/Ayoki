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
from datetime import date
from odoo.exceptions import UserError



class ProjectTask(models.Model):
    _inherit = 'project.task'

    start_date = fields.Datetime(
        string="Actual Start Date",
        index=True
    )
    date_deadline = fields.Datetime(
        string='Planned End Date', index=True,
        tracking=True, copy=False)


    milestone_start_date = fields.Date(
        string="Milestone Start Date",
        related='milestone_id.start_date'
    )

    milestone_end_date = fields.Date(
        string="Milestone End Date",
        related='milestone_id.deadline'
    )

    planned_start_date = fields.Datetime(
        string="planned Start Date"
    )

    planned_end_date = fields.Datetime(
        string="Actual End Date"
    )

    duration_task = fields.Integer(
        string="Duration (Days)",
        compute="_compute_duration",
    )

    task_delay = fields.Integer(
        string="Task Delay (Days)",
        compute='_compute_project_delay',
    )

    weightage = fields.Float("Weightage")

    weightage_progress = fields.Float(
        string="Weightage Progress",
        compute="_compute_weightage_progress",
    )


    @api.constrains('weightage_progress','weightage','milestone_id')
    def _check_milestone_task_weightage(self):
        for task in self:
            if not task.parent_id:
                tasks = task.milestone_id.task_ids.filtered(
                    lambda t: not t.parent_id)
                total_weight = sum(tasks.mapped('weightage'))
                if total_weight > 100:
                    raise UserError(_(
                        "The total weightage of tasks in milestone '%s' cannot exceed 100%%.\n"
                        "Current total: %.2f%%"
                    ) % (task.milestone_id.name, total_weight))

    @api.constrains('weightage', 'parent_id')
    def _check_subtask_weightage(self):
        for task in self:
            if task.parent_id:
                total_weight = sum(task.parent_id.child_ids.mapped('weightage'))
                if total_weight > 100:
                    raise UserError(_(
                        "The total weightage of subtasks for '%s' cannot exceed 100%%.\n"
                        "Current total: %.2f%%"
                    ) % (task.parent_id.name, total_weight))

    @api.depends('start_date', 'date_deadline')
    def _compute_duration(self):
        for rec in self:
            if rec.start_date and rec.date_deadline:
                rec.duration_task = (rec.date_deadline - rec.start_date).days
            else:
                rec.duration_task = 0

    @api.depends(
        'child_ids.weightage_progress',
        'child_ids.weightage',
        'stage_id'
    )
    def _compute_weightage_progress(self):
        done_stage = self.env['project.task.type'].search(
            [('is_done', '=', True)])
        for task in self:
            if task.child_ids:
                total_weight = sum(task.child_ids.mapped('weightage'))
                if total_weight:
                    task.weightage_progress = (
                            sum(
                                child.weightage * child.weightage_progress
                                for child in task.child_ids
                            ) / total_weight
                    )
                else:
                    task.weightage_progress = 0
            else:
                task.weightage_progress = 100 if task.stage_id in done_stage else 0

    @api.depends('date_deadline', 'name', 'start_date')
    def _compute_project_delay(self):
        today = date.today()
        for rec in self:
            rec.task_delay = 0
            if rec.date_deadline and rec.date_deadline.date() < today:
                if rec.state not in ['1_done', '1_canceled']:
                    rec.task_delay = max((today - rec.date_deadline.date()).days,0)
                else:
                    rec.task_delay = 0
            else:
                rec.task_delay = 0



class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    is_done = fields.Boolean(string='Completed',default=False)
