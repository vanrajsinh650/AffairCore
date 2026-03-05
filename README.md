# IndiaBix Current Affairs Scraper

This is a Python-based web scraper that automatically fetches current affairs questions from IndiaBix, translates them into Gujarati, and generates beautiful PDF documents.

It's designed to run both locally on your computer and be easily deployed online using Streamlit Cloud or Docker.

## How It Works (The Scraper)

The core logic of the scraper is simple but robust:

1. **Dropping a Link:** Instead of scrolling through endless calendars, you just paste the exact link to the current affairs page you want (like a specific day on IndiaBix or PendulumEdu). The scraper instantly goes straight to that exact page.
2. **Extracting Data:** It carefully pulls out the question text, the multiple-choice options, the correct answer, and the detailed explanation.
3. **Translation:** Since the original content is in English, the script uses `deep-translator` (Google Translate) to translate the questions and explanations into Gujarati. It handles the translation in small, safe chunks to prevent the translation service from blocking us.
4. **Saving:** The raw data is saved as simple JSON files in the `output/` folder so you always have the original text if you need it.

## The PDF Generation Challenge

Translating text is easy, but generating a professional-looking PDF with Gujarati fonts was the biggest challenge of this project.

Initially, we used a library called `ReportLab`, but the design was very basic and hard to style with colors and borders. So, we upgraded to **WeasyPrint**, which lets us design the PDF exactly like a website using HTML and CSS.

**The Corner Cases We Solved for PDFs:**

- **Missing Fonts (The "Square Box" problem):** When we deployed the app to Streamlit Cloud, the server didn't have Gujarati fonts installed. WeasyPrint didn't know how to draw the letters, so it just printed empty square boxes `□□□`.
- **The Solution:** We explicitly added Debian Linux font packages (`fonts-gujr` and `fonts-dejavu-core`) to a special `packages.txt` file and our `Dockerfile`. This forces the server to download the correct fonts before running the Python code, completely fixing the square boxes.
- **Word Wrapping:** Sometimes long explanations would run right off the edge of the PDF page. We fixed this by adding CSS rules (`word-wrap: break-word` and `hyphens: auto`) to ensure sentences break cleanly.
- **Page Breaks:** We added `page-break-inside: avoid` so that a single question and its options don't awkwardly split across two different pages.

## How to Run It Locally

The project is built to be simple. You don't need any complex setup scripts anymore.

1. **Create a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python packages:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install System Fonts (Linux Only):**
   If you are on Linux and want to test PDF generation locally, you need WeasyPrint's dependencies:

   ```bash
   sudo apt-get install libpango-1.0-0 libcairo2 fonts-gujr
   ```

4. **Run the App:**
   - To run the visual dashboard: `streamlit run app.py`
   - To run just the background script: `python main.py`

## How It Is Deployed

This project is natively ready for **Streamlit Cloud**.
Because we placed `app.py`, `requirements.txt`, and `packages.txt` right in the main folder, Streamlit Cloud automatically knows how to build the app without any extra configuration. It reads `packages.txt` to install the system fonts, then reads `requirements.txt` to install Python libraries, and finally runs the UI.

If you ever want to run it on a private server, we also included a `Dockerfile` and `docker-compose.yml` so you can spin it up anywhere with one command: `docker-compose up`.
