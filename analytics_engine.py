"""
Analytics Engine for Ultimate Chemistry Bot
============================================

Comprehensive performance tracking, pattern detection, and personalized insights.
Production-ready with type hints, context-managed sessions, and Railway optimization.

Features:
- User performance tracking with streaks and leveling
- Topic-wise analytics with adaptive difficulty
- Weakness detection and personalized recommendations
- Peer comparison and percentile rankings
- Error pattern recognition
- Achievement system
- Multi-tier leaderboards (daily/weekly/all-time)

Author: Enhanced for JEE Advanced Chemistry Bot
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import numpy as np

from database import (
    User, ProblemSolved, TopicStatistics, ErrorPattern,
    ExplanationEffectiveness, UserAchievement, Leaderboard,
    get_db_session
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# ANALYTICS ENGINE
# ============================================================================

class AnalyticsEngine:
    """
    Central analytics engine for comprehensive tracking and insights.
    
    Provides:
    - Real-time performance tracking
    - Adaptive difficulty adjustment
    - Pattern detection and recommendations
    - Social features (leaderboards, comparisons)
    """
    
    def __init__(self) -> None:
        """Initialize analytics engine."""
        logger.info("✅ Analytics Engine initialized")
    
    # ========================================================================
    # USER TRACKING & PERFORMANCE
    # ========================================================================
    
    def track_problem(
        self, 
        user_id: int, 
        topic: str, 
        is_correct: bool, 
        time_taken: int, 
        difficulty: int = 5, 
        hint_used: bool = False, 
        **kwargs: Any
    ) -> int:
        """
        Track a solved problem with comprehensive analytics update.
        
        Args:
            user_id: Telegram user ID
            topic: Chemistry topic (SN1, SN2, NGP, etc.)
            is_correct: Whether answer was correct
            time_taken: Time in seconds
            difficulty: Problem difficulty (1-10)
            hint_used: Whether hint was used
            **kwargs: Additional metadata (error_type, explanation, etc.)
        
        Returns:
            int: Problem ID, or -1 on error
        """
        with get_db_session() as db:
            try:
                # Create problem record
                problem = ProblemSolved(
                    user_id=user_id,
                    topic=topic,
                    is_correct=is_correct,
                    time_taken_seconds=time_taken,
                    difficulty=difficulty,
                    hint_used=hint_used,
                    **kwargs
                )
                db.add(problem)
                db.flush()  # Get problem ID
                
                # Update user stats
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if user:
                    self._update_user_stats(user, is_correct, time_taken, difficulty, hint_used, db)
                    self._update_streak(user, db)
                    self._check_level_up(user)
                
                # Update topic statistics
                self._update_topic_stats(user_id, topic, is_correct, time_taken, db)
                
                # Check for achievements
                if user:
                    self._check_achievements(user_id, topic, is_correct, db)
                
                logger.info(f"📊 Tracked problem for user {user_id}: {topic} ({'✅' if is_correct else '❌'})")
                return problem.id
                
            except Exception as e:
                logger.error(f"Error tracking problem: {e}", exc_info=True)
                return -1
    
    def _update_user_stats(
        self, 
        user: User, 
        is_correct: bool, 
        time_taken: int, 
        difficulty: int, 
        hint_used: bool,
        db: Session
    ) -> None:
        """Update user's overall statistics."""
        user.total_problems_solved += 1
        if is_correct:
            user.total_correct += 1
        
        user.last_active = datetime.utcnow()
        user.last_problem_date = datetime.utcnow()
        
        # Calculate and award points
        points = self._calculate_points(difficulty, is_correct, time_taken, hint_used)
        user.experience_points += points
        user.total_score += points
    
    def _update_streak(self, user: User, db: Session) -> None:
        """
        Update user's solving streak.
        
        Streak rules:
        - Same day: streak continues
        - Next day: streak increments
        - Gap > 1 day: streak resets to 1
        """
        if not user.last_problem_date:
            user.current_streak = 1
            user.longest_streak = 1
            return
        
        days_diff = (datetime.utcnow() - user.last_problem_date).days
        
        if days_diff == 0:
            # Same day, streak continues (no change)
            pass
        elif days_diff == 1:
            # Next day, increment streak
            user.current_streak += 1
            if user.current_streak > user.longest_streak:
                user.longest_streak = user.current_streak
        else:
            # Streak broken
            user.current_streak = 1
    
    def _calculate_points(
        self, 
        difficulty: int, 
        is_correct: bool, 
        time_taken: int, 
        hint_used: bool
    ) -> int:
        """
        Calculate points earned for a problem.
        
        Scoring formula:
        - Base: 10 points
        - Difficulty bonus: 2 * difficulty
        - Speed bonus: up to 30 points (if < 60s)
        - Hint penalty: -10 points
        - Minimum: 5 points (consolation for incorrect)
        """
        if not is_correct:
            return 5  # Consolation points
        
        base_points = 10
        difficulty_bonus = difficulty * 2
        
        # Speed bonus (if under 60 seconds)
        speed_bonus = max(0, 30 - time_taken // 2) if time_taken < 60 else 0
        
        # Hint penalty
        hint_penalty = -10 if hint_used else 0
        
        total = base_points + difficulty_bonus + speed_bonus + hint_penalty
        return max(5, total)  # Minimum 5 points
    
    def _check_level_up(self, user: User) -> None:
        """Check if user should level up (100 XP per level)."""
        required_xp = user.level * 100
        if user.experience_points >= required_xp:
            user.level += 1
            user.experience_points -= required_xp
            logger.info(f"🎉 User {user.telegram_id} leveled up to {user.level}!")
    
    def _update_topic_stats(
        self, 
        user_id: int, 
        topic: str, 
        is_correct: bool, 
        time_taken: int, 
        db: Session
    ) -> None:
        """
        Update statistics for a specific topic with adaptive difficulty.
        
        Calculates:
        - Accuracy percentage
        - Average time
        - Mastery level (0-1 scale)
        - Adaptive difficulty adjustment
        """
        stats = db.query(TopicStatistics).filter(
            and_(TopicStatistics.user_id == user_id, TopicStatistics.topic == topic)
        ).first()
        
        if not stats:
            stats = TopicStatistics(user_id=user_id, topic=topic)
            db.add(stats)
        
        stats.problems_attempted += 1
        if is_correct:
            stats.problems_correct += 1
        
        stats.accuracy = (stats.problems_correct / stats.problems_attempted) * 100
        stats.total_time_seconds += time_taken
        stats.average_time_seconds = stats.total_time_seconds // stats.problems_attempted
        stats.last_practiced = datetime.utcnow()
        
        # Calculate mastery level (0-1 scale)
        accuracy_factor = stats.accuracy / 100
        volume_factor = min(1.0, stats.problems_attempted / 50)  # Mastery after 50 problems
        stats.mastery_level = (accuracy_factor * 0.7) + (volume_factor * 0.3)
        
        # Adaptive difficulty adjustment
        if stats.accuracy > 85 and stats.problems_attempted >= 5:
            stats.current_difficulty = min(10, stats.current_difficulty + 1)
        elif stats.accuracy < 50 and stats.problems_attempted >= 5:
            stats.current_difficulty = max(1, stats.current_difficulty - 1)
    
    def _check_achievements(
        self, 
        user_id: int, 
        topic: str, 
        is_correct: bool, 
        db: Session
    ) -> None:
        """
        Check and award achievements.
        
        Achievement types:
        - Milestones (1st, 100th, 500th problem)
        - Streaks (7-day, 30-day)
        - Topic mastery (100% accuracy with 10+ problems)
        """
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            return
        
        achievements_to_award: List[str] = []
        
        # Milestone achievements
        if user.total_problems_solved == 1:
            achievements_to_award.append("first_solve")
        elif user.total_problems_solved == 100:
            achievements_to_award.append("hundred_club")
        elif user.total_problems_solved == 500:
            achievements_to_award.append("quincentennial")
        
        # Streak achievements
        if user.current_streak == 7:
            achievements_to_award.append("streak_7")
        elif user.current_streak == 30:
            achievements_to_award.append("streak_30")
        elif user.current_streak == 100:
            achievements_to_award.append("streak_100")
        
        # Topic mastery achievements
        if topic == "NGP":
            topic_stats = db.query(TopicStatistics).filter(
                and_(TopicStatistics.user_id == user_id, TopicStatistics.topic == "NGP")
            ).first()
            if topic_stats and topic_stats.accuracy == 100 and topic_stats.problems_attempted >= 10:
                achievements_to_award.append("ngp_master")
        
        # Award new achievements
        for ach_code in achievements_to_award:
            existing = db.query(UserAchievement).filter(
                and_(
                    UserAchievement.user_id == user_id, 
                    UserAchievement.achievement_code == ach_code
                )
            ).first()
            
            if not existing:
                achievement = UserAchievement(
                    user_id=user_id,
                    achievement_code=ach_code
                )
                db.add(achievement)
                logger.info(f"🏆 Achievement unlocked for user {user_id}: {ach_code}")
    
    # ========================================================================
    # ANALYTICS & INSIGHTS
    # ========================================================================
    
    def get_user_weaknesses(
        self, 
        user_id: int, 
        threshold: float = 70.0
    ) -> List[Dict[str, Any]]:
        """
        Identify topics where user struggles (accuracy < threshold).
        
        Args:
            user_id: User ID
            threshold: Accuracy threshold (default 70%)
        
        Returns:
            List of weakness dicts with topic, accuracy, recommendations
        """
        with get_db_session() as db:
            stats = db.query(TopicStatistics).filter(
                and_(
                    TopicStatistics.user_id == user_id,
                    TopicStatistics.accuracy < threshold,
                    TopicStatistics.problems_attempted >= 3
                )
            ).order_by(TopicStatistics.accuracy.asc()).all()
            
            weaknesses: List[Dict[str, Any]] = []
            for s in stats:
                weaknesses.append({
                    "topic": s.topic,
                    "accuracy": round(s.accuracy, 1),
                    "problems_solved": s.problems_attempted,
                    "mastery": round(s.mastery_level * 100, 1),
                    "last_practiced": s.last_practiced.isoformat() if s.last_practiced else None,
                    "recommendation": self._get_weakness_recommendation(s)
                })
            
            return weaknesses
    
    def _get_weakness_recommendation(self, stats: TopicStatistics) -> str:
        """Generate personalized recommendation for weakness."""
        if stats.accuracy < 50:
            return f"Review fundamentals. Try /flashcard {stats.topic}"
        elif stats.accuracy < 70:
            return f"Practice more problems. Use /practice {stats.topic}"
        else:
            return "Almost there! Focus on tricky edge cases."
    
    def get_performance_over_time(
        self, 
        user_id: int, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get user's performance trend over time period.
        
        Args:
            user_id: User ID
            days: Number of days to analyze
        
        Returns:
            Dict with dates, accuracies, and overall stats
        """
        with get_db_session() as db:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            problems = db.query(ProblemSolved).filter(
                and_(
                    ProblemSolved.user_id == user_id,
                    ProblemSolved.timestamp >= cutoff
                )
            ).order_by(ProblemSolved.timestamp.asc()).all()
            
            if not problems:
                return {"message": "No data for this period"}
            
            # Group by date
            daily_stats: Dict[Any, Dict[str, int]] = {}
            for p in problems:
                date_key = p.timestamp.date()
                if date_key not in daily_stats:
                    daily_stats[date_key] = {"total": 0, "correct": 0}
                daily_stats[date_key]["total"] += 1
                if p.is_correct:
                    daily_stats[date_key]["correct"] += 1
            
            # Calculate daily accuracy
            dates = []
            accuracies = []
            for date in sorted(daily_stats.keys()):
                dates.append(date.isoformat())
                accuracy = (daily_stats[date]["correct"] / daily_stats[date]["total"]) * 100
                accuracies.append(round(accuracy, 1))
            
            total_correct = sum(1 for p in problems if p.is_correct)
            overall_accuracy = (total_correct / len(problems)) * 100
            
            return {
                "dates": dates,
                "accuracies": accuracies,
                "total_problems": len(problems),
                "total_correct": total_correct,
                "overall_accuracy": round(overall_accuracy, 1)
            }
    
    def get_topic_breakdown(self, user_id: int) -> Dict[str, List[Any]]:
        """
        Get breakdown of problems by topic.
        
        Returns:
            Dict with parallel lists of topics, solved counts, correct counts, accuracies
        """
        with get_db_session() as db:
            stats = db.query(TopicStatistics).filter(
                TopicStatistics.user_id == user_id
            ).all()
            
            topics = []
            solved = []
            correct = []
            accuracies = []
            
            for s in stats:
                topics.append(s.topic)
                solved.append(s.problems_attempted)
                correct.append(s.problems_correct)
                accuracies.append(round(s.accuracy, 1))
            
            return {
                "topics": topics,
                "solved": solved,
                "correct": correct,
                "accuracies": accuracies
            }
    
    def compare_to_peers(self, user_id: int, topic: str) -> Dict[str, Any]:
        """
        Compare user's performance to all users on a topic.
        
        Args:
            user_id: User ID
            topic: Topic to compare
        
        Returns:
            Dict with percentile ranking and comparison data
        """
        with get_db_session() as db:
            user_stats = db.query(TopicStatistics).filter(
                and_(TopicStatistics.user_id == user_id, TopicStatistics.topic == topic)
            ).first()
            
            if not user_stats:
                return {"message": f"No data for {topic}"}
            
            # Get all users' stats for this topic
            all_stats = db.query(TopicStatistics).filter(
                TopicStatistics.topic == topic
            ).all()
            
            if len(all_stats) < 2:
                return {"message": "Not enough data for comparison"}
            
            # Calculate percentiles
            accuracies = [s.accuracy for s in all_stats]
            user_percentile = (sum(1 for a in accuracies if a < user_stats.accuracy) / len(accuracies)) * 100
            
            avg_accuracy = float(np.mean(accuracies))
            
            return {
                "your_accuracy": round(user_stats.accuracy, 1),
                "average_accuracy": round(avg_accuracy, 1),
                "percentile": round(user_percentile, 0),
                "total_students": len(all_stats),
                "difference": round(user_stats.accuracy - avg_accuracy, 1)
            }
    
    def detect_error_patterns(
        self, 
        user_id: int, 
        topic: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Detect common error patterns for a user in a topic.
        
        Args:
            user_id: User ID
            topic: Topic to analyze
            limit: Max recent problems to analyze
        
        Returns:
            List of error patterns with frequency and advice
        """
        with get_db_session() as db:
            incorrect_problems = db.query(ProblemSolved).filter(
                and_(
                    ProblemSolved.user_id == user_id,
                    ProblemSolved.topic == topic,
                    ProblemSolved.is_correct == False
                )
            ).order_by(ProblemSolved.timestamp.desc()).limit(limit).all()
            
            error_types: Dict[str, int] = {}
            for p in incorrect_problems:
                if p.error_type:
                    error_types[p.error_type] = error_types.get(p.error_type, 0) + 1
            
            patterns: List[Dict[str, Any]] = []
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                patterns.append({
                    "error_type": error_type,
                    "frequency": count,
                    "advice": self._get_error_advice(error_type)
                })
            
            return patterns
    
    def _get_error_advice(self, error_type: str) -> str:
        """Get targeted advice for common error types."""
        advice_map = {
            "ngp_distance": "⚠️ Remember: NGP only works within 2-3 atoms!",
            "rate_law_confusion": "📝 SN1 = k[RX], SN2 = k[Nu][RX]",
            "stereochemistry": "🔄 SN2 = Inversion (180°), SN1 = Racemization",
            "mechanism_selection": "🎯 Check substrate: 1° → SN2, 3° → SN1, 2° → check NGP!"
        }
        return advice_map.get(error_type, "Review the concept and try more practice problems")
    
    # ========================================================================
    # LEADERBOARDS
    # ========================================================================
    
    def update_leaderboards(self) -> None:
        """Update all leaderboard categories (daily, weekly, all-time)."""
        with get_db_session() as db:
            try:
                self._update_daily_leaderboard(db)
                self._update_weekly_leaderboard(db)
                self._update_alltime_leaderboard(db)
                logger.info("✅ Leaderboards updated successfully")
            except Exception as e:
                logger.error(f"Error updating leaderboards: {e}", exc_info=True)
                raise
    
    def _update_daily_leaderboard(self, db: Session) -> None:
        """Update daily leaderboard (resets at midnight UTC)."""
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        # Get today's top performers
        top_users = db.query(
            ProblemSolved.user_id,
            func.count(ProblemSolved.id).label('problems_solved'),
            func.sum(func.case((ProblemSolved.is_correct == True, 1), else_=0)).label('correct')
        ).filter(
            ProblemSolved.timestamp >= today_start
        ).group_by(ProblemSolved.user_id).order_by(
            func.count(ProblemSolved.id).desc()
        ).limit(100).all()
        
        # Clear old daily leaderboard
        db.query(Leaderboard).filter(
            and_(Leaderboard.category == 'daily', Leaderboard.period_start == today_start)
        ).delete()
        
        # Add new entries
        for rank, (user_id, solved, correct) in enumerate(top_users, 1):
            entry = Leaderboard(
                user_id=user_id,
                category='daily',
                score=solved * 10 + correct * 5,  # Scoring formula
                rank=rank,
                period_start=today_start,
                period_end=datetime.combine(today, datetime.max.time())
            )
            db.add(entry)
    
    def _update_weekly_leaderboard(self, db: Session) -> None:
        """Update weekly leaderboard (last 7 days)."""
        week_start = datetime.utcnow() - timedelta(days=7)
        
        top_users = db.query(
            ProblemSolved.user_id,
            func.count(ProblemSolved.id).label('problems_solved'),
            func.sum(func.case((ProblemSolved.is_correct == True, 1), else_=0)).label('correct')
        ).filter(
            ProblemSolved.timestamp >= week_start
        ).group_by(ProblemSolved.user_id).order_by(
            func.count(ProblemSolved.id).desc()
        ).limit(100).all()
        
        db.query(Leaderboard).filter(Leaderboard.category == 'weekly').delete()
        
        for rank, (user_id, solved, correct) in enumerate(top_users, 1):
            entry = Leaderboard(
                user_id=user_id,
                category='weekly',
                score=solved * 10 + correct * 5,
                rank=rank,
                period_start=week_start,
                period_end=datetime.utcnow()
            )
            db.add(entry)
    
    def _update_alltime_leaderboard(self, db: Session) -> None:
        """Update all-time leaderboard (total score ranking)."""
        top_users = db.query(User).order_by(User.total_score.desc()).limit(100).all()
        
        db.query(Leaderboard).filter(Leaderboard.category == 'all_time').delete()
        
        for rank, user in enumerate(top_users, 1):
            entry = Leaderboard(
                user_id=user.telegram_id,
                category='all_time',
                score=user.total_score,
                rank=rank
            )
            db.add(entry)
    
    def get_leaderboard(
        self, 
        category: str = 'daily', 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard entries for a category.
        
        Args:
            category: 'daily', 'weekly', or 'all_time'
            limit: Number of entries to return
        
        Returns:
            List of leaderboard entries with rank, username, score
        """
        with get_db_session() as db:
            entries = db.query(Leaderboard).filter(
                Leaderboard.category == category
            ).order_by(Leaderboard.rank.asc()).limit(limit).all()
            
            result: List[Dict[str, Any]] = []
            for entry in entries:
                user = db.query(User).filter(User.telegram_id == entry.user_id).first()
                result.append({
                    "rank": entry.rank,
                    "username": user.username if user else "Unknown",
                    "score": entry.score,
                    "user_id": entry.user_id
                })
            
            return result


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

analytics = AnalyticsEngine()
