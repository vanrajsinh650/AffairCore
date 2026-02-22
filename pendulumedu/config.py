from datetime import datetime, timedelta

# Base URL configuration for PendulumEdu
BASE_URL = "https://pendulumedu.com"
QUIZ_LIST_URL = f"{BASE_URL}/quiz/current-affairs"

# Request headers to avoid 403 errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Referer': QUIZ_LIST_URL,
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
TIMEOUT = 30  # seconds

# PDF configuration
PDF_OUTPUT_DIR = "output"
PDF_FONT_SIZE = 12
PDF_TITLE_FONT_SIZE = 16

# How many days to scrape backwards
DAYS_TO_SCRAPE = 2


def get_date_range():
    """
    Calculate the date range for PAST 6 days from today (going backwards)

    Example: If today is Feb 21, 2026:
    - Returns: [Feb 21, Feb 20, Feb 19, Feb 18, Feb 17, Feb 16]

    Note: Matches IndiaBix pattern - uses range(DAYS_TO_SCRAPE), not range(DAYS_TO_SCRAPE + 1)
    """
    today = datetime.now()
    dates = []

    # Go backwards from today for DAYS_TO_SCRAPE days
    for i in range(DAYS_TO_SCRAPE):
        date = today - timedelta(days=i)
        dates.append(date)

    return dates


def get_quiz_url(date_obj):
    """
    Convert datetime object to PendulumEdu quiz URL

    Example: Feb 21, 2026 → https://pendulumedu.com/quiz/current-affairs/21-february-2026-current-affairs-quiz
    """
    # Format: 21-february-2026
    slug = date_obj.strftime("%d-%B-%Y").lower()
    quiz_url = f"{BASE_URL}/quiz/current-affairs/{slug}-current-affairs-quiz"
    return quiz_url
