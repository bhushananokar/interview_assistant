"""
Skill-Based Interview Question Generator
Generates 3 questions per skill and provides individual star ratings for each skill
"""
import os
import json
import logging
import random
from typing import Dict, List, Any, Optional, Tuple

from llm.groq_client import GroqClient
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionGenerator:
    """
    Generates 3 questions per skill and tracks skill-specific performance
    """
    def __init__(self):
        # Initialize the Groq client for LLM-based processing
        self.groq_client = GroqClient()
        
        # Base path for question templates (fallback only)
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.templates_dir = os.path.join(base_dir, "templates", "interview_questions")
        
        # Load template questions as fallback
        self.technical_templates = self._load_question_templates("technical.json")
        self.behavioral_templates = self._load_question_templates("behavioral.json")
        
    def _load_question_templates(self, filename: str) -> List[str]:
        """
        Load question templates from JSON file (fallback only)
        """
        try:
            filepath = os.path.join(self.templates_dir, filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Check if file exists, create with default templates if not
            if not os.path.exists(filepath):
                if "technical" in filename:
                    default_templates = {
                        "questions": [
                            "Describe a challenging problem you faced in your field and how you solved it.",
                            "How do you stay updated with the latest developments in your area of expertise?",
                            "Explain a complex concept from your field to someone who is new to it."
                        ]
                    }
                else:
                    default_templates = {
                        "questions": [
                            "Tell me about a time when you had to work with a difficult team member.",
                            "Describe a situation where you had to meet a tight deadline.",
                            "How do you handle feedback and criticism?"
                        ]
                    }
                
                # Write default templates to file
                with open(filepath, 'w') as f:
                    json.dump(default_templates, f, indent=2)
                    
                return default_templates["questions"]
            
            # Load templates from file
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            return data.get("questions", [])
            
        except Exception as e:
            logger.error(f"Error loading question templates from {filename}: {str(e)}")
            return ["Tell me about your experience.", "What are your strengths?", "Why are you interested in this role?"]

    def parse_skills(self, skills_input: str) -> List[str]:
        """
        Parse skills from comma-separated input
        
        Args:
            skills_input: Comma-separated skills string
            
        Returns:
            List of individual skills
        """
        if not skills_input:
            return ["general skills"]
            
        # Split by comma and clean up
        skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in skills:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique_skills.append(skill)
        
        logger.info(f"Parsed {len(unique_skills)} unique skills: {unique_skills}")
        return unique_skills

    def generate_skill_specific_questions(
        self, 
        skill: str, 
        job_description: str,
        questions_per_skill: int = 3
    ) -> List[Dict[str, str]]:
        """
        Generate questions specific to one skill
        
        Args:
            skill: Single skill to generate questions for
            job_description: Job description for context
            questions_per_skill: Number of questions to generate for this skill
            
        Returns:
            List of question dictionaries with skill metadata
        """
        skill_prompt = [
            {
                "role": "system", 
                "content": f"""You are an expert interviewer specializing in assessing specific skills. 

Your task is to generate {questions_per_skill} focused questions that specifically assess the skill: "{skill}"

Analyze the skill to understand its domain and generate questions that:
1. Test practical knowledge and application of this specific skill
2. Use appropriate terminology and concepts for this skill's domain
3. Range from basic to advanced aspects of this skill
4. Focus on real-world scenarios where this skill is applied
5. Allow assessment of the candidate's proficiency level in this skill

For example:
- If the skill is "Python programming": Ask about Python-specific syntax, libraries, best practices
- If the skill is "cooking": Ask about cooking techniques, ingredient knowledge, kitchen skills
- If the skill is "project management": Ask about planning, coordination, stakeholder management
- If the skill is "graphic design": Ask about design principles, tools, creative process

Generate questions that will help determine if the candidate is a beginner, intermediate, or expert in this specific skill."""
            },
            {
                "role": "user", 
                "content": f"""Generate exactly {questions_per_skill} questions to assess the skill: "{skill}"

Job context: {job_description}

Requirements:
1. Each question should specifically test "{skill}" - not general knowledge
2. Questions should help determine proficiency level (beginner/intermediate/expert)
3. Use domain-appropriate language and terminology for "{skill}"
4. Focus on practical application and real-world scenarios
5. Make questions specific enough to accurately assess this skill

Return ONLY a JSON array of question strings:
["question 1 about {skill}", "question 2 about {skill}", "question 3 about {skill}"]

Each question must clearly assess the "{skill}" skill specifically."""
            }
        ]
        
        try:
            logger.info(f"Generating {questions_per_skill} questions for skill: {skill}")
            response = self.groq_client.generate_response(skill_prompt, temperature=0.7)
            
            if "error" in response:
                logger.error(f"Groq API error for skill '{skill}': {response['error']}")
                return self._fallback_skill_questions(skill, questions_per_skill)
                
            content = response["choices"][0]["message"]["content"]
            
            # Parse the JSON response
            try:
                questions = json.loads(content)
                if isinstance(questions, list) and len(questions) >= questions_per_skill:
                    # Create question objects with skill metadata
                    skill_questions = []
                    for i, question in enumerate(questions[:questions_per_skill]):
                        skill_questions.append({
                            "question": question,
                            "skill": skill,
                            "question_type": "skill_specific",
                            "skill_index": i + 1
                        })
                    
                    logger.info(f"Successfully generated {len(skill_questions)} questions for skill: {skill}")
                    return skill_questions
                    
            except json.JSONDecodeError:
                # Try to extract from markdown code block
                import re
                json_match = re.search(r'```(?:json)?\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    try:
                        questions = json.loads(json_match.group(1))
                        if isinstance(questions, list) and len(questions) >= questions_per_skill:
                            skill_questions = []
                            for i, question in enumerate(questions[:questions_per_skill]):
                                skill_questions.append({
                                    "question": question,
                                    "skill": skill,
                                    "question_type": "skill_specific", 
                                    "skill_index": i + 1
                                })
                            return skill_questions
                    except:
                        pass
                
                # Try line-by-line parsing
                lines = content.split('\n')
                questions = []
                for line in lines:
                    if re.match(r'^(\d+\.|\*|\-|•)\s+', line):
                        question = re.sub(r'^(\d+\.|\*|\-|•)\s+', '', line).strip()
                        if question and '?' in question:
                            questions.append(question)
                
                if len(questions) >= questions_per_skill:
                    skill_questions = []
                    for i, question in enumerate(questions[:questions_per_skill]):
                        skill_questions.append({
                            "question": question,
                            "skill": skill,
                            "question_type": "skill_specific",
                            "skill_index": i + 1
                        })
                    return skill_questions
                    
            logger.warning(f"Failed to parse Groq response for skill '{skill}', using fallback")
            return self._fallback_skill_questions(skill, questions_per_skill)
            
        except Exception as e:
            logger.error(f"Error generating questions for skill '{skill}': {str(e)}")
            return self._fallback_skill_questions(skill, questions_per_skill)

    def _fallback_skill_questions(self, skill: str, questions_per_skill: int) -> List[Dict[str, str]]:
        """
        Fallback method for skill-specific questions when Groq fails
        """
        logger.info(f"Using fallback method for skill: {skill}")
        
        fallback_questions = [
            f"How would you rate your proficiency in {skill} and why?",
            f"Describe a challenging situation where you had to use your {skill} skills.",
            f"What are the most important aspects to consider when applying {skill}?",
            f"How do you stay updated with best practices in {skill}?",
            f"Tell me about a project where {skill} was crucial to success."
        ]
        
        # Create question objects
        skill_questions = []
        for i in range(questions_per_skill):
            question_text = fallback_questions[i % len(fallback_questions)]
            skill_questions.append({
                "question": question_text,
                "skill": skill,
                "question_type": "skill_specific",
                "skill_index": i + 1
            })
        
        return skill_questions

    def generate_questions_for_skills_assessment(
        self, 
        skills_input: str, 
        job_description: str,
        questions_per_skill: int = 3
    ) -> Dict[str, Any]:
        """
        Generate questions for individual skill assessment
        
        Args:
            skills_input: Comma-separated skills string
            job_description: Job description for context
            questions_per_skill: Number of questions per skill
            
        Returns:
            Dictionary with questions organized by skill
        """
        # Parse individual skills
        skills = self.parse_skills(skills_input)
        
        logger.info(f"Generating {questions_per_skill} questions each for {len(skills)} skills")
        logger.info(f"Total questions to generate: {len(skills) * questions_per_skill}")
        
        # Generate questions for each skill
        all_questions = []
        skills_metadata = {}
        
        for skill in skills:
            skill_questions = self.generate_skill_specific_questions(
                skill, 
                job_description, 
                questions_per_skill
            )
            
            # Add to all questions list
            all_questions.extend(skill_questions)
            
            # Store metadata for this skill
            skills_metadata[skill] = {
                "question_count": len(skill_questions),
                "question_indices": list(range(len(all_questions) - len(skill_questions), len(all_questions)))
            }
        
        return {
            "questions": all_questions,
            "skills_metadata": skills_metadata,
            "total_questions": len(all_questions),
            "skills_assessed": skills,
            "questions_per_skill": questions_per_skill
        }

    def calculate_individual_skill_ratings(
        self, 
        evaluations: List[Dict[str, Any]], 
        skills_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate star ratings for individual skills based on their specific questions
        
        Args:
            evaluations: List of all question evaluations
            skills_metadata: Metadata about which questions belong to which skills
            
        Returns:
            Dictionary with individual skill ratings
        """
        skill_ratings = {}
        
        for skill, metadata in skills_metadata.items():
            skill_scores = []
            skill_evaluations = []
            
            # Get evaluations for this specific skill
            for eval_data in evaluations:
                if "skill" in eval_data and eval_data["skill"] == skill:
                    if "evaluation" in eval_data and "score" in eval_data["evaluation"]:
                        skill_scores.append(eval_data["evaluation"]["score"])
                        skill_evaluations.append(eval_data)
            
            if skill_scores:
                # Calculate average score for this skill
                avg_score = sum(skill_scores) / len(skill_scores)
                
                # Convert to star rating (1-5 stars)
                star_rating = self._convert_score_to_stars(avg_score)
                
                # Determine proficiency level
                proficiency_level = self._determine_proficiency_level(avg_score)
                
                # Collect feedback for this skill
                skill_feedback = []
                for eval_data in skill_evaluations:
                    if "evaluation" in eval_data:
                        feedback = eval_data["evaluation"].get("feedback", "")
                        if feedback:
                            skill_feedback.append(feedback)
                
                skill_ratings[skill] = {
                    "average_score": round(avg_score, 2),
                    "star_rating": star_rating,
                    "proficiency_level": proficiency_level,
                    "questions_answered": len(skill_scores),
                    "individual_scores": skill_scores,
                    "feedback": skill_feedback,
                    "skill_summary": f"{skill}: {star_rating}/5 stars ({proficiency_level})"
                }
            else:
                # No scores available for this skill
                skill_ratings[skill] = {
                    "average_score": 0,
                    "star_rating": 1,
                    "proficiency_level": "Not Assessed",
                    "questions_answered": 0,
                    "individual_scores": [],
                    "feedback": [],
                    "skill_summary": f"{skill}: Not assessed"
                }
        
        # Calculate overall rating across all skills
        all_skill_scores = []
        for skill_data in skill_ratings.values():
            if skill_data["average_score"] > 0:
                all_skill_scores.append(skill_data["average_score"])
        
        overall_score = sum(all_skill_scores) / len(all_skill_scores) if all_skill_scores else 0
        overall_stars = self._convert_score_to_stars(overall_score)
        overall_proficiency = self._determine_proficiency_level(overall_score)
        
        return {
            "individual_skills": skill_ratings,
            "overall_rating": {
                "average_score": round(overall_score, 2),
                "star_rating": overall_stars,
                "proficiency_level": overall_proficiency,
                "skills_count": len(skill_ratings)
            },
            "assessment_summary": {
                "total_skills_assessed": len([s for s in skill_ratings.values() if s["questions_answered"] > 0]),
                "highest_rated_skill": max(skill_ratings.items(), key=lambda x: x[1]["average_score"])[0] if skill_ratings else None,
                "lowest_rated_skill": min(skill_ratings.items(), key=lambda x: x[1]["average_score"])[0] if skill_ratings else None,
                "skills_by_proficiency": self._group_skills_by_proficiency(skill_ratings)
            }
        }

    def _convert_score_to_stars(self, score: float) -> int:
        """
        Convert 1-10 score to 1-5 star rating
        
        Args:
            score: Score from 1-10
            
        Returns:
            Star rating from 1-5
        """
        if score >= 9:
            return 5  # Expert (5 stars)
        elif score >= 7:
            return 4  # Advanced (4 stars)
        elif score >= 5:
            return 3  # Intermediate (3 stars)
        elif score >= 3:
            return 2  # Beginner (2 stars)
        else:
            return 1  # Novice (1 star)

    def _determine_proficiency_level(self, score: float) -> str:
        """
        Determine proficiency level based on score
        
        Args:
            score: Score from 1-10
            
        Returns:
            Proficiency level string
        """
        if score >= 9:
            return "Expert"
        elif score >= 7:
            return "Advanced"
        elif score >= 5:
            return "Intermediate"
        elif score >= 3:
            return "Beginner"
        else:
            return "Novice"

    def _group_skills_by_proficiency(self, skill_ratings: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Group skills by proficiency level
        
        Args:
            skill_ratings: Individual skill ratings
            
        Returns:
            Dictionary grouping skills by proficiency level
        """
        proficiency_groups = {
            "Expert": [],
            "Advanced": [],
            "Intermediate": [],
            "Beginner": [],
            "Novice": [],
            "Not Assessed": []
        }
        
        for skill, data in skill_ratings.items():
            proficiency = data["proficiency_level"]
            proficiency_groups[proficiency].append(skill)
        
        # Remove empty groups
        return {k: v for k, v in proficiency_groups.items() if v}

    # Legacy methods for backward compatibility
    def generate_technical_questions(self, resume_data: Dict[str, Any], job_description: str, num_questions: int = 5) -> List[str]:
        """Legacy method - now redirects to skill-based generation"""
        skills_input = self._extract_skills_from_resume(resume_data)
        result = self.generate_questions_for_skills_assessment(skills_input, job_description, 1)
        return [q["question"] for q in result["questions"][:num_questions]]
    
    def generate_behavioral_questions(self, resume_data: Dict[str, Any], job_description: str, num_questions: int = 5) -> List[str]:
        """Legacy method for behavioral questions"""
        return self.behavioral_templates[:num_questions]
    
    def generate_job_specific_questions(self, resume_data: Dict[str, Any], job_description: str, num_questions: int = 3) -> List[str]:
        """Legacy method for job-specific questions"""
        default_questions = [
            "Why are you interested in this specific role?",
            "How does your previous experience prepare you for this position?",
            "What do you think would be the biggest challenge in this role?"
        ]
        return default_questions[:num_questions]

    def _extract_skills_from_resume(self, resume_data: Dict[str, Any]) -> str:
        """Extract skills from resume data for legacy compatibility"""
        skills = []
        if "skills" in resume_data:
            if isinstance(resume_data["skills"], list):
                skills.extend(resume_data["skills"])
            elif isinstance(resume_data["skills"], str):
                skills.extend([skill.strip() for skill in resume_data["skills"].split(',')])
        return ", ".join(skills) if skills else "general skills"

    def generate_full_interview_set(
        self, 
        resume_data: Dict[str, Any], 
        job_description: str,
        technical_count: int = 5,
        behavioral_count: int = 3,
        job_specific_count: int = 2
    ) -> Dict[str, List[str]]:
        """
        Generate full interview set using skill-based approach
        """
        # Extract skills from resume data
        skills_input = self._extract_skills_from_resume(resume_data)
        
        # Generate skill-specific questions (3 per skill)
        skill_result = self.generate_questions_for_skills_assessment(skills_input, job_description, 3)
        
        # Extract just the questions for legacy compatibility
        technical_questions = [q["question"] for q in skill_result["questions"]]
        behavioral_questions = self.generate_behavioral_questions(resume_data, job_description, behavioral_count)
        job_specific_questions = self.generate_job_specific_questions(resume_data, job_description, job_specific_count)
        
        return {
            "technical": technical_questions,
            "behavioral": behavioral_questions,
            "job_specific": job_specific_questions,
            "all": technical_questions + behavioral_questions + job_specific_questions,
            "skills_metadata": skill_result["skills_metadata"],  # Add metadata for tracking
            "skills_assessed": skill_result["skills_assessed"]
        }