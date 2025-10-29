"""
Self-Learning Engine
Bot learns which explanations work best for each student
Impact: MASSIVE | Effort: 3 days
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database import SessionLocal, User, ProblemSolved
from sqlalchemy import func

logger = logging.getLogger(__name__)

class SelfLearningEngine:
    """
    Tracks which explanation styles work best for each user
    Adapts future explanations based on success patterns
    """
    
    def __init__(self):
        self.explanation_styles = [
            "systematic",       # Step-by-step logical approach
            "visual",          # Diagrams and visual aids
            "comparative",     # Compare/contrast with similar concepts
            "real_world",      # Real-world analogies
            "mathematical",    # Heavy math focus
            "conceptual",      # Focus on WHY, not just HOW
            "ms_chouhan",      # MS Chouhan textbook style
            "paula_bruice",    # Paula Bruice textbook style
        ]
    
    def track_explanation_success(self, user_id: int, problem_id: int, 
                                  explanation_style: str, success: bool,
                                  time_taken: int, hints_used: int):
        """Track how well an explanation style worked"""
        db = SessionLocal()
        try:
            # Update problem record with explanation metadata
            problem = db.query(ProblemSolved).filter(
                ProblemSolved.user_id == user_id,
                ProblemSolved.id == problem_id
            ).first()
            
            if problem:
                # Store explanation effectiveness metrics
                effectiveness_score = self._calculate_effectiveness(
                    success, time_taken, hints_used
                )
                
                # Store in problem metadata (assuming we add a JSON column)
                logger.info(f"User {user_id}: {explanation_style} effectiveness = {effectiveness_score}")
                
            return effectiveness_score
        except Exception as e:
            logger.error(f"Error tracking explanation success: {e}")
            return 0
        finally:
            db.close()
    
    def get_best_explanation_style(self, user_id: int, topic: str = None) -> str:
        """Determine which explanation style works best for this user"""
        db = SessionLocal()
        try:
            # Analyze user's historical performance with different styles
            recent_problems = db.query(ProblemSolved).filter(
                ProblemSolved.user_id == user_id
            ).order_by(ProblemSolved.solved_at.desc()).limit(50).all()
            
            if len(recent_problems) < 5:
                # Not enough data, use default
                return "systematic"
            
            # Score each explanation style
            style_scores = {}
            for style in self.explanation_styles:
                style_scores[style] = self._calculate_style_score(
                    recent_problems, style
                )
            
            # Return best performing style
            best_style = max(style_scores, key=style_scores.get)
            logger.info(f"Best style for user {user_id}: {best_style}")
            
            return best_style
        except Exception as e:
            logger.error(f"Error getting best explanation style: {e}")
            return "systematic"
        finally:
            db.close()
    
    def _calculate_effectiveness(self, success: bool, time_taken: int, 
                                 hints_used: int) -> float:
        """Calculate how effective an explanation was"""
        score = 0.0
        
        if success:
            score += 50  # Success is worth 50 points
            
            # Bonus for solving quickly (inversely proportional to time)
            if time_taken < 300:  # Under 5 minutes
                score += 30
            elif time_taken < 600:  # Under 10 minutes
                score += 20
            elif time_taken < 1200:  # Under 20 minutes
                score += 10
            
            # Bonus for not using hints
            if hints_used == 0:
                score += 20
            elif hints_used == 1:
                score += 10
            elif hints_used == 2:
                score += 5
        
        return score
    
    def _calculate_style_score(self, problems: List, style: str) -> float:
        """Calculate average score for a particular explanation style"""
        # In real implementation, we'd track style per problem
        # For now, we'll use problem characteristics to infer style effectiveness
        
        # Placeholder scoring logic
        total_score = 0
        count = 0
        
        for problem in problems:
            if problem.correct:
                total_score += 1
                count += 1
        
        return total_score / max(count, 1)
    
    def get_learning_insights(self, user_id: int) -> Dict:
        """Get insights about how the user learns best"""
        db = SessionLocal()
        try:
            best_style = self.get_best_explanation_style(user_id)
            
            # Get user's problem-solving patterns
            problems = db.query(ProblemSolved).filter(
                ProblemSolved.user_id == user_id
            ).order_by(ProblemSolved.solved_at.desc()).limit(100).all()
            
            total_problems = len(problems)
            correct_problems = sum(1 for p in problems if p.correct)
            accuracy = (correct_problems / total_problems * 100) if total_problems > 0 else 0
            
            # Average time per problem
            avg_time = sum(p.time_taken for p in problems if p.time_taken) / max(len([p for p in problems if p.time_taken]), 1)
            
            return {
                "best_explanation_style": best_style,
                "total_problems": total_problems,
                "accuracy": accuracy,
                "avg_time_minutes": avg_time / 60,
                "learning_recommendations": self._generate_recommendations(
                    best_style, accuracy, avg_time
                )
            }
        except Exception as e:
            logger.error(f"Error getting learning insights: {e}")
            return {}
        finally:
            db.close()
    
    def _generate_recommendations(self, style: str, accuracy: float, 
                                  avg_time: float) -> List[str]:
        """Generate personalized learning recommendations"""
        recommendations = []
        
        if style == "visual":
            recommendations.append("📊 You learn best with diagrams and visual aids. I'll include more reaction mechanisms and molecular visualizations.")
        elif style == "systematic":
            recommendations.append("📝 You prefer step-by-step logical approaches. I'll break down solutions into clear sequential steps.")
        elif style == "conceptual":
            recommendations.append("🧠 You grasp concepts deeply when you understand WHY. I'll focus on fundamental principles.")
        
        if accuracy < 50:
            recommendations.append("💪 Your accuracy is building up. Let's focus on foundational concepts before tackling harder problems.")
        elif accuracy > 80:
            recommendations.append("🎯 Excellent accuracy! You're ready for JEE Advanced level challenge problems.")
        
        if avg_time > 1200:  # >20 minutes per problem
            recommendations.append("⚡ Let's work on solving speed. I'll give you time-saving tricks and shortcuts.")
        
        return recommendations
