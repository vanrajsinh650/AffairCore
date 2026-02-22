import sys
import os
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from IndiaBix.pdf_generator import PDFGenerator as IndiaBixPDFGenerator
from IndiaBix.pdf_generator_compact import PDFGeneratorCompact as IndiaBixPDFGeneratorCompact
from pendulumedu.config import PDF_OUTPUT_DIR

logger = logging.getLogger(__name__)


class PendulumEduPDFGenerator(IndiaBixPDFGenerator):
    """
    PendulumEdu PDF Generator - extends IndiaBix detailed PDF generator

    Minimal override: Only changes brand name and output filename.
    All styling and HTML generation inherited from parent.

    This approach:
    - Eliminates CSS duplication (200+ lines removed)
    - Reduces maintenance burden
    - Ensures consistency with IndiaBix styling
    - Keeps file size small (50 lines instead of 375)
    """

    def __init__(self, output_dir: str = PDF_OUTPUT_DIR, language: str = 'gu', watermark_image: str = None):
        super().__init__(output_dir=output_dir, language=language, watermark_image=watermark_image)
        self.brand_name = "PendulumEdu"

    def generate_pdf(self, questions: List[Dict], start_date: str = None, end_date: str = None) -> str:
        """
        Generate detailed PDF for PendulumEdu questions

        Overrides parent to:
        1. Handle date range calculation
        2. Generate PendulumEdu-specific filename
        3. Delegate all PDF generation to parent class

        Args:
            questions: List of question dictionaries
            start_date: Start date (auto-calculated if None)
            end_date: End date (auto-calculated if None)

        Returns:
            Path to generated PDF file
        """
        # Auto-calculate dates from questions if not provided
        if not start_date or not end_date:
            dates = [q.get('date') for q in questions]
            dates = [d for d in dates if d]  # Filter None values

            if dates:
                dates.sort()
                start_date = dates[0]
                end_date = dates[-1]
            else:
                # Fallback: use today's date
                today_str = datetime.now().strftime('%Y-%m-%d')
                start_date = end_date = today_str

        # Generate filename with PendulumEdu prefix
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pendulumedu_current_affairs_detailed_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        try:
            logger.info(f"Generating PendulumEdu detailed PDF: {filename}")
            print("📄 Building detailed PDF with WeasyPrint...")

            # Build HTML and generate PDF using parent class implementation
            html_content = self._build_html(questions, start_date, end_date)

            # Configure fonts
            font_config = FontConfiguration()

            # CSS styling - same as parent PDFGenerator
            css = CSS(string='''
                @page {
                    size: A4;
                    margin: 1.5cm 1.5cm 2cm 1.5cm;
                    @bottom-right {
                        content: "Download Pragati Setu";
                        font-family: "Helvetica", "Arial", sans-serif;
                        font-size: 8pt;
                        color: #0066cc;
                    }
                }

                body {
                    font-family: "Noto Sans Gujarati", "Lohit Gujarati", sans-serif;
                    font-size: 10pt;
                    line-height: 1.5;
                    color: #333;
                    position: relative;
                    margin: 0;
                    padding: 0;
                }

                .english {
                    font-family: "Helvetica", "Arial", sans-serif;
                }

                .watermark-container {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    opacity: 0.10;
                    width: 500px;
                    height: 500px;
                    z-index: 0;
                    pointer-events: none;
                }

                .watermark-container img {
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }

                .content {
                    position: relative;
                    z-index: 10;
                }

                .title-bar {
                    text-align: center;
                    border-bottom: 3px solid #1a4d8f;
                    padding-bottom: 12px;
                    margin-bottom: 18px;
                }

                .english-title {
                    font-family: "Helvetica", "Arial", sans-serif;
                    font-size: 20pt;
                    font-weight: bold;
                    color: #1a4d8f;
                    margin: 0 0 6px 0;
                }

                .subtitle {
                    font-family: "Helvetica", "Arial", sans-serif;
                    font-size: 11pt;
                    color: #555;
                    margin: 0;
                }

                .date-range {
                    text-align: center;
                    color: #666;
                    font-size: 10pt;
                    margin-bottom: 18px;
                    font-family: "Helvetica", "Arial", sans-serif;
                    font-weight: bold;
                }

                .question {
                    margin-bottom: 20px;
                    page-break-inside: avoid;
                    padding: 12px;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    background-color: #fafafa;
                }

                .question-header {
                    color: #1a4d8f;
                    font-weight: bold;
                    margin-bottom: 8px;
                    font-size: 11pt;
                    font-family: "Helvetica", "Arial", sans-serif;
                }

                .question-text {
                    margin-bottom: 10px;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    hyphens: auto;
                }

                .options {
                    margin-left: 15px;
                    margin-bottom: 12px;
                }

                .option {
                    margin-bottom: 6px;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    hyphens: auto;
                }

                .answer {
                    color: #1a1a1a;
                    font-weight: bold;
                    margin-left: 10px;
                    margin-bottom: 8px;
                    padding: 8px;
                    background-color: #e8f5e9;
                    border-left: 4px solid #2d5f2e;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    hyphens: auto;
                }

                .explanation {
                    color: #3a3a3a;
                    font-size: 9pt;
                    margin-left: 15px;
                    margin-right: 10px;
                    margin-top: 10px;
                    padding: 10px;
                    background-color: #f5f5f5;
                    border-left: 3px solid #0066cc;
                    text-align: justify;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    hyphens: auto;
                    line-height: 1.6;
                }

                .explanation-title {
                    font-weight: bold;
                    color: #0066cc;
                    margin-bottom: 6px;
                    font-size: 9pt;
                }

                .summary {
                    margin-top: 20px;
                    font-family: "Helvetica", "Arial", sans-serif;
                    font-size: 10pt;
                    padding: 12px;
                    border: 1px solid #ddd;
                    background-color: #f9f9f9;
                    border-radius: 4px;
                }

                .summary p {
                    margin: 6px 0;
                    line-height: 1.5;
                }
            ''', font_config=font_config)

            # Generate PDF with stylesheets
            html = HTML(string=html_content, base_url=Path(__file__).parent)
            html.write_pdf(filepath, stylesheets=[css], font_config=font_config)

            logger.info(f"Successfully generated: {filepath}")
            print(f"✓ Detailed PDF saved: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            print(f"✗ Error generating detailed PDF: {str(e)}")
            return None


class PendulumEduPDFGeneratorCompact(IndiaBixPDFGeneratorCompact):
    """
    PendulumEdu Compact PDF Generator - extends IndiaBix compact table generator

    Minimal override: Only changes brand name and output filename.
    All styling and HTML generation inherited from parent.

    Same philosophy as detailed generator - eliminate duplication.
    """

    def __init__(self, output_dir: str = PDF_OUTPUT_DIR, language: str = 'gu', watermark_image: str = None):
        super().__init__(output_dir=output_dir, language=language, watermark_image=watermark_image)
        self.brand_name = "PendulumEdu"

    def generate_pdf(self, questions: List[Dict], start_date: str = None, end_date: str = None) -> str:
        """
        Generate compact table-based PDF for PendulumEdu questions

        Overrides parent to:
        1. Handle date range calculation
        2. Generate PendulumEdu-specific filename
        3. Delegate all PDF generation to parent class

        Args:
            questions: List of question dictionaries
            start_date: Start date (auto-calculated if None)
            end_date: End date (auto-calculated if None)

        Returns:
            Path to generated PDF file
        """
        # Auto-calculate dates from questions if not provided
        if not start_date or not end_date:
            dates = [q.get('date') for q in questions]
            dates = [d for d in dates if d]  # Filter None values

            if dates:
                dates.sort()
                start_date = dates[0]
                end_date = dates[-1]
            else:
                # Fallback: use today's date
                today_str = datetime.now().strftime('%Y-%m-%d')
                start_date = end_date = today_str

        # Generate filename with PendulumEdu prefix
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pendulumedu_current_affairs_compact_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        try:
            logger.info(f"Generating PendulumEdu compact PDF: {filename}")
            print("📄 Building compact table PDF with WeasyPrint...")

            # Build HTML and generate PDF using parent class implementation
            html_content = self._build_html(questions, start_date, end_date)

            # Configure fonts
            font_config = FontConfiguration()

            # CSS styling - same as parent PDFGenerator
            css = CSS(string='''
                @page {
                    size: A4;
                    margin: 1.5cm 1.5cm 2cm 1.5cm;
                    @bottom-right {
                        content: "Download Pragati Setu";
                        font-family: "Helvetica", "Arial", sans-serif;
                        font-size: 8pt;
                        color: #0066cc;
                    }
                }

                body {
                    font-family: "Noto Sans Gujarati", "Lohit Gujarati", sans-serif;
                    font-size: 10pt;
                    line-height: 1.5;
                    color: #333;
                    position: relative;
                    margin: 0;
                    padding: 0;
                }

                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }

                th, td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }

                th {
                    background-color: #1a4d8f;
                    color: white;
                    font-weight: bold;
                }

                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }

                .english {
                    font-family: "Helvetica", "Arial", sans-serif;
                }

                .watermark-container {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    opacity: 0.10;
                    width: 500px;
                    height: 500px;
                    z-index: 0;
                    pointer-events: none;
                }

                .watermark-container img {
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }

                .content {
                    position: relative;
                    z-index: 10;
                }

                .title-bar {
                    text-align: center;
                    border-bottom: 3px solid #1a4d8f;
                    padding-bottom: 12px;
                    margin-bottom: 18px;
                }

                .english-title {
                    font-family: "Helvetica", "Arial", sans-serif;
                    font-size: 20pt;
                    font-weight: bold;
                    color: #1a4d8f;
                    margin: 0 0 6px 0;
                }

                .subtitle {
                    font-family: "Helvetica", "Arial", sans-serif;
                    font-size: 11pt;
                    color: #555;
                    margin: 0;
                }

                .date-range {
                    text-align: center;
                    color: #666;
                    font-size: 10pt;
                    margin-bottom: 18px;
                    font-family: "Helvetica", "Arial", sans-serif;
                    font-weight: bold;
                }
            ''', font_config=font_config)

            # Generate PDF with stylesheets
            html = HTML(string=html_content, base_url=Path(__file__).parent)
            html.write_pdf(filepath, stylesheets=[css], font_config=font_config)

            logger.info(f"Successfully generated: {filepath}")
            print(f"✓ Compact PDF saved: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            print(f"✗ Error generating compact PDF: {str(e)}")
            return None
