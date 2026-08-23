"""
Knowledge Enhancer Bot - ULTRA SIMPLE WORKING VERSION
Uses hardcoded questions (no API calls = no errors)
"""

import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import init_db, get_session_maker, User, Question, Transaction

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FSM States
class QuizState(StatesGroup):
    selecting_subject = State()
    answering_question = State()

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Global session maker
AsyncSessionLocal = None

# Subjects
SUBJECTS = ["Math", "Physics", "Chemistry", "History", "GK", "English"]

# HARDCODED QUESTIONS (No API needed!)
QUESTIONS_DB = {
    "Math": [
        {"q": "What is 2+2?", "opts": ["3", "4", "5", "6"], "ans": 1, "exp": "2+2 = 4"},
        {"q": "What is 5×6?", "opts": ["25", "30", "35", "40"], "ans": 1, "exp": "5×6 = 30"},
        {"q": "What is 10÷2?", "opts": ["3", "4", "5", "6"], "ans": 2, "exp": "10÷2 = 5"},
        {"q": "What is 7²?", "opts": ["49", "50", "48", "51"], "ans": 0, "exp": "7² = 49"},
        {"q": "What is 3³?", "opts": ["27", "28", "26", "25"], "ans": 0, "exp": "3³ = 27"},
    ],
    "Physics": [
        {"q": "What is the speed of light?", "opts": ["3×10⁸ m/s", "2×10⁸ m/s", "4×10⁸ m/s", "1×10⁸ m/s"], "ans": 0, "exp": "Speed of light = 3×10⁸ m/s"},
        {"q": "Newton's 2nd law is?", "opts": ["F=ma", "F=mv", "F=m+a", "F=m/a"], "ans": 0, "exp": "F = ma (Force = mass × acceleration)"},
        {"q": "What is Gravity acceleration?", "opts": ["9.8 m/s²", "10 m/s²", "8 m/s²", "12 m/s²"], "ans": 0, "exp": "g = 9.8 m/s²"},
        {"q": "Sound speed in air?", "opts": ["330 m/s", "340 m/s", "320 m/s", "350 m/s"], "ans": 1, "exp": "Sound ≈ 340 m/s"},
        {"q": "What is 1 Newton?", "opts": ["kg·m/s²", "kg·m/s", "kg/m·s²", "kg·s²"], "ans": 0, "exp": "1 N = 1 kg·m/s²"},
    ],
    "Chemistry": [
        {"q": "What is H₂O?", "opts": ["Salt", "Water", "Acid", "Base"], "ans": 1, "exp": "H₂O is water"},
        {"q": "Atomic number of Carbon?", "opts": ["4", "5", "6", "7"], "ans": 2, "exp": "Carbon = 6"},
        {"q": "What is pH 7?", "opts": ["Acidic", "Neutral", "Basic", "Strong"], "ans": 1, "exp": "pH 7 is neutral"},
        {"q": "NaCl is?", "opts": ["Acid", "Salt", "Base", "Gas"], "ans": 1, "exp": "NaCl = sodium chloride (salt)"},
        {"q": "What is Oxidation?", "opts": ["Loss of O", "Gain of O", "Loss of e⁻", "Gain of e⁻"], "ans": 2, "exp": "Oxidation = loss of electrons"},
    ],
    "History": [
        {"q": "When did WW2 end?", "opts": ["1943", "1944", "1945", "1946"], "ans": 2, "exp": "WW2 ended in 1945"},
        {"q": "Who was first US President?", "opts": ["Jefferson", "Washington", "Adams", "Madison"], "ans": 1, "exp": "George Washington"},
        {"q": "When was India independent?", "opts": ["1945", "1946", "1947", "1948"], "ans": 2, "exp": "India got independence in 1947"},
        {"q": "Who wrote Declaration?", "opts": ["Franklin", "Washington", "Jefferson", "Adams"], "ans": 2, "exp": "Thomas Jefferson wrote it"},
        {"q": "Great Wall of China built by?", "opts": ["Ming Dynasty", "Han Dynasty", "Qin Dynasty", "Zhou Dynasty"], "ans": 0, "exp": "Ming Dynasty built most of it"},
    ],
    "GK": [
        {"q": "Capital of France?", "opts": ["Lyon", "Paris", "Marseille", "Nice"], "ans": 1, "exp": "Paris is capital of France"},
        {"q": "Largest continent?", "opts": ["Africa", "Europe", "Asia", "N. America"], "ans": 2, "exp": "Asia is largest"},
        {"q": "Currency of Japan?", "opts": ["Won", "Yuan", "Yen", "Bath"], "ans": 2, "exp": "Yen is Japanese currency"},
        {"q": "Deepest ocean?", "opts": ["Atlantic", "Indian", "Arctic", "Pacific"], "ans": 3, "exp": "Pacific Ocean is deepest"},
        {"q": "Mount Everest height?", "opts": ["8500m", "8848m", "8700m", "8900m"], "ans": 1, "exp": "Mount Everest = 8848m"},
    ],
    "English": [
        {"q": "Opposite of 'Happy'?", "opts": ["Joyful", "Sad", "Excited", "Calm"], "ans": 1, "exp": "Opposite of happy is sad"},
        {"q": "Plural of 'Child'?", "opts": ["Childs", "Children", "Childes", "Childer"], "ans": 1, "exp": "Plural = children"},
        {"q": "Which is adjective?", "opts": ["Run", "Beautiful", "Quickly", "Eat"], "ans": 1, "exp": "Beautiful describes a noun"},
        {"q": "'Their' is a?", "opts": ["Verb", "Noun", "Pronoun", "Adjective"], "ans": 2, "exp": "Their is a possessive pronoun"},
        {"q": "Antonym of 'Start'?", "opts": ["Begin", "Commence", "End", "Go"], "ans": 2, "exp": "Antonym of start is end"},
    ],
}

# Premium packages
PREMIUM_PACKAGES = {
    "weekly": {"stars": 10, "days": 7, "name": "Weekly"},
    "monthly": {"stars": 20, "days": 30, "name": "Monthly"},
    "yearly": {"stars": 100, "days": 365, "name": "Yearly"},
}


async def on_startup():
    """Initialize database"""
    global AsyncSessionLocal
    logger.info("🚀 Bot starting...")
    engine = await init_db()
    AsyncSessionLocal = get_session_maker(engine)
    logger.info("✅ Ready!")


async def get_or_create_user(user_id: int, username: str = None, first_name: str = None):
    """Get or create user"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        
        if not user:
            user = User(user_id=user_id, username=username, first_name=first_name)
            session.add(user)
            await session.commit()
        
        # Reset daily questions
        now = datetime.utcnow()
        if (now - user.last_daily_reset).days >= 1:
            user.free_questions_today = 5
            user.last_daily_reset = now
            await session.commit()
        
        # Check premium expiry
        if user.is_premium and user.premium_expires_at and now > user.premium_expires_at:
            user.is_premium = False
            await session.commit()
        
        return user


# ==================== HANDLERS ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Start command"""
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    text = (
        f"🧠 <b>Knowledge Enhancer</b>\n\n"
        f"Rating: {user.current_rating:.1f}\n"
        f"Questions: {user.total_questions}\n"
        f"Free Today: {user.free_questions_today}/5\n\n"
        f"<b>Select Subject:</b>"
    )
    
    builder = InlineKeyboardBuilder()
    for subj in SUBJECTS:
        builder.button(text=subj, callback_data=f"subj_{subj}")
    builder.button(text="💎 Premium", callback_data="prem")
    builder.adjust(2)
    
    await message.answer(text, reply_markup=builder.as_markup())
    await state.set_state(QuizState.selecting_subject)


@dp.callback_query(F.data.startswith("subj_"))
async def select_subject(query: types.CallbackQuery, state: FSMContext):
    """Subject selected"""
    subject = query.data.replace("subj_", "")
    user = await get_or_create_user(query.from_user.id)
    
    # Check daily limit
    if not user.is_premium and user.free_questions_today <= 0:
        await query.answer("❌ Daily limit reached!", show_alert=True)
        return
    
    # Deduct question
    if not user.is_premium:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.user_id == query.from_user.id))
            u = result.scalars().first()
            u.free_questions_today -= 1
            await session.commit()
    
    # Get random question
    import random
    q_data = random.choice(QUESTIONS_DB[subject])
    
    # Store in DB
    async with AsyncSessionLocal() as session:
        q = Question(
            user_id=query.from_user.id,
            subject=subject,
            difficulty=int(user.current_rating),
            question_text=q_data["q"],
            options=str(q_data["opts"]),
            correct_index=q_data["ans"],
            explanation=q_data["exp"]
        )
        session.add(q)
        await session.commit()
        q_id = q.id
    
    # Show question
    text = f"<b>{subject}</b>\n\n{q_data['q']}\n\n"
    
    builder = InlineKeyboardBuilder()
    for i, opt in enumerate(q_data["opts"]):
        builder.button(text=f"{'ABCD'[i]}: {opt}", callback_data=f"ans_{q_id}_{i}")
    builder.adjust(1)
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(QuizState.answering_question)


@dp.callback_query(F.data.startswith("ans_"))
async def answer_question(query: types.CallbackQuery):
    """Answer selected"""
    parts = query.data.replace("ans_", "").split("_")
    q_id = int(parts[0])
    ans = int(parts[1])
    
    # Get question
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Question).where(Question.id == q_id))
        q = result.scalars().first()
        
        correct = (ans == q.correct_index)
        q.is_correct = correct
        await session.commit()
    
    # Update rating
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == query.from_user.id))
        user = result.scalars().first()
        
        if correct:
            user.current_rating += 1.0
            user.total_correct += 1
            user.current_streak += 1
        else:
            user.current_rating = max(0, user.current_rating - 0.5)
            user.total_wrong += 1
            user.current_streak = 0
        
        user.total_questions += 1
        await session.commit()
    
    # Show result
    opts = eval(q.options)
    emoji = "✅" if correct else "❌"
    
    text = (
        f"{emoji} <b>{'CORRECT!' if correct else 'WRONG!'}</b>\n\n"
        f"Your: {opts[ans]}\n"
        f"Right: {opts[q.correct_index]}\n\n"
        f"{q.explanation}\n\n"
        f"Rating: {user.current_rating:.1f}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Next", callback_data="home")
    builder.button(text="📊 Stats", callback_data="stats")
    builder.adjust(2)
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())


@dp.callback_query(F.data == "home")
async def go_home(query: types.CallbackQuery, state: FSMContext):
    """Go back home"""
    user = await get_or_create_user(query.from_user.id)
    
    text = f"🧠 Rating: {user.current_rating:.1f} | Free: {user.free_questions_today}/5\n\n<b>Select:</b>"
    
    builder = InlineKeyboardBuilder()
    for subj in SUBJECTS:
        builder.button(text=subj, callback_data=f"subj_{subj}")
    builder.button(text="💎 Premium", callback_data="prem")
    builder.adjust(2)
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())
    await state.set_state(QuizState.selecting_subject)


@dp.callback_query(F.data == "stats")
async def show_stats(query: types.CallbackQuery):
    """Show stats"""
    user = await get_or_create_user(query.from_user.id)
    
    text = (
        f"📊 <b>Stats</b>\n\n"
        f"Rating: {user.current_rating:.1f}\n"
        f"Questions: {user.total_questions}\n"
        f"✅ Correct: {user.total_correct}\n"
        f"❌ Wrong: {user.total_wrong}\n"
        f"🔥 Streak: {user.current_streak}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Home", callback_data="home")
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())


@dp.callback_query(F.data == "prem")
async def premium(query: types.CallbackQuery):
    """Premium options"""
    text = "<b>💎 Go Premium!</b>\n\n"
    
    builder = InlineKeyboardBuilder()
    for pid, pkg in PREMIUM_PACKAGES.items():
        text += f"⭐ {pkg['name']}: {pkg['stars']}⭐\n"
        builder.button(text=f"{pkg['name']} - {pkg['stars']}⭐", callback_data=f"buy_{pid}")
    
    builder.button(text="Back", callback_data="home")
    builder.adjust(1)
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("buy_"))
async def buy_premium(query: types.CallbackQuery):
    """Buy premium"""
    pkg_id = query.data.replace("buy_", "")
    pkg = PREMIUM_PACKAGES[pkg_id]
    
    await bot.send_invoice(
        chat_id=query.from_user.id,
        title=f"Premium {pkg['name']}",
        description=f"{pkg['days']} days unlimited",
        payload=f"prem_{pkg_id}",
        provider_token="",
        currency="XTR",
        prices=[{"label": "Premium", "amount": pkg['stars']}]
    )


@dp.pre_checkout_query()
async def pre_checkout(pre_checkout: types.PreCheckoutQuery):
    """Validate payment"""
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@dp.message(F.successful_payment)
async def payment_done(message: types.Message):
    """Payment successful"""
    pkg_id = message.successful_payment.invoice_payload.replace("prem_", "")
    pkg = PREMIUM_PACKAGES[pkg_id]
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == message.from_user.id))
        user = result.scalars().first()
        user.is_premium = True
        user.premium_type = pkg_id
        user.premium_expires_at = datetime.utcnow() + timedelta(days=pkg['days'])
        await session.commit()
    
    await message.answer(f"✅ Premium activated for {pkg['days']} days!")


# ==================== MAIN ====================

async def main():
    """Start bot"""
    await on_startup()
    logger.info("🤖 Bot running!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
