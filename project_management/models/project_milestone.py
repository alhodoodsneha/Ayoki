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



class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'

    start_date = fields.Date(
        string="Actual Start Date"
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ],
        string="Status",
        default='draft',
        tracking=True
    )

    starting_delay = fields.Integer(
        string="Starting Delay",
        compute="_compute_delays",
        store=True
    )

    closing_delay = fields.Integer(
        string="Closing Delay",
        compute="_compute_delays",
        store=True
    )

    duration = fields.Integer(
        string="Duration (Days)",
        compute="_compute_duration",
        store=True
    )

    planned_start_date = fields.Date(
        string="planned Start Date"
    )

    planned_end_date = fields.Date(
        string="Actual End Date"
    )

    remark = fields.Text(
        string="Remark",
        tracking=True
    )
    weightage = fields.Float(
        string="Weightage",
        tracking=True
    )

    weightage_progress = fields.Float(
        string="Progress (%)",
        compute="_compute_weightage_progress",
        store=True,
    )

    is_project_modifier = fields.Boolean(
        string="Milestone Modifier",
        compute='compute_project_modifier'
    )

    project_verified = fields.Boolean(
        string="Project Verified",
        default=False
    )

    @api.depends('name', 'project_id', 'start_date','planned_start_date')
    def compute_project_modifier(self):
        for rec in self:
            if self.env.user.has_group('project_management.group_project_milestone_modifier'):
                rec.is_project_modifier = True
            else:
                rec.is_project_modifier = False

    def action_verify_project(self):
        self.project_verified = True

    @api.depends(
        'task_ids.weightage_progress',
        'task_ids.weightage'
    )
    def _compute_weightage_progress(self):
        for milestone in self:
            tasks = milestone.task_ids.filtered(lambda t: not t.parent_id)
            total_weight = sum(tasks.mapped('weightage'))
            if total_weight:
                milestone.weightage_progress = (
                        sum(
                            task.weightage * task.weightage_progress
                            for task in tasks
                        ) / total_weight
                )
            else:
                milestone.weightage_progress = 0

    def cron_check_milestone_delay(self):
        today = date.today()
        milestones = self.search([
            ('deadline', '<', today),
            ('state', '!=', 'completed')
        ])
        for milestone in milestones:
            project = milestone.project_id
            recipients = [project.user_id.partner_id.id]
            if project.report_manager:
                recipients.append(project.report_manager.partner_id.id)
            if recipients:
                subject = f"Milestone Delay Reminder -  {milestone.name} ❗️"
                body = f""" <p>Dear<strong> {project.user_id.name}</strong>, </p>
                              <p>The milestone <b>{milestone.name}</b> on project<b>{project.name}</b> is delayed. Deadline: {milestone.deadline}.</p>
                              <p>Please take the necessary actions to complete this milestone at the earliest.</p>
                              <p>Regards,<br/>
                                   Project Monitoring System</p>
                                          """
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': project.user_id.email,
                    'email_cc': project.report_manager.email,
                }
                self.env['mail.mail'].create(mail_values).send()

    @api.depends('start_date', 'deadline', 'state','planned_start_date')
    def _compute_delays(self):
        today = fields.Date.today()
        for record in self:
            if record.planned_start_date and record.state in ('draft',
                                                      'pending') and today > record.planned_start_date:
                record.starting_delay = (today - record.planned_start_date).days
            else:
                record.starting_delay = 0
            if record.deadline and record.state != 'completed' and today > record.deadline:
                record.closing_delay = (today - record.deadline).days
            else:
                record.closing_delay = 0

    def action_set_pending(self):
        self.state = 'pending'

    def action_set_in_progress(self):
        self.state = 'in_progress'

    def action_set_completed(self):
        not_done_tasks = self.task_ids.filtered(
            lambda t: t.state not in ['1_done', '1_canceled'])
        if not_done_tasks:
            raise UserError(
                "Please complete all tasks before completing the milestone.!!")
        self.state = 'completed'
        self.is_reached = True

    @api.depends('start_date', 'deadline','planned_start_date')
    def _compute_duration(self):
        for rec in self:
            if rec.planned_start_date and rec.deadline:
                rec.duration = (rec.deadline - rec.planned_start_date).days + 1
            else:
                rec.duration = 0

    def action_view_tasks_milestones(self):
        return {
            'name': 'Milestone Tasks',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'project.task',
            'domain': [('milestone_id', '=', self.id),
                       ('project_id', '=', self.project_id.id)],
            'target': 'new',
            'context': {
                'create': False,
                'delete': False,
                'edit': False
            },

        }

