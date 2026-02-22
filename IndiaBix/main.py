import sys
import logging
import os
from pathlib import Path
from datetime import datetime
from config import get_date_range
from scraper import scrape_weekly_questions
from translator import translate_questions_with_ai
from pdf_generator import PDFGenerator
from pdf_generator_compact import PDFGeneratorCompact

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main function"""
    
    logger.info("="*60)
    logger.info("IndiaBix Current Affairs Scraper - AI Translation")
    logger.info("="*60)
    
    try:
        dates = get_date_range()
        start_date = dates[-1].strftime('%Y-%m-%d')
        end_date = dates[0].strftime('%Y-%m-%d')
        
        logger.info(f"Date range: {start_date} to {end_date}")
        
        logger.info("Scraping questions...")
        print("\nScraping questions...")
        questions = scrape_weekly_questions(dates)
        
        if not questions:
            print("No questions found")
            return False
        
        logger.info(f"Scraped {len(questions)} questions")
        print(f"Scraped {len(questions)} questions")
        
        gujarati_questions = translate_questions_with_ai(questions)

        # Use Path to get watermark relative to this script file
        watermark_path = Path(__file__).parent / "pragati_setu.jpg"

        if watermark_path.exists():
            print(f"Watermark loaded: {watermark_path}")
        else:
            print(f"WARNING: Watermark not found at {watermark_path}")
            watermark_path = None

        # Set output directory relative to this script
        output_dir = Path(__file__).parent / "output"

        logger.info("Generating detailed PDF...")
        print("\nGenerating Detailed PDF (Style 1)...")

        pdf_gen_detailed = PDFGenerator(
            output_dir=str(output_dir),
            language='gu',
            watermark_image=str(watermark_path) if watermark_path else None
        )
        
        pdf_path_detailed = pdf_gen_detailed.generate_pdf(
            gujarati_questions,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info("Generating compact table PDF...")
        print("\nGenerating Compact Table PDF (Style 2)...")

        pdf_gen_compact = PDFGeneratorCompact(
            output_dir=str(output_dir),
            language='gu',
            watermark_image=str(watermark_path) if watermark_path else None
        )
        
        pdf_path_compact = pdf_gen_compact.generate_pdf(
            gujarati_questions,
            start_date=start_date,
            end_date=end_date
        )
        
        print("\n" + "="*60)
        print("SUCCESS! BOTH PDFs GENERATED")
        print("="*60)
        
        if pdf_path_detailed:
            print(f"PDF 1 (Detailed): {pdf_path_detailed}")
        else:
            print("PDF 1 (Detailed): FAILED")
        
        if pdf_path_compact:
            print(f"PDF 2 (Compact): {pdf_path_compact}")
        else:
            print("PDF 2 (Compact): FAILED")
        
        print(f"\nTotal questions: {len(gujarati_questions)}")
        print(f"\nFiles created:")
        print(f"output/questions_english.json")
        print(f"output/questions_gujarati.json")
        if pdf_path_detailed:
            print(f"{pdf_path_detailed}")
        if pdf_path_compact:
            print(f"{pdf_path_compact}")
        print("="*60)
        
        return pdf_path_detailed and pdf_path_compact
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
