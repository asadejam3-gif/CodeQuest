"""
CodeQuest Bot - FINAL ULTRA-SIMPLE VERSION
Pure hardcoded questions, no database dependencies in callbacks
"""

import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuizState(StatesGroup):
    selecting_subject = State()
    answering_question = State()

bot = Bot(token=TOKEN)
dp = Dispatcher()

SUBJECTS = ["Math", "Physics", "Chemistry", "History", "GK", "English"]

# HARDCODED QUESTIONS
QUESTIONS_DB = {
    "Math": [
        {"q": "What is 2+2?", "opts": ["3", "4", "5", "6"], "ans": 1, "exp": "2+2 = 4"},
        {"q": "What is 5×6?", "opts": ["25", "30", "35", "40"], "ans": 1, "exp": "5×6 = 30"},
        {"q": "What is 10÷2?", "opts": ["3", "4", "5", "6"], "ans": 2, "exp": "10÷2 = 5"},
        {"q": "What is 7²?", "opts": ["49", "50", "48", "51"], "ans": 0, "exp": "7² = 49"},
        {"q": "What is 3³?", "opts": ["27", "28", "26", "25"], "ans": 0, "exp": "3³ = 27"},
    ],
    "Physics": [
        {"q": "Speed of light?", "opts": ["3×10⁸", "2×10⁸", "4×10⁸", "1×10⁸"], "ans": 0, "exp": "c = 3×10⁸ m/s"},
        {"q": "Newton's 2nd law?", "opts": ["F=ma", "F=mv", "F=m+a", "F=m/a"], "ans": 0, "exp": "F = ma"},
        {"q": "Gravity acceleration?", "opts": ["9.8", "10", "8", "12"], "ans": 0, "exp": "g = 9.8 m/s²"},
        {"q": "Sound speed in air?", "opts": ["330", "340", "320", "350"], "ans": 1, "exp": "≈ 340 m/s"},
        {"q": "1 Newton is?", "opts": ["kg·m/s²", "kg·m/s", "kg/m·s²", "kg·s²"], "ans": 0, "exp": "1 N = 1 kg·m/s²"},
    ],
    "Chemistry": [
        {"q": "H₂O is?", "opts": ["Salt", "Water", "Acid", "Base"], "ans": 1, "exp": "H₂O = water"},
        {"q": "Carbon atomic number?", "opts": ["4", "5", "6", "7"], "ans": 2, "exp": "C = 6"},
        {"q": "pH 7 is?", "opts": ["Acidic", "Neutral", "Basic", "Strong"], "ans": 1, "exp": "pH 7 = neutral"},
        {"q": "NaCl is?", "opts": ["Acid", "Salt", "Base", "Gas"], "ans": 1, "exp": "Salt"},
        {"q": "Oxidation is?", "opts": ["Loss of O", "Gain of O", "Loss of e⁻", "Gain of e⁻"], "ans": 2, "exp": "Loss of electrons"},
    ],
    "History": [
        {"q": "WW2 ended?", "opts": ["1943", "1944", "1945", "1946"], "ans": 2, "exp": "1945"},
        {"q": "First US President?", "opts": ["Jefferson", "Washington", "Adams", "Madison"], "ans": 1, "exp": "Washington"},
        {"q": "India independence?", "opts": ["1945", "1946", "1947", "1948"], "ans": 2, "exp": "1947"},
        {"q": "Declaration author?", "opts": ["Franklin", "Washington", "Jefferson", "Adams"], "ans": 2, "exp": "Jefferson"},
        {"q": "Great Wall built by?", "opts": ["Ming", "Han", "Qin", "Zhou"], "ans": 0, "exp": "Ming Dynasty"},
    ],
    "GK": [
        {"q": "France capital?", "opts": ["Lyon", "Paris", "Marseille", "Nice"], "ans": 1, "exp": "Paris"},
        {"q": "Largest continent?", "opts": ["Africa", "Europe", "Asia", "N.America"], "ans": 2, "exp": "Asia"},
        {"q": "Japan currency?", "opts": ["Won", "Yuan", "Yen", "Bath"], "ans": 2, "exp": "Yen"},
        {"q": "Deepest ocean?", "opts": ["Atlantic", "Indian", "Arctic", "Pacific"], "ans": 3, "exp": "Pacific"},
        {"q": "Everest height?", "opts": ["8500m", "8848m", "8700m", "8900m"], "ans": 1, "exp": "8848m"},
    ],
    "English": [
        {"q": "Opposite of Happy?", "opts": ["Joyful", "Sad", "Excited", "Calm"], "ans": 1, "exp": "Sad"},
        {"q": "Plural of Child?", "opts": ["Childs", "Children", "Childes", "Childer"], "ans": 1, "exp": "Children"},
        {"q": "Which is adjective?", "opts": ["Run", "Beautiful", "Quickly", "Eat"], "ans": 1, "exp": "Beautiful"},
        {"q": "'Their' is a?", "opts": ["Verb", "Noun", "Pronoun", "Adjective"], "ans": 2, "exp": "Pronoun"},
        {"q": "Antonym of Start?", "opts": ["Begin", "Commence", "End", "Go"], "ans": 2, "exp": "End"},
    ],
}

# User stats (in memory - simple!)
user_stats = {}

def get_user_stats(user_id):
    if user_id not in user_stats:
        user_stats[user_id] = {
            "rating": 0.0,
            "correct": 0,
            "wrong": 0,
            "questions": 0,
            "streak": 0,
            "best_streak": 0
        }
    return user_stats[user_id]

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    stats = get_user_stats(message.from_user.id)
    
    text = (
        f"🧠 <b>CodeQuest</b>\n\n"
        f"Rating: {stats['rating']:.1f}\n"
        f"Questions: {stats['questions']}\n"
        f"✅ {stats['correct']} | ❌ {stats['wrong']}\n"
        f"🔥 {stats['streak']}\n\n"
        f"<b>Select Subject:</b>"
    )
    
    builder = InlineKeyboardBuilder()
    for subj in SUBJECTS:
        builder.button(text=subj, callback_data=f"q_{subj}")
    builder.adjust(2)
    
    await message.answer(text, reply_markup=builder.as_markup())
    await state.set_state(QuizState.selecting_subject)

@dp.callback_query(F.data.startswith("q_"))
async def show_question(query: types.CallbackQuery, state: FSMContext):
    subject = query.data.replace("q_", "")
    
    qdata = random.choice(QUESTIONS_DB[subject])
    
    text = f"<b>{subject}</b>\n\n{qdata['q']}\n\n"
    
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(qdata["opts"]):
        builder.button(text=f"{'ABCD'[i]}: {opt}", callback_data=f"a_{subject}_{i}_{qdata['ans']}")
    builder.adjust(1)
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(QuizState.answering_question)

@dp.callback_query(F.data.startswith("a_"))
async def show_answer(query: types.CallbackQuery, state: FSMContext):
    parts = query.data.replace("a_", "").split("_")
    subject = parts[0]
    user_ans = int(parts[1])
    correct_ans = int(parts[2])
    
    stats = get_user_stats(query.from_user.id)
    
    is_correct = (user_ans == correct_ans)
    
    if is_correct:
        stats['rating'] += 1.0
        stats['correct'] += 1
        stats['streak'] += 1
        if stats['streak'] > stats['best_streak']:
            stats['best_streak'] = stats['streak']
        emoji = "✅ CORRECT!"
    else:
        stats['rating'] = max(0, stats['rating'] - 0.5)
        stats['wrong'] += 1
        stats['streak'] = 0
        emoji = "❌ WRONG!"
    
    stats['questions'] += 1
    
    # Get correct answer
    qdata = random.choice(QUESTIONS_DB[subject])
    correct_text = qdata["opts"][correct_ans]
    exp = qdata["exp"]
    
    text = (
        f"{emoji}\n\n"
        f"Correct: {correct_text}\n\n"
        f"<b>{exp}</b>\n\n"
        f"Rating: {stats['rating']:.1f}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Next", callback_data="home")
    builder.button(text="📊 Stats", callback_data="stats")
    builder.adjust(2)
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "home")
async def go_home(query: types.CallbackQuery, state: FSMContext):
    stats = get_user_stats(query.from_user.id)
    
    text = (
        f"🧠 Rating: {stats['rating']:.1f}\n"
        f"Questions: {stats['questions']}\n"
        f"Streak: {stats['streak']}\n\n"
        f"<b>Pick Subject:</b>"
    )
    
    builder = InlineKeyboardBuilder()
    for subj in SUBJECTS:
        builder.button(text=subj, callback_data=f"q_{subj}")
    builder.adjust(2)
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(QuizState.selecting_subject)

@dp.callback_query(F.data == "stats")
async def show_stats(query: types.CallbackQuery):
    stats = get_user_stats(query.from_user.id)
    
    text = (
        f"📊 <b>Your Stats</b>\n\n"
        f"Rating: {stats['rating']:.1f}\n"
        f"Total: {stats['questions']}\n"
        f"✅ {stats['correct']}\n"
        f"❌ {stats['wrong']}\n"
        f"🔥 Current: {stats['streak']}\n"
        f"🏆 Best: {stats['best_streak']}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Home", callback_data="home")
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())

async def main():
    logger.info("🚀 Starting...")
    logger.info("✅ Ready!")
    logger.info("🤖 Bot running!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
