import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_question(subject: str, difficulty: int) -> dict:
    """Generate question using Google Gemini API"""
    
    if difficulty <= 10:
        level = "Beginner"
    elif difficulty <= 20:
        level = "Easy"
    elif difficulty <= 35:
        level = "Medium"
    elif difficulty <= 50:
        level = "Hard"
    else:
        level = "Expert"
    
    prompt = f"""Generate a 100% ORIGINAL multiple-choice question.
Subject: {subject}
Difficulty Level: {level} (Rating: {difficulty})

Return ONLY valid JSON (no markdown):
{{
  "question": "<Clear problem>",
  "options": ["<Option A>", "<Option B>", "<Option C>", "<Option D>"],
  "correct_index": <0-3>,
  "explanation": "<Why correct and why others fail>"
}}"""
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        question_data = json.loads(response_text)
        question_data["difficulty"] = difficulty
        question_data["subject"] = subject
        
        return question_data
    except Exception as e:
        logger.error(f"Error generating question: {e}")
        return None

async def get_difficulty_for_rating(rating: float) -> int:
    return int(max(0, min(100, rating * 5)))
