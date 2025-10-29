"""
Cognitive Load Detection + Predictive Intervention + Socratic Mode
Detects when student is tired/frustrated, adjusts difficulty
Warns students BEFORE they make mistakes
Bot asks questions instead of giving answers
Impact: MEDIUM-VERY HIGH | Effort: 3-4 days
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database import SessionLocal, User, ProblemSolved, Session
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

class CognitiveLoadDetector:
    """Detects student mental state and adjusts accordingly"""
    
    def __init__(self):
        self.fatigue_indicators = {
            "increased_error_rate": 0.3,
            "slower_response_time": 0.4,
            "more_hints_needed": 0.2,
            "giving_up_quickly": 0.1
        }
    
    def detect_cognitive_state(self, user_id: int) -> Dict:
        """Analyze if student is tired, frustrated, or in flow state"""
        db = SessionLocal()
        try:
            # Get recent activity (last 30 minutes)
            recent_cutoff = datetime.utcnow() - timedelta(minutes=30)
            recent_problems = db.query(ProblemSolved).filter(
                and_(
                    ProblemSolved.user_id == user_id,
                    ProblemSolved.solved_at >= recent_cutoff
                )
            ).order_by(ProblemSolved.solved_at.desc()).all()
            
            if len(recent_problems) < 3:
                return {"state": "insufficient_data", "confidence": 0}
            
            # Calculate fatigue indicators
            recent_accuracy = sum(1 for p in recent_problems if p.correct) / len(recent_problems)
            avg_time = sum(p.time_taken for p in recent_problems if p.time_taken) / max(len([p for p in recent_problems if p.time_taken]), 1)
            
            # Compare with user's baseline
            baseline = self._get_baseline_performance(db, user_id)
            
            # Determine state
            if recent_accuracy < baseline["accuracy"] * 0.6:
                state = "fatigued"
                confidence = 0.8
            elif recent_accuracy > baseline["accuracy"] * 1.2 and avg_time < baseline["avg_time"] * 0.8:
                state = "flow"
                confidence = 0.9
            elif recent_accuracy < baseline["accuracy"] * 0.8:
                state = "struggling"
                confidence = 0.7
            else:
                state = "normal"
                confidence = 0.6
            
            return {
                "state": state,
                "confidence": confidence,
                "recent_accuracy": recent_accuracy,
                "baseline_accuracy": baseline["accuracy"],
                "suggestion": self._get_adjustment_suggestion(state)
            }
        except Exception as e:
            logger.error(f"Error detecting cognitive state: {e}")
            return {"state": "error", "confidence": 0}
        finally:
            db.close()
    
    def _get_baseline_performance(self, db, user_id: int) -> Dict:
        """Get user's normal performance baseline"""
        baseline_problems = db.query(ProblemSolved).filter(
            ProblemSolved.user_id == user_id
        ).order_by(ProblemSolved.solved_at.desc()).limit(50).all()
        
        if not baseline_problems:
            return {"accuracy": 0.5, "avg_time": 600}
        
        accuracy = sum(1 for p in baseline_problems if p.correct) / len(baseline_problems)
        avg_time = sum(p.time_taken for p in baseline_problems if p.time_taken) / max(len([p for p in baseline_problems if p.time_taken]), 1)
        
        return {"accuracy": accuracy, "avg_time": avg_time}
    
    def _get_adjustment_suggestion(self, state: str) -> str:
        """Suggest what to do based on cognitive state"""
        suggestions = {
            "fatigued": "😴 You seem tired. Take a 10-minute break or try easier problems to rebuild confidence.",
            "struggling": "💪 This topic seems challenging. Let's review fundamentals or try a different approach.",
            "flow": "🔥 You're in the zone! Let's tackle some harder problems while you're sharp.",
            "normal": "✅ Steady progress! Keep going at your pace."
        }
        return suggestions.get(state, "Keep learning!")


class PredictiveIntervention:
    """Warns students BEFORE they make mistakes"""
    
    def __init__(self):
        self.error_predictor = CognitiveLoadDetector()
    
    def predict_and_warn(self, user_id: int, topic: str, difficulty: int) -> List[str]:
        """Predict likely mistakes and warn preemptively"""
        warnings = []
        
        # Check cognitive state
        state = self.error_predictor.detect_cognitive_state(user_id)
        if state["state"] == "fatigued":
            warnings.append("⚠️ You've been studying for a while - this might be a good time for a short break!")
        
        # Get user's weak areas
        db = SessionLocal()
        try:
            weak_topics = db.query(
                ProblemSolved.topic,
                func.avg(func.cast(ProblemSolved.correct, type_=db.Integer)).label('accuracy')
            ).filter(
                ProblemSolved.user_id == user_id
            ).group_by(ProblemSolved.topic).all()
            
            weak_dict = {topic: float(acc) for topic, acc in weak_topics}
            
            if topic in weak_dict and weak_dict[topic] < 0.5:
                warnings.append(f"📊 Heads up! Your accuracy in {topic} is {weak_dict[topic]*100:.0f}%. Take extra care.")
            
            if difficulty >= 8:
                warnings.append("🎯 This is a JEE Advanced level problem - don't rush, check each step carefully!")
            
            return warnings
        except Exception as e:
            logger.error(f"Error predicting intervention: {e}")
            return []
        finally:
            db.close()


class SocraticDialogueMode:
    """Bot asks questions instead of giving direct answers"""
    
    def __init__(self):
        self.question_templates = {
            "SN1": [
                "What type of carbocation would form here? Is it stable?",
                "Is this substrate likely to undergo rearrangement? Why?",
                "What's the rate-determining step in SN1?",
                "Will the product be racemic or optically active?"
            ],
            "SN2": [
                "Can the nucleophile attack from the backside here?",
                "What's the stereochemistry of the product?",
                "Is there steric hindrance preventing SN2?",
                "Compare the nucleophile strength - which is stronger?"
            ],
            "NGP": [
                "Is there a neighboring group 2-3 atoms away?",
                "Can this group donate electrons to stabilize the carbocation?",
                "How much faster will this reaction be with NGP?",
                "What will the product structure look like with the bridged intermediate?"
            ]
        }
    
    def generate_socratic_questions(self, topic: str, difficulty: int, 
                                   problem_context: str = None) -> List[str]:
        """Generate thought-provoking questions instead of answers"""
        questions = []
        
        # Get topic-specific questions
        if topic in self.question_templates:
            # Select questions based on difficulty
            all_questions = self.question_templates[topic]
            num_questions = min(difficulty // 2, len(all_questions))
            questions = all_questions[:num_questions]
        
        # Add meta-cognitive questions
        questions.extend([
            "What concept is being tested here?",
            "What are the key factors that determine the mechanism?",
            "What would change if we modified the structure slightly?"
        ])
        
        return questions
    
    def provide_guided_hint(self, topic: str, hint_level: int = 1) -> str:
        """Provide hints as questions, not answers"""
        hints = {
            "SN1": {
                1: "💭 Think: What forms first in SN1? (Hint: it's a charged species)",
                2: "🤔 After the carbocation forms, what attacks it? From which side?",
                3: "💡 Remember: SN1 → Carbocation → Racemic mixture (usually)"
            },
            "SN2": {
                1: "💭 Think: Where does the nucleophile attack? (Front or back?)",
                2: "🤔 What happens to the stereochemistry during backside attack?",
                3: "💡 Remember: SN2 → Backside attack → Inversion of configuration"
            },
            "NGP": {
                1: "💭 Think: Is there an atom nearby that can help stabilize the intermediate?",
                2: "🤔 How far away should the neighboring group be? (Count atoms)",
                3: "💡 Remember: NGP → Bridged intermediate → Unusual products + rate boost"
            }
        }
        
        if topic in hints and hint_level in hints[topic]:
            return hints[topic][hint_level]
        
        return "💭 Take your time. What do you notice about the structure that might be important?"
