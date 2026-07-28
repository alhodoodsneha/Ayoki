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



class ProjectEmployeeAllocateWizard(models.TransientModel):
    _name = 'project.employee.allocate.wizard'
    _description = 'Allocate/Remove Employee'

    project_id = fields.Many2one(
        "project.project",
        required=True,
    )

    action = fields.Selection(
        [
            ("allocate", "Allocate"),
            ("remove", "Remove"),
        ],
        default="allocate",
        required=True,
    )

    employee_ids = fields.Many2many(
        "hr.employee",
        string="Employee",
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()
        if self.action == "allocate":
            self.project_id.write({
                "employee_ids": [(4, emp.id) for emp in self.employee_ids]
            })
        else:
            project_employees = self.project_id.employee_ids
            not_allocated = self.employee_ids.filtered(
                lambda emp: emp not in project_employees
            )
            if not_allocated:
                raise UserError(_(
                    "The following employee(s) are not allocated to this project:\n\n%s"
                ) % ("\n".join(not_allocated.mapped("name"))))
            self.project_id.write({
                "employee_ids": [(3, emp.id) for emp in self.employee_ids]
            })

