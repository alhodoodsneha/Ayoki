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

{
    'name': 'Project Management',
    'version': '19.0.0.0.3',
    'category':  'Services/Project',
    'summary': 'Project Management',
    'description': 'Project Management',
    'author': 'Alhodood Technologies',
    'depends': ['mail','project','hr_timesheet'],
    'data': [
        'security/security_group.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'views/project_project.xml',
        'views/payment_certificate.xml',
        'views/project_milestone.xml',
        'views/hr_job.xml',
        'views/project_task.xml',
        'views/project_absent_employee.xml',
        'views/project_manpower_planning.xml',
        'wizard/payment_certificate_wizard.xml',
        'wizard/employee_allocation_wizard.xml',
        'wizard/bulk_timesheet_update.xml',
        'wizard/manpower_report_wizard.xml',
    ],
    'demo': [
    ],
    'assets': {
        'web.assets_frontend': [

    ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
