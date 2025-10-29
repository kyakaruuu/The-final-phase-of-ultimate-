"""
Error Pattern Recognition
Automatically detects common mistakes across all students
Impact: HIGH | Effort: 2 days
"""

import logging
from typing import Dict, List, Set
from collections import Counter
from database import SessionLocal, ProblemSolved, User
from sqlalchemy import func

logger = logging.getLogger(__name__)

class ErrorPatternRecognition:
    """
    Identifies common mistakes students make
    Provides targeted interventions
    """
    
    def __init__(self):
        self.common_error_patterns = {
            "SN1": [
                "carbocation_rearrangement_missed",
                "racemization_forgotten",
                "solvent_effect_ignored",
                "rate_law_incorrect"
            ],
            "SN2": [
                "stereochemistry_inverted_wrong",
                "steric_hindrance_ignored",
                "nucleophile_strength_misjudged",
                "leaving_group_forgotten"
            ],
            "NGP": [
                "distance_miscalculated",
                "rate_enhancement_underestimated",
                "product_formation_wrong",
                "mechanism_path_incorrect"
            ],
            "E1": [
                "zaitsev_violated",
                "carbocation_stability_wrong",
                "temperature_effect_ignored",
                "vs_sn1_confused"
            ],
            "E2": [
                "anti_periplanar_forgotten",
                "hofmann_vs_zaitsev_confused",
                "base_strength_misjudged",
                "syn_elimination_attempted"
            ]
        }
    
    def analyze_student_errors(self, user_id: int, topic: str = None) -> Dict:
        """Analyze what errors a specific student commonly makes"""
        db = SessionLocal()
        try:
            # Get user's incorrect problems
            incorrect_problems = db.query(ProblemSolved).filter(
                ProblemSolved.user_id == user_id,
                ProblemSolved.correct == False
            ).order_by(ProblemSolved.solved_at.desc()).limit(50).all()
            
            if topic:
                incorrect_problems = [p for p in incorrect_problems if p.topic == topic]
            
            # Count error types (would need to extract from problem metadata)
            error_count = Counter()
            for problem in incorrect_problems:
                # In real implementation, we'd parse the specific error type
                # For now, simulate based on topic
                if problem.topic in self.common_error_patterns:
                    # Simulate error detection
                    error_count[problem.topic] += 1
            
            total_errors = sum(error_count.values())
            
            return {
                "total_errors": total_errors,
                "error_breakdown": dict(error_count),
                "most_common_mistake": error_count.most_common(1)[0][0] if error_count else None,
                "error_rate": total_errors / max(len(incorrect_problems), 1)
            }
        except Exception as e:
            logger.error(f"Error analyzing student errors: {e}")
            return {}
        finally:
            db.close()
    
    def get_global_error_patterns(self, topic: str = None) -> Dict:
        """Identify mistakes that MANY students are making"""
        db = SessionLocal()
        try:
            # Get all incorrect problems across all users
            query = db.query(ProblemSolved).filter(
                ProblemSolved.correct == False
            )
            
            if topic:
                query = query.filter(ProblemSolved.topic == topic)
            
            incorrect_problems = query.limit(1000).all()
            
            # Group by topic
            topic_errors = Counter()
            for problem in incorrect_problems:
                topic_errors[problem.topic] += 1
            
            # Calculate error rates
            total_problems = db.query(func.count(ProblemSolved.id)).scalar()
            
            error_rates = {}
            for topic, count in topic_errors.items():
                topic_total = db.query(func.count(ProblemSolved.id)).filter(
                    ProblemSolved.topic == topic
                ).scalar()
                error_rates[topic] = (count / max(topic_total, 1)) * 100
            
            return {
                "most_difficult_topics": topic_errors.most_common(5),
                "error_rates_by_topic": error_rates,
                "total_errors_analyzed": len(incorrect_problems)
            }
        except Exception as e:
            logger.error(f"Error getting global patterns: {e}")
            return {}
        finally:
            db.close()
    
    def generate_error_prevention_tips(self, user_id: int, topic: str) -> List[str]:
        """Generate tips to prevent common errors"""
        errors = self.analyze_student_errors(user_id, topic)
        tips = []
        
        if topic in self.common_error_patterns:
            patterns = self.common_error_patterns[topic]
            
            if topic == "SN1":
                tips.extend([
                    "⚠️ Always check for possible carbocation rearrangements",
                    "🔄 Remember: SN1 leads to racemization (NOT inversion)",
                    "📊 Write the rate law: Rate = k[substrate] (first order)",
                    "💧 Polar protic solvents favor SN1"
                ])
            elif topic == "SN2":
                tips.extend([
                    "🔄 SN2 = Inversion of configuration (Walden inversion)",
                    "⛔ Steric hindrance kills SN2 (methyl > 1° > 2° >> 3°)",
                    "⚡ Strong nucleophile + good leaving group = SN2",
                    "📊 Rate = k[substrate][nucleophile] (second order)"
                ])
            elif topic == "NGP":
                tips.extend([
                    "📏 Neighboring group MUST be 2-3 atoms away",
                    "⚡ NGP gives 100-10000x rate enhancement",
                    "🔄 Look for oxygen, nitrogen, or halogen neighbors",
                    "⚠️ NGP changes the product (bridged intermediate)"
                ])
        
        return tips
    
    def predict_likely_mistakes(self, user_id: int, topic: str, 
                               difficulty: int) -> List[str]:
        """Predict what mistakes user is likely to make"""
        user_errors = self.analyze_student_errors(user_id, topic)
        global_errors = self.get_global_error_patterns(topic)
        
        likely_mistakes = []
        
        # Based on user's history
        if user_errors.get("most_common_mistake"):
            likely_mistakes.append(
                f"⚠️ Watch out! You often miss: {user_errors['most_common_mistake']}"
            )
        
        # Based on problem difficulty
        if difficulty >= 7:
            likely_mistakes.append(
                "🎯 This is a hard problem - common trap: rushing without analyzing all possibilities"
            )
        
        # Based on global patterns
        if topic in global_errors.get("most_difficult_topics", []):
            likely_mistakes.append(
                f"⚠️ {topic} is tricky for many students - take your time"
            )
        
        return likely_mistakes
