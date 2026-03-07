import sys
import logging
import os   
import json
from pathlib import Path
from datetime import datetime
from config import get_date_range
from scraper import scrape_weekly_questions
from translator import translate_questions_with_ai
from pdf_generator import PDFGenerator
from pdf_generator_compact import PDFGeneratorCompact
from image_generator import get_ai_image_url
from imgbb_uploader import upload_url_to_imagebb

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
    
    logger.info("="*60)
    logger.info("indiabix current affairs scraper - ai translation")
    logger.info("="*60)
    
    try:
        dates = get_date_range()
        start_date = dates[-1].strftime('%Y-%m-%d')
        end_date = dates[0].strftime('%Y-%m-%d')
        
        logger.info(f"date range: {start_date} to {end_date}")
        
        logger.info("scraping questions...")
        print("\nscraping questions...")
        questions = scrape_weekly_questions(dates)
        
        if not questions:
            print("no questions found")
            return False
        
        logger.info(f"scraped {len(questions)} questions")
        print(f"scraped {len(questions)} questions")
        
        gujarati_questions = translate_questions_with_ai(questions)

        #image generation and json packging box
        try:
            logger.info("generating context-aware thumbnail...")
            print("\ngenerating AI thumbnail using groq LLM and pollinations image generation...")

            ai_url = get_ai_image_url(gujarati_questions)

            logger.info("uploding thumbnail to imageBB...")
            pemanent_image_url = upload_url_to_imagebb(ai_url)

            output_dir = Path(__file__).parent / "output"
            output_dir.mkdir(exist_ok=True)

            gujarati_json_path = output_dir / "questions_gujarati.json"

            with open(gujarati_json_path, "w", encoding="utf-8") as f:
                json.dump(gujarati_questions, f, ensure_ascii=False, indent=4)

            link_path = output_dir / "thumbnail_link.txt"
            if pemanent_image_url:
                with open(link_path, "w", encoding="utf-8") as f:
                    f.write(pemanent_image_url)
                logger.info(f"thumbnail uploaded to imageBB: {pemanent_image_url}")
                print(f"thumbnail uploaded to imageBB: {pemanent_image_url}")
            else:
                logger.warning("thumbnail upload failed, using original AI URL")
                print("thumbnail upload failed, using original AI URL")
                with open(link_path, "w", encoding="utf-8") as f:
                    f.write(ai_url)

        except Exception as e:
            logger.error(f"error in image generation or hosting: {str(e)}", exc_info=True)
            print(f"\nerror in image generation or hosting: {str(e)}")

        # use path to get watermark relative to this script file
        watermark_path = Path(__file__).parent / "pragati_setu.jpg"

        if watermark_path.exists():
            print(f"watermark loaded: {watermark_path}")
        else:
            print(f"warning: watermark not found at {watermark_path}")
            watermark_path = None

        # set output directory relative to this script
        output_dir = Path(__file__).parent / "output"

        logger.info("generating detailed pdf...")
        print("\ngenerating detailed pdf (style 1)...")

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
        
        logger.info("generating compact table pdf...")
        print("\ngenerating compact table pdf (style 2)...")

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
        print("success! both pdfs generated")
        print("="*60)
        
        if pdf_path_detailed:
            print(f"pdf 1 (detailed): {pdf_path_detailed}")
        else:
            print("pdf 1 (detailed): failed")
        
        if pdf_path_compact:
            print(f"pdf 2 (compact): {pdf_path_compact}")
        else:
            print("pdf 2 (compact): failed")
        
        print(f"\ntotal questions: {len(gujarati_questions)}")
        print(f"\nfiles created:")
        print(f"output/questions_english.json")
        print(f"output/questions_gujarati.json")
        print(f"output/thumbnail_link.txt")
        if pdf_path_detailed:
            print(f"{pdf_path_detailed}")
        if pdf_path_compact:
            print(f"{pdf_path_compact}")
        print("="*60)
        
        return pdf_path_detailed and pdf_path_compact
        
    except Exception as e:
        logger.error(f"error: {str(e)}", exc_info=True)
        print(f"\nerror: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
