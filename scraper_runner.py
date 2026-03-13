import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from scraper import scrape_date_wise, create_session
from translator import translate_questions_with_ai
from pdf_generator import PDFGenerator
from pdf_generator_compact import PDFGeneratorCompact

class CallbackHandler(logging.Handler):
    """sends every log record to a callback(str)."""

    def __init__(self, callback: Callable[[str], None]):
        super().__init__()
        self.callback = callback

    def emit(self, record: logging.LogRecord):
        try:
            self.callback(self.format(record))
        except Exception:
            pass


# Main runner 
def run_pipeline(
    date_obj: datetime,
    log_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    result = {
        "success": False,
        "questions_count": 0,
        "date": date_obj.strftime("%Y-%m-%d"),
        "pdf_detailed": None,
        "pdf_compact": None,
        "json_english": None,
        "json_gujarati": None,
        "error": None,
    }

    def log(msg: str):
        if log_callback:
            log_callback(msg)

    assert isinstance(date_obj, datetime), "date_obj must be a datetime object"

    # redirect root logger to callback, suppress console output
    root_logger = logging.getLogger()
    old_handlers = root_logger.handlers[:]
    cb_handler = None

   

    if log_callback:
         # remove existing console stream handlers
        stream_handlers = [h for h in old_handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
        for sh in stream_handlers:
            root_logger.removeHandler(sh)
        cb_handler = CallbackHandler(log_callback)
        cb_handler.setFormatter(logging.Formatter("%(levelname)s  %(message)s"))
        root_logger.addHandler(cb_handler)

    try:
        date_str = date_obj.strftime("%Y-%m-%d")
        log(f"selected date : {date_str}")
        log("─" * 50)

        # scrape
        log("step 1/3 — scraping indiabix...")
        session = create_session()
        questions_en = scrape_date_wise(date_obj, session)

        if not questions_en:
            result["error"] = f"no questions found for {date_str}. the page may not exist yet."
            log(f"{result['error']}")
            return result

        log(f"scraped {len(questions_en)} questions")
        result["questions_count"] = len(questions_en)

        # translate
        log("step 2/3 — translating to gujarati (ai)...")
        log("this may take a few minutes...")
        questions_gu = translate_questions_with_ai(questions_en)
        if not questions_gu:
            result["error"] = "translation failed, no questions to process further."
            log(result["error"])
            return result
        log(f"translation complete — {len(questions_gu)} questions ready")

        # save jsons
        script_dir = Path(__file__).parent
        output_dir = script_dir / "output"
        output_dir.mkdir(exist_ok=True)

        json_en_path = output_dir / "questions_english.json"
        json_gu_path = output_dir / "questions_gujarati.json"

        with open(json_en_path, "w", encoding="utf-8") as f:
            json.dump(questions_en, f, ensure_ascii=False, indent=2)
        with open(json_gu_path, "w", encoding="utf-8") as f:
            json.dump(questions_gu, f, ensure_ascii=False, indent=2)

        result["json_english"] = str(json_en_path)
        result["json_gujarati"] = str(json_gu_path)
        log(f"json files saved to output/")


        # generate pdfs
        log("step 3/3 — generating pdfs...")
        watermark_path = script_dir / "pragati_setu.jpg"
        watermark = str(watermark_path) if watermark_path.exists() else None

        # generate pdfs using weasyprint fallback
        try:
            # detailed pdf
            gen_detailed = PDFGenerator(
                output_dir=str(output_dir), language="gu", watermark_image=watermark,
            )
            pdf_detailed = gen_detailed.generate_pdf(
                questions_gu, start_date=date_str, end_date=date_str
            )
            if pdf_detailed:
                result["pdf_detailed"] = pdf_detailed
                log(f"detailed pdf -> {Path(pdf_detailed).name}")

            # compact pdf
            gen_compact = PDFGeneratorCompact(
                output_dir=str(output_dir), language="gu", watermark_image=watermark,
            )
            pdf_compact = gen_compact.generate_pdf(
                questions_gu, start_date=date_str, end_date=date_str
            )
            if pdf_compact:
                result["pdf_compact"] = pdf_compact
                log(f"compact pdf  -> {Path(pdf_compact).name}")

        except Exception as pdf_exc:
            log(f"pdf generation failed: {pdf_exc}")

        # done
        log("─" * 50)
        log(f"pipeline complete!  {len(questions_gu)} questions processed.")
        result["success"] = True

    except Exception as exc:
        result["error"] = str(exc)
        log(f"Error: {exc}\n{traceback.format_exc()}")

    finally:
        # Restore original logger handlers
        if cb_handler and cb_handler in root_logger.handlers:
            root_logger.removeHandler(cb_handler)
            
        # Re-attach the old console handlers
        for h in old_handlers:
            if h not in root_logger.handlers:
                root_logger.addHandler(h)

    return result
