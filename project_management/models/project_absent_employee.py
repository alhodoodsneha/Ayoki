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

class ProjectAbsentEmployee(models.Model):
    _name = "project.absent.employee"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Project Absent Employee"
    _rec_name = 'project_id'
    _order = "date desc"

    employee_id = fields.Many2one(
        "hr.employee",
        required=True,
        ondelete="cascade",
    )

    project_id = fields.Many2one(
        "project.project",
        required=True,
        ondelete="cascade",
    )

    date = fields.Date(
        required=True,
    )

    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
