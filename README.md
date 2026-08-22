# Knowledge Enhancer Bot 🧠

**An adaptive AI-powered learning bot that generates unique questions and tracks user progress with a premium subscription model.**

Built with Python 3.9+, aiogram 3.x, SQLAlchemy (async), Anthropic Claude API, and Telegram Stars payments.

---

## 🎯 Features

✅ **AI-Generated Questions** - 100% original, adaptive difficulty questions  
✅ **Smart Difficulty Scaling** - Questions adapt to user rating (+1 correct, -0.5 wrong)  
✅ **6 Subject Categories** - Math, Physics, Chemistry, History, GK, English  
✅ **Daily Limits** - 5 free questions/day for free users  
✅ **Premium Subscriptions** - Weekly (10⭐), Monthly (20⭐), Yearly (100⭐)  
✅ **Rating System** - Beginner → Easy → Medium → Hard → Expert progression  
✅ **Streak Tracking** - Current and best streak counter  
✅ **Statistics Dashboard** - View detailed performance metrics  
✅ **Telegram Stars Payment** - Native in-app premium purchases  

---

## 📋 Prerequisites

- Python 3.9+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Anthropic API Key (from [console.anthropic.com](https://console.anthropic.com))
- Your Telegram User ID (from [@userinfobot](https://t.me/userinfobot))

---

## ⚡ Quick Setup (Local Development)

### Step 1: Clone and Install

```bash
git clone https://github.com/yourusername/KnowledgeEnhancerBot.git
cd KnowledgeEnhancerBot
pip install -r requirements.txt
```

### Step 2: Create `.env` File

```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnoPQRstuvWxyz
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=sqlite+aiosqlite:///./knowledgebot.db
```

### Step 3: Run the Bot

```bash
python bot.py
```

You should see:
```
✅ Database initialized and ready
🤖 Knowledge Enhancer Bot is running...
```

### Step 4: Test

1. Search your bot on Telegram
2. Send `/start`
3. Select a subject (Math, Physics, etc.)
4. Answer questions!

---

## 🚀 Production Deployment (Railway)

### Step 1: Connect GitHub to Railway

1. Push code to GitHub
2. Go to [railway.app](https://railway.app)
3. Create new project → GitHub
4. Select your repository
5. Connect and deploy

### Step 2: Set Environment Variables

In Railway dashboard:
1. Click "Variables"
2. Add:
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `ANTHROPIC_API_KEY` = your API key
   - `DATABASE_URL` = PostgreSQL connection string (Railway auto-provides)

### Step 3: Deploy

Click "Deploy" - bot runs 24/7! ✅

---

## 💡 How It Works

### Question Generation

Instead of storing static questions, the bot **generates original questions on-the-fly** using Claude:

1. User selects subject + gets assigned difficulty based on rating
2. Bot calls Claude API with:
   - Subject
   - Difficulty level
   - Recent topics to avoid
3. Claude generates:
   - Original question
   - 4 options (1 correct + 3 misconceptions)
   - Explanation
4. User answers
5. Rating updated (+1 or -0.5)
6. Next question difficulty auto-adjusts

### Rating & Difficulty Progression

```
Rating 0-10      → Difficulty 0-10 (Beginner)
Rating 11-20     → Difficulty 11-20 (Easy)
Rating 21-35     → Difficulty 21-35 (Medium)
Rating 36-50     → Difficulty 36-50 (Hard)
Rating 51+       → Difficulty 51+ (Expert)
```

### Daily Limits

**Free Users:**
- 5 questions/day
- Reset at UTC midnight
- Can't exceed unless premium

**Premium Users:**
- Unlimited questions
- No daily limits
- Full week/month/year access

### Scoring System

- **Correct Answer:** +1.0 rating
- **Wrong Answer:** -0.5 rating
- **Streak:** Increases on correct, resets on wrong
- **Minimum Rating:** 0 (can't go below)

### Premium Pricing (Telegram Stars)

| Package | Stars | Duration | Price USD |
|---------|-------|----------|-----------|
| Weekly | 10⭐ | 7 days | ~$0.99 |
| Monthly | 20⭐ | 30 days | ~$1.99 |
| Yearly | 100⭐ | 365 days | ~$9.99 |

---

## 📊 Revenue Potential

**Estimated Monthly Revenue:**
- 100 active users (20% convert to premium) = ₹1000-3000/month
- 500 active users = ₹5000-15000/month
- 1000 active users = ₹10000-30000/month
- 10000 active users = ₹100K-300K/month

---

## 🗄️ Database Schema

### Users Table
```
user_id (PK)           → Telegram ID
username               → Username
first_name             → First name
current_rating         → User's rating (float)
total_correct          → Correct answers
total_wrong            → Wrong answers
free_questions_today   → Remaining free Q/day (0-5)
is_premium             → Premium status
premium_type           → "weekly", "monthly", "yearly"
premium_expires_at     → Expiration timestamp
current_streak         → Current correct streak
best_streak            → Best streak ever
```

### User Progress Table
```
user_id (FK)           → User ID
subject                → Subject name
difficulty             → Difficulty rating
correct_count          → Correct answers on this combo
wrong_count            → Wrong answers on this combo
```

### Questions Table
```
user_id (FK)           → Who answered
subject                → Subject name
difficulty             → Difficulty rating
question_text          → Full question
options                → JSON with 4 options
correct_index          → Index of correct option (0-3)
explanation            → Why answer is correct
is_correct             → User's correctness
```

### Transactions Table
```
user_id (FK)           → Who paid
amount_paid            → Stars spent
credits_added          → Days of premium
payment_status         → "pending", "completed", "failed"
telegram_payment_id    → Telegram payment identifier
```

---

## 🔧 Customization

### Change Daily Limit

In `bot.py`, `get_or_create_user()`:
```python
user.free_questions_today = 10  # Change from 5 to 10
```

### Add More Subjects

In `bot.py`, update `SUBJECTS`:
```python
SUBJECTS = ["Math", "Physics", "Chemistry", "History", "GK", "English", "Biology", "Economics"]
```

### Modify Premium Pricing

In `bot.py`, `PREMIUM_PACKAGES`:
```python
PREMIUM_PACKAGES = {
    "weekly": {"stars": 15, "days": 7, "name": "Weekly Pass"},  # Changed from 10
    # ...
}
```

### Adjust Scoring

In `bot.py`, `update_user_rating()`:
```python
user.current_rating += 1.5  # Change from 1.0
user.current_rating = max(0, user.current_rating - 0.75)  # Change from 0.5
```

---

## 📝 Commands

| Command | Description |
|---------|-------------|
| `/start` | Begin quiz, select subject |
| `/help` | Show help guide |
| `/stats` | View personal statistics |

---

## 🎯 User Flow

```
/start
  ↓
Select Subject (Math, Physics, Chemistry, History, GK, English)
  ↓
Generate Question (AI-powered, based on difficulty)
  ↓
Display Question + 4 Options
  ↓
User Selects Answer
  ↓
Show Result (✅ Correct / ❌ Wrong)
  ↓
Update Rating (+1 or -0.5)
  ↓
Next Question (with adjusted difficulty)
  ↓
(5 questions free) → Show "Buy Premium" prompt
  ↓
Premium Users: Unlimited | Free Users: Wait until tomorrow
```

---

## 🚨 Troubleshooting

### Bot doesn't respond

- Check token in `.env` is correct
- Verify bot is running: `Database initialized and ready`
- Check BotFather permissions

### Questions not generating

- Verify `ANTHROPIC_API_KEY` in `.env`
- Check API key has credits
- Review logs for error messages

### Payment not working

- Ensure Telegram Stars available in your region
- Check `telegram_payment_id` in transactions table
- Verify premium expiration logic

### Database errors

- SQLite: `rm knowledgebot.db` to reset
- PostgreSQL: Verify connection string and credentials

---

## 📈 Monetization Strategy

1. **Premium Subscriptions** - Main revenue (Telegram Stars)
2. **Sponsored Questions** - Brands pay to appear in specific subjects
3. **API Access** - Developers pay for question generation API
4. **Advanced Analytics** - Premium stats dashboard

---

## 🤝 Contributing

Contributions welcome! To add features:

1. Fork the repo
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit: `git commit -am 'Add feature'`
4. Push: `git push origin feature/new-feature`
5. Submit pull request

---

## 📜 License

MIT License - see LICENSE file

---

## 💬 Support

- **Issues**: GitHub Issues
- **Email**: support@knowledgebot.com

---

## 🎯 Roadmap

- [ ] Mobile app (iOS/Android)
- [ ] Leaderboards
- [ ] Group competitions
- [ ] Audio questions
- [ ] Video explanations
- [ ] Offline mode
- [ ] Custom question sets
- [ ] Teacher dashboard
- [ ] School integrations

---

**Built with ❤️ by Asad**

Happy Learning! 🚀
