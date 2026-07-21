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
from odoo.exceptions import UserError
from datetime import timedelta


class PaymentCertificate(models.Model):
    _name = 'payment.certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Payment Certificate'
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char(
        string="Sequence",
        tracking=True
    )

    stage_id = fields.Selection([
        ('draft','Draft'),
         ('submit_to_client','Submit To Client'),
         ('client_approved','client Approved'),
         ('client_reject','client Rejected')
    ],
         string="Stage",
        default='draft',
         tracking = True
    )

    requested_date = fields.Date(
        string="Requested Date",
        tracking=True
    )

    approved_date = fields.Date(
        string="Approved Date",
        tracking=True
    )

    approved_percentage = fields.Float(
        string="Approved Percentage",
        defaut=0.0,
        tracking=True
    )

    approved_amount = fields.Float(
        string="Approved Amount",
        tracking=True,
        compute='_compute_approved_amount'
    )

    requested_percentage = fields.Float(
        string="Requested Percentage",
        defaut=0.0,
        tracking=True
    )

    requested_amount = fields.Float(
        string="Requested Amount",
        tracking=True,
        compute='_compute_requested_amount'

    )

    building_certificate_date = fields.Date(
        string="Building Certification Date",
        tracking=True
    )

    expiry_date = fields.Date(
        string="Expiry Date",
        tracking=True
    )

    project_id = fields.Many2one(
        'project.project',
        string="Project",
        tracking=True
    )

    project_total_amount = fields.Float(
        string="Total Project Amount",
        related='project_id.project_total_amount',
        tracking=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Partner",
        related='project_id.partner_id',
        tracking=True
    )

    requested_by = fields.Many2one(
        'res.users',
        string="Requested By",
        tracking=True,
        default=lambda self: self.env.user,
    )

    rejected_by = fields.Many2one(
        'res.users',
        string="Rejected By",
        tracking=True,
    )

    approved_by = fields.Many2one(
        'res.users',
        string="Approved By",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for spt in res:
            sequence_code = self.env['ir.sequence'].next_by_code(
                'payment.certificate')
            spt.name = sequence_code
        return res

    def action_submit_to_client(self):
        if not self.expiry_date:
            raise UserError(
                _("Please Add Expiry Date!!.."))
        self.stage_id  = 'submit_to_client'

    def action_approve(self):
        if self.approved_percentage <= 0.0:
            raise UserError(
                _("Please Add Approved Percentage !!.."))
        total_per = self.project_id.bill_percentage + self.approved_percentage
        if total_per > 100:
            raise UserError(
                _("Approved Percentage Is More Than Pending Percentage !!"))
        self.approved_date =fields.Date.today()
        self.approved_by =self.env.user.id
        self.stage_id = 'client_approved'
        self.project_id.bill_percentage = self.project_id.bill_percentage + self.approved_percentage

    def action_rejected(self):
        self.rejected_by = self.env.user.id
        self.stage_id = 'client_reject'

    @api.depends('name','stage_id','requested_percentage','project_total_amount')
    def _compute_requested_amount(self):
        for rec in self:
            rec.requested_amount = 0.0
            if rec.project_total_amount >0.0:
                rec.requested_amount = (rec.project_total_amount * rec.requested_percentage)/100

    @api.depends('name', 'stage_id', 'approved_percentage',
                 'project_total_amount')
    def _compute_approved_amount(self):
        for rec in self:
            rec.approved_amount = 0.0
            if rec.project_total_amount > 0.0:
                rec.approved_amount = (rec.project_total_amount * rec.approved_percentage) / 100

    @api.model
    def _cron_notify_expiry(self):
        notify_date = fields.Date.today() + timedelta(days=2)
        certificates = self.search([
            ('expiry_date', '=', notify_date),
            ('stage_id', 'not in', ['client_reject','client_approved']),
            ('requested_by', '!=', False),
        ])
        for certificate in certificates:
            email_to = certificate.requested_by.partner_id.email
            if not email_to:
                continue
            mail_values = {
                'subject': _("Payment Certificate Expiry Reminder"),
                'email_to': email_to,
                'body_html': """
                        <p>Dear %s,</p>

                        <p>This is a reminder that the Payment Certificate <strong>%s</strong>
                        will expire on <strong>%s</strong>.</p>

                        <p>Please review it.</p>

                        <p>Regards,<br/>%s</p>
                    """ % (
                    certificate.requested_by.name,
                    certificate.name,
                    certificate.expiry_date,
                    self.env.company.name,
                ),
            }
            self.env['mail.mail'].sudo().create(mail_values).send()