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


class TimesheetLine(models.Model):
    _inherit = 'account.analytic.line'

    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    labour_cost = fields.Float(string="Labour Cost",compute='_compute_hour_cost')

    @api.depends('unit_amount','employee_id')
    def _compute_hour_cost(self):
        for rec in self:
            if rec.employee_id.hourly_cost and rec.unit_amount:
                rec.labour_cost = rec.employee_id.hourly_cost *  round(rec.unit_amount,2)
            else:
                rec.labour_cost = 0.0




