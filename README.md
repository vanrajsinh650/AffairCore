# AffairCore: Professional Current Affairs Extraction & Publishing Suite

AffairCore is a high-performance intelligence extraction engine designed to automate the lifecycle of educational content-from raw web scraping to multilingual translation and professional PDF publishing. Built for researchers, educators, and content creators, it provides a seamless bridge between English-source data and Gujarati-speaking audiences.

---

## 🏗️ Architecture & Core Intelligence

### 1. Advanced Scraping Engine

The core extraction logic utilizes a modular approach to navigate complex educational portals (e.g., IndiaBix, PendulumEdu).

- **Targeted Extraction**: Precision-fetches questions, multi-choice options, and detailed pedagogical explanations.
- **Smart Lookback Logic**: Automatically scans previous dates if today's data is not yet published, ensuring zero downtime in content availability.

### 2. Dual-Layer Multilingual Translation

To ensure the highest linguistic accuracy, the suite employs a proprietary fallback mechanism:

- **Primary Tier**: Google Translation (via `deep-translator`) for rapid, high-volume processing.
- **Intelligence Fallback**: If the primary tier encounters rate limits or complex syntax, the system automatically escalates to **Groq (Llama-3.3-70b-versatile)** to maintain professional educational terminology.
- **Entity Protection**: Specialized regex-based filters protect Article numbers, financial figures, and proper nouns from translation artifacts.

### 3. Professional PDF Engineering (The Gujarati Challenge)

Generating high-fidelity PDFs in Indic scripts (Gujarati) is notoriously difficult due to complex ligatures and character shaping.

- **The Solution**: We abandoned legacy engines (ReportLab) in favor of **WeasyPrint**, utilizing the **Pango** layout engine for pixel-perfect Gujarati conjunct rendering.
- **Typography**: Optimized using `Noto Sans Gujarati` and `Lohit Gujarati` for maximum readability.
- **Branding**: Dynamic, low-opacity (10%) watermarking integrated directly into the PDF layout via CSS-fixed-positioning. (Utilizing the **Pragati Setu** brand assets).

---

## 🚀 Quick Deployment & Installation

The Pragati Setu Suite is designed for maximum portability. Choose the method that fits your environment.

### 🌐 Live Dashboard

Access the production-grade application instantly via Streamlit Cloud:
**[Launch AffairCore (Pragati Setu)]((https://affaircore.streamlit.app/))**

---

### Option A: Production-Grade Containerization (Docker)

The most reliable way to deploy AffairCore, ensuring all system-level fonts and dependencies are correctly mapped regardless of your host OS.

```bash
# Clone the repository
git clone [repository-url]
cd AffairCore

# Deploy using Docker Compose
docker-compose up -d --build
```

_The logic will be live at `http://localhost:8501`._

---

### Option B: Manual Virtual Environment Setup

For local development and specialized OS environments.

#### 🐧 Linux (Ubuntu/Debian)

Ensure you have the required fonts and Pango rendering libraries installed:

```bash
sudo apt-get update
sudo apt-get install -y libpango-1.0-0 libharfbuzz0b libpangocairo-1.0-0 fonts-noto-core fonts-lohit-gujr
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

#### 🍎 macOS

Use Homebrew to install the rendering engine dependencies:

```bash
brew install pango libffi
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

#### 🪟 Windows

Windows requires the **GTK3 runtime** for WeasyPrint to function correctly.

1. Download and install the [GTK for Windows Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases).
2. Open PowerShell and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 🛠️ Project Ecosystem

```text
AffairCore/
├── app.py                 # Premium Streamlit GUI Dashboard
├── n8n_trigger.py         # Automation Server (webhook endpoint)
├── scraper_runner.py      # Orchestration Pipeline
├── translator.py          # Dual-Layer Translation Logic
├── pdf_generator.py       # Pango-powered PDF Engine
├── config.py              # Global Environment Parameters
├── pragati_setu.jpg       # High-Resolution Brand Asset (Pragati Setu)
└── output/                # Intelligence Artifacts (JSON/PDF)
```

---

## 🤖 Automation Workflow (n8n Integration)

AffairCore is designed for zero-touch automation using **n8n**. The system provides a dedicated trigger server (`n8n_trigger.py`) that handles the heavy lifting, allowing n8n to orchestrate the final data delivery.

### 1. Start the Automation Trigger

```bash
python n8n_trigger.py
```

_Accessible at `http://localhost:5000/run?days=1`._

### 2. n8n Orchestration (One-Click Upload)

In your n8n workflow, the automation follows this high-efficiency path:

1. **HTTP Request**: n8n calls the trigger URL (`http://localhost:5000/run`).
2. **Processing**: The script scraper, translates, and generates the Gujarati JSON.
3. **API Upload (n8n-side)**: Use an **HTTP Request** node in n8n to POST the generated JSON directly to your server API.

This architecture allows you to manage API credentials and endpoints securely within n8n, keeping the local Python environment lean and focused on extraction.

---

## 🔍 Debugging Insights: The "JSON-First" Approach

During development, we encountered "broken text" issues in direct PDF generation.
**The Breakthrough**: By adopting a **JSON-First** translation workflow (English JSON -> Translated Gujarati JSON -> PDF Generation), we decoupled the linguistic logic from the rendering engine. This solved character-jointing issues and allowed for robust debugging of the translation layer before the final document is published.
