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
    'name': 'Asset Management',
    'version': '19.0.1.0.1',
    'category': 'Services/Project',
    'summary': 'Asset Management',
    'description': 'Asset Management',
    'author': 'Alhodood Technologies',
    'depends': [
        'project','stock','hr','hr_timesheet','mail','purchase'
    ],
    'data': [
        'data/ir_sequence.xml',
        'security/security_group.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/product_product.xml',
        'views/project_project.xml',
        'views/project_task.xml',
        'views/stock_location.xml',
        'views/maintenance_request.xml',
        'views/asset_menu.xml',
        'views/allot_asset.xml',
        'views/asset_planning.xml',
        'wizard/return_wizard.xml',
        'wizard/scrap_wizard.xml',
    ],
    'assets': {},
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
