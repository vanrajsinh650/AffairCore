import json
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path to import from IndiaBix
sys.path.insert(0, str(Path(__file__).parent.parent))

from pendulumedu.pendulumedu_scraper import scrape_weekly_questions
from pendulumedu.config import get_date_range, PDF_OUTPUT_DIR
from pendulumedu.pendulumedu_pdf_generator import PendulumEduPDFGenerator, PendulumEduPDFGeneratorCompact
from IndiaBix.translator import translate_questions_with_ai

logger = logging.getLogger(__name__)


def save_json(data: list, filename: str, output_dir: str):
    """Save questions to JSON file"""
    try:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(data)} questions to {filepath}")
        print(f"✓ Saved: {filepath}")

    except Exception as e:
        logger.error(f"Error saving JSON: {str(e)}")
        print(f"✗ Failed to save {filename}: {str(e)}")


def main():
    """Main orchestration pipeline for PendulumEdu scraping"""
    print("\n" + "="*60)
    print("   PENDULUMEDU CURRENT AFFAIRS SCRAPER")
    print("="*60 + "\n")

    # Set output directory relative to this script
    output_dir = str(Path(__file__).parent / "output")

    # Step 1: Get date range
    dates = get_date_range()
    print(f"📅 Scraping dates: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")

    # Step 2: Scrape English questions
    print("\n🔄 Step 1: Scraping English questions from PendulumEdu...")
    english_questions = scrape_weekly_questions(dates)

    if not english_questions:
        print("✗ No questions scraped. Exiting.")
        return

    print(f"✓ Scraped {len(english_questions)} English questions")

    # Extract date information for filenames
    all_dates = [q.get('date') for q in english_questions]
    if all_dates:
        start_date = min(all_dates)
        end_date = max(all_dates)
    else:
        start_date = end_date = None

    # Step 3: Save English JSON
    print("\n💾 Step 2: Saving English questions...")
    save_json(english_questions, 'pendulumedu_questions_english.json', output_dir)

    # Step 4: Translate to Gujarati using shared IndiaBix translator
    print("\n🌐 Step 3: Translating to Gujarati...")
    gujarati_questions = translate_questions_with_ai(english_questions)

    if not gujarati_questions:
        print("✗ Translation failed. Exiting.")
        return

    save_json(gujarati_questions, 'pendulumedu_questions_gujarati.json', output_dir)

    # Load watermark from pendulumedu folder
    watermark_path = None
    watermark_candidate = Path(__file__).parent / "pragati_setu.jpg"

    if watermark_candidate.exists():
        watermark_path = str(watermark_candidate.absolute())
        print(f"✓ Watermark loaded: {watermark_path}")
    else:
        print(f"⚠️  Watermark not found at {watermark_candidate}")

    # Step 5: Generate PDFs
    print("\n📄 Step 4: Generating PDFs...")
    if gujarati_questions:
        # Generate detailed PDF
        print("\n   📋 Generating detailed PDF...")
        detailed_gen = PendulumEduPDFGenerator(
            output_dir=output_dir,
            language='gu',
            watermark_image=watermark_path
        )
        detailed_pdf = detailed_gen.generate_pdf(gujarati_questions, start_date, end_date)

        # Generate compact PDF
        print("   📊 Generating compact table PDF...")
        compact_gen = PendulumEduPDFGeneratorCompact(
            output_dir=output_dir,
            language='gu',
            watermark_image=watermark_path
        )
        compact_pdf = compact_gen.generate_pdf(gujarati_questions, start_date, end_date)

        if detailed_pdf and compact_pdf:
            print("\n✓ Both PDFs generated successfully!")
        else:
            print("\n⚠️  Some PDFs failed to generate")
    else:
        print("   ⚠️  No questions to generate PDFs")

    print("\n" + "="*60)
    print("✓ PendulumEdu scraping pipeline complete!")
    print("="*60)
    print(f"\nTotal questions: {len(gujarati_questions)}")
    print(f"\nFiles created:")
    print(f"output/pendulumedu/pendulumedu_questions_english.json")
    print(f"output/pendulumedu/pendulumedu_questions_gujarati.json")
    if detailed_pdf:
        print(f"{detailed_pdf}")
    if compact_pdf:
        print(f"{compact_pdf}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
