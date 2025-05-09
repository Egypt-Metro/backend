import csv
import io
import xlsxwriter
from datetime import datetime

from django.http import HttpResponse


class ExportService:
    """Service for exporting dashboard data"""

    @staticmethod
    def export_to_csv(data, filename_prefix):
        """Export data to CSV file"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        if not data or not isinstance(data, list) or not data:
            # Return empty CSV with headers if no data
            writer = csv.writer(response)
            writer.writerow(['No data available'])
            return response

        writer = csv.writer(response)

        # Write headers
        headers = data[0].keys()
        writer.writerow(headers)

        # Write data rows
        for item in data:
            writer.writerow(item.values())

        return response

    @staticmethod
    def export_to_excel(data_dict, filename_prefix):
        """Export multiple data sets to Excel file with multiple sheets"""
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)

        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'color': 'white',
            'border': 1
        })

        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        currency_format = workbook.add_format({'num_format': '#,##0.00 EGP'})

        # Process each data set
        for sheet_name, data in data_dict.items():
            if not data:
                continue

            # Create sheet
            worksheet = workbook.add_worksheet(sheet_name)

            # Find column types for formatting
            date_columns = []
            currency_columns = []

            # Write headers if data is a list of dicts
            if isinstance(data, list) and isinstance(data[0], dict):
                headers = list(data[0].keys())

                # Write header row
                for col_idx, header in enumerate(headers):
                    worksheet.write(0, col_idx, header, header_format)

                    # Identify date and currency columns by name
                    lower_header = header.lower()
                    if 'date' in lower_header:
                        date_columns.append(col_idx)
                    elif any(term in lower_header for term in ['revenue', 'price', 'amount', 'cost']):
                        currency_columns.append(col_idx)

                # Write data rows
                for row_idx, row_data in enumerate(data, start=1):
                    for col_idx, header in enumerate(headers):
                        value = row_data.get(header, '')

                        # Apply formatting based on column type
                        if col_idx in date_columns and isinstance(value, (datetime, str)) and 'date' in header.lower():
                            try:
                                if isinstance(value, str):
                                    value = datetime.strptime(value, '%Y-%m-%d')
                                worksheet.write(row_idx, col_idx, value, date_format)
                            except ValueError:
                                worksheet.write(row_idx, col_idx, value)
                        elif col_idx in currency_columns:
                            try:
                                worksheet.write(row_idx, col_idx, float(value) if value else 0, currency_format)
                            except (ValueError, TypeError):
                                worksheet.write(row_idx, col_idx, value)
                        else:
                            worksheet.write(row_idx, col_idx, value)

                # Auto-fit columns
                for col_idx, header in enumerate(headers):
                    worksheet.set_column(col_idx, col_idx, max(len(header) + 2, 12))

        workbook.close()

        # Prepare response
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

        return response
