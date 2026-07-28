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
import base64
import io
from datetime import datetime, time, timedelta
import xlsxwriter
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ManpowerReportWizard(models.TransientModel):
    _name = 'manpower.report.wizard'
    _description = 'Manpower Report Wizard'

    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    project_ids = fields.Many2many('project.project',
                                   string='Projects')

    def action_print_report(self):
        self.ensure_one()
        if not self.date_start and not self.date_end:
            raise UserError(_('Please choose a date.'))

        date_start = self.date_start or self.date_end
        date_end = self.date_end or self.date_start
        if date_start > date_end:
            raise UserError(_('Start Date cannot be after End Date.'))

        staff_jobs = self.env['hr.job'].search(
            [('manpower_category', '=', 'staff')], order='name')
        worker_jobs = self.env['hr.job'].search(
            [('manpower_category', '=', 'worker')], order='name')

        if not staff_jobs and not worker_jobs:
            raise UserError(_(
                'No Job Positions are set up with a Manpower Category '
                '(Staff / Worker). Go to Employees > Configuration > Job '
                'Positions and set it on each job position first.'))

        attachment = self._build_xlsx(date_start, date_end, staff_jobs,
                                      worker_jobs)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

        # --------------------------------------------------------------- #
        # helpers
        # --------------------------------------------------------------- #

    def _get_timesheet_domain(self, current_date, project):
        domain = [('date', '=', current_date), ('employee_id', '!=', False)]
        if project:
            domain.append(('project_id', '=', project.id))
        return domain

    def _get_holiday_dates(self, date_start, date_end):
        """Return a set of dates (within range) that are Sundays or
        company-wide public holidays (global resource.calendar.leaves,
        i.e. records with no resource_id, no specific calendar/employee)."""
        holiday_dates = set()

        current = date_start
        while current <= date_end:
            if current.weekday() == 6:
                holiday_dates.add(current)
            current += timedelta(days=1)

        range_start_dt = datetime.combine(date_start, time.min)
        range_end_dt = datetime.combine(date_end, time.max)

        leaves = self.env['resource.calendar.leaves'].search([
            ('date_from', '<=', range_end_dt),
            ('date_to', '>=', range_start_dt),
        ])
        for leave in leaves:
            user_tz = self.env.user.tz or 'UTC'
            leave_start = fields.Datetime.context_timestamp(
                self.with_context(tz=user_tz),
                leave.date_from
            ).date()
            leave_end = fields.Datetime.context_timestamp(
                self.with_context(tz=user_tz),
                leave.date_to
            ).date()
            leave_start = max(leave_start, date_start)
            leave_end = min(leave_end, date_end)
            d = leave_start
            while d <= leave_end:
                holiday_dates.add(d)
                d += timedelta(days=1)
        return holiday_dates

        # --------------------------------------------------------------- #
        # report building
        # --------------------------------------------------------------- #

    def _build_xlsx(self, date_start, date_end, staff_jobs, worker_jobs):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Manpower Report')

        n_staff = len(staff_jobs)
        n_worker = len(worker_jobs)
        col_date = 0
        col_staff_start = 1
        col_staff_end = col_staff_start + n_staff - 1 if n_staff else col_staff_start - 1
        col_total_staff = col_staff_end + 1
        col_worker_start = col_total_staff + 1
        col_worker_end = col_worker_start + n_worker - 1 if n_worker else col_worker_start - 1
        col_total_worker = col_worker_end + 1
        col_grand_total = col_total_worker + 1
        last_col = col_grand_total
        formats = self._build_formats(workbook)
        sheet.set_column(col_date, col_date, 12)
        if n_staff:
            sheet.set_column(col_staff_start, col_staff_end, 4.5)
        sheet.set_column(col_total_staff, col_total_staff, 8)
        if n_worker:
            sheet.set_column(col_worker_start, col_worker_end, 4.5)
        sheet.set_column(col_total_worker, col_total_worker, 9)
        sheet.set_column(col_grand_total, col_grand_total, 9)

        holiday_dates = self._get_holiday_dates(date_start, date_end)
        row = 0
        company = self.env.company.name
        today_str = fields.Date.today().strftime('%d.%m.%Y')
        month_str = date_start.strftime('%b-%y')

        sheet.merge_range(row, 0, row, 2, _('Contractor:'),
                          formats['title_label'])
        sheet.merge_range(row, 3, row, col_total_worker - 1, company,
                          formats['title_value'])
        sheet.merge_range(row, col_total_worker, row, col_total_worker,
                          _('Month :'), formats['title_label'])
        sheet.merge_range(row, col_total_worker + 1, row, last_col - 1,
                          month_str, formats['title_value'])
        sheet.write(row, last_col, _('Report Date :'), formats['title_label'])
        row += 1
        sheet.merge_range(row, last_col - 1, row, last_col, today_str,
                          formats['report_date_value'])
        row += 1

        projects = self.project_ids
        column_headers = (staff_jobs, worker_jobs, col_staff_start,
                          col_total_staff,
                          col_worker_start, col_total_worker, col_grand_total,
                          col_date)
        if projects:
            for project in projects:
                row = self._write_section(
                    sheet, formats, row, project.name, date_start, date_end,
                    staff_jobs, worker_jobs, column_headers, project,
                    holiday_dates)
                row += 1
        else:
            row = self._write_section(
                sheet, formats, row, _('MAN POWER REPORT'), date_start,
                date_end,
                staff_jobs, worker_jobs, column_headers, False, holiday_dates)

        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Manpower_Report_%s_to_%s.xlsx' % (date_start, date_end),
            'type': 'binary',
            'datas': file_data,
            'res_model': self._name,
            'res_id': self.id,
        })
        return attachment

    def _build_formats(self, workbook):
        f = {}
        f['title_label'] = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'left', 'valign': 'vcenter',
        })
        f['title_value'] = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
        })
        f['report_date_value'] = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#8DB255', 'font_color': 'white',
        })
        f['section'] = workbook.add_format({
            'bold': True, 'font_size': 12, 'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#8DB255', 'font_color': 'white', 'border': 1,
        })
        f['group_header'] = workbook.add_format({
            'bold': True, 'font_size': 11, 'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#C6D9A0', 'border': 1,
        })
        f['col_header'] = workbook.add_format({
            'bold': True, 'text_wrap': True, 'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#C6D9A0', 'border': 1, 'rotation': 90,
        })
        f['date_header'] = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#C6D9A0', 'border': 1,
        })
        f['total_header'] = workbook.add_format({
            'bold': True, 'text_wrap': True, 'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#8DB255', 'font_color': 'white', 'border': 1,
            'rotation': 90,
        })
        f['date_cell'] = workbook.add_format(
            {'bold': True, 'align': 'left', 'border': 1})
        f['num_cell'] = workbook.add_format({'align': 'center', 'border': 1})
        f['total_num_cell'] = workbook.add_format({
            'align': 'center', 'border': 1, 'bold': True,
            'bg_color': '#EAF1DD',
        })
        f['date_cell_holiday'] = workbook.add_format({
            'bold': True, 'align': 'left', 'border': 1, 'bg_color': '#FF0000',
            'font_color': 'white',
        })
        f['num_cell_holiday'] = workbook.add_format({
            'align': 'center', 'border': 1, 'bg_color': '#FF0000',
            'font_color': 'white',
        })
        f['total_num_cell_holiday'] = workbook.add_format({
            'align': 'center', 'border': 1, 'bold': True,
            'bg_color': '#CC0000', 'font_color': 'white',
        })
        return f

    def _write_section(self, sheet, f, row, title, date_start, date_end,
                       staff_jobs, worker_jobs, column_headers, project,
                       holiday_dates):
        (staff_jobs, worker_jobs, col_staff_start, col_total_staff,
         col_worker_start, col_total_worker, col_grand_total,
         col_date) = column_headers

        n_staff = len(staff_jobs)
        n_worker = len(worker_jobs)
        col_staff_end = col_staff_start + n_staff - 1 if n_staff else col_staff_start - 1
        col_worker_end = col_worker_start + n_worker - 1 if n_worker else col_worker_start - 1
        last_col = col_grand_total

        sheet.merge_range(row, 0, row, last_col, title, f['section'])
        row += 1

        header_row1 = row
        if n_staff:
            sheet.merge_range(header_row1, col_staff_start, header_row1,
                              col_staff_end, _('STAFF'), f['group_header'])
        if n_worker:
            sheet.merge_range(header_row1, col_worker_start, header_row1,
                              col_worker_end, _('WORKERS'), f['group_header'])
        row += 1

        header_row2 = row
        sheet.merge_range(header_row2, col_date, header_row2 + 1, col_date,
                          _('Dates'), f['date_header'])
        for i, job in enumerate(staff_jobs):
            sheet.write(header_row2, col_staff_start + i, job.name,
                        f['col_header'])
        sheet.merge_range(header_row2, col_total_staff, header_row2 + 1,
                          col_total_staff,
                          _('Total Staff'), f['total_header'])
        for i, job in enumerate(worker_jobs):
            sheet.write(header_row2, col_worker_start + i, job.name,
                        f['col_header'])
        sheet.merge_range(header_row2, col_total_worker, header_row2 + 1,
                          col_total_worker,
                          _('Total Workforce'), f['total_header'])
        sheet.merge_range(header_row2, col_grand_total, header_row2 + 1,
                          col_grand_total,
                          _('Grand Total'), f['total_header'])

        max_label_len = max(
            [len(j.name) for j in list(staff_jobs) + list(worker_jobs)] + [10])
        sheet.set_row(header_row2, min(max_label_len * 7 + 20, 200))
        row += 2

        Timesheet = self.env['account.analytic.line']
        current = date_start
        while current <= date_end:
            is_holiday = current in holiday_dates
            date_fmt = f['date_cell_holiday'] if is_holiday else f['date_cell']
            num_fmt = f['num_cell_holiday'] if is_holiday else f['num_cell']
            total_fmt = f['total_num_cell_holiday'] if is_holiday else f[
                'total_num_cell']

            lines = Timesheet.search(
                self._get_timesheet_domain(current, project))

            emp_by_job = {}
            for line in lines:
                job = line.employee_id.job_id
                if not job:
                    continue
                emp_by_job.setdefault(job.id, set()).add(line.employee_id.id)

            sheet.write(row, col_date, str(current), date_fmt)

            total_staff = 0
            for i, job in enumerate(staff_jobs):
                count = len(emp_by_job.get(job.id, set()))
                total_staff += count
                sheet.write(row, col_staff_start + i, count, num_fmt)
            sheet.write(row, col_total_staff, total_staff, total_fmt)

            total_worker = 0
            for i, job in enumerate(worker_jobs):
                count = len(emp_by_job.get(job.id, set()))
                total_worker += count
                sheet.write(row, col_worker_start + i, count, num_fmt)
            sheet.write(row, col_total_worker, total_worker, total_fmt)

            sheet.write(row, col_grand_total, total_staff + total_worker,
                        total_fmt)
            row += 1
            current += timedelta(days=1)
        return row