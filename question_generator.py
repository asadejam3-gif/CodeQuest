"""
Question Generator - Dynamically creates original questions using Claude API
"""

import json
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

client = Anthropic()


async def generate_question(subject: str, difficulty: int) -> dict:
    """
    Generate a completely original question using Claude
    
    Args:
        subject: "Math", "Physics", "Chemistry", "History", "GK", "English"
        difficulty: 0-10=Beginner, 11-20=Easy, 21-35=Medium, 36-50=Hard, 51+=Expert
    
    Returns:
        Dictionary with question, options, correct_index, explanation
    """
    
    # Map difficulty ranges to levels
    if difficulty <= 10:
        level = "Beginner"
        description = "Deep conceptual fundamentals and intuitive traps with minimal heavy calculation"
    elif difficulty <= 20:
        level = "Easy"
        description = "Straightforward logic, multi-step reasoning, solvable with moderate thinking"
    elif difficulty <= 35:
        level = "Medium"
        description = "Advanced thinking required, edge cases, multi-concept synthesis"
    elif difficulty <= 50:
        level = "Hard"
        description = "Expert-level problems with rigorous logic and non-standard setups"
    else:
        level = "Expert"
        description = "Olympiad-level synthesis with extreme edge cases and advanced reasoning"
    
    # Create the prompt for question generation
    prompt = f"""You are an elite competitive problem setter. Generate a 100% ORIGINAL, NOVEL multiple-choice question.

Subject: {subject}
Difficulty Level: {level} (Difficulty Rating: {difficulty})
Description: {description}

CRITICAL REQUIREMENTS:
1. Generate a COMPLETELY UNIQUE question (never use textbook problems)
2. Ensure 3 incorrect options are DELIBERATE distractors based on:
   - Common misconceptions
   - Sign flips
   - Partial logic
   - Off-by-one errors
   - Unit confusion
3. Make wrong options plausible to test understanding, not random
4. For Math: Include specific numbers and real scenarios
5. For Physics: Use realistic physical scenarios
6. For Chemistry: Create novel compound/reaction setups
7. For History: Ask about lesser-known but factual events
8. For GK: Test deep knowledge, not just facts
9. For English: Test grammar, idioms, or comprehension deeply

OUTPUT FORMAT: Return ONLY valid JSON (no markdown, no code fences):
{{
  "question": "<Clear, unambiguous problem using LaTeX or plain text>",
  "options": ["<Option A>", "<Option B>", "<Option C>", "<Option D>"],
  "correct_index": <0, 1, 2, or 3>,
  "explanation": "<Why correct answer is right and why each distractor fails>"
}}

Generate the question now:"""
    
    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text.strip()
        
        # Remove markdown formatting if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        question_data = json.loads(response_text)
        
        # Validate the response
        required_keys = {"question", "options", "correct_index", "explanation"}
        if not all(key in question_data for key in required_keys):
            logger.error(f"Invalid question format: missing keys")
            return None
        
        if len(question_data["options"]) != 4:
            logger.error(f"Invalid options count: {len(question_data['options'])}")
            return None
        
        if question_data["correct_index"] not in [0, 1, 2, 3]:
            logger.error(f"Invalid correct_index: {question_data['correct_index']}")
            return None
        
        question_data["difficulty"] = difficulty
        question_data["subject"] = subject
        
        return question_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return None
    except Exception as e:
        logger.error(f"Error generating question: {e}")
        return None


async def get_difficulty_for_rating(rating: float) -> int:
    """
    Map user rating to question difficulty
    
    Rating 0-10 → Difficulty 0-10 (Beginner)
    Rating 11-20 → Difficulty 11-20 (Easy)
    Rating 21-35 → Difficulty 21-35 (Medium)
    Rating 36-50 → Difficulty 36-50 (Hard)
    Rating 51+ → Difficulty 51+ (Expert)
    """
    return int(max(0, min(100, rating * 5)))  # Scale rating to difficulty
