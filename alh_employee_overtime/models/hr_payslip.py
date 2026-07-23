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
#############################################################################from odoo import models
from odoo import api, models, fields,_


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def get_inputs(self, contracts, date_from, date_to):
        res = super().get_inputs(contracts, date_from, date_to)
        for slip in self:
            ot_line = self.env['overtime.calculation.line'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('calculation_id.state', '=', 'approved'),
                ('calculation_id.date_from', '>=', date_from),
                ('calculation_id.date_to', '<=', date_to),
            ], limit=1)

            if ot_line:
                for line in res:
                    if line.get('code') == 'NOTM':
                        line['amount'] = ot_line.approved_normal_ot

                    elif line.get('code') == 'PUBOTM':
                        line['amount'] = ot_line.approved_public_ot
        return res