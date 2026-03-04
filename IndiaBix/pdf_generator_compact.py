import os
import logging
from datetime import datetime
from typing import List, Dict
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import base64


logger = logging.getLogger(__name__)


class PDFGeneratorCompact:
    """Generate compact table-based PDF using WeasyPrint for proper Gujarati rendering"""

    def __init__(self, output_dir: str = "output", language: str = 'gu', watermark_image: str = None):
        """Initialize compact PDF generator
        
        Args:
            output_dir: Output directory for PDFs
            language: Language code (default: 'gu' for Gujarati)
            watermark_image: Path to watermark image file
        """
        self.output_dir = output_dir
        self.language = language
        self.watermark_image = watermark_image
        self.app_url = "https://play.google.com/store/apps/details?id=com.pragatisetu.app"
        self.brand_name = "Indiabix"
        
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Initialized compact PDF generator for language: {language}")

    def generate_pdf(self, questions: List[Dict], start_date: str = None, 
                     end_date: str = None) -> str:
        """Generate compact table-based PDF using WeasyPrint"""
        if not questions:
            logger.warning("No questions provided for PDF generation")
            return None

        try:
            filename = "current_affairs_compact.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            logger.info(f"Generating compact PDF: {filename}")
            print(f"Building compact PDF with WeasyPrint...")
            
            html_content = self._build_html(questions, start_date, end_date)
            font_config = FontConfiguration()
            css = CSS(string=self._get_css_styles(), font_config=font_config)
            
            HTML(string=html_content).write_pdf(
                filepath,
                stylesheets=[css],
                font_config=font_config
            )
            
            logger.info(f"Compact PDF generated successfully: {filepath}")
            print(f"Compact PDF created: {filepath}")
            print(f"App Link: {self.app_url}")
            print(f"Brand: {self.brand_name}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating compact PDF: {str(e)}", exc_info=True)
            print(f"Error generating compact PDF: {str(e)}")
            return None

    def _get_image_base64(self) -> str:
        """Convert watermark image to base64"""
        if self.watermark_image and os.path.exists(self.watermark_image):
            try:
                with open(self.watermark_image, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                    return f"data:image/jpeg;base64,{img_data}"
            except Exception as e:
                logger.error(f"Error converting image to base64: {e}")
                return ""
        return ""

    def _get_css_styles(self) -> str:
        """Get CSS styling for compact table format with watermark on EVERY page"""
        
        # Get base64 encoded watermark
        watermark_data_uri = self._get_image_base64()
        
        page_css = '''
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
        '''
        
        # Build watermark CSS if image exists
        watermark_css = ""
        if watermark_data_uri:
            logger.info("Adding watermark via running() element")
            watermark_css = f'''
            @page {{
                @top-center {{
                    content: element(watermark);
                }}
            }}
            
            .watermark {{
                position: running(watermark);
                width: 100%;
                height: 500px;
                text-align: center;
            }}
            
            .watermark img {{
                width: 450px;
                height: 450px;
                opacity: 0.10;
                object-fit: contain;
            }}
            '''
        
        return page_css + watermark_css + '''
            body {
                font-family: "Noto Sans Gujarati", "Lohit Gujarati", sans-serif;
                font-size: 9pt;
                line-height: 1.4;
                color: #333;
                margin: 0;
                padding: 0;
            }
            
            .content {
                position: relative;
                z-index: 10;
            }
            
            .title-bar {
                text-align: center;
                border-bottom: 2px solid #1a4d8f;
                padding-bottom: 8px;
                margin-bottom: 6px;
            }
            
            .english-title {
                font-family: "Helvetica", "Arial", sans-serif;
                font-size: 16pt;
                font-weight: bold;
                color: #1a4d8f;
                margin: 0;
            }
            
            .subtitle {
                font-family: "Helvetica", "Arial", sans-serif;
                font-size: 9pt;
                color: #555;
                margin: 3px 0 0 0;
            }
            
            .date-range {
                text-align: center;
                color: #666;
                font-size: 9pt;
                margin-bottom: 12px;
                font-family: "Helvetica", "Arial", sans-serif;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 0;
                font-size: 9pt;
            }
            
            thead {
                background-color: #1a4d8f;
                color: white;
            }
            
            th {
                padding: 8px 6px;
                text-align: center;
                font-weight: bold;
                font-family: "Noto Sans Gujarati", "Lohit Gujarati", sans-serif;
                font-size: 10pt;
                border: 1px solid #1a4d8f;
            }
            
            td {
                padding: 8px 6px;
                border: 1px solid #ccc;
                vertical-align: top;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }
            
            .table-num {
                text-align: center;
                font-weight: bold;
                width: 4%;
                font-family: "Helvetica", "Arial", sans-serif;
                font-size: 9pt;
            }
            
            .table-question {
                width: 71%;
                text-align: left;
                line-height: 1.5;
            }
            
            .table-answer {
                width: 25%;
                text-align: left;
                color: #1a1a1a;
                font-weight: bold;
                font-size: 9pt;
            }
            
            tbody tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            
            tbody tr:nth-child(odd) {
                background-color: #ffffff;
            }
            
            .summary {
                margin-top: 20px;
                font-family: "Helvetica", "Arial", sans-serif;
                font-size: 9pt;
                padding: 12px;
                border-top: 1px solid #ccc;
            }
            
            .summary p {
                margin: 4px 0;
                line-height: 1.5;
            }
        '''

    def _build_html(self, questions: List[Dict], start_date: str, 
                    end_date: str) -> str:
        """Build HTML content with table format"""
        
        html = '''<!DOCTYPE html>
<html lang="gu">
<head>
    <meta charset="UTF-8">
    <title>Current Affairs Compact - Pragati Setu</title>
</head>
<body>
'''
        
        # Add watermark element that will repeat on every page
        watermark_data_uri = self._get_image_base64()
        if watermark_data_uri:
            html += f'''<div class="watermark">
    <img src="{watermark_data_uri}" alt="Watermark" />
</div>
'''
        
        html += '<div class="content">'
        
        html += f'''<div class="title-bar">
    <p class="english-title">{self.brand_name} Current Affairs</p>
    <p class="subtitle">Current Affairs by {self.brand_name}</p>
</div>'''
        
        if start_date and end_date:
            html += f'<div class="date-range">{start_date} to {end_date}</div>'
        else:
            html += f'<div class="date-range">Generated on {datetime.now().strftime("%d-%m-%Y")}</div>'
        
        html += '''<table>
<thead>
    <tr>
        <th class="table-num">નં.</th>
        <th class="table-question">પ્રશ્ન</th>
        <th class="table-answer">જવાબ</th>
    </tr>
</thead>
<tbody>
'''
        
        for idx, q in enumerate(questions, 1):
            question_text = self._escape_html(q.get('question', ''))
            answer = self._escape_html(q.get('answer', 'N/A'))
            
            html += f'''<tr>
    <td class="table-num">{idx}</td>
    <td class="table-question">{question_text}</td>
    <td class="table-answer">{answer}</td>
</tr>
'''
        
        html += '''</tbody>
</table>
'''
        
        html += f'''<div class="summary">
    <p><b>Total Questions:</b> {len(questions)}</p>
    <p><b>Powered by:</b> {self.brand_name}</p>
    <p><b>App:</b> <a href="{self.app_url}">Download Pragati Setu</a></p>
</div>
'''
        
        html += '</div></body></html>'
        return html

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))
