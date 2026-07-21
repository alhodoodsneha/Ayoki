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


class PaymentCertificateWizard(models.TransientModel):
    _name = 'payment.certificate.wizard'
    _description = 'Payment Certificate'

    requested_percentage = fields.Float(
        string="Requested Percentage",
        defaut=0.0,
        tracking=True
    )

    project_id = fields.Many2one(
        'project.project',
        string="Project",
        tracking=True
    )

    def action_confirm(self):
        pending_percentage = 100 - self.project_id.bill_percentage
        if self.requested_percentage > pending_percentage:
            raise UserError(_("Requested Percentage Is Greater Than Actual Pending percentage !!.."))

        self.env['payment.certificate'].create({
            'project_id':self.project_id.id,
            'requested_date':fields.Date.today(),
            'requested_percentage':self.requested_percentage,
        })
        self.project_id.bill_created = True



