"""
scraper_runner.py
-----------------
Pipeline helper used by app.py (Streamlit UI).
Takes a single datetime object and runs:
  1. Scrape → 2. Translate → 3. Generate both PDFs + save JSONs
Streams log lines via a callback so the UI can display live progress.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# ── Project imports ────────────────────────────────────────────────────────────
from scraper import scrape_date_wise, create_session
from translator import translate_questions_with_ai
from pdf_generator import PDFGenerator
from pdf_generator_compact import PDFGeneratorCompact


# ── Logging helper that forwards to a callback ─────────────────────────────────
class CallbackHandler(logging.Handler):
    """Sends every log record to a caller-supplied callback(str)."""

    def __init__(self, callback: Callable[[str], None]):
        super().__init__()
        self.callback = callback

    def emit(self, record: logging.LogRecord):
        try:
            self.callback(self.format(record))
        except Exception:
            pass


# ── Main runner ─────────────────────────────────────────────────────────────────
def run_pipeline(
    date_obj: datetime,
    log_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Run the full scrape → translate → PDF pipeline for a single date.

    Parameters
    ----------
    date_obj     : datetime – the date to scrape
    log_callback : callable(str) – receives each log/print line in real time

    Returns
    -------
    dict with keys:
        success          : bool
        questions_count  : int
        date             : str  (YYYY-MM-DD)
        pdf_detailed     : str | None  (absolute path)
        pdf_compact      : str | None  (absolute path)
        json_english     : str | None  (absolute path)
        json_gujarati    : str | None  (absolute path)
        error            : str | None
    """

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

    # Redirect root logger to callback, suppress console (StreamHandler) output
    root_logger = logging.getLogger()
    old_handlers = root_logger.handlers[:]
    cb_handler = None

    # Remove existing StreamHandlers (console) so logs only flow to the UI
    stream_handlers = [h for h in old_handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
    for sh in stream_handlers:
        root_logger.removeHandler(sh)

    if log_callback:
        cb_handler = CallbackHandler(log_callback)
        cb_handler.setFormatter(logging.Formatter("%(levelname)s  %(message)s"))
        root_logger.addHandler(cb_handler)

    try:
        date_str = date_obj.strftime("%Y-%m-%d")
        log(f"📅  Date selected : {date_str}")
        log("─" * 50)

        # ── 1. Scrape ──────────────────────────────────────────────────────────
        log("🔍  Step 1/3 — Scraping IndiaBix …")
        session = create_session()
        questions_en = scrape_date_wise(date_obj, session)

        if not questions_en:
            result["error"] = f"No questions found for {date_str}. The page may not exist yet."
            log(f"❌  {result['error']}")
            return result

        log(f"✅  Scraped {len(questions_en)} questions")
        result["questions_count"] = len(questions_en)

        # ── 2. Translate ───────────────────────────────────────────────────────
        log("🌐  Step 2/3 — Translating to Gujarati (AI) …")
        log("    This may take a few minutes …")
        questions_gu = translate_questions_with_ai(questions_en)
        log(f"✅  Translation complete — {len(questions_gu)} questions ready")

        # ── 3. Save JSONs ──────────────────────────────────────────────────────
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
        log(f"💾  JSON files saved to output/")

        # ── 4. Generate PDFs ───────────────────────────────────────────────────
        log("📄  Step 3/3 — Generating PDFs …")
        watermark_path = script_dir / "pragati_setu.jpg"
        watermark = str(watermark_path) if watermark_path.exists() else None

        # Detailed PDF
        gen_detailed = PDFGenerator(
            output_dir=str(output_dir),
            language="gu",
            watermark_image=watermark,
        )
        pdf_detailed = gen_detailed.generate_pdf(
            questions_gu,
            start_date=date_str,
            end_date=date_str,
        )
        if pdf_detailed:
            result["pdf_detailed"] = pdf_detailed
            log(f"✅  Detailed PDF → {Path(pdf_detailed).name}")

        # Compact PDF
        gen_compact = PDFGeneratorCompact(
            output_dir=str(output_dir),
            language="gu",
            watermark_image=watermark,
        )
        pdf_compact = gen_compact.generate_pdf(
            questions_gu,
            start_date=date_str,
            end_date=date_str,
        )
        if pdf_compact:
            result["pdf_compact"] = pdf_compact
            log(f"✅  Compact PDF  → {Path(pdf_compact).name}")

        # ── Done ───────────────────────────────────────────────────────────────
        log("─" * 50)
        log(f"🎉  Pipeline complete!  {len(questions_gu)} questions processed.")
        result["success"] = True

    except Exception as exc:
        result["error"] = str(exc)
        log(f"❌  Error: {exc}")

    finally:
        # Restore original logger handlers
        if cb_handler and cb_handler in root_logger.handlers:
            root_logger.removeHandler(cb_handler)
            
        # Re-attach the old console handlers
        for h in old_handlers:
            if h not in root_logger.handlers:
                root_logger.addHandler(h)

    return result
