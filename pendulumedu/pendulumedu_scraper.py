import requests
from bs4 import BeautifulSoup
import time
import logging
import re
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pendulumedu.config import HEADERS, MAX_RETRIES, RETRY_DELAY, TIMEOUT, BASE_URL, get_date_range, get_quiz_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    """Create a requests session with retry strategy"""
    session = requests.Session()

    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_DELAY,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def fetch_page(url: str, session: requests.Session) -> Optional[BeautifulSoup]:
    """Fetch and parse a webpage"""
    try:
        logger.info(f"Fetching: {url}")
        response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')
        logger.info(f"Successfully fetched: {url}")
        return soup

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None


def extract_option_text(option_div) -> tuple[str, str]:
    """
    Extract option letter and text from option div

    Returns: (letter, text)
    Example: ("A", "New Delhi")
    """
    try:
        # Get option letter from .checkmark.containerr-option
        letter_elem = option_div.find('div', class_=['checkmark', 'containerr-option'])
        letter = letter_elem.get_text(strip=True) if letter_elem else ""

        # Get option text from .containerr-text-opt > p > span
        text_elem = option_div.find('div', class_='containerr-text-opt')
        if text_elem:
            span = text_elem.find('span')
            text = span.get_text(strip=True) if span else ""
        else:
            text = ""

        return letter, text
    except Exception as e:
        logger.error(f"Error extracting option: {str(e)}")
        return "", ""


def extract_questions_from_soup(soup: BeautifulSoup, language='english') -> List[Dict]:
    """
    Extract questions from PendulumEdu quiz page

    Args:
        soup: BeautifulSoup object of the page
        language: 'english' or 'hindi' - which section to extract from

    Returns:
        List of question dictionaries
    """
    questions_data = []

    try:
        # Select appropriate quiz section
        if language == 'english':
            quiz_section = soup.find('div', class_='english_quiz_class')
        else:  # hindi
            quiz_section = soup.find('div', class_='hindi_quiz_class')

        if not quiz_section:
            logger.warning(f"No {language} quiz section found on page")
            return questions_data

        # Find all question sections within the quiz section
        question_sections = quiz_section.find_all('div', class_='q-section-inner', recursive=True)

        if not question_sections:
            logger.warning(f"No question sections found in {language} section")
            return questions_data

        logger.info(f"Found {len(question_sections)} question sections in {language}")

        for idx, section in enumerate(question_sections, 1):
            try:
                # Extract question number
                q_num_elem = section.find('div', class_='q-number')
                q_num_text = q_num_elem.get_text(strip=True) if q_num_elem else f"Question {idx}"

                # Extract question text
                q_name_elem = section.find('div', class_='q-name')
                question_text = ""
                if q_name_elem:
                    more_elem = q_name_elem.find('div', class_='more')
                    if more_elem:
                        span_elem = more_elem.find('span', attrs={'itemprop': 'description'})
                        if span_elem:
                            p_elem = span_elem.find('p')
                            if p_elem:
                                inner_span = p_elem.find('span')
                                if inner_span:
                                    question_text = inner_span.get_text(strip=True)

                if not question_text:
                    logger.warning(f"Skipping question {idx} - no question text found")
                    continue

                # Extract options (A, B, C, D)
                options = []
                option_divs = section.find_all('div', class_='q')

                for opt_div in option_divs:
                    letter, text = extract_option_text(opt_div)
                    if text:
                        options.append(text)

                if len(options) != 4:
                    logger.warning(f"Question {idx} has {len(options)} options, expected 4")
                    # Continue anyway - we'll use what we have

                # Extract answer from solution section
                answer = ""
                solution_elem = section.find('div', class_='solution-sec')
                if solution_elem:
                    answr_elem = solution_elem.find('div', class_='answr')
                    if answr_elem:
                        answr_text = answr_elem.get_text(strip=True)
                        # Parse "Answer : Option D" format
                        match = re.search(r'Option ([A-D])', answr_text)
                        if match:
                            answer_letter = match.group(1)
                            answer_index = ord(answer_letter) - ord('A')
                            if answer_index < len(options):
                                answer = f"Option {answer_letter}: {options[answer_index]}"
                            else:
                                answer = f"Option {answer_letter}"
                        else:
                            logger.warning(f"Could not parse answer from: {answr_text}")
                else:
                    logger.debug(f"No solution section found for question {idx}")

                # Extract explanation
                explanation = ""
                if solution_elem:
                    ans_text_elem = solution_elem.find('div', class_='ans-text')
                    if ans_text_elem:
                        # Extract all text from explanation section
                        explanation = ans_text_elem.get_text(strip=True)

                # Build question data
                question_data = {
                    'question_no': idx,
                    'question': question_text,
                    'options': options,
                    'answer': answer,
                    'explanation': explanation,
                    'category': 'Current Affairs'  # Static category for PendulumEdu
                }

                questions_data.append(question_data)
                logger.info(f"Extracted Q{idx} ({language}): {question_text[:60]}...")

            except Exception as e:
                logger.error(f"Error extracting question {idx}: {str(e)}")
                continue

        logger.info(f"Total {language} questions extracted: {len(questions_data)}")
        return questions_data

    except Exception as e:
        logger.error(f"Error in extract_questions_from_soup ({language}): {str(e)}")
        return questions_data


def scrape_quiz_page(date_obj, session: requests.Session) -> tuple[List[Dict], List[Dict]]:
    """
    Scrape a single PendulumEdu quiz page for both English and Hindi

    Returns: (english_questions, hindi_questions)
    """
    quiz_url = get_quiz_url(date_obj)
    date_str = date_obj.strftime('%Y-%m-%d')

    logger.info(f"Scraping quiz for date: {date_str}")

    soup = fetch_page(quiz_url, session)
    if not soup:
        logger.warning(f"Failed to fetch quiz page for {date_str}")
        return [], []

    # Check if page exists (look for 404 or no content)
    q_sections = soup.find_all('div', class_='q-section-inner')
    if not q_sections:
        logger.warning(f"No quiz content found for {date_str}")
        return [], []

    # Extract English questions
    english_questions = extract_questions_from_soup(soup, language='english')

    # Extract Hindi questions (optional - but we focus on English for now)
    # hindi_questions = extract_questions_from_soup(soup, language='hindi')

    # Add date metadata to each question
    for question in english_questions:
        question['date'] = date_str

    # Add a small delay to avoid rate limiting
    time.sleep(1)

    return english_questions, []


def scrape_weekly_questions(dates: List = None) -> List[Dict]:
    """
    Scrape questions for all dates (NO TRANSLATION - just scraping)

    Args:
        dates: List of datetime objects. If None, uses get_date_range()

    Returns:
        List of question dictionaries with all metadata
    """
    if dates is None:
        dates = get_date_range()

    all_questions = []
    session = create_session()

    logger.info(f"Starting PendulumEdu scrape for {len(dates)} days (going backwards from today)")

    for date_obj in dates:
        english_qs, hindi_qs = scrape_quiz_page(date_obj, session)
        all_questions.extend(english_qs)

    logger.info(f"PendulumEdu scrape complete. Total questions: {len(all_questions)}")
    return all_questions
