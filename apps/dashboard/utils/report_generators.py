# apps/dashboard/utils/report_generators.py

import io
from typing import Dict, List
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


class ReportGenerator:
    """
    Advanced report generation utilities
    """
    @classmethod
    def generate_excel_report(
        cls,
        data: List[Dict],
        filename: str
    ) -> str:
        """
        Generate comprehensive Excel report
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Write headers
        headers = list(data[0].keys())
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Write data
        for row, item in enumerate(data, start=1):
            for col, header in enumerate(headers):
                worksheet.write(row, col, item.get(header, ''))

        workbook.close()
        output.seek(0)

        return output

    @classmethod
    def generate_pdf_report(
        cls,
        data: List[Dict],
        filename: str
    ) -> str:
        """
        Generate comprehensive PDF report
        """
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Title
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(inch, height - inch, "Performance Report")

        # Table headers and data
        y = height - 2 * inch
        for item in data:
            pdf.setFont("Helvetica", 10)
            for key, value in item.items():
                pdf.drawString(inch, y, f"{key}: {value}")
                y -= 15

        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        return buffer
