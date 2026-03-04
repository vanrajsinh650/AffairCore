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
# NOTE: PDFGenerator is imported lazily inside run_pipeline() to avoid crashes
# on Streamlit Cloud when weasyprint system libs are not installed at import time.


# ── Professional PDF generator matching reference WeasyPrint design ─────────────
def _generate_pdf_bytes_reportlab(questions: list, date_str: str) -> bytes:
    """Generate styled PDF bytes in-memory using ReportLab platypus.
    Design matches reference CSS: blue title bar, question cards, green answer."""
    from io import BytesIO
    from html import escape as _esc
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        Table, TableStyle, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

    # ── Colors matching reference CSS ─────────────────────────────────────────
    BLUE      = colors.HexColor("#1a4d8f")
    BLUE_LINK = colors.HexColor("#0066cc")
    DARK_TEXT = colors.HexColor("#333333")
    GREY_TEXT = colors.HexColor("#555555")
    DATE_TEXT = colors.HexColor("#666666")
    ANS_TEXT  = colors.HexColor("#1a1a1a")
    ANS_BG    = colors.HexColor("#e8f5e9")
    ANS_BAR   = colors.HexColor("#2d5f2e")
    CARD_BG   = colors.HexColor("#fafafa")
    CARD_BDR  = colors.HexColor("#e0e0e0")
    EXP_BG    = colors.HexColor("#f5f5f5")

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=2*cm,
        title="Pragati Setu — Current Affairs",
    )

    s = getSampleStyleSheet()

    # ── Styles ─────────────────────────────────────────────────────────────────
    title_st = ParagraphStyle("rl_title",
        fontName="Helvetica-Bold", fontSize=20, leading=26,
        textColor=BLUE, alignment=TA_CENTER, spaceAfter=6)

    sub_st = ParagraphStyle("rl_sub",
        fontName="Helvetica", fontSize=11, leading=15,
        textColor=GREY_TEXT, alignment=TA_CENTER, spaceAfter=4)

    date_st = ParagraphStyle("rl_date",
        fontName="Helvetica-Bold", fontSize=10, leading=14,
        textColor=DATE_TEXT, alignment=TA_CENTER, spaceAfter=14)

    qhdr_st = ParagraphStyle("rl_qhdr",
        fontName="Helvetica-Bold", fontSize=11, leading=15,
        textColor=BLUE, spaceAfter=6)

    q_st = ParagraphStyle("rl_q",
        fontName="Helvetica", fontSize=10, leading=15,
        textColor=DARK_TEXT, spaceAfter=8, wordWrap="CJK")

    opt_st = ParagraphStyle("rl_opt",
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=DARK_TEXT, leftIndent=12, spaceAfter=4, wordWrap="CJK")

    ans_label_st = ParagraphStyle("rl_ans",
        fontName="Helvetica-Bold", fontSize=10, leading=14,
        textColor=ANS_TEXT, spaceAfter=0, wordWrap="CJK")

    footer_st = ParagraphStyle("rl_footer",
        fontName="Helvetica", fontSize=8,
        textColor=BLUE_LINK, alignment=TA_CENTER)

    # ── Title block ────────────────────────────────────────────────────────────
    story = [
        Paragraph("Pragati Setu", title_st),
        Paragraph("Current Affairs — IndiaBix", sub_st),
        HRFlowable(width="100%", thickness=3, color=BLUE, spaceAfter=6),
        Paragraph(f"Date: {_esc(date_str)}   |   Questions: {len(questions)}", date_st),
    ]

    labels = ["A", "B", "C", "D"]

    for i, q in enumerate(questions, 1):
        qt  = _esc(q.get("question", "").strip())
        ans = _esc(q.get("correct_answer", "").strip())
        opts = q.get("options", [])

        # ── Build card contents ─────────────────────────────────────────────
        card_items = [
            Paragraph(f"Question {i}", qhdr_st),
            Paragraph(qt or "—", q_st),
        ]
        for j, opt in enumerate(opts):
            lbl = labels[j] if j < 4 else str(j + 1)
            card_items.append(Paragraph(f"<b>{lbl}.</b> {_esc(str(opt))}", opt_st))

        if ans:
            # Green answer box using a 1-cell table
            ans_table = Table(
                [[Paragraph(f"<b>✓ Answer:</b> {ans}", ans_label_st)]],
                colWidths=["100%"],
            )
            ans_table.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,-1), ANS_BG),
                ("LEFTPADDING",  (0,0), (-1,-1), 8),
                ("RIGHTPADDING", (0,0), (-1,-1), 8),
                ("TOPPADDING",   (0,0), (-1,-1), 8),
                ("BOTTOMPADDING",(0,0), (-1,-1), 8),
                ("LINEBEFORE",  (0,0), (0,-1), 4, ANS_BAR),
                ("ROWBACKGROUNDS",(0,0),(-1,-1),[ANS_BG]),
            ]))
            card_items.append(Spacer(1, 6))
            card_items.append(ans_table)

        # ── Wrap in question card (bordered table) ──────────────────────────
        card_table = Table(
            [[card_items]],
            colWidths=[doc.width],
        )
        card_table.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), CARD_BG),
            ("BOX",          (0,0), (-1,-1), 1,  CARD_BDR),
            ("LEFTPADDING",  (0,0), (-1,-1), 12),
            ("RIGHTPADDING", (0,0), (-1,-1), 12),
            ("TOPPADDING",   (0,0), (-1,-1), 10),
            ("BOTTOMPADDING",(0,0), (-1,-1), 10),
            ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ]))

        story.append(KeepTogether([card_table, Spacer(1, 10)]))

    # ── Footer ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=CARD_BDR, spaceAfter=6))
    story.append(Paragraph("Download Pragati Setu App", footer_st))

    doc.build(story)
    return buf.getvalue()



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

        # ── Generate PDFs via ReportLab (pure Python, no system libs needed) ──
        try:
            _pdf_bytes = _generate_pdf_bytes_reportlab(questions_gu, date_str)
            result["pdf_detailed_bytes"] = _pdf_bytes
            result["pdf_compact_bytes"] = _pdf_bytes
            log(f"✅  PDFs generated ({len(_pdf_bytes)//1024} KB)")
        except Exception as pdf_exc:
            log(f"❌  PDF generation failed: {pdf_exc}")





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
