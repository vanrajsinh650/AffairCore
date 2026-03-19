from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.
    New websites should implement a subclass of BaseScraper.
    """
    
    @abstractmethod
    def scrape_date(self, date_obj: datetime) -> List[Dict]:
        """
        Scrape questions for a specific date.
        
        Args:
            date_obj (datetime): The target date to scrape.
            
        Returns:
            List[Dict]: A list of scraped questions with metadata.
        """
        raise NotImplementedError("Subclasses must implement scrape_date")

    def scrape_range(self, dates: List[datetime]) -> List[Dict]:
        """
        Scrape questions for a sequence of dates.
        
        Args:
            dates (List[datetime]): A list of dates to scrape.
            
        Returns:
            List[Dict]: A combined list of all questions across the dates.
        """
        all_questions = []
        for date_obj in dates:
            questions = self.scrape_date(date_obj)
            all_questions.extend(questions)
        return all_questions
