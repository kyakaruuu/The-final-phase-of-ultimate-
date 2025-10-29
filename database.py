"""
Database Module for Ultimate Chemistry Bot
===========================================

Comprehensive data models supporting 50+ features with PostgreSQL/SQLite compatibility.
Includes repository pattern, type hints, and optimized for Railway deployment.

Features Supported:
- User profiles and preferences
- Problem tracking and analytics
- Gamification and achievements
- Spaced repetition (SM-2 algorithm)
- Social learning features
- Content generation and scheduling
- Advanced analytics and patterns
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any, Generator
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm import Session as SQLSession
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import Engine

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

def get_database_url() -> str:
    """
    Get database URL with Railway PostgreSQL compatibility.
    
    Returns:
        str: Properly formatted database URL
    """
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///chemistry_bot.db')
    
    # Fix Railway PostgreSQL URL format (postgres:// -> postgresql://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info("✅ PostgreSQL database URL detected and normalized")
    else:
        logger.info("✅ Using SQLite database")
    
    return database_url


def create_database_engine() -> Engine:
    """
    Create SQLAlchemy engine with optimized connection pooling.
    
    Returns:
        Engine: Configured SQLAlchemy engine
    """
    database_url = get_database_url()
    is_postgresql = 'postgresql' in database_url
    
    connect_args = {}
    if is_postgresql:
        connect_args = {
            "connect_timeout": 10,
            "options": "-c timezone=utc"
        }
    
    engine = create_engine(
        database_url,
        poolclass=NullPool,  # No connection pooling for Railway free tier
        echo=False,
        connect_args=connect_args
    )
    
    return engine


# Initialize database engine and session factory
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# SESSION MANAGEMENT (Repository Pattern)
# ============================================================================

@contextmanager
def get_db_session() -> Generator[SQLSession, None, None]:
    """
    Context manager for database sessions with automatic cleanup.
    
    Usage:
        with get_db_session() as db:
            user = db.query(User).filter_by(telegram_id=123).first()
    
    Yields:
        SQLSession: SQLAlchemy database session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db() -> Generator[SQLSession, None, None]:
    """
    Get database session for dependency injection (FastAPI-style).
    
    Yields:
        SQLSession: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# USER MODELS
# ============================================================================

class User(Base):
    """
    Main user profile with comprehensive tracking and preferences.
    
    Attributes:
        telegram_id: Unique Telegram user ID
        username: Telegram username
        first_name: User's first name
        language: Interface language (en, hi, hinglish)
        learning_style: Detected learning style (visual, verbal, kinesthetic)
        career_goal: Target exam (JEE_Mains, JEE_Advanced, NEET)
        total_problems_solved: Lifetime problem count
        current_streak: Current daily solving streak
        level: Gamification level
        experience_points: XP for leveling up
    """
    __tablename__ = 'users'
    
    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # User preferences
    language = Column(String(10), default='en', nullable=False)
    learning_style = Column(String(20), default='unknown', nullable=False)
    pdf_mode = Column(String(10), default='light', nullable=False)
    difficulty_level = Column(Integer, default=5, nullable=False)
    career_goal = Column(String(20), default='JEE_Advanced', nullable=False)
    
    # Feature toggles
    spaced_repetition_enabled = Column(Boolean, default=True, nullable=False)
    smart_reminders_enabled = Column(Boolean, default=True, nullable=False)
    daily_quiz_enabled = Column(Boolean, default=True, nullable=False)
    daily_facts_enabled = Column(Boolean, default=False, nullable=False)
    
    # Learning metrics
    total_problems_solved = Column(Integer, default=0, nullable=False)
    total_correct = Column(Integer, default=0, nullable=False)
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    last_problem_date = Column(DateTime, nullable=True)
    
    # Gamification
    total_score = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    experience_points = Column(Integer, default=0, nullable=False)
    
    # Social features
    is_helper = Column(Boolean, default=False, nullable=False)
    help_count = Column(Integer, default=0, nullable=False)
    
    # Relationships (cascade delete orphans)
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    problems = relationship("ProblemSolved", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    topic_stats = relationship("TopicStatistics", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("SpacedReview", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
    
    def get_accuracy(self) -> float:
        """
        Calculate overall accuracy percentage.
        
        Returns:
            float: Accuracy as percentage (0-100)
        """
        if self.total_problems_solved == 0:
            return 0.0
        return (self.total_correct / self.total_problems_solved) * 100


class Session(Base):
    """
    Track individual user study sessions for analytics.
    
    Attributes:
        user_id: Foreign key to User
        start_time: Session start timestamp
        end_time: Session end timestamp
        duration_seconds: Total session duration
        problems_attempted: Number of problems in session
        problems_correct: Number of correct answers
        topics_covered: JSON list of topics studied
    """
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0, nullable=False)
    problems_attempted = Column(Integer, default=0, nullable=False)
    problems_correct = Column(Integer, default=0, nullable=False)
    topics_covered = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, duration={self.duration_seconds}s)>"


# ============================================================================
# PROBLEM TRACKING
# ============================================================================

class ProblemSolved(Base):
    """
    Track individual problem attempts with comprehensive metadata.
    
    Supports multi-agent analysis, auto-tagging, error pattern detection,
    and performance analytics for adaptive difficulty.
    """
    __tablename__ = 'problems_solved'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Problem classification
    problem_type = Column(String(50), nullable=True)
    topic = Column(String(100), index=True, nullable=True)
    subtopics = Column(JSON, nullable=True)
    difficulty = Column(Integer, nullable=True)
    
    # Performance metrics
    is_correct = Column(Boolean, nullable=False)
    time_taken_seconds = Column(Integer, nullable=True)
    attempts = Column(Integer, default=1, nullable=False)
    hint_used = Column(Boolean, default=False, nullable=False)
    
    # AI analysis metadata
    confidence_score = Column(Float, nullable=True)
    strategies_used = Column(JSON, nullable=True)
    error_type = Column(String(100), nullable=True)
    
    # Auto-tagging for knowledge graph
    tags = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="problems")
    
    def __repr__(self) -> str:
        return f"<ProblemSolved(id={self.id}, topic={self.topic}, correct={self.is_correct})>"
    
    def get_correct(self) -> bool:
        """
        Get correct status (backwards compatibility helper).
        
        Returns:
            bool: Whether problem was solved correctly
        """
        return bool(self.is_correct)


# ============================================================================
# ANALYTICS & LEARNING
# ============================================================================

class TopicStatistics(Base):
    """
    Per-topic performance statistics for adaptive difficulty and mastery tracking.
    
    Enables personalized learning paths by tracking topic-specific performance,
    time investment, and error patterns.
    """
    __tablename__ = 'topic_statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    
    # Performance metrics
    problems_attempted = Column(Integer, default=0, nullable=False)
    problems_correct = Column(Integer, default=0, nullable=False)
    accuracy = Column(Float, default=0.0, nullable=False)
    
    # Time investment tracking
    total_time_seconds = Column(Integer, default=0, nullable=False)
    average_time_seconds = Column(Integer, default=0, nullable=False)
    last_practiced = Column(DateTime, nullable=True)
    
    # Adaptive difficulty progression
    current_difficulty = Column(Integer, default=5, nullable=False)
    mastery_level = Column(Float, default=0.0, nullable=False)
    
    # Error pattern detection
    error_patterns = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="topic_stats")
    
    def __repr__(self) -> str:
        return f"<TopicStatistics(user_id={self.user_id}, topic={self.topic}, accuracy={self.accuracy:.1f}%)>"


class ErrorPattern(Base):
    """
    Track common error patterns across all users for collective intelligence.
    
    Enables predictive intervention and improved explanations based on
    community-wide error analysis.
    """
    __tablename__ = 'error_patterns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(100), nullable=False, index=True)
    error_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    frequency = Column(Integer, default=1, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Example problem IDs for reference
    example_problems = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ErrorPattern(topic={self.topic}, type={self.error_type}, frequency={self.frequency})>"


class ExplanationEffectiveness(Base):
    """
    Track which explanation strategies work best (Self-Learning Engine).
    
    Uses Bayesian analysis to determine optimal explanation style per user
    and topic, enabling personalized teaching approaches.
    """
    __tablename__ = 'explanation_effectiveness'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(100), nullable=False, index=True)
    explanation_type = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Effectiveness tracking
    times_shown = Column(Integer, default=0, nullable=False)
    times_understood = Column(Integer, default=0, nullable=False)
    times_not_understood = Column(Integer, default=0, nullable=False)
    effectiveness_score = Column(Float, default=0.5, nullable=False)
    
    # Learning style correlation
    works_best_for_style = Column(String(20), nullable=True)
    
    def __repr__(self) -> str:
        return f"<ExplanationEffectiveness(topic={self.topic}, type={self.explanation_type}, score={self.effectiveness_score:.2f})>"


# ============================================================================
# GAMIFICATION
# ============================================================================

class Achievement(Base):
    """
    Achievement definitions with unlock criteria and rewards.
    
    Supports milestone, skill, social, and streak-based achievements
    for comprehensive gamification.
    """
    __tablename__ = 'achievements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(10), nullable=True)
    category = Column(String(50), nullable=False)
    points = Column(Integer, default=10, nullable=False)
    
    # Unlock criteria stored as JSON
    criteria = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Achievement(code={self.code}, name={self.name}, points={self.points})>"


class UserAchievement(Base):
    """
    Track unlocked achievements per user.
    
    Attributes:
        achievement_code: Reference to Achievement.code
        is_featured: Whether to display prominently in profile
    """
    __tablename__ = 'user_achievements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    achievement_code = Column(String(50), nullable=False, index=True)
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    
    def __repr__(self) -> str:
        return f"<UserAchievement(user_id={self.user_id}, code={self.achievement_code})>"


class Leaderboard(Base):
    """
    Leaderboard entries with support for multiple categories and time periods.
    
    Supports daily, weekly, all-time, and topic-specific leaderboards.
    """
    __tablename__ = 'leaderboard'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    topic = Column(String(100), nullable=True)
    score = Column(Integer, default=0, nullable=False)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Leaderboard(user_id={self.user_id}, category={self.category}, rank={self.rank})>"


# ============================================================================
# SPACED REPETITION (SuperMemo SM-2 Algorithm)
# ============================================================================

class SpacedReview(Base):
    """
    Spaced repetition schedule implementing SuperMemo SM-2 algorithm.
    
    Attributes:
        ease_factor: How easily the user recalls (default 2.5)
        interval_days: Days until next review
        repetitions: Number of successful consecutive reviews
        quality_last_review: User rating 0-5 (5=perfect recall)
    """
    __tablename__ = 'spaced_reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    
    # SM-2 algorithm parameters
    ease_factor = Column(Float, default=2.5, nullable=False)
    interval_days = Column(Integer, default=1, nullable=False)
    repetitions = Column(Integer, default=0, nullable=False)
    
    # Scheduling timestamps
    last_reviewed = Column(DateTime, nullable=True)
    next_review = Column(DateTime, nullable=False, index=True)
    
    # User performance rating
    quality_last_review = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    
    def __repr__(self) -> str:
        return f"<SpacedReview(user_id={self.user_id}, topic={self.topic}, next={self.next_review})>"


# ============================================================================
# SOCIAL FEATURES
# ============================================================================

class StudyGroup(Base):
    """
    Study groups matched by skill level for collaborative learning.
    
    Attributes:
        skill_level_min/max: Allowed skill range (0-1 scale)
        max_members: Maximum group size
        is_active: Whether group is accepting members
    """
    __tablename__ = 'study_groups'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    skill_level_min = Column(Float, nullable=True)
    skill_level_max = Column(Float, nullable=True)
    max_members = Column(Integer, default=5, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    members = relationship("StudyGroupMember", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<StudyGroup(id={self.id}, name={self.name}, active={self.is_active})>"


class StudyGroupMember(Base):
    """
    Study group membership records.
    """
    __tablename__ = 'study_group_members'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('study_groups.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    group = relationship("StudyGroup", back_populates="members")
    
    def __repr__(self) -> str:
        return f"<StudyGroupMember(group_id={self.group_id}, user_id={self.user_id})>"


class SharedProblem(Base):
    """
    Community-shared problems for collaborative learning.
    
    Supports content moderation and engagement tracking.
    """
    __tablename__ = 'shared_problems'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    topic = Column(String(100), nullable=True, index=True)
    difficulty = Column(Integer, nullable=True)
    
    # Moderation flags
    is_approved = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Engagement metrics
    attempts = Column(Integer, default=0, nullable=False)
    likes = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<SharedProblem(id={self.id}, title={self.title}, likes={self.likes})>"


class Explanation(Base):
    """
    Student-generated explanations with community voting.
    
    Enables peer learning through student-contributed content.
    """
    __tablename__ = 'explanations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # Community voting
    upvotes = Column(Integer, default=0, nullable=False)
    downvotes = Column(Integer, default=0, nullable=False)
    
    # Featured status
    is_featured = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Explanation(id={self.id}, topic={self.topic}, votes={self.upvotes - self.downvotes})>"


class DoubtSession(Base):
    """
    Peer-to-peer doubt resolution sessions.
    
    Connects students seeking help with volunteer helpers,
    tracking session quality through ratings.
    """
    __tablename__ = 'doubt_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asker_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    helper_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    topic = Column(String(100), nullable=True)
    question = Column(Text, nullable=True)
    
    # Session lifecycle
    status = Column(String(20), default='pending', nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    # Quality feedback
    helpfulness_rating = Column(Integer, nullable=True)
    
    def __repr__(self) -> str:
        return f"<DoubtSession(id={self.id}, status={self.status})>"


# ============================================================================
# AUTOMATION & SCHEDULING
# ============================================================================

class ScheduledMessage(Base):
    """
    Scheduled notifications and reminders for smart automation.
    
    Supports multiple message types: reminders, quizzes, facts, reviews, reports.
    """
    __tablename__ = 'scheduled_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    message_type = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=True)
    scheduled_for = Column(DateTime, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    is_sent = Column(Boolean, default=False, nullable=False, index=True)
    
    def __repr__(self) -> str:
        return f"<ScheduledMessage(type={self.message_type}, scheduled={self.scheduled_for}, sent={self.is_sent})>"


class WeeklyChallenge(Base):
    """
    Weekly study challenges with rewards and badges.
    
    Challenge types: solve_problems, help_others, streak, accuracy.
    """
    __tablename__ = 'weekly_challenges'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    challenge_type = Column(String(50), nullable=False)
    target_value = Column(Integer, nullable=False)
    reward_points = Column(Integer, default=0, nullable=False)
    badge_code = Column(String(50), nullable=True)
    
    # Time period
    week_start = Column(DateTime, nullable=False, index=True)
    week_end = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<WeeklyChallenge(title={self.title}, type={self.challenge_type})>"


class ChallengeProgress(Base):
    """
    User progress tracking for weekly challenges.
    """
    __tablename__ = 'challenge_progress'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    challenge_id = Column(Integer, ForeignKey('weekly_challenges.id'), nullable=False, index=True)
    current_value = Column(Integer, default=0, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ChallengeProgress(user_id={self.user_id}, challenge_id={self.challenge_id}, completed={self.is_completed})>"


# ============================================================================
# CONTENT & ANALYTICS
# ============================================================================

class GeneratedProblem(Base):
    """
    AI-generated practice problems with quality tracking.
    
    Tracks usage and success rates to improve generation quality.
    """
    __tablename__ = 'generated_problems'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(100), nullable=False, index=True)
    difficulty = Column(Integer, nullable=True)
    problem_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)
    correct_answer = Column(String(10), nullable=False)
    explanation = Column(Text, nullable=True)
    
    # Quality metrics
    times_used = Column(Integer, default=0, nullable=False)
    success_rate = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<GeneratedProblem(id={self.id}, topic={self.topic}, difficulty={self.difficulty})>"


class JEETrend(Base):
    """
    JEE exam pattern trends for strategic preparation.
    
    Analyzes historical exam data to identify high-frequency topics
    and difficulty trends.
    """
    __tablename__ = 'jee_trends'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    frequency = Column(Integer, nullable=True)
    average_difficulty = Column(Float, nullable=True)
    trend = Column(String(20), nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<JEETrend(year={self.year}, topic={self.topic}, trend={self.trend})>"


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db() -> bool:
    """
    Initialize database and create all tables.
    
    Creates schema and populates default achievements.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database schema initialized successfully")
        
        # Populate default achievements
        create_default_achievements()
        
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        return False


def create_default_achievements() -> None:
    """
    Create default achievement definitions.
    
    Populates the achievements table with milestone, skill,
    social, and streak-based achievements.
    """
    default_achievements: List[Dict[str, Any]] = [
        {
            "code": "first_solve",
            "name": "First Steps",
            "description": "Solved your first problem!",
            "icon": "🎯",
            "category": "milestone",
            "points": 10
        },
        {
            "code": "speed_demon",
            "name": "Speed Demon",
            "description": "Solved a problem in under 30 seconds",
            "icon": "⚡",
            "category": "skill",
            "points": 25
        },
        {
            "code": "ngp_master",
            "name": "NGP Master",
            "description": "100% accuracy on NGP problems (10+ solved)",
            "icon": "🏆",
            "category": "skill",
            "points": 100
        },
        {
            "code": "streak_7",
            "name": "Week Warrior",
            "description": "7-day solving streak",
            "icon": "🔥",
            "category": "streak",
            "points": 50
        },
        {
            "code": "streak_30",
            "name": "Month Master",
            "description": "30-day solving streak",
            "icon": "💎",
            "category": "streak",
            "points": 200
        },
        {
            "code": "hundred_club",
            "name": "Century",
            "description": "100 problems solved",
            "icon": "💯",
            "category": "milestone",
            "points": 150
        },
        {
            "code": "helpful_student",
            "name": "Helping Hand",
            "description": "Helped 10 other students",
            "icon": "🤝",
            "category": "social",
            "points": 75
        },
        {
            "code": "perfectionist",
            "name": "Perfectionist",
            "description": "10 problems in a row correct",
            "icon": "✨",
            "category": "skill",
            "points": 50
        },
        {
            "code": "all_rounder",
            "name": "All-Rounder",
            "description": "Solved problems in all topics",
            "icon": "🌟",
            "category": "milestone",
            "points": 100
        },
        {
            "code": "early_bird",
            "name": "Early Bird",
            "description": "Solved 5 problems before 7 AM",
            "icon": "🌅",
            "category": "streak",
            "points": 30
        },
        {
            "code": "night_owl",
            "name": "Night Owl",
            "description": "Solved 5 problems after 11 PM",
            "icon": "🦉",
            "category": "streak",
            "points": 30
        },
    ]
    
    with get_db_session() as db:
        try:
            # Check if achievements already exist
            if db.query(Achievement).count() > 0:
                logger.info("✅ Achievements already exist, skipping creation")
                return
            
            # Add all default achievements
            for achievement_data in default_achievements:
                achievement = Achievement(**achievement_data)
                db.add(achievement)
            
            logger.info(f"✅ Created {len(default_achievements)} default achievements")
        except Exception as e:
            logger.error(f"❌ Error creating achievements: {e}")
            raise


def wait_for_db(max_retries: int = 5, retry_delay: int = 2) -> bool:
    """
    Wait for database to be ready (useful for Railway deployment).
    
    Attempts to connect to the database with exponential backoff.
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Seconds to wait between retries
    
    Returns:
        bool: True if connection established, False otherwise
    """
    for attempt in range(1, max_retries + 1):
        try:
            with get_db_session() as db:
                db.execute(text("SELECT 1"))
            
            logger.info("✅ Database connection established")
            return True
        except Exception as e:
            logger.warning(
                f"⚠️ Database not ready (attempt {attempt}/{max_retries}): {e}"
            )
            if attempt < max_retries:
                time.sleep(retry_delay)
    
    logger.error("❌ Failed to connect to database after all retries")
    return False


# ============================================================================
# REPOSITORY HELPER FUNCTIONS
# ============================================================================

def get_or_create_user(telegram_id: int, username: Optional[str] = None, 
                       first_name: Optional[str] = None) -> User:
    """
    Get existing user or create new one.
    
    Args:
        telegram_id: Telegram user ID
        username: Optional Telegram username
        first_name: Optional user first name
    
    Returns:
        User: User object
    """
    with get_db_session() as db:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            db.add(user)
            db.flush()
            logger.info(f"✅ Created new user: {telegram_id}")
        else:
            # Update last active timestamp
            user.last_active = datetime.utcnow()
            db.flush()
        
        return user


def update_user_streak(user_id: int) -> None:
    """
    Update user's daily solving streak.
    
    Args:
        user_id: User database ID
    """
    with get_db_session() as db:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return
        
        now = datetime.utcnow()
        last_date = user.last_problem_date
        
        if not last_date:
            # First problem ever
            user.current_streak = 1
        elif (now.date() - last_date.date()).days == 1:
            # Consecutive day
            user.current_streak += 1
            user.longest_streak = max(user.longest_streak, user.current_streak)
        elif (now.date() - last_date.date()).days > 1:
            # Streak broken
            user.current_streak = 1
        
        user.last_problem_date = now
        db.flush()
        logger.info(f"✅ Updated streak for user {user_id}: {user.current_streak} days")


# Module exports
__all__ = [
    'Base', 'engine', 'SessionLocal', 'get_db', 'get_db_session',
    'User', 'Session', 'ProblemSolved', 'TopicStatistics', 'ErrorPattern',
    'ExplanationEffectiveness', 'Achievement', 'UserAchievement', 'Leaderboard',
    'SpacedReview', 'StudyGroup', 'StudyGroupMember', 'SharedProblem',
    'Explanation', 'DoubtSession', 'ScheduledMessage', 'WeeklyChallenge',
    'ChallengeProgress', 'GeneratedProblem', 'JEETrend',
    'init_db', 'wait_for_db', 'get_or_create_user', 'update_user_streak'
]
