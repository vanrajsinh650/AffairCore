import sys
import logging
import os   
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

from config import get_date_range, PDF_OUTPUT_DIR, WATERMARK_FILENAME, DAYS_TO_SCRAPE
from scraper import IndiabixScraper
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
    """main function"""
    
    parser = argparse.ArgumentParser(description="IndiaBix Current Affairs Scraper CLI")
    parser.add_argument("--days", type=int, default=DAYS_TO_SCRAPE, help="Number of days to scrape backwards (default from config)")
    args = parser.parse_args()

    logger.info("="*60)
    logger.info("indiabix current affairs scraper - ai translation")
    logger.info("="*60)
    
    try:
        # Calculate dates based on argument or config
        today = datetime.now()
        dates = [today - timedelta(days=i) for i in range(args.days)]
        
        start_date = dates[-1].strftime('%Y-%m-%d')
        end_date = dates[0].strftime('%Y-%m-%d')
        
        logger.info(f"date range: {start_date} to {end_date} ({args.days} days)")
        
        logger.info("scraping questions...")
        print(f"\nscraping questions for {args.days} days...")
        
        scraper = IndiabixScraper()
        questions = scraper.scrape_range(dates)
        
        if not questions:
            print("no questions found")
            return False
        
        logger.info(f"scraped {len(questions)} questions")
        print(f"scraped {len(questions)} questions")
        
        gujarati_questions = translate_questions_with_ai(questions)

        # json packaging box
        output_dir = Path(__file__).parent / PDF_OUTPUT_DIR
        output_dir.mkdir(exist_ok=True)
        
        gujarati_json_path = output_dir / "questions_gujarati.json"
        
        try:
            with open(gujarati_json_path, "w", encoding="utf-8") as f:
                json.dump(gujarati_questions, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"error in saving JSON: {str(e)}", exc_info=True)
            print(f"\nerror in saving JSON: {str(e)}")

        # use path to get watermark relative to this script file
        watermark_path = Path(__file__).parent / WATERMARK_FILENAME
        if not watermark_path.exists():
            watermark_path = None

        logger.info("generating pdfs...")
        
        # detailed pdf
        pdf_gen_detailed = PDFGenerator(
            output_dir=str(output_dir),
            language='gu',
            watermark_image=str(watermark_path) if watermark_path else None
        )
        pdf_path_detailed = pdf_gen_detailed.generate_pdf(
            gujarati_questions, start_date=start_date, end_date=end_date
        )
        
        # compact pdf
        pdf_gen_compact = PDFGeneratorCompact(
            output_dir=str(output_dir),
            language='gu',
            watermark_image=str(watermark_path) if watermark_path else None
        )
        pdf_path_compact = pdf_gen_compact.generate_pdf(
            gujarati_questions, start_date=start_date, end_date=end_date
        )
        
        print("\n" + "="*60)
        print("SUCCESS! Scraping and Translation Complete")
        print("="*60)
        
        print(f"TOTAL QUESTIONS: {len(gujarati_questions)}")
        print(f"GUJARATI JSON: {gujarati_json_path.absolute()}")
        if pdf_path_detailed:
            print(f"DETAILED PDF: {Path(pdf_path_detailed).absolute()}")
        if pdf_path_compact:
            print(f"COMPACT PDF: {Path(pdf_path_compact).absolute()}")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"error: {str(e)}", exc_info=True)
        print(f"\nerror: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
