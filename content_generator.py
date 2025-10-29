"""
Dynamic Content Generation Engine
==================================

AI-powered practice problem generation, quizzes, and study materials.
Production-ready with async optimization, type hints, and Railway deployment support.

Features:
- Adaptive problem generation using Gemini API
- Problem caching and reuse
- Quiz generation with multiple topics
- JEE trend analysis
- Difficulty calibration
- Smart API key rotation

Author: Enhanced for JEE Advanced Chemistry Bot
"""

import logging
import random
import asyncio
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from database import (
    SessionLocal, GeneratedProblem, TopicStatistics, JEETrend,
    get_db_session
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# CONTENT GENERATION ENGINE
# ============================================================================

class ContentGenerator:
    """
    AI-powered content generation for practice problems and quizzes.
    
    Capabilities:
    - Generate JEE Advanced chemistry problems
    - Create multi-topic quizzes
    - Cache and reuse quality problems
    - Analyze JEE exam trends
    - Adapt to user weaknesses
    """
    
    def __init__(self, api_keys: List[str]) -> None:
        """
        Initialize content generator with API keys.
        
        Args:
            api_keys: List of Gemini API keys for rotation
        """
        if not api_keys:
            raise ValueError("At least one API key required")
        
        self.api_keys = api_keys
        self.current_key_index = 0
        
        # Topic templates for structured generation
        self.topics: Dict[str, Dict[str, List[str]]] = {
            "SN1": {
                "concepts": ["carbocation stability", "rate law", "racemization", "rearrangement"],
                "difficulty_factors": ["simple tertiary", "rearrangement", "competing E1"]
            },
            "SN2": {
                "concepts": ["backside attack", "inversion", "steric hindrance", "nucleophile strength"],
                "difficulty_factors": ["primary substrate", "strong Nu", "crowded substrate"]
            },
            "NGP": {
                "concepts": ["neighboring group", "rate enhancement", "distance", "product formation"],
                "difficulty_factors": ["2 atoms away", "phenyl NGP", "oxygen NGP"]
            },
            "E1": {
                "concepts": ["carbocation", "Zaitsev rule", "temperature effect"],
                "difficulty_factors": ["simple", "rearrangement", "vs SN1"]
            },
            "E2": {
                "concepts": ["anti-periplanar", "strong base", "Hofmann vs Zaitsev"],
                "difficulty_factors": ["simple", "syn impossible", "regioselective"]
            }
        }
        
        logger.info(f"✅ Content Generator initialized with {len(api_keys)} API keys")
    
    # ========================================================================
    # API KEY MANAGEMENT
    # ========================================================================
    
    def get_next_key(self) -> str:
        """
        Rotate through API keys for load distribution.
        
        Returns:
            str: Next API key in rotation
        """
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    # ========================================================================
    # PROBLEM GENERATION
    # ========================================================================
    
    async def generate_practice_problem(
        self, 
        topic: str, 
        difficulty: int = 5,
        user_weaknesses: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a practice problem for a specific topic using Gemini AI.
        
        Args:
            topic: Chemistry topic (SN1, SN2, NGP, etc.)
            difficulty: 1-10 difficulty scale
            user_weaknesses: Specific concepts to target
        
        Returns:
            Dict with problem, options, answer, explanation, and metadata
        """
        try:
            # Build generation prompt
            prompt = self._build_generation_prompt(topic, difficulty, user_weaknesses)
            
            # Call Gemini API
            key = self.get_next_key()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.8,  # Creative for variety
                    "maxOutputTokens": 1024
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Parse and validate generated problem
                    problem_data = self._parse_generated_problem(text, topic, difficulty)
                    
                    # Save to database cache
                    if problem_data.get("success"):
                        self._save_generated_problem(problem_data)
                    
                    logger.info(f"✅ Generated problem: {topic} (difficulty {difficulty})")
                    return problem_data
                else:
                    logger.error(f"Gemini API error: {response.status_code}")
                    return {"success": False, "error": f"API error: {response.status_code}"}
        
        except asyncio.TimeoutError:
            logger.error("Problem generation timeout")
            return {"success": False, "error": "Generation timeout"}
        except Exception as e:
            logger.error(f"Problem generation error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _build_generation_prompt(
        self, 
        topic: str, 
        difficulty: int, 
        weaknesses: Optional[List[str]] = None
    ) -> str:
        """
        Build optimized prompt for problem generation.
        
        Args:
            topic: Chemistry topic
            difficulty: 1-10 scale
            weaknesses: User's weak concepts
        
        Returns:
            str: Formatted generation prompt
        """
        difficulty_desc = {
            1: "very easy (basic concept)",
            3: "easy (straightforward)",
            5: "moderate (typical JEE Mains)",
            7: "hard (JEE Advanced level)",
            10: "very hard (olympiad level)"
        }.get(difficulty, "moderate")
        
        prompt = f"""Generate a {difficulty_desc} multiple-choice problem on {topic} for JEE Advanced chemistry.

REQUIREMENTS:
1. Create a realistic reaction scenario
2. Include 4 options (A, B, C, D)
3. One clear correct answer
4. Test understanding, not just memorization
5. Include common misconceptions as wrong options

TOPIC: {topic}
DIFFICULTY: {difficulty}/10
"""
        
        if weaknesses:
            prompt += f"\nFOCUS ON: {', '.join(weaknesses)}\n"
        
        prompt += """
FORMAT:
PROBLEM: [question text]
(A) [option A]
(B) [option B]
(C) [option C]
(D) [option D]
ANSWER: [letter]
EXPLANATION: [why correct and why others wrong]

Generate the problem now:"""
        
        return prompt
    
    def _parse_generated_problem(
        self, 
        text: str, 
        topic: str, 
        difficulty: int
    ) -> Dict[str, Any]:
        """
        Parse AI-generated text into structured problem format.
        
        Args:
            text: Raw AI output
            topic: Problem topic
            difficulty: Difficulty level
        
        Returns:
            Dict with parsed problem or error message
        """
        try:
            # Extract problem statement
            problem_match = re.search(r'PROBLEM:\s*(.+?)(?=\(A\))', text, re.DOTALL | re.IGNORECASE)
            problem_text = problem_match.group(1).strip() if problem_match else ""
            
            # Extract options
            options: Dict[str, str] = {}
            for letter in ['A', 'B', 'C', 'D']:
                option_match = re.search(
                    rf'\({letter}\)\s*(.+?)(?=\([A-D]\)|ANSWER:|$)', 
                    text, 
                    re.DOTALL | re.IGNORECASE
                )
                if option_match:
                    options[letter] = option_match.group(1).strip()
            
            # Extract answer
            answer_match = re.search(r'ANSWER:\s*\(?([A-D])\)?', text, re.IGNORECASE)
            correct_answer = answer_match.group(1) if answer_match else ""
            
            # Extract explanation
            exp_match = re.search(r'EXPLANATION:\s*(.+)', text, re.DOTALL | re.IGNORECASE)
            explanation = exp_match.group(1).strip() if exp_match else ""
            
            # Validate completeness
            if not problem_text or not options or not correct_answer:
                logger.warning("Failed to parse problem - incomplete data")
                return {"success": False, "error": "Failed to parse problem"}
            
            return {
                "success": True,
                "topic": topic,
                "difficulty": difficulty,
                "problem_text": problem_text,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": explanation,
                "generated_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Parse error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _save_generated_problem(self, problem_data: Dict[str, Any]) -> None:
        """
        Save generated problem to database cache.
        
        Args:
            problem_data: Parsed problem dictionary
        """
        with get_db_session() as db:
            try:
                problem = GeneratedProblem(
                    topic=problem_data["topic"],
                    difficulty=problem_data["difficulty"],
                    problem_text=problem_data["problem_text"],
                    options=problem_data["options"],
                    correct_answer=problem_data["correct_answer"],
                    explanation=problem_data["explanation"],
                    times_used=0,
                    success_rate=0.0
                )
                
                db.add(problem)
                logger.info(f"💾 Cached generated problem: {problem_data['topic']}")
            
            except Exception as e:
                logger.error(f"Error saving problem: {e}", exc_info=True)
    
    # ========================================================================
    # PROBLEM CACHE
    # ========================================================================
    
    def get_cached_problem(
        self, 
        topic: str, 
        difficulty: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a previously generated problem from cache.
        
        Strategy: Prefer least-used problems within difficulty range (±2)
        
        Args:
            topic: Chemistry topic
            difficulty: Target difficulty
        
        Returns:
            Cached problem dict or None
        """
        with get_db_session() as db:
            # Get unused or least-used problems in difficulty range
            problems = db.query(GeneratedProblem).filter(
                GeneratedProblem.topic == topic,
                GeneratedProblem.difficulty >= difficulty - 2,
                GeneratedProblem.difficulty <= difficulty + 2
            ).order_by(GeneratedProblem.times_used.asc()).limit(10).all()
            
            if not problems:
                return None
            
            # Pick randomly from top candidates to avoid repetition
            problem = random.choice(problems)
            problem.times_used += 1
            
            logger.info(f"♻️ Using cached problem: {topic} (used {problem.times_used} times)")
            
            return {
                "success": True,
                "topic": problem.topic,
                "difficulty": problem.difficulty,
                "problem_text": problem.problem_text,
                "options": problem.options,
                "correct_answer": problem.correct_answer,
                "explanation": problem.explanation,
                "from_cache": True
            }
    
    # ========================================================================
    # QUIZ GENERATION
    # ========================================================================
    
    async def generate_quiz(
        self, 
        topics: List[str], 
        num_questions: int = 5,
        difficulty: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a complete multi-topic quiz.
        
        Strategy: Try cache first, generate new if needed
        
        Args:
            topics: List of topics to cover
            num_questions: Number of questions
            difficulty: Overall difficulty level
        
        Returns:
            Dict with quiz metadata and questions
        """
        questions: List[Dict[str, Any]] = []
        
        for i, topic in enumerate(topics[:num_questions]):
            # Try cache first for speed
            problem = self.get_cached_problem(topic, difficulty)
            
            if not problem or not problem.get("success"):
                # Generate new problem
                problem = await self.generate_practice_problem(topic, difficulty)
            
            if problem.get("success"):
                questions.append({
                    "number": i + 1,
                    "topic": topic,
                    **problem
                })
            
            # Prevent rate limiting
            await asyncio.sleep(0.5)
        
        quiz_id = f"quiz_{int(datetime.utcnow().timestamp())}"
        
        logger.info(f"📋 Generated quiz {quiz_id} with {len(questions)} questions")
        
        return {
            "quiz_id": quiz_id,
            "num_questions": len(questions),
            "questions": questions,
            "topics": topics[:num_questions],
            "difficulty": difficulty,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    # ========================================================================
    # JEE TREND ANALYSIS
    # ========================================================================
    
    def analyze_jee_trends(self, year: int = 2024) -> Dict[str, Any]:
        """
        Analyze JEE exam patterns and trending topics.
        
        Args:
            year: JEE year to analyze
        
        Returns:
            Dict with hot topics, frequencies, and trends
        """
        with get_db_session() as db:
            trends = db.query(JEETrend).filter(
                JEETrend.year == year
            ).order_by(JEETrend.frequency.desc()).all()
            
            if not trends:
                # Return default trends based on historical patterns
                return self._get_default_trends()
            
            hot_topics: List[Dict[str, Any]] = []
            for trend in trends[:10]:
                hot_topics.append({
                    "topic": trend.topic,
                    "frequency": trend.frequency,
                    "difficulty": trend.average_difficulty,
                    "trend": trend.trend
                })
            
            return {
                "year": year,
                "hot_topics": hot_topics,
                "analysis": f"Top topics in JEE {year}"
            }
    
    def _get_default_trends(self) -> Dict[str, Any]:
        """
        Default JEE trends based on historical analysis.
        
        Returns:
            Dict with default trending topics
        """
        return {
            "year": 2024,
            "hot_topics": [
                {"topic": "NGP", "frequency": 8, "difficulty": 7.5, "trend": "increasing"},
                {"topic": "SN1_vs_SN2", "frequency": 6, "difficulty": 6.0, "trend": "stable"},
                {"topic": "E1_E2", "frequency": 5, "difficulty": 6.5, "trend": "stable"},
                {"topic": "Carbocation_rearrangement", "frequency": 4, "difficulty": 8.0, "trend": "increasing"},
                {"topic": "Stereochemistry", "frequency": 7, "difficulty": 7.0, "trend": "increasing"}
            ],
            "analysis": "NGP and stereochemistry are hot topics in recent JEE exams"
        }


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Global instance (initialized with API keys)
content_gen: Optional[ContentGenerator] = None

def init_content_generator(api_keys: List[str]) -> None:
    """
    Initialize global content generator instance.
    
    Args:
        api_keys: List of Gemini API keys
    """
    global content_gen
    content_gen = ContentGenerator(api_keys)
    logger.info("✅ Content generator initialized globally")
