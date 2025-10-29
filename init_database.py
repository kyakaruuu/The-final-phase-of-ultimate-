"""
Database Initialization Script
Creates all tables for the Ultimate Chemistry Bot
"""

import logging
from database import Base, engine, SessionLocal
from database import (
    User, Session, ProblemSolved, TopicStatistics,
    UserAchievement, Achievement, Leaderboard, ErrorPattern,
    ExplanationEffectiveness, SpacedReview, StudyGroup
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database with all tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully!")
        
        # Verify tables
        db = SessionLocal()
        try:
            db.execute("SELECT 1")  # type: ignore
            logger.info("✓ Database connection verified")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
        finally:
            db.close()
        
        # Create default achievements
        create_default_achievements()
        
        logger.info("✓ Database initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def create_default_achievements():
    """Create default achievement badges"""
    db = SessionLocal()
    try:
        # Check if achievements already exist
        existing = db.query(Achievement).first()
        if existing:
            logger.info("Achievements already exist, skipping...")
            return
        
        achievements = [
            Achievement(
                code="first_solve",
                name="First Steps",
                description="Solved your first problem",
                icon="🎯",
                category="milestone",
                points=10,
                criteria={"type": "problems_solved", "value": 1}
            ),
            Achievement(
                code="speed_demon",
                name="Speed Demon",
                description="Solved a problem in under 30 seconds",
                icon="⚡",
                category="skill",
                points=15,
                criteria={"type": "solve_time", "value": 30}
            ),
            Achievement(
                code="ngp_master",
                name="NGP Master",
                description="100% accuracy on 10+ NGP problems",
                icon="🏆",
                category="skill",
                points=50,
                criteria={"type": "topic_mastery", "topic": "NGP", "accuracy": 100, "minimum": 10}
            ),
            Achievement(
                code="streak_7",
                name="Weekly Warrior",
                description="7-day solving streak",
                icon="🔥",
                category="streak",
                points=30,
                criteria={"type": "streak", "value": 7}
            ),
            Achievement(
                code="hundred_club",
                name="Century Club",
                description="100 problems solved",
                icon="💯",
                category="milestone",
                points=100,
                criteria={"type": "problems_solved", "value": 100}
            ),
            Achievement(
                code="perfect_ten",
                name="Perfect Ten",
                description="10 correct answers in a row",
                icon="✨",
                category="skill",
                points=25,
                criteria={"type": "streak_correct", "value": 10}
            ),
        ]
        
        db.add_all(achievements)
        db.commit()
        logger.info(f"✓ Created {len(achievements)} default achievements")
        
    except Exception as e:
        logger.error(f"Error creating achievements: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
