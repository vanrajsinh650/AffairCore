import json
import logging
import os
import re
import time
import socket
import textwrap
from typing import Optional, List, Dict, Tuple, Any, cast
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from groq import Groq

# Monkeypatch requests to enforce a timeout globally for deep-translator
import requests
_orig_get = requests.get
def _timeout_get(*args, **kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 5
    return _orig_get(*args, **kwargs)
requests.get = _timeout_get

load_dotenv()
logger = logging.getLogger(__name__)

class GroqTranslator:
    """Translation using Groq LLM (much faster and more reliable than Google Translate)"""
    
    client: Optional[Groq]
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            self.client = None
            logger.warning("GROQ_API_KEY not found in environment")
            return
            
        try:
            self.client = Groq(api_key=self.api_key)
            logger.info("✓ Groq Translator Ready")
        except Exception as e:
            logger.error(f"Failed to initialize Groq: {e}")
            self.client = None

    def translate_batch(self, questions: list) -> list:
        """Translate all questions in batches for speed and context"""
        if not self.client:
            return []

        translated = []
        total = len(questions)
        
        # We can translate questions one by one or in small batches
        # For simplicity and to avoid context window issues, we'll do one by one but without delays
        for i, q in enumerate(questions, 1):
            if not self.client: # Re-check for type narrowing
                translated.append(q)
                continue
                
            print(f"Translating Q{i}/{total} with Groq...", end=" ", flush=True)
            try:
                # Prepare a structured prompt for the LLM
                prompt = f"""
                Translate the following Current Affairs question from English to Gujarati.
                Maintain professional educational terminology.
                
                Question: {q.get('question', '')}
                Options: {", ".join(q.get('options', []))}
                Correct Answer: {q.get('answer', '')}
                Explanation: {q.get('explanation', '')}
                
                Return ONLY a JSON object with keys: "question", "options" (list), "answer", "explanation".
                Do not include any conversational text.
                """
                
                # Explicitly cast to avoid NoneType linter error
                safe_client = cast(Groq, self.client)
                response = safe_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a professional English-to-Gujarati translator specializing in competitive exam content."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.3-70b-versatile", # High quality, fast model
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response from Groq")
                
                result = json.loads(content)
                
                t_q = q.copy()
                t_q.update({
                    "question": str(result.get("question", q["question"])),
                    "options": list(result.get("options", q["options"])),
                    "answer": str(result.get("answer", q["answer"])),
                    "explanation": str(result.get("explanation", q["explanation"])),
                })
                translated.append(t_q)
                print("DONE!")
                
            except Exception as e:
                logger.error(f"Groq translation failed for Q{i}: {e}")
                print(f"FAILED (using English)")
                translated.append(q)
                
        return translated

class ImprovedGujaratiTranslator:
    """Enhanced Google Translator with pre/post-processing (Fallback)"""
    
    def __init__(self):
        try:
            self.translator = GoogleTranslator(source='en', target='gu')
            print("✓ Enhanced Gujarati Translator Ready")
            logger.info("✓ Translator initialized")
        except Exception as e:
            logger.error(f"Failed: {e}")
            self.translator = None
    
    def preprocess_text(self, text: str) -> tuple[str, dict]:
        """Clean English before translation & extract entities"""
        if not text:
            return "", {}
        
        # Store proper nouns and special terms to restore later
        entities = {}
        state = {'counter': 0}
        
        # Protect proper nouns (capitalized words)
        def protect_entity(match):
            placeholder = f"__ENTITY{state['counter']}__"
            entities[placeholder] = match.group(0)
            state['counter'] += 1
            return placeholder
        
        # Protect: Article numbers
        text = re.sub(r'\bArticle \d+(?:\(\d+\))?', protect_entity, text)
        
        # Protect: Numbers with units ($, km, %, kg, etc.)
        text = re.sub(r'\$[\d,\.]+\s*(?:billion|million|thousand)?', protect_entity, text)
        text = re.sub(r'\d+[\d,\.]*\s*(?:km|kg|crore|lakh|million|billion|%|feet|tonnes?)', protect_entity, text, flags=re.IGNORECASE)
        
        # Protect: Years and dates
        text = re.sub(r'\b(19|20)\d{2}(?:-\d{2}-\d{2})?\b', protect_entity, text)
        
        # Protect: Organization abbreviations
        text = re.sub(r'\b[A-Z]{2,}(?:-[A-Z]{2,})?\b', protect_entity, text)
        
        # Clean up spacing
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Fix common punctuation
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text, entities
    
    def postprocess_text(self, gujarati: str, entities: dict) -> str:
        """Restore entities after translation"""
        if not gujarati:
            return ""
        
        # Restore protected entities
        for placeholder, original in entities.items():
            gujarati = gujarati.replace(placeholder, original)
        
        # Fix spacing around punctuation
        gujarati = re.sub(r'\s+([?,\.!।])', r'\1', gujarati)
        gujarati = re.sub(r'([?,\.!।])\s*', r'\1 ', gujarati)
        gujarati = gujarati.strip()
        
        return gujarati
    
    def translate_text(self, text: str, max_retries: int = 1) -> str:
        """Translate with pre/post processing"""
        if not text or not text.strip():
            return text
        
        # Preprocess
        clean_text, entities = self.preprocess_text(text)
        if not clean_text or not self.translator:
            return text
            
        curr_text: str = str(clean_text)
        
        # Translate
        for attempt in range(max_retries):
            try:
                if len(curr_text) > 4500:
                    # textwrap.wrap produces a list of strings
                    chunks = textwrap.wrap(curr_text, 4500, break_long_words=True, replace_whitespace=False)
                    
                    result_list: List[str] = []
                    for chunk_item in chunks:
                        res = self.translator.translate(chunk_item)
                        if res:
                            result_list.append(str(res))
                    result = ' '.join(result_list)
                else:
                    result = self.translator.translate(curr_text)
                
                if result and '□' not in result:
                    # Postprocess
                    result = self.postprocess_text(str(result), entities)
                    return result
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return text
                time.sleep(2 ** attempt)
        
        return text
    
    def translate_question(self, question: dict, q_num: int) -> dict:
        """Translate question with special handling"""
        if not self.translator:
            return question
            
        translated = question.copy()
        
        try:
            # Question text
            if 'question' in question:
                translated['question'] = self.translate_text(question['question'])
            
            # Options - keep format clean
            if 'options' in question:
                translated['options'] = [
                    self.translate_text(opt) for opt in question['options']
                ]
            
            # Answer - keep option letter
            if 'answer' in question:
                # Extract "Option A: " part and translate rest
                match = re.match(r'(Option [A-D]:\s*)(.*)', question['answer'])
                if match:
                    prefix, answer_text = match.groups()
                    translated['answer'] = f"{prefix}{self.translate_text(answer_text)}"
                else:
                    translated['answer'] = self.translate_text(question['answer'])
            
            # Explanation
            if 'explanation' in question and question['explanation']:
                translated['explanation'] = self.translate_text(question['explanation'])
            
            # Category - keep English
            if 'category' in question:
                translated['category'] = question['category']  # Keep English
            
            # Date - keep English format
            if 'date' in question:
                translated['date'] = question['date']  # Keep YYYY-MM-DD
            
            return translated
            
        except Exception as e:
            logger.error(f"Q{q_num} translation failed: {e}")
            return question
    
    def translate_all(self, questions: list) -> list:
        """Translate all questions"""
        if not self.translator:
            return questions
        
        translated = []
        total = len(questions)
        
        print(f"Translating {total} questions with Google Translate...")
        
        for i, q in enumerate(questions, 1):
            print(f"Q{i}/{total}...", end=" ", flush=True)
            translated.append(self.translate_question(q, i))
            print("DONE!")
            time.sleep(1.5)  # Rate limit
        
        return translated

def save_questions_json(questions: list, filename: str):
    os.makedirs("output", exist_ok=True)
    filepath = os.path.join("output", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    return filepath

def translate_questions_with_ai(questions: list) -> list:
    """Translate questions trying Google first, with Groq as a high-quality fallback"""
    start = time.time()
    
    logger.info("Saving English JSON...")
    save_questions_json(questions, "questions_english.json")
    
    # Initialize both translators
    google_translator = ImprovedGujaratiTranslator()
    groq_translator = GroqTranslator()
    
    translated = []
    total = len(questions)
    
    logger.info(f"Translating {total} questions (Google -> Groq Fallback)...")
    
    for i, q in enumerate(questions, 1):
        logger.info(f"Translating Q{i}/{total}...")
        q_translated = None
        
        # 1. Try Google first
        if google_translator.translator:
            try:
                # If Google succeeds and actually translates (doesn't return original text), use it.
                cand = google_translator.translate_question(q, i)
                if cand['question'] != q['question']:
                    q_translated = cand
                    logger.info(f"✓ Q{i} translated by Google")
            except Exception as e:
                logger.warning(f"Google failed for Q{i}: {e}")

        # 2. Fallback to Groq if Google failed or didn't translate
        if not q_translated and groq_translator.client:
            try:
                # Translate THIS single question with Groq
                cand = groq_translator.translate_batch([q])[0]
                if cand['question'] != q['question']:
                    q_translated = cand
                    logger.info(f"✓ Q{i} translated by Groq (Fallback)")
            except Exception as e:
                logger.error(f"Groq fallback failed for Q{i}: {e}")

        # 3. Last fallback: Keep English
        if not q_translated:
            q_translated = q
            logger.warning(f"⚠ Q{i} kept in English (All translators failed)")
            
        translated.append(q_translated)
        
        # Small delay to prevent rate limits
        if i < total:
            time.sleep(0.5)
    
    logger.info("Saving Gujarati JSON...")
    save_questions_json(translated, "questions_gujarati.json")
    
    elapsed = time.time() - start
    logger.info(f"Translation complete in {elapsed:.0f}s")
    
    return translated
