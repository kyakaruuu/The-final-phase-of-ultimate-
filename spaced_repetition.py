"""
Spaced Repetition System (SuperMemo SM-2 Algorithm)
Optimal review scheduling for long-term retention
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from database import SpacedReview, User, TopicStatistics, SessionLocal

logger = logging.getLogger(__name__)

class SpacedRepetitionSystem:
    """
    Implementation of SuperMemo SM-2 algorithm
    Optimizes review intervals based on recall quality
    """
    
    def __init__(self):
        self.db = None
    
    def get_db(self) -> Session:
        """Get database session"""
        if not self.db or not self.db.is_active:
            self.db = SessionLocal()
        return self.db
    
    def close_db(self):
        """Close database session"""
        if self.db:
            self.db.close()
            self.db = None
    
    def add_topic_for_review(self, user_id: int, topic: str):
        """
        Add a topic to spaced repetition schedule
        Called after user first learns a topic
        """
        db = self.get_db()
        try:
            # Check if already exists
            existing = db.query(SpacedReview).filter(
                SpacedReview.user_id == user_id,
                SpacedReview.topic == topic
            ).first()
            
            if existing:
                logger.info(f"Topic {topic} already in review schedule for user {user_id}")
                return existing
            
            # Create new review schedule
            review = SpacedReview(
                user_id=user_id,
                topic=topic,
                ease_factor=2.5,  # Default ease
                interval_days=1,  # Review tomorrow
                repetitions=0,
                last_reviewed=datetime.utcnow(),
                next_review=datetime.utcnow() + timedelta(days=1)
            )
            
            db.add(review)
            db.commit()
            
            logger.info(f"✅ Added {topic} to review schedule for user {user_id}")
            return review
        
        except Exception as e:
            logger.error(f"Error adding topic for review: {e}")
            db.rollback()
            return None
        finally:
            self.close_db()
    
    def record_review(self, user_id: int, topic: str, quality: int) -> Dict:
        """
        Record a review session and calculate next interval
        
        Args:
            user_id: User ID
            topic: Topic reviewed
            quality: Quality of recall (0-5)
                0: Complete blackout
                1: Incorrect, but recognized
                2: Incorrect, but easy to recall correct
                3: Correct with difficulty
                4: Correct after hesitation
                5: Perfect recall
        
        Returns:
            Dict with next_review_date and interval_days
        """
        db = self.get_db()
        try:
            review = db.query(SpacedReview).filter(
                SpacedReview.user_id == user_id,
                SpacedReview.topic == topic
            ).first()
            
            if not review:
                # Create new if doesn't exist
                review = self.add_topic_for_review(user_id, topic)
                if not review:
                    return {"error": "Failed to create review schedule"}
            
            # SM-2 Algorithm
            if quality < 3:
                # Failed recall - restart
                review.repetitions = 0
                review.interval_days = 1
            else:
                # Successful recall
                if review.repetitions == 0:
                    review.interval_days = 1
                elif review.repetitions == 1:
                    review.interval_days = 6
                else:
                    review.interval_days = int(review.interval_days * review.ease_factor)
                
                review.repetitions += 1
                
                # Update ease factor
                review.ease_factor = max(1.3, 
                    review.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
                )
            
            # Update review dates
            review.last_reviewed = datetime.utcnow()
            review.next_review = datetime.utcnow() + timedelta(days=review.interval_days)
            review.quality_last_review = quality
            
            db.commit()
            
            return {
                "topic": topic,
                "next_review": review.next_review.isoformat(),
                "interval_days": review.interval_days,
                "ease_factor": round(review.ease_factor, 2),
                "repetitions": review.repetitions
            }
        
        except Exception as e:
            logger.error(f"Error recording review: {e}")
            db.rollback()
            return {"error": str(e)}
        finally:
            self.close_db()
    
    def get_due_reviews(self, user_id: int) -> List[Dict]:
        """Get topics due for review"""
        db = self.get_db()
        try:
            reviews = db.query(SpacedReview).filter(
                SpacedReview.user_id == user_id,
                SpacedReview.next_review <= datetime.utcnow()
            ).order_by(SpacedReview.next_review.asc()).all()
            
            due = []
            for review in reviews:
                due.append({
                    "topic": review.topic,
                    "last_reviewed": review.last_reviewed.isoformat() if review.last_reviewed else None,
                    "days_overdue": (datetime.utcnow() - review.next_review).days,
                    "repetitions": review.repetitions
                })
            
            return due
        finally:
            self.close_db()
    
    def get_upcoming_reviews(self, user_id: int, days_ahead: int = 7) -> List[Dict]:
        """Get reviews scheduled in the next N days"""
        db = self.get_db()
        try:
            cutoff = datetime.utcnow() + timedelta(days=days_ahead)
            
            reviews = db.query(SpacedReview).filter(
                SpacedReview.user_id == user_id,
                SpacedReview.next_review > datetime.utcnow(),
                SpacedReview.next_review <= cutoff
            ).order_by(SpacedReview.next_review.asc()).all()
            
            upcoming = []
            for review in reviews:
                days_until = (review.next_review - datetime.utcnow()).days
                upcoming.append({
                    "topic": review.topic,
                    "next_review": review.next_review.isoformat(),
                    "days_until": days_until,
                    "repetitions": review.repetitions
                })
            
            return upcoming
        finally:
            self.close_db()
    
    def get_review_summary(self, user_id: int) -> Dict:
        """Get summary of user's review schedule"""
        db = self.get_db()
        try:
            all_reviews = db.query(SpacedReview).filter(
                SpacedReview.user_id == user_id
            ).all()
            
            due_now = sum(1 for r in all_reviews if r.next_review <= datetime.utcnow())
            due_today = sum(1 for r in all_reviews 
                           if r.next_review.date() == datetime.utcnow().date())
            due_week = sum(1 for r in all_reviews 
                          if r.next_review <= datetime.utcnow() + timedelta(days=7))
            
            total_topics = len(all_reviews)
            mastered = sum(1 for r in all_reviews if r.repetitions >= 5)
            
            return {
                "total_topics": total_topics,
                "due_now": due_now,
                "due_today": due_today,
                "due_this_week": due_week,
                "mastered": mastered,
                "retention_rate": round((mastered / total_topics * 100) if total_topics > 0 else 0, 1)
            }
        finally:
            self.close_db()
    
    def format_review_message(self, user_id: int) -> str:
        """Format review summary for Telegram"""
        summary = self.get_review_summary(user_id)
        due = self.get_due_reviews(user_id)
        upcoming = self.get_upcoming_reviews(user_id, days_ahead=3)
        
        message = "📚 **SPACED REPETITION SUMMARY**\n\n"
        
        # Overall stats
        message += f"📊 Topics tracked: {summary['total_topics']}\n"
        message += f"🏆 Mastered: {summary['mastered']} ({summary['retention_rate']}%)\n\n"
        
        # Due now
        if summary['due_now'] > 0:
            message += f"⚠️ **{summary['due_now']} topics need review NOW!**\n"
            for topic_info in due[:5]:  # Show first 5
                topic = topic_info['topic']
                overdue = topic_info['days_overdue']
                message += f"• {topic} ({overdue}d overdue)\n"
            message += "\n"
        else:
            message += "✅ All caught up! No reviews due.\n\n"
        
        # Upcoming
        if upcoming:
            message += "📅 **Coming up (next 3 days):**\n"
            for topic_info in upcoming[:5]:
                topic = topic_info['topic']
                days = topic_info['days_until']
                message += f"• {topic} (in {days}d)\n"
            message += "\n"
        
        message += "💡 Tip: Regular review = long-term retention!\n"
        message += "Use /review [topic] to practice a topic."
        
        return message
    
    def auto_schedule_from_performance(self, user_id: int):
        """
        Automatically add topics to review schedule based on user's learning
        Called periodically
        """
        db = self.get_db()
        try:
            # Get topics user has practiced
            stats = db.query(TopicStatistics).filter(
                TopicStatistics.user_id == user_id,
                TopicStatistics.problems_attempted >= 3  # At least 3 problems
            ).all()
            
            added_count = 0
            for stat in stats:
                # Check if already in review schedule
                existing = db.query(SpacedReview).filter(
                    SpacedReview.user_id == user_id,
                    SpacedReview.topic == stat.topic
                ).first()
                
                if not existing:
                    self.add_topic_for_review(user_id, stat.topic)
                    added_count += 1
            
            logger.info(f"Auto-scheduled {added_count} topics for user {user_id}")
            return added_count
        
        finally:
            self.close_db()

# Global instance
spaced_repetition = SpacedRepetitionSystem()
