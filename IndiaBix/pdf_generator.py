import os
import logging
from datetime import datetime
from typing import List, Dict
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


logger = logging.getLogger(__name__)


class PDFGenerator:
    def __init__(self, output_dir: str = "output", language: str = 'gu', watermark_image: str = None):
        self.output_dir = output_dir
        self.language = language
        self.watermark_image = watermark_image
        self.app_url = "https://play.google.com/store/apps/details?id=com.pragatisetu.app"
        self.brand_name = "Indiabix"
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_pdf(self, questions: List[Dict], start_date: str, end_date: str) -> str:
        """Generate detailed PDF using WeasyPrint with proper word wrapping"""
        try:
            filename = "current_affairs_detailed.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            logger.info(f"Generating detailed PDF: {filename}")
            print("Building detailed PDF with WeasyPrint...")
            
            # Build HTML content
            html_content = self._build_html(questions, start_date, end_date)
            
            # Configure fonts
            font_config = FontConfiguration()
            
            # CSS styling with proper word wrapping and box styling
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
            
            # Generate PDF
            HTML(string=html_content).write_pdf(
                filepath,
                stylesheets=[css],
                font_config=font_config
            )
            
            logger.info(f"Detailed PDF generated successfully: {filepath}")
            print(f"Detailed PDF created: {filepath}")
            print(f"App Link: {self.app_url}")
            print(f"Brand: {self.brand_name}")
            print(f"Total Questions: {len(questions)}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
            print(f"Error generating PDF: {str(e)}")
            return None
    
    def _build_html(self, questions: List[Dict], start_date: str, end_date: str) -> str:
        """Build HTML content for detailed PDF"""
        
        # Start HTML
        html = '''<!DOCTYPE html>
<html lang="gu">
<head>
    <meta charset="UTF-8">
    <title>Current Affairs - Pragati Setu</title>
</head>
<body>
'''
        
        # Add watermark
        if self.watermark_image and os.path.exists(self.watermark_image):
            image_uri = f"file://{os.path.abspath(self.watermark_image)}"
            logger.info(f"Using watermark: {image_uri}")
            html += f'''<div class="watermark-container">
    <img src="{image_uri}" alt="Logo" />
</div>
'''
        
        # Content wrapper
        html += '<div class="content">'
        
        # Title section
        html += '''<div class="title-bar">
    <p class="english-title">Indiabix Current Affairs</p>
    <p class="subtitle">Questions & Answers with Detailed Explanations</p>
</div>'''
        
        # Date range
        html += f'<div class="date-range">{start_date} to {end_date}</div>'
        
        # Questions
        for idx, q in enumerate(questions, 1):
            html += '<div class="question">'
            
            # Question header
            html += f'<div class="question-header"><span class="english">Q. {idx}</span></div>'
            
            # Question text
            question_text = self._escape_html(q.get('question', ''))
            html += f'<div class="question-text">{question_text}</div>'
            
            # Options
            html += '<div class="options">'
            options = q.get('options', [])
            option_letters = ['A', 'B', 'C', 'D', 'E', 'F']
            for opt_idx, option in enumerate(options):
                if opt_idx < len(option_letters):
                    option_text = self._escape_html(option)
                    html += f'<div class="option"><span class="english"><b>{option_letters[opt_idx]}.</b></span> {option_text}</div>'
            html += '</div>'
            
            # Answer
            answer = self._escape_html(q.get('answer', 'Not available'))
            html += f'<div class="answer"><span class="english">✓ Answer:</span> {answer}</div>'
            
            # Explanation
            explanation = q.get('explanation', '')
            if explanation and explanation.strip():
                exp_text = self._escape_html(explanation)
                html += f'<div class="explanation"><div class="explanation-title">સમજૂતી (Explanation):</div>{exp_text}</div>'
            
            html += '</div>'  # Close question
        
        # Summary section
        html += f'''
<div class="summary">
    <p><b>Total Questions:</b> {len(questions)}</p>
    <p><b>Brand:</b> {self.brand_name}</p>
    <p><b>App:</b> <a href="{self.app_url}">Download Pragati Setu</a></p>
</div>
'''
        
        # Close content wrapper
        html += '</div>'
        html += '</body>\n</html>'
        
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
