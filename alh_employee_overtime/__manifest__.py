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
    'name': 'Employee Overtime Management',
    'version': '19.0.0.2.1',
    'category':  'Services/Project',
    'summary': 'Employee Overtime Management',
    'description': 'Employee Overtime Management',
    'author': 'Alhodood Technologies',
    'depends': ['mail','project','hr_timesheet','hr','hr_payroll_community'],
    'data': [
        'data/alh_hr_payroll_demo_data.xml',
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/over_time_calculation.xml',
    ],
    'demo': [
    ],
    'assets': {

    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
