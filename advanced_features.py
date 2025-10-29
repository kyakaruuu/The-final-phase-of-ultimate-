"""
Advanced Features Integration for Ultimate Chemistry Bot
Adds analytics, achievements, leaderboards, practice generation, and more
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import SessionLocal, User
from analytics_engine import AnalyticsEngine
from content_generator import ContentGenerator
from multi_agent import MultiAgentDebateSystem
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize modules (will be set up when bot starts)
analytics = None
content_gen = None

def init_advanced_features(api_keys):
    """Initialize advanced features with API keys"""
    global analytics, content_gen
    analytics = AnalyticsEngine()
    content_gen = ContentGenerator(api_keys)

def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None) -> User:
    """Get existing user or create new one in database"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"✓ Created new user: {telegram_id} ({username})")
        else:
            # Update last active
            user.last_active = datetime.utcnow()
            db.commit()
        
        return user
    except Exception as e:
        logger.error(f"Error getting/creating user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user performance dashboard"""
    global analytics
    
    if not analytics:
        analytics = AnalyticsEngine()
    
    user = update.effective_user
    
    # Get or create user in database
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    if not db_user:
        await update.message.reply_text("❌ Unable to load your dashboard. Please try again later.")
        return
    
    try:
        # Get stats from analytics
        stats = analytics.get_user_stats(db_user.telegram_id) if analytics else {}
        
        message = f"""
📊 *YOUR PERFORMANCE DASHBOARD*

👤 *Profile*
• User: {user.first_name or user.username}
• Level: {db_user.level}
• XP: {db_user.experience_points}
• Total Score: {db_user.total_score}

📈 *Problem Solving*
• Total Solved: {db_user.total_problems_solved}
• Correct: {db_user.total_correct}
• Accuracy: {(db_user.total_correct / max(db_user.total_problems_solved, 1) * 100):.1f}%

🔥 *Streaks*
• Current Streak: {db_user.current_streak} days
• Longest Streak: {db_user.longest_streak} days

⚙️ *Settings*
• Difficulty Level: {db_user.difficulty_level}/10
• Career Goal: {db_user.career_goal}
• Spaced Repetition: {'✓ On' if db_user.spaced_repetition_enabled else '✗ Off'}

💡 *Use these commands:*
/weaknesses - See your weak topics
/achievements - View your badges
/leaderboard - See rankings
/practice - Generate practice problems
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        await update.message.reply_text("❌ Error loading dashboard. Please try again later.")

async def weaknesses_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's weak topics and suggestions"""
    global analytics
    
    if not analytics:
        analytics = AnalyticsEngine()
    
    user = update.effective_user
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    
    if not db_user:
        await update.message.reply_text("❌ Unable to load your data. Please try again later.")
        return
    
    try:
        weaknesses = analytics.get_user_weaknesses(db_user.telegram_id) if analytics else {}
        
        if not weaknesses:
            await update.message.reply_text(
                "🎉 *Great job!*\n\nNo significant weaknesses detected yet. "
                "Keep solving more problems to get personalized insights!",
                parse_mode='Markdown'
            )
            return
        
        message = "📊 *YOUR WEAKNESS ANALYSIS*\n\n"
        
        for topic, data in weaknesses.items():
            accuracy = data.get('accuracy', 0)
            problems_solved = data.get('problems_solved', 0)
            
            message += f"⚠️ *{topic}*\n"
            message += f"   • Accuracy: {accuracy:.1f}%\n"
            message += f"   • Problems Solved: {problems_solved}\n"
            message += f"   • Practice: /practice {topic}\n\n"
        
        message += "💡 *Tip:* Focus on your weakest topics first for maximum improvement!"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Weaknesses command error: {e}")
        await update.message.reply_text("❌ Error loading weaknesses. Please try again later.")

async def achievements_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user achievements"""
    global analytics
    
    if not analytics:
        analytics = AnalyticsEngine()
    
    user = update.effective_user
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    
    if not db_user:
        await update.message.reply_text("❌ Unable to load your achievements. Please try again later.")
        return
    
    try:
        user_achievements = analytics.get_user_achievements(db_user.telegram_id) if analytics else []
        all_achievements = analytics.get_all_achievements() if analytics else []
        
        message = f"🏆 *YOUR ACHIEVEMENTS*\n\n"
        message += f"*Unlocked: {len(user_achievements)}/{len(all_achievements)}*\n\n"
        
        if user_achievements:
            message += "*✨ Earned Badges:*\n"
            for ach in user_achievements:
                message += f"{ach['icon']} {ach['name']} - {ach['description']}\n"
        else:
            message += "🎯 *Start solving problems to earn achievements!*\n"
        
        message += "\n*🔒 Locked Achievements:*\n"
        locked_count = 0
        for ach in all_achievements:
            if ach['code'] not in [a['code'] for a in user_achievements]:
                if locked_count < 3:
                    message += f"🔒 {ach['name']} - {ach['description']}\n"
                locked_count += 1
        
        if locked_count > 3:
            message += f"... and {locked_count - 3} more!\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Achievements command error: {e}")
        await update.message.reply_text("❌ Error loading achievements. Please try again later.")

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboards"""
    global analytics
    
    if not analytics:
        analytics = AnalyticsEngine()
    
    try:
        # Get leaderboard type from args or default to 'weekly'
        board_type = context.args[0] if context.args else 'weekly'
        
        leaderboard = analytics.get_leaderboard(board_type) if analytics else []
        
        message = f"🏆 *LEADERBOARD - {board_type.upper()}*\n\n"
        
        if not leaderboard:
            message += "No data available yet. Keep solving!\n"
        else:
            for idx, entry in enumerate(leaderboard[:10], 1):
                medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
                message += f"{medal} {entry['username']} - {entry['score']} pts\n"
        
        message += f"\n💡 *Use: /leaderboard [daily/weekly/alltime]*"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Leaderboard command error: {e}")
        await update.message.reply_text("❌ Error loading leaderboard. Please try again later.")

async def practice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate personalized practice problems"""
    global content_gen
    
    user = update.effective_user
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    
    if not db_user:
        await update.message.reply_text("❌ Unable to generate practice. Please try again later.")
        return
    
    topic = ' '.join(context.args) if context.args else None
    
    if not topic:
        await update.message.reply_text(
            "🎯 *PRACTICE MODE*\n\n"
            "*Usage:* /practice <topic>\n\n"
            "*Examples:*\n"
            "/practice SN1\n"
            "/practice NGP\n"
            "/practice E2\n"
            "/practice stereochemistry\n\n"
            "💡 I'll generate personalized problems based on your weaknesses!",
            parse_mode='Markdown'
        )
        return
    
    try:
        await update.message.reply_text(
            f"🔬 *Generating {topic} practice problems...*\n\n"
            "This may take a moment as I create problems tailored to your level!",
            parse_mode='Markdown'
        )
        
        # Generate problems using content generator
        if not content_gen:
            await update.message.reply_text(
                "❌ Practice problem generation is not available yet. Try sending a photo of a problem instead!",
                parse_mode='Markdown'
            )
            return
        
        problems = content_gen.generate_practice_problems(
            user_id=db_user.telegram_id,
            topic=topic,
            difficulty=db_user.difficulty_level,
            count=3
        )
        
        if problems:
            message = f"📝 *{topic.upper()} PRACTICE PROBLEMS*\n\n"
            for idx, problem in enumerate(problems, 1):
                message += f"*Problem {idx}:*\n{problem['question']}\n\n"
                for opt_key, opt_val in problem.get('options', {}).items():
                    message += f"  {opt_key}) {opt_val}\n"
                message += "\n"
            
            message += "📸 *Send me a photo of the problem to get the full analysis!*"
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                f"❌ Unable to generate {topic} problems. Try another topic or check back later!",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Practice command error: {e}")
        await update.message.reply_text("❌ Error generating practice problems. Please try again later.")

async def multidebate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle multi-agent debate mode"""
    await update.message.reply_text(
        "🤖 *MULTI-AGENT DEBATE MODE*\n\n"
        "This feature uses 3-5 AI agents that debate each problem to achieve 98-99% accuracy!\n\n"
        "*How it works:*\n"
        "1️⃣ Systematic Agent analyzes step-by-step\n"
        "2️⃣ MS Chouhan Agent finds THE key difference\n"
        "3️⃣ Paula Bruice Agent does orbital analysis\n"
        "4️⃣ Devil's Advocate finds errors\n"
        "5️⃣ Consensus Agent synthesizes the best answer\n\n"
        "⏱️ Takes 5-10 minutes per problem (vs 2-8 min normal mode)\n"
        "📸 Just send a photo with 'multidebate' in caption!\n\n"
        "💡 *Coming soon - this feature is being finalized!*",
        parse_mode='Markdown'
    )
