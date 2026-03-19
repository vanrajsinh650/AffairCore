import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

from config import HEADERS, MAX_RETRIES, RETRY_DELAY, TIMEOUT, BASE_URL
from base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class IndiabixScraper(BaseScraper):
    """Scraper implementation for Indiabix"""
    
    def __init__(self):
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """create a requests session with retry strategy"""
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

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """fetch and parse a webpage"""
        try:
            logger.info(f"fetching: {url}")
            response = self.session.get(url, headers=HEADERS, timeout=TIMEOUT)
            
            # Handle standard missing pages
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            logger.info(f"successfully fetched: {url}")
            return soup
        
        except requests.exceptions.RequestException as e:
            logger.error(f"error fetching {url}: {str(e)}")
            return None

    def extract_questions(self, soup: BeautifulSoup) -> List[Dict]:
        """extract questions, options, and answers from indiabix current affairs page"""
        questions_data = []
        
        try:
            # find all question containers
            question_blocks = soup.find_all('div', class_='bix-div-container')
            
            if not question_blocks:
                logger.warning("no question blocks found on page")
                return questions_data
            
            logger.info(f"found {len(question_blocks)} question blocks")
            
            for idx, block in enumerate(question_blocks, 1):
                try:
                    q_text_div = block.find('div', class_='bix-td-qtxt')
                    if not q_text_div:
                        continue
                    question_text = q_text_div.get_text(strip=True)
                    
                    options = []
                    option_container = block.find('div', class_='bix-tbl-options')
                    if option_container:
                        option_divs = option_container.find_all('div', class_='bix-td-option-val')
                        for opt_div in option_divs:
                            opt_text = opt_div.get_text(strip=True)
                            if opt_text:
                                options.append(opt_text)
                    
                    answer = "Not available"
                    answer_input = block.find('input', class_='jq-hdnakq')
                    if answer_input:
                        answer_value = answer_input.get('value', '')
                        if answer_value and len(options) >= ord(answer_value) - ord('A') + 1:
                            answer_index = ord(answer_value) - ord('A')
                            answer = f"Option {answer_value}: {options[answer_index]}"
                        else:
                            answer = f"Option {answer_value}"
                    
                    explanation = ""
                    exp_div = block.find('div', class_='bix-ans-description')
                    if exp_div:
                        explanation = exp_div.get_text(strip=True)
                    
                    category = ""
                    cat_link = block.find('div', class_='explain-link')
                    if cat_link:
                        cat_a = cat_link.find('a')
                        if cat_a:
                            category = cat_a.get_text(strip=True)
                    
                    question_data = {
                        'question_no': idx,
                        'question': question_text,
                        'options': options,
                        'answer': answer,
                        'explanation': explanation,
                        'category': category
                    }
                    
                    questions_data.append(question_data)
                    logger.info(f"extracted q{idx}: {question_text[:60]}...")
                    
                except Exception as e:
                    logger.error(f"error extracting question {idx}: {str(e)}")
                    continue
            
            logger.info(f"total questions extracted: {len(questions_data)}")
            return questions_data
        
        except Exception as e:
            logger.error(f"error in extract_questions: {str(e)}")
            return questions_data

    def scrape_date(self, date_obj: datetime) -> List[Dict]:
        """scrape questions for a specific date"""
        date_url = f"{BASE_URL}/current-affairs/{date_obj.strftime('%Y-%m-%d')}/"
        logger.info(f"scraping for date: {date_obj.strftime('%Y-%m-%d')}")
        
        soup = self.fetch_page(date_url)
        if not soup:
            logger.warning(f"failed to fetch page for {date_obj.strftime('%Y-%m-%d')}")
            return []
        
        # fallback string check for their specific 404 alert, just in case they return 200 OK
        error_alert = soup.find('div', class_='alert-danger')
        if error_alert and 'not found' in error_alert.get_text().lower():
            logger.warning(f"page not found for {date_obj.strftime('%Y-%m-%d')}")
            return []
        
        questions = self.extract_questions(soup)
        
        for question in questions:
            question['date'] = date_obj.strftime('%Y-%m-%d')
        
        time.sleep(1)
        return questions
