"""
Advanced Analytics Features (4 features):
1. Strength/Weakness Heatmap
2. Comparative Analytics
3. Prediction Model
4. JEE Rank Predictor
Impact: HIGH-VERY HIGH
"""

import logging
from typing import Dict, List
from database import SessionLocal, User, ProblemSolved
from sqlalchemy import func
import json

logger = logging.getLogger(__name__)

class HeatmapGenerator:
    """Visual heatmap of strengths/weaknesses"""
    
    def generate_heatmap_data(self, user_id: int) -> Dict:
        """Create heatmap data structure"""
        db = SessionLocal()
        try:
            problems = db.query(ProblemSolved).filter(
                ProblemSolved.user_id == user_id
            ).all()
            
            # Group by topic
            topic_stats = {}
            for problem in problems:
                topic = problem.topic
                if topic not in topic_stats:
                    topic_stats[topic] = {"correct": 0, "total": 0}
                topic_stats[topic]["total"] += 1
                if problem.correct:
                    topic_stats[topic]["correct"] += 1
            
            # Calculate accuracy percentages
            heatmap = {}
            for topic, stats in topic_stats.items():
                accuracy = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
                heatmap[topic] = {
                    "accuracy": accuracy,
                    "color": "green" if accuracy >= 75 else "yellow" if accuracy >= 50 else "red",
                    "problems_solved": stats["total"]
                }
            
            return heatmap
        finally:
            db.close()


class ComparativeAnalytics:
    """Compare user to averages"""
    
    def get_comparative_report(self, user_id: int) -> Dict:
        """Show how user compares to average"""
        db = SessionLocal()
        try:
            # User stats
            user_problems = db.query(ProblemSolved).filter(
                ProblemSolved.user_id == user_id
            ).all()
            
            user_accuracy = sum(1 for p in user_problems if p.correct) / max(len(user_problems), 1)
            
            # Global average
            global_accuracy = db.query(
                func.avg(func.cast(ProblemSolved.correct, type_=db.Integer))
            ).scalar() or 0.5
            
            return {
                "your_accuracy": user_accuracy * 100,
                "average_accuracy": global_accuracy * 100,
                "percentile": 65,  # Simplified
                "comparison": f"{'above' if user_accuracy > global_accuracy else 'below'} average"
            }
        finally:
            db.close()


class PerformancePredictor:
    """Predicts future performance"""
    
    def predict_mastery_time(self, user_id: int, topic: str) -> Dict:
        """Estimate when user will master topic"""
        db = SessionLocal()
        try:
            recent_problems = db.query(ProblemSolved).filter(
                ProblemSolved.user_id == user_id,
                ProblemSolved.topic == topic
            ).order_by(ProblemSolved.solved_at.desc()).limit(10).all()
            
            if len(recent_problems) < 3:
                return {"message": "Need more data"}
            
            # Simple trend analysis
            accuracy = sum(1 for p in recent_problems if p.correct) / len(recent_problems)
            
            if accuracy >= 0.85:
                days_to_mastery = 0
                message = f"✅ You've mastered {topic}!"
            elif accuracy >= 0.7:
                days_to_mastery = 3
                message = f"📈 At current pace, you'll master {topic} in ~{days_to_mastery} days"
            else:
                days_to_mastery = 7
                message = f"💪 Keep practicing! Estimated {days_to_mastery} days to master {topic}"
            
            return {"days_to_mastery": days_to_mastery, "message": message, "current_accuracy": accuracy * 100}
        finally:
            db.close()


class JEERankPredictor:
    """Predicts JEE rank based on performance"""
    
    def predict_jee_rank(self, user_id: int) -> Dict:
        """Estimate potential JEE rank"""
        db = SessionLocal()
        try:
            problems = db.query(ProblemSolved).filter(
                ProblemSolved.user_id == user_id
            ).all()
            
            total = len(problems)
            correct = sum(1 for p in problems if p.correct)
            accuracy = (correct / total * 100) if total > 0 else 0
            
            # Simplified prediction model
            if accuracy >= 90:
                predicted_rank = "Under 1000 (IIT Bombay CS possible!)"
            elif accuracy >= 80:
                predicted_rank = "1000-5000 (Top IITs possible)"
            elif accuracy >= 70:
                predicted_rank = "5000-15000 (Good IITs/NITs)"
            elif accuracy >= 60:
                predicted_rank = "15000-30000 (NITs possible)"
            else:
                predicted_rank = "Need to improve (30000+)"
            
            return {
                "predicted_rank": predicted_rank,
                "accuracy": accuracy,
                "problems_solved": total,
                "recommendation": "Focus on weak topics to improve rank"
            }
        finally:
            db.close()
