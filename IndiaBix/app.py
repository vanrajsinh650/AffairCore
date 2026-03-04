"""
app.py  —  Pragati Setu Current Affairs Scraper
============================================================
Run with:
    streamlit run app.py
"""

import re
import time
import threading
from datetime import datetime
from pathlib import Path
import base64

import streamlit as st

# ── Session-state initialisation (early so it's ready for config) ────────────
# On a fresh page load, we always start clean (not running, not done).
# Within a session, st.rerun() loops don't reset this because the session persists.
_DEFAULTS = {
    "running": False,
    "done": False,
    "logs": [],
    "result": None,
    "theme": "Light",
    "_date_obj": None,
}
for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Page config ───────────────────────────────────────────────────────────────
logo_path = Path(__file__).parent / "pragati_setu.jpg"
icon = str(logo_path) if logo_path.exists() else "🎯"

st.set_page_config(
    page_title="Pragati Setu Scraper",
    page_icon=icon,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Dynamic Theme & CSS ───────────────────────────────────────────────────────
themes = {
    "Light": {
        "bg": "#fafafa", "text": "#171717", "subtext": "#737373", 
        "card_bg": "#ffffff", "input_bg": "#ffffff", "border": "#e5e5e5", 
        "btn_bg": "#171717", "btn_hover": "#262626", "btn_text": "white",
        "log_bg": "#f5f5f5", "log_text": "#525252"
    },
    "Dark": {
        "bg": "#0a0a0a", "text": "#fafafa", "subtext": "#a3a3a3", 
        "card_bg": "#171717", "input_bg": "#0a0a0a", "border": "#262626", 
        "btn_bg": "#fafafa", "btn_hover": "#e5e5e5", "btn_text": "#0a0a0a",
        "log_bg": "#000000", "log_text": "#d4d4d4"
    }
}
t = themes[st.session_state.theme]

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

        /* Force typography font, but carefully exclude Streamlit's internal icons to prevent _arrow_right_ss text bugs */
        h1, h2, h3, h4, h5, h6, p, a, button, input, div:not([class*="stIcon"]):not([class*="st-emotion"]):not([data-testid="stExpanderToggleIcon"]) {{
            font-family: 'Plus Jakarta Sans', sans-serif;
        }}
        
        /* Explicitly protect Streamlit's Material Symbols */
        .stIcon, 
        [data-testid="stExpanderToggleIcon"],
        [class*="icon"],
        .material-symbols-rounded {{
            font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
        }}
        
        /* Force background for the whole app */
        .stApp, .stApp > header, .stApp > footer {{
            background-color: {t['bg']};
        }}
        
        /* Force text colors across radio labels, markdown, etc. */
        .stApp, .stMarkdown p, .stRadio label div, .stRadio label span, .stCheckbox label span {{
            color: {t['text']} !important;
        }}

        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* Main Container */
        .main-wrapper {{
            max-width: 850px;
            margin: 0 auto;
            padding: 2rem 0;
        }}

        /* Branding Header */
        .brand-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid {t['border']};
            margin-bottom: 2.5rem;
        }}
        .brand-header h1 {{
            font-size: 1.75rem;
            font-weight: 700;
            color: {t['text']};
            margin: 0;
            letter-spacing: -0.02em;
        }}
        .brand-header p {{
            color: {t['subtext']};
            font-size: 0.95rem;
            margin: 0.2rem 0 0 0;
        }}

        /* Responsive Top Bar */
        .top-bar-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid {t['border']};
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        .top-bar-left {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        .top-bar-right {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        @media (max-width: 768px) {{
            .top-bar-container {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .top-bar-right {{
                width: 100%;
                justify-content: flex-start;
            }}
        }}

        /* Input styling */
        .stTextInput > div > div > input {{
            background-color: {t['input_bg']} !important;
            border: 1px solid {t['border']} !important;
            border-radius: 8px !important;
            color: {t['text']} !important;
            font-size: 1rem !important;
            padding: 0.8rem 1rem !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
            transition: all 0.2s;
        }}
        .stTextInput > div > div > input::placeholder {{
            color: {t['subtext']} !important;
            opacity: 0.8 !important;
        }}
        .stTextInput > div > div > input:focus {{
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
            background-color: {t['card_bg']} !important;
        }}
        .stTextInput label {{
            color: {t['text']} !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            margin-bottom: 0.5rem !important;
        }}

        /* Primary Button */
        .stButton > button {{
            background-color: {t['btn_bg']} !important;
            color: {t['btn_text']} !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.8rem 2rem !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            transition: all 0.2s ease !important;
            width: 100%;
            height: 100%;
        }}
        .stButton > button:hover {{
            background-color: {t['btn_hover']} !important;
            transform: translateY(-1px) !important;
            color: white !important;
        }}

        /* Outline Buttons (Downloads) */
        .stDownloadButton > button {{
            background-color: transparent !important;
            color: {t['text']} !important;
            border: 1px solid {t['border']} !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            width: 100%;
            padding: 0.6rem 1rem !important;
            transition: all 0.2s !important;
        }}
        .stDownloadButton > button:hover {{
            background-color: {t['input_bg']} !important;
            border-color: {t['subtext']} !important;
        }}

        /* Log box */
        .log-container {{
            margin-top: 2rem;
            background: {t['log_bg']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 1.2rem;
            font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
            font-size: 0.85rem;
            color: {t['log_text']};
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            line-height: 1.6;
        }}

        /* Status Pills */
        .status-pill {{
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 500;
            background-color: rgba(5, 150, 105, 0.1);
            color: #10b981;
            margin-bottom: 1rem;
        }}

        /* Results Card */
        .results-card {{
            background: {t['card_bg']};
            border: 1px solid {t['border']};
            border-radius: 12px;
            padding: 2rem;
            margin-top: 2rem;
        }}

        /* Stat Grid */
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-bottom: 2rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid {t['border']};
        }}
        @media (max-width: 600px) {{
            .stat-grid {{
                grid-template-columns: 1fr;
                gap: 1rem;
            }}
        }}
        .stat-item {{
            display: flex;
            flex-direction: column;
        }}
        .stat-label {{
            color: {t['subtext']};
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.4rem;
        }}
        .stat-val {{
            color: {t['text']};
            font-size: 1.5rem;
            font-weight: 700;
        }}

        /* Responsive Layouts for Mobile */
        @media (max-width: 768px) {{
            .main-wrapper {{
                padding: 1rem;
            }}
            .stButton > button {{
                padding: 1rem !important;
                margin-top: 0.5rem;
            }}
            div[data-testid="column"] {{
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }}
        }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ───────────────────────────────────────────────────────────────────
INDIABIX_PATTERN = re.compile(
    r"https?://(?:www\.)?indiabix\.com/current-affairs/(\d{4}-\d{2}-\d{2})/?",
    re.IGNORECASE,
)

def parse_url(url: str):
    """Return (date_obj, None)  or  (None, error_str)."""
    url = url.strip()
    if not url:
        return None, "Please paste the source URL."
    m = INDIABIX_PATTERN.match(url)
    if not m:
        return None, "Invalid URL format. Expected: current-affairs/YYYY-MM-DD/"
    try:
        date_obj = datetime.strptime(m.group(1), "%Y-%m-%d")
    except ValueError as e:
        return None, f"Could not parse date: {e}"
    if date_obj > datetime.now():
        return None, "That date is in the future."
    return date_obj, None

def read_bytes(path: str | None):
    """Safely read a file as bytes; return None if missing."""
    if path and Path(path).exists():
        return Path(path).read_bytes()
    return None

def get_logo_base64():
    if logo_path.exists():
        return base64.b64encode(logo_path.read_bytes()).decode()
    return ""


# ── Main Layout ───────────────────────────────────────────────────────────────
st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)

# Top Bar (Logo + Toggles)
logo_b64 = get_logo_base64()
img_html = f'<img src="data:image/jpeg;base64,{logo_b64}" width="50" height="50" style="border-radius: 8px;">' if logo_b64 else '🎯'

st.markdown(f"""
    <div class="top-bar-container">
        <div class="top-bar-left">
            {img_html}
            <div>
                <h1 style="font-size: 1.75rem; font-weight: 700; color: {t['text']}; margin: 0; line-height: 1.2;">Pragati Setu</h1>
                <p style="color: {t['subtext']}; margin: 0; font-size: 0.95rem;">Content Generator</p>
            </div>
        </div>
""", unsafe_allow_html=True)

# We use columns just for the interactive parts holding the radio & button
# But wrap them so they sit nicely on mobile
col_theme, col_deploy = st.columns([1, 1])
with col_theme:
    new_theme = st.radio(
        "Theme", 
        ["Light", "Dark"], 
        index=0 if st.session_state.theme == "Light" else 1,
        horizontal=True,
        label_visibility="collapsed"
    )
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

with col_deploy:
    if st.button("🚀 Deploy", use_container_width=True):
        st.toast("Deploy command triggered!", icon="🚀")

st.markdown("</div>", unsafe_allow_html=True) # close top-bar-container


# ── Input section ─────────────────────────────────────────────────────────────
# We use st.container to group, letting our mobile CSS handle stacking
with st.container():
    col_input, col_btn = st.columns([3, 1], vertical_alignment="bottom")

    with col_input:
        url_input = st.text_input(
            "Source URL",
        placeholder="Past link here (e.g. current-affairs/2026-03-02/)",
        label_visibility="visible",
        key="url_field",
        disabled=st.session_state.running,
    )

with col_btn:
    st.markdown('<div style="height: 0px;"></div>', unsafe_allow_html=True)
    run_clicked = st.button(
        "Generate",
        disabled=st.session_state.running,
        use_container_width=True,
    )

# ── Validation & kick off ─────────────────────────────────────────────────────
if run_clicked:
    date_obj, err = parse_url(url_input)
    if err:
        st.error(err, icon="⚠️")
    else:
        st.session_state.running = True
        st.session_state.done = False
        st.session_state.logs = [f"Starting generation process..."]
        st.session_state.result = None
        st.session_state["_date_obj"] = date_obj
        st.rerun()

# ── Running pipeline (threaded) ───────────────────────────────────────────────
# Strict check: only run if BOTH running=True AND a valid date was set THIS session
if st.session_state.running and not st.session_state.done and isinstance(st.session_state.get("_date_obj"), datetime):
    from scraper_runner import run_pipeline

    date_obj = st.session_state["_date_obj"]
    log_lines = st.session_state.logs

    log_placeholder = st.empty()
    result_holder = {}

    def _worker():
        def cb(line):
            clean = line.replace("INFO  ", "").replace("WARNING  ", "").strip()
            if clean and "Starting new HTTPS connection" not in clean and "urllib3" not in clean:
                log_lines.append(clean)
        
        result_holder["res"] = run_pipeline(date_obj, log_callback=cb)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

    while thread.is_alive():
        log_placeholder.markdown(
            f'<div class="log-container">{chr(10).join(log_lines)}</div>',
            unsafe_allow_html=True,
        )
        time.sleep(0.5)

    thread.join()

    log_placeholder.markdown(
        f'<div class="log-container">{chr(10).join(log_lines)}</div>',
        unsafe_allow_html=True,
    )

    st.session_state.result = result_holder.get("res")
    st.session_state.logs = log_lines
    st.session_state.running = False
    st.session_state.done = True
    st.rerun()

# ── Show saved logs when done ─────────────────────────────────────────────────
if st.session_state.done and st.session_state.logs:
    with st.expander("Show Process Logs", expanded=False):
        st.markdown(
            f'<div class="log-container" style="margin-top:0;">{chr(10).join(st.session_state.logs)}</div>',
            unsafe_allow_html=True,
        )

# ── Results & downloads ───────────────────────────────────────────────────────
if st.session_state.done and st.session_state.result:
    res = st.session_state.result

    if not res.get("success"):
        st.error(f"Generation failed: {res.get('error', 'Unknown error')}", icon="❌")
    else:
        st.markdown(
f"""
<div class="results-card">
    <div class="status-pill">✓ Successfully Generated</div>
    
    <div class="stat-grid">
        <div class="stat-item">
            <span class="stat-label">Content Date</span>
            <span class="stat-val">{res['date']}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Questions Extracted</span>
            <span class="stat-val">{res['questions_count']}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Language</span>
            <span class="stat-val">Gujarati</span>
        </div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )
        
        st.markdown(f"<h4 style='margin: 1.5rem 0 1rem; color: {t['text']}; font-size: 1.1rem;'>Download Assets</h4>", unsafe_allow_html=True)

        dl1, dl2, dl3, dl4 = st.columns(4)

        with dl1:
            data = read_bytes(res.get("pdf_detailed"))
            st.download_button(
                label="Detailed PDF",
                data=data or b"",
                file_name=f"pragati_setu_detailed_{res['date']}.pdf",
                mime="application/pdf",
                disabled=data is None,
                use_container_width=True,
            )

        with dl2:
            data = read_bytes(res.get("pdf_compact"))
            st.download_button(
                label="Compact Tables PDF",
                data=data or b"",
                file_name=f"pragati_setu_compact_{res['date']}.pdf",
                mime="application/pdf",
                disabled=data is None,
                use_container_width=True,
            )

        with dl3:
            data = read_bytes(res.get("json_gujarati"))
            st.download_button(
                label="Gujarati Data (JSON)",
                data=data or b"",
                file_name=f"pragati_setu_gu_{res['date']}.json",
                mime="application/json",
                disabled=data is None,
                use_container_width=True,
            )

        with dl4:
            data = read_bytes(res.get("json_english"))
            st.download_button(
                label="English Data (JSON)",
                data=data or b"",
                file_name=f"pragati_setu_en_{res['date']}.json",
                mime="application/json",
                disabled=data is None,
                use_container_width=True,
            )

st.markdown('</div>', unsafe_allow_html=True)