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

    def action_create_payment_certificate(self):
        requested_percentage = 100 - self.bill_percentage
        return {
            'name': _('Payment Certificate'),
            'type': 'ir.actions.act_window',
            'res_model': 'payment.certificate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_project_id': self.id,
                        'default_requested_percentage':requested_percentage,
                        }
        }

    def action_view_payment_certificate(self):
        if self.bill_percentage >=100:
            raise UserError(
                _("100 % Invoiced  !!.."))
        return {
            'name': 'Payment Certificate',
            'type': 'ir.actions.act_window',
            'res_model': 'payment.certificate',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'target': 'current',
        }

