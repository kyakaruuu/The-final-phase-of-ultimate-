"""
Self-Learning Engine & Error Pattern Recognition
=================================================

Adaptive teaching strategies that learn what works for each student.
Production-ready with type hints, context management, and Railway optimization.

Features:
- Explanation effectiveness tracking
- Learning style detection (visual/verbal/kinesthetic)
- Error pattern recognition across all users
- Predictive intervention
- JEE exam trap cataloging
- Personalized teaching adaptation

Author: Enhanced for JEE Advanced Chemistry Bot
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from database import (
    SessionLocal, ExplanationEffectiveness, ErrorPattern,
    ProblemSolved, TopicStatistics, User,
    get_db_session
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# SELF-LEARNING ENGINE
# ============================================================================

class SelfLearningEngine:
    """
    Tracks explanation effectiveness and adapts teaching strategies.
    
    Core Features:
    - Tracks which explanation styles work for each user
    - Detects individual learning styles
    - Provides personalized teaching recommendations
    - Uses Bayesian statistics for robust effectiveness scores
    """
    
    def __init__(self) -> None:
        """Initialize self-learning engine with explanation strategies."""
        # Available explanation strategies
        self.strategies: Dict[str, str] = {
            "systematic": "Step-by-step systematic breakdown",
            "chouhan": "MS Chouhan one-key-difference method",
            "bruice": "Paula Bruice deep orbital analysis",
            "socratic": "Question-guided Socratic dialogue",
            "visual": "Visual diagrams and molecule models",
            "analogy": "Real-world analogies and comparisons"
        }
        
        logger.info("✅ Self-Learning Engine initialized")
    
    # ========================================================================
    # EXPLANATION TRACKING
    # ========================================================================
    
    def track_explanation(
        self, 
        user_id: int, 
        topic: str, 
        strategy: str, 
        understood: bool
    ) -> float:
        """
        Track whether a particular explanation strategy worked.
        
        Uses Bayesian averaging to calculate robust effectiveness scores
        even with limited data.
        
        Args:
            user_id: Student ID
            topic: Topic explained
            strategy: Which strategy was used
            understood: Whether student solved similar problem after
        
        Returns:
            float: Effectiveness score (0-1)
        """
        with get_db_session() as db:
            try:
                # Find or create effectiveness record
                record = db.query(ExplanationEffectiveness).filter(
                    and_(
                        ExplanationEffectiveness.user_id == user_id,
                        ExplanationEffectiveness.topic == topic,
                        ExplanationEffectiveness.explanation_type == strategy
                    )
                ).first()
                
                if not record:
                    record = ExplanationEffectiveness(
                        user_id=user_id,
                        topic=topic,
                        explanation_type=strategy
                    )
                    db.add(record)
                
                # Update metrics
                record.times_shown += 1
                if understood:
                    record.times_understood += 1
                else:
                    record.times_not_understood += 1
                
                # Calculate effectiveness using Bayesian average
                # Prior belief: α=2 (successes), β=2 (failures)
                alpha, beta = 2, 2
                successes = record.times_understood + alpha
                failures = record.times_not_understood + beta
                record.effectiveness_score = successes / (successes + failures)
                
                logger.info(
                    f"📊 Explanation tracking: {strategy} for {topic} "
                    f"(effectiveness: {record.effectiveness_score:.2f})"
                )
                
                return record.effectiveness_score
            
            except Exception as e:
                logger.error(f"Error tracking explanation: {e}", exc_info=True)
                return 0.5  # Neutral score on error
    
    def get_best_strategy(self, user_id: int, topic: str) -> str:
        """
        Determine which explanation strategy works best for this user/topic.
        
        Args:
            user_id: User ID
            topic: Topic to explain
        
        Returns:
            str: Best strategy name (or default if insufficient data)
        """
        with get_db_session() as db:
            records = db.query(ExplanationEffectiveness).filter(
                and_(
                    ExplanationEffectiveness.user_id == user_id,
                    ExplanationEffectiveness.topic == topic,
                    ExplanationEffectiveness.times_shown >= 2  # Minimum data requirement
                )
            ).order_by(ExplanationEffectiveness.effectiveness_score.desc()).all()
            
            if records:
                best = records[0]
                logger.info(
                    f"🎯 Best strategy for {topic}: {best.explanation_type} "
                    f"({best.effectiveness_score:.2f} effectiveness)"
                )
                return best.explanation_type
            
            # Insufficient data - use learning style preference
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user and user.learning_style == 'visual':
                return 'visual'
            elif user and user.learning_style == 'verbal':
                return 'systematic'
            else:
                return 'systematic'  # Default fallback
    
    # ========================================================================
    # LEARNING STYLE DETECTION
    # ========================================================================
    
    def detect_learning_style(self, user_id: int) -> str:
        """
        Automatically detect user's learning style based on strategy effectiveness.
        
        Classification:
        - Visual: High effectiveness with visual/analogy strategies
        - Verbal: High effectiveness with socratic/systematic strategies
        - Kinesthetic: Mixed or unclear patterns
        
        Args:
            user_id: User ID
        
        Returns:
            str: 'visual', 'verbal', 'kinesthetic', or 'unknown'
        """
        with get_db_session() as db:
            records = db.query(ExplanationEffectiveness).filter(
                and_(
                    ExplanationEffectiveness.user_id == user_id,
                    ExplanationEffectiveness.times_shown >= 3  # Minimum data
                )
            ).all()
            
            if not records or len(records) < 3:
                return 'unknown'
            
            # Calculate average effectiveness by strategy type
            strategy_scores: Dict[str, List[float]] = {}
            for record in records:
                if record.explanation_type not in strategy_scores:
                    strategy_scores[record.explanation_type] = []
                strategy_scores[record.explanation_type].append(record.effectiveness_score)
            
            avg_scores = {k: sum(v)/len(v) for k, v in strategy_scores.items()}
            
            # Classify learning style based on high-performing strategies
            if avg_scores.get('visual', 0) > 0.7 or avg_scores.get('analogy', 0) > 0.7:
                style = 'visual'
            elif avg_scores.get('socratic', 0) > 0.7 or avg_scores.get('systematic', 0) > 0.7:
                style = 'verbal'
            else:
                style = 'kinesthetic'
            
            # Update user profile
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.learning_style = style
            
            logger.info(f"🧠 Detected learning style for user {user_id}: {style}")
            return style


# ============================================================================
# ERROR PATTERN RECOGNIZER
# ============================================================================

class ErrorPatternRecognizer:
    """
    Identifies and catalogs common error patterns across all users.
    
    Features:
    - Global error pattern tracking
    - User-specific error analysis
    - Predictive intervention
    - JEE exam trap cataloging
    """
    
    def __init__(self) -> None:
        """Initialize error pattern recognizer with taxonomy."""
        # Comprehensive error taxonomy for organic chemistry
        self.error_taxonomy: Dict[str, str] = {
            "ngp_distance": "NGP participants too far (>3 atoms)",
            "ngp_missed": "Overlooked available NGP",
            "rate_law": "Confused SN1/SN2 rate laws",
            "stereochemistry": "Wrong stereochemical outcome",
            "mechanism_choice": "Selected wrong mechanism",
            "carbocation_stability": "Misjudged carbocation stability",
            "nucleophile_strength": "Wrong nucleophile strength ranking",
            "leaving_group": "Incorrect leaving group assessment",
            "solvent_effect": "Ignored solvent polarity effects",
            "temperature": "Misapplied temperature effects"
        }
        
        logger.info("✅ Error Pattern Recognizer initialized")
    
    # ========================================================================
    # ERROR RECORDING
    # ========================================================================
    
    def record_error(
        self, 
        user_id: int, 
        topic: str, 
        error_type: str, 
        problem_id: Optional[int] = None
    ) -> None:
        """
        Record a specific error pattern globally.
        
        Args:
            user_id: User who made the error
            topic: Topic of the error
            error_type: Error classification
            problem_id: Optional problem ID for examples
        """
        with get_db_session() as db:
            try:
                # Find or create global error pattern
                global_pattern = db.query(ErrorPattern).filter(
                    and_(
                        ErrorPattern.topic == topic,
                        ErrorPattern.error_type == error_type
                    )
                ).first()
                
                if not global_pattern:
                    global_pattern = ErrorPattern(
                        topic=topic,
                        error_type=error_type,
                        description=self.error_taxonomy.get(error_type, "Unknown error"),
                        frequency=0,
                        example_problems=[]
                    )
                    db.add(global_pattern)
                
                # Update frequency and examples
                global_pattern.frequency += 1
                global_pattern.last_seen = datetime.utcnow()
                
                if problem_id and problem_id not in (global_pattern.example_problems or []):
                    if not global_pattern.example_problems:
                        global_pattern.example_problems = []
                    global_pattern.example_problems.append(problem_id)
                
                logger.info(
                    f"📝 Error recorded: {error_type} in {topic} "
                    f"(global frequency: {global_pattern.frequency})"
                )
            
            except Exception as e:
                logger.error(f"Error recording pattern: {e}", exc_info=True)
    
    # ========================================================================
    # ERROR ANALYSIS
    # ========================================================================
    
    def get_common_errors(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get most common errors for a topic across all users.
        
        Args:
            topic: Topic to analyze
            limit: Max errors to return
        
        Returns:
            List of error dicts with type, frequency, and advice
        """
        with get_db_session() as db:
            patterns = db.query(ErrorPattern).filter(
                ErrorPattern.topic == topic
            ).order_by(ErrorPattern.frequency.desc()).limit(limit).all()
            
            errors: List[Dict[str, Any]] = []
            for p in patterns:
                errors.append({
                    "error_type": p.error_type,
                    "description": p.description,
                    "frequency": p.frequency,
                    "advice": self._get_prevention_advice(p.error_type)
                })
            
            return errors
    
    def _get_prevention_advice(self, error_type: str) -> str:
        """
        Get targeted prevention advice for error types.
        
        Args:
            error_type: Error classification
        
        Returns:
            str: Prevention advice
        """
        advice = {
            "ngp_distance": "⚠️ Always count atoms! NGP only works within 2-3 atoms.",
            "ngp_missed": "🔍 Check ALL atoms near leaving group for lone pairs or π bonds!",
            "rate_law": "📝 Remember: SN1 = k[RX], SN2 = k[Nu][RX]",
            "stereochemistry": "🔄 SN2 = 100% inversion (180°), SN1 = racemization (50/50)",
            "mechanism_choice": "🎯 1° substrate → SN2, 3° → SN1, 2° → check for NGP!",
            "carbocation_stability": "➕ Stability: 3° > 2° > 1° > methyl (hyperconjugation!)",
            "nucleophile_strength": "💪 Stronger nucleophile favors SN2",
            "leaving_group": "🚪 Better leaving group = weaker base (I⁻ > Br⁻ > Cl⁻)",
            "solvent_effect": "🌊 Polar protic → SN1, Polar aprotic → SN2",
            "temperature": "🌡️ Higher temp → more SN1 (entropy favored)"
        }
        return advice.get(error_type, "Review the concept carefully")
    
    # ========================================================================
    # PREDICTIVE INTERVENTION
    # ========================================================================
    
    def predict_likely_error(self, user_id: int, topic: str) -> Dict[str, Any]:
        """
        Predict what error user is likely to make for predictive intervention.
        
        Analyzes user's recent error history and compares with global patterns.
        
        Args:
            user_id: User ID
            topic: Topic to predict for
        
        Returns:
            Dict with likely error, frequency, and warning
        """
        with get_db_session() as db:
            # Get user's recent errors on this topic (last 30 days)
            recent_problems = db.query(ProblemSolved).filter(
                and_(
                    ProblemSolved.user_id == user_id,
                    ProblemSolved.topic == topic,
                    ProblemSolved.is_correct == False,
                    ProblemSolved.timestamp >= datetime.utcnow() - timedelta(days=30)
                )
            ).order_by(ProblemSolved.timestamp.desc()).limit(10).all()
            
            if not recent_problems:
                return {"message": "No error history for this topic"}
            
            # Count error types
            error_counts: Dict[str, int] = {}
            for p in recent_problems:
                if p.error_type:
                    error_counts[p.error_type] = error_counts.get(p.error_type, 0) + 1
            
            if not error_counts:
                return {"message": "No categorized errors"}
            
            # Most common user error
            common_error = max(error_counts.items(), key=lambda x: x[1])
            
            # Get global frequency for context
            global_pattern = db.query(ErrorPattern).filter(
                and_(
                    ErrorPattern.topic == topic,
                    ErrorPattern.error_type == common_error[0]
                )
            ).first()
            
            return {
                "likely_error": common_error[0],
                "description": self.error_taxonomy.get(common_error[0], "Unknown"),
                "user_frequency": common_error[1],
                "global_frequency": global_pattern.frequency if global_pattern else 0,
                "warning": self._get_prevention_advice(common_error[0]),
                "is_common_trap": (global_pattern and global_pattern.frequency > 20)
            }
    
    # ========================================================================
    # JEE EXAM TRAPS
    # ========================================================================
    
    def get_jee_traps(self, topic: str) -> List[str]:
        """
        Get common JEE exam traps and tricks for a topic.
        
        Based on historical JEE Advanced patterns.
        
        Args:
            topic: Chemistry topic
        
        Returns:
            List of common exam traps
        """
        traps: Dict[str, List[str]] = {
            "SN1": [
                "Carbocation rearrangement (hydride/methyl shift)",
                "Racemization vs pure inversion",
                "E1 competition at high temperature"
            ],
            "SN2": [
                "Steric hindrance blocking reaction",
                "Solvent effects (aprotic vs protic)",
                "Inversion may not be visible if symmetric"
            ],
            "NGP": [
                "Distance miscounting (must be 2-3 atoms!)",
                "Missing NGP from oxygen in ether",
                "Phenyl NGP rate boost (10^11 times!)"
            ],
            "E1": [
                "Zaitsev vs Hofmann product",
                "Carbocation rearrangement",
                "Temperature dependence"
            ],
            "E2": [
                "Anti-periplanar geometry requirement",
                "Regioselectivity",
                "Syn elimination impossibility"
            ]
        }
        
        return traps.get(topic, ["No specific traps cataloged for this topic"])


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

learning_engine = SelfLearningEngine()
error_recognizer = ErrorPatternRecognizer()
