"""
Knowledge Enhancer Bot - SIMPLIFIED WORKING VERSION
Complete implementation with adaptive difficulty and premium system
"""

import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import init_db, get_session_maker, User, UserProgress, Question, Transaction
from gemini_question_generator import generate_question

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

# Subjects available
SUBJECTS = ["Math", "Physics", "Chemistry", "History", "GK", "English"]

# Premium packages (in Telegram Stars)
PREMIUM_PACKAGES = {
    "weekly": {"stars": 10, "days": 7, "name": "Weekly Pass"},
    "monthly": {"stars": 20, "days": 30, "name": "Monthly Pass"},
    "yearly": {"stars": 100, "days": 365, "name": "Yearly Pass"},
}


async def on_startup():
    """Initialize database on bot startup"""
    global AsyncSessionLocal
    logger.info("🚀 Knowledge Enhancer Bot starting up...")
    engine = await init_db()
    AsyncSessionLocal = get_session_maker(engine)
    logger.info("✅ Database initialized and ready")


async def get_or_create_user(user_id: int, username: str = None, first_name: str = None) -> User:
    """Get or create user"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        
        if not user:
            user = User(user_id=user_id, username=username, first_name=first_name)
            session.add(user)
            await session.commit()
            logger.info(f"✨ New user created: {user_id}")
        
        # Reset daily free questions if needed
        now = datetime.utcnow()
        if (now - user.last_daily_reset).days >= 1:
            user.free_questions_today = 5
            user.last_daily_reset = now
            user.questions_today = 0
            await session.commit()
        
        # Check if premium expired
        if user.is_premium and user.premium_expires_at and now > user.premium_expires_at:
            user.is_premium = False
            user.premium_type = None
            user.premium_expires_at = None
            await session.commit()
        
        return user


async def check_can_attempt_question(user_id: int) -> tuple[bool, str]:
    """Check if user can attempt a question"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        
        if user.is_premium:
            return True, ""
        
        if user.free_questions_today > 0:
            return True, ""
        else:
            next_reset = (user.last_daily_reset + timedelta(days=1)).strftime("%H:%M UTC")
            return False, f"❌ Daily limit reached (5/day)\n\nNext questions available at {next_reset}\n\n💎 Or upgrade to Premium!"


async def deduct_question_limit(user_id: int):
    """Deduct one free question"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        
        if not user.is_premium and user.free_questions_today > 0:
            user.free_questions_today -= 1
            user.questions_today += 1
            await session.commit()


async def update_user_rating(user_id: int, is_correct: bool, subject: str, difficulty: int):
    """Update user rating: +1 for correct, -0.5 for incorrect"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        
        if is_correct:
            user.current_rating += 1.0
            user.total_correct += 1
            user.current_streak += 1
            if user.current_streak > user.best_streak:
                user.best_streak = user.current_streak
        else:
            user.current_rating = max(0, user.current_rating - 0.5)
            user.total_wrong += 1
            user.current_streak = 0
        
        user.total_questions += 1
        await session.commit()


# ==================== COMMAND HANDLERS ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Handle /start command"""
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    welcome_text = (
        f"🧠 <b>Welcome to Knowledge Enhancer Bot!</b>\n\n"
        f"Hi {message.from_user.first_name}! 👋\n\n"
        f"<b>📊 Your Stats:</b>\n"
        f"• Rating: <b>{user.current_rating:.1f}</b>\n"
        f"• Correct: <b>{user.total_correct}</b> | Wrong: <b>{user.total_wrong}</b>\n"
        f"• Streak: <b>{user.current_streak}</b>\n"
        f"• Free Questions: <b>{user.free_questions_today}/5</b>\n\n"
        f"<b>📚 Choose a Subject:</b>"
    )
    
    builder = InlineKeyboardBuilder()
    for subject in SUBJECTS:
        builder.button(text=subject, callback_data=f"subject_{subject}")
    
    builder.button(text="💎 Premium", callback_data="premium")
    builder.button(text="📊 Stats", callback_data="stats")
    builder.adjust(2)
    
    await message.answer(welcome_text, reply_markup=builder.as_markup())
    await state.set_state(QuizState.selecting_subject)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Help command"""
    help_text = (
        "<b>🎯 Knowledge Enhancer Bot</b>\n\n"
        "<b>📝 How It Works:</b>\n"
        "• 5 free questions per day\n"
        "• +1 for correct, -0.5 for wrong\n"
        "• Difficulty adapts to your rating\n\n"
        "<b>💎 Premium (Telegram Stars):</b>\n"
        "• Weekly: 10⭐ (7 days unlimited)\n"
        "• Monthly: 20⭐ (30 days unlimited)\n"
        "• Yearly: 100⭐ (365 days unlimited)\n\n"
        "/start - Begin\n"
        "/stats - Your stats\n"
        "/help - This message"
    )
    await message.answer(help_text)


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Show statistics"""
    user = await get_or_create_user(message.from_user.id)
    
    premium_info = ""
    if user.is_premium:
        days_left = (user.premium_expires_at - datetime.utcnow()).days
        premium_info = f"\n🌟 Premium: {user.premium_type.upper()} ({days_left} days left)"
    
    stats_text = (
        f"<b>📊 Your Statistics</b>\n\n"
        f"⏰ Member Since: {user.created_at.strftime('%d-%m-%Y')}\n\n"
        f"<b>🎯 Rating:</b> {user.current_rating:.1f}\n"
        f"<b>Questions:</b> {user.total_questions}\n"
        f"<b>Correct:</b> {user.total_correct} ({user.total_correct*100//max(1,user.total_questions)}%)\n"
        f"<b>Wrong:</b> {user.total_wrong}\n\n"
        f"<b>🔥 Streaks:</b>\n"
        f"Current: {user.current_streak} | Best: {user.best_streak}\n\n"
        f"<b>📝 Daily:</b> {user.free_questions_today}/5 free left"
        f"{premium_info}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Back", callback_data="back_home")
    
    await message.answer(stats_text, reply_markup=builder.as_markup())


# ==================== CALLBACK HANDLERS ====================

@dp.callback_query(F.data == "back_home")
async def callback_back_home(query: types.CallbackQuery, state: FSMContext):
    """Go back to home"""
    user = await get_or_create_user(query.from_user.id)
    
    welcome_text = (
        f"🧠 <b>Knowledge Enhancer Bot</b>\n\n"
        f"Rating: <b>{user.current_rating:.1f}</b> | "
        f"Streak: <b>{user.current_streak}</b> | "
        f"Free: <b>{user.free_questions_today}/5</b>\n\n"
        f"<b>Select Subject:</b>"
    )
    
    builder = InlineKeyboardBuilder()
    for subject in SUBJECTS:
        builder.button(text=subject, callback_data=f"subject_{subject}")
    
    builder.button(text="💎 Premium", callback_data="premium")
    builder.button(text="📊 Stats", callback_data="stats")
    builder.adjust(2)
    
    await query.message.edit_text(welcome_text, reply_markup=builder.as_markup())
    await state.set_state(QuizState.selecting_subject)
    await query.answer()


@dp.callback_query(F.data.startswith("subject_"))
async def callback_select_subject(query: types.CallbackQuery, state: FSMContext):
    """Handle subject selection"""
    subject = query.data.replace("subject_", "")
    
    can_attempt, message_text = await check_can_attempt_question(query.from_user.id)
    if not can_attempt:
        await query.answer(message_text, show_alert=True)
        return
    
    await deduct_question_limit(query.from_user.id)
    
    user = await get_or_create_user(query.from_user.id)
    difficulty = int(user.current_rating * 5)
    
    await query.message.edit_text(f"⏳ Generating {subject} question...", reply_markup=None)
    
    question_data = await generate_question(subject, difficulty)
    
    if not question_data:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Back", callback_data="back_home")
        await query.message.edit_text("❌ Failed to generate question. Try again.", reply_markup=builder.as_markup())
        return
    
    # Store question
    async with AsyncSessionLocal() as session:
        question = Question(
            user_id=query.from_user.id,
            subject=subject,
            difficulty=difficulty,
            question_text=question_data["question"],
            options=str(question_data["options"]),
            correct_index=question_data["correct_index"],
            explanation=question_data["explanation"]
        )
        session.add(question)
        await session.commit()
        question_id = question.id
    
    # Display question
    question_text = f"<b>{subject}</b> (Difficulty: {difficulty})\n\n{question_data['question']}\n\n"
    
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(question_data["options"]):
        builder.button(text=f"{'ABCD'[i]}: {option}", callback_data=f"answer_{question_id}_{i}")
    builder.adjust(1)
    
    await query.message.edit_text(question_text, reply_markup=builder.as_markup())
    await state.set_state(QuizState.answering_question)


@dp.callback_query(F.data.startswith("answer_"))
async def callback_answer_question(query: types.CallbackQuery):
    """Handle answer selection"""
    parts = query.data.replace("answer_", "").split("_")
    question_id = int(parts[0])
    user_answer = int(parts[1])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Question).where(Question.id == question_id))
        question = result.scalars().first()
        
        is_correct = user_answer == question.correct_index
        question.is_correct = is_correct
        await session.commit()
    
    await update_user_rating(query.from_user.id, is_correct, question.subject, question.difficulty)
    
    result_emoji = "✅" if is_correct else "❌"
    result_text = "CORRECT!" if is_correct else "WRONG!"
    
    user = await get_or_create_user(query.from_user.id)
    options_list = eval(question.options)
    
    feedback = (
        f"{result_emoji} <b>{result_text}</b>\n\n"
        f"Your Answer: {options_list[user_answer]}\n"
        f"Correct: {options_list[question.correct_index]}\n\n"
        f"<b>Explanation:</b>\n{question.explanation}\n\n"
        f"Rating: {'+1.0' if is_correct else '-0.5'} → {user.current_rating:.1f}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Next", callback_data="back_home")
    builder.button(text="📊 Stats", callback_data="stats")
    builder.adjust(2)
    
    await query.message.edit_text(feedback, reply_markup=builder.as_markup())
    await query.answer()


@dp.callback_query(F.data == "premium")
async def callback_premium(query: types.CallbackQuery):
    """Show premium packages"""
    premium_text = "<b>💎 Get Premium - Unlimited Questions!</b>\n\n🌟 Telegram Stars:\n\n"
    
    for pkg_id, pkg_info in PREMIUM_PACKAGES.items():
        premium_text += f"⭐ <b>{pkg_info['name']}</b>\n   {pkg_info['stars']} stars • {pkg_info['days']} days\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for pkg_id, pkg_info in PREMIUM_PACKAGES.items():
        builder.button(
            text=f"{pkg_info['name']} - {pkg_info['stars']}⭐",
            callback_data=f"buy_{pkg_id}"
        )
    
    builder.button(text="⬅️ Back", callback_data="back_home")
    builder.adjust(1)
    
    await query.message.edit_text(premium_text, reply_markup=builder.as_markup())
    await query.answer()


@dp.callback_query(F.data.startswith("buy_"))
async def callback_buy_premium(query: types.CallbackQuery):
    """Send invoice for premium purchase"""
    pkg_id = query.data.replace("buy_", "")
    
    if pkg_id not in PREMIUM_PACKAGES:
        await query.answer("Invalid package")
        return
    
    pkg = PREMIUM_PACKAGES[pkg_id]
    
    await bot.send_invoice(
        chat_id=query.from_user.id,
        title=f"{pkg['name']}",
        description=f"Unlimited questions for {pkg['days']} days",
        payload=f"premium_{pkg_id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Premium Access", amount=pkg['stars'])]
    )
    
    await query.answer()


@dp.callback_query(F.data == "stats")
async def callback_stats(query: types.CallbackQuery):
    """Show stats"""
    user = await get_or_create_user(query.from_user.id)
    
    premium_info = ""
    if user.is_premium:
        days_left = (user.premium_expires_at - datetime.utcnow()).days
        premium_info = f"\n🌟 {user.premium_type.upper()} ({days_left} days)"
    
    stats_text = (
        f"<b>📊 Stats</b>\n\n"
        f"Rating: {user.current_rating:.1f}\n"
        f"Questions: {user.total_questions}\n"
        f"Correct: {user.total_correct} | Wrong: {user.total_wrong}\n"
        f"Streak: {user.current_streak} (Best: {user.best_streak})\n"
        f"Free Today: {user.free_questions_today}/5"
        f"{premium_info}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Home", callback_data="back_home")
    
    await query.message.edit_text(stats_text, reply_markup=builder.as_markup())
    await query.answer()


@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout: types.PreCheckoutQuery):
    """Validate payment"""
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    """Handle successful premium purchase"""
    payment = message.successful_payment
    pkg_id = payment.invoice_payload.replace("premium_", "")
    
    if pkg_id not in PREMIUM_PACKAGES:
        await message.answer("❌ Error processing payment")
        return
    
    pkg = PREMIUM_PACKAGES[pkg_id]
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == message.from_user.id))
        user = result.scalars().first()
        
        if user:
            user.is_premium = True
            user.premium_type = pkg_id
            user.premium_expires_at = datetime.utcnow() + timedelta(days=pkg["days"])
            
            transaction = Transaction(
                user_id=user.user_id,
                amount_paid=pkg["stars"],
                credits_added=pkg["days"],
                payment_method="telegram_stars",
                payment_status="completed",
                telegram_payment_id=payment.telegram_payment_charge_id
            )
            session.add(transaction)
            await session.commit()
    
    await message.answer(
        f"✅ <b>Premium Activated!</b>\n\n"
        f"🌟 {pkg['name']}\n"
        f"⏰ Valid for {pkg['days']} days\n"
        f"📝 Unlimited questions unlocked!\n\n"
        f"Ready? /start"
    )


# ==================== MAIN ====================

async def main():
    """Start the bot"""
    await on_startup()
    logger.info("🤖 Knowledge Enhancer Bot is running...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
