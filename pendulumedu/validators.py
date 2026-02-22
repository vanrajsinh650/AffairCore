"""
Validation module for Current Affairs questions
Ensures data integrity before PDF generation and translation
"""
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class QuestionValidator:
    """Validates question data structure and content"""

    @staticmethod
    def validate_question(question: Dict, question_no: int = None) -> Tuple[bool, str]:
        """
        Validate a single question dictionary

        Args:
            question: Question dictionary to validate
            question_no: Question number for logging

        Returns:
            (is_valid, error_message)
        """
        q_id = f"Q{question_no}" if question_no else "Unknown"

        # Check required fields
        required_fields = ['question_no', 'question', 'options', 'answer', 'explanation', 'category', 'date']
        for field in required_fields:
            if field not in question:
                return False, f"{q_id}: Missing required field '{field}'"

        # Validate question_no (must be positive integer)
        if not isinstance(question['question_no'], int) or question['question_no'] <= 0:
            return False, f"{q_id}: question_no must be positive integer"

        # Validate question text (must be non-empty string)
        if not isinstance(question['question'], str) or not question['question'].strip():
            return False, f"{q_id}: question text is empty"

        # Validate options (must be list with 3-5 items)
        if not isinstance(question['options'], list):
            return False, f"{q_id}: options must be a list"

        if len(question['options']) < 3 or len(question['options']) > 5:
            return False, f"{q_id}: expected 3-5 options, got {len(question['options'])}"

        for i, opt in enumerate(question['options']):
            if not isinstance(opt, str) or not opt.strip():
                return False, f"{q_id}: option {i} is empty or not a string"

        # Validate answer (must be in "Option X: text" format)
        if not isinstance(question['answer'], str):
            return False, f"{q_id}: answer must be a string"

        if question['answer']:  # Only validate if non-empty
            # Should match "Option A/B/C/D: text" format
            answer_match = re.match(r'Option\s+([A-D]):\s*(.+)', question['answer'], re.IGNORECASE)
            if not answer_match:
                logger.warning(f"{q_id}: answer format unexpected: {question['answer'][:50]}")
                # Don't fail on this - some answers might be in different format

            # If we have letter, verify it corresponds to an option
            if answer_match:
                letter = answer_match.group(1).upper()
                option_index = ord(letter) - ord('A')
                if option_index >= len(question['options']):
                    return False, f"{q_id}: answer refers to Option {letter} but only {len(question['options'])} options exist"

        # Validate date format (YYYY-MM-DD)
        if not isinstance(question['date'], str):
            return False, f"{q_id}: date must be a string"

        date_match = re.match(r'^\d{4}-\d{2}-\d{2}$', question['date'])
        if not date_match:
            return False, f"{q_id}: date format should be YYYY-MM-DD, got {question['date']}"

        # All validations passed
        return True, ""

    @staticmethod
    def validate_questions(questions: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate a list of questions

        Args:
            questions: List of question dictionaries

        Returns:
            (valid_questions, invalid_questions)
        """
        valid = []
        invalid = []

        for i, question in enumerate(questions, 1):
            is_valid, error_msg = QuestionValidator.validate_question(question, i)
            if is_valid:
                valid.append(question)
            else:
                logger.error(error_msg)
                invalid.append(question)

        if invalid:
            logger.warning(f"Validation: {len(valid)} valid, {len(invalid)} invalid out of {len(questions)} questions")
        else:
            logger.info(f"✓ All {len(valid)} questions validated successfully")

        return valid, invalid
