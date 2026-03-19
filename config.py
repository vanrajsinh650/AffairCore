from datetime import datetime, timedelta

# base url configuration
BASE_URL = "https://www.indiabix.com"
CURRENT_AFFAIRS_URL = f"{BASE_URL}/current-affairs/questions-and-answers/"

# request headers to avoid 403 errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
TIMEOUT = 30  # seconds

# pdf configuration
PDF_OUTPUT_DIR = "output"
PDF_FONT_SIZE = 12
PDF_TITLE_FONT_SIZE = 16

# branding and output config
BRAND_NAME = "Indiabix"
APP_URL = "https://play.google.com/store/apps/details?id=com.pragatisetu.app"
WATERMARK_FILENAME = "pragati_setu.jpg"

# scheduler configuration
SCHEDULE_DAY = "sun"  # run every sunday
SCHEDULE_HOUR = 23
SCHEDULE_MINUTE = 59

# how many days to scrape backwards
DAYS_TO_SCRAPE = 2


def get_date_range():
    """
    calculate the date range for past 7 days from today (going backwards)
    
    example: if today is dec 28, 2025:
    - returns: [dec 28, dec 27, dec 26, dec 25, dec 24, dec 23, dec 22]
    """
    today = datetime.now()
    dates = []
    
    # go backwards from today for DAYS_TO_SCRAPE days
    for i in range(DAYS_TO_SCRAPE):
        date = today - timedelta(days=i)
        dates.append(date)
    
    return dates
