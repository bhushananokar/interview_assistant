"""
Updated Interview service module
Handles skill-based interview creation with individual skill ratings
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ml.question_generator import QuestionGenerator
from ml.response_evaluator import ResponseEvaluator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InterviewService:
    """Service for managing skill-based interview operations"""

    def __init__(self):
        """Initialize the interview service"""
        self.question_generator = QuestionGenerator()
        self.response_evaluator = ResponseEvaluator()

    def create_skill_based_interview(
        self, 
        candidate_name: str, 
        skills: str, 
        skill_area: str = "general",
        questions_per_skill: int = 3
    ) -> Dict[str, Any]:
        """
        Create a skill-based interview with individual skill assessment
        
        Args:
            candidate_name: Name of the candidate
            skills: Comma-separated skills to assess
            skill_area: General skill area category
            questions_per_skill: Number of questions per skill (default: 3)
            
        Returns:
            Dictionary with interview data and skill-specific questions
        """
        try:
            # Create job description based on skills
            job_description = self._create_job_description_for_skills(skills, skill_area)
            
            # Generate skill-specific questions
            question_result = self.question_generator.generate_questions_for_skills_assessment(
                skills, 
                job_description, 
                questions_per_skill
            )
            
            # Create interview data structure
            interview_data = {
                "candidate_name": candidate_name,
                "skills_input": skills,
                "skill_area": skill_area,
                "questions_per_skill": questions_per_skill,
                "questions": question_result["questions"],
                "skills_metadata": question_result["skills_metadata"],
                "skills_assessed": question_result["skills_assessed"],
                "total_questions": question_result["total_questions"],
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"Created skill-based interview for {len(question_result['skills_assessed'])} skills")
            logger.info(f"Skills: {question_result['skills_assessed']}")
            logger.info(f"Total questions: {question_result['total_questions']}")
            
            return {
                "success": True,
                "interview_data": interview_data
            }
            
        except Exception as e:
            logger.error(f"Error creating skill-based interview: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _create_job_description_for_skills(self, skills: str, skill_area: str) -> str:
        """
        Create a job description based on entered skills
        
        Args:
            skills: Skills entered by user
            skill_area: General skill area category
            
        Returns:
            Job description string
        """
        skill_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        
        job_description = f"""Position requiring expertise in {', '.join(skill_list)}. 
        
The ideal candidate should demonstrate proficiency in each of these areas:
{chr(10).join([f"- {skill}" for skill in skill_list])}

This role involves practical application of these skills in real-world scenarios. 
Candidates will be assessed on their depth of knowledge, problem-solving abilities, 
and hands-on experience with each skill area.

Success in this position requires not only technical/practical competency but also 
the ability to apply these skills effectively in professional environments."""
        
        return job_description

    def evaluate_skill_response(
        self, 
        question: str, 
        response: str, 
        skill: str,
        question_type: str = "skill_specific"
    ) -> Dict[str, Any]:
        """
        Evaluate a response for a specific skill
        
        Args:
            question: The interview question
            response: Candidate's response
            skill: The specific skill being assessed
            question_type: Type of question
            
        Returns:
            Dictionary with evaluation results including skill context
        """
        try:
            # Create skill-specific context for evaluation
            skill_context = f"This question specifically assesses the skill: {skill}. " \
                          f"Evaluate how well the response demonstrates knowledge and proficiency in {skill}."
            
            # Evaluate the response with skill context
            evaluation = self.response_evaluator.evaluate_response(
                question,
                response,
                skill_context,
                question_type
            )
            
            # Add skill metadata to evaluation
            evaluation["assessed_skill"] = skill
            evaluation["skill_specific"] = True
            
            return {
                "success": True,
                "evaluation": evaluation,
                "skill": skill
            }
            
        except Exception as e:
            logger.error(f"Error evaluating skill response for {skill}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "evaluation": {
                    "score": 5,
                    "feedback": f"Unable to evaluate response for {skill} due to technical error.",
                    "assessed_skill": skill,
                    "skill_specific": True
                }
            }

    def calculate_skill_based_ratings(
        self, 
        evaluations: List[Dict[str, Any]], 
        skills_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate individual star ratings for each skill
        
        Args:
            evaluations: List of evaluation results with skill information
            skills_metadata: Metadata about skills and questions
            
        Returns:
            Dictionary with individual skill ratings and overall assessment
        """
        try:
            # Use the question generator's rating calculation method
            skill_ratings = self.question_generator.calculate_individual_skill_ratings(
                evaluations, 
                skills_metadata
            )
            
            # Add additional analysis
            total_skills = len(skill_ratings["individual_skills"])
            assessed_skills = len([s for s in skill_ratings["individual_skills"].values() if s["questions_answered"] > 0])
            
            # Create skill summary for easy viewing
            skill_summary = []
            for skill, data in skill_ratings["individual_skills"].items():
                summary_line = f"{skill}: {data['star_rating']}/5 stars ({data['proficiency_level']})"
                skill_summary.append(summary_line)
            
            # Add comprehensive results
            result = {
                **skill_ratings,
                "assessment_details": {
                    "total_skills_defined": total_skills,
                    "skills_actually_assessed": assessed_skills,
                    "assessment_completion": f"{assessed_skills}/{total_skills}",
                    "skill_summary_lines": skill_summary
                },
                "recommendations": self._generate_skill_recommendations(skill_ratings["individual_skills"])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating skill-based ratings: {str(e)}")
            return {
                "individual_skills": {},
                "overall_rating": {
                    "average_score": 0,
                    "star_rating": 1,
                    "proficiency_level": "Error in Assessment"
                },
                "error": str(e)
            }

    def _generate_skill_recommendations(self, individual_skills: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Generate recommendations based on skill assessment results
        
        Args:
            individual_skills: Individual skill ratings data
            
        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            "strengths": [],
            "improvement_areas": [],
            "focus_suggestions": []
        }
        
        for skill, data in individual_skills.items():
            star_rating = data["star_rating"]
            
            if star_rating >= 4:
                recommendations["strengths"].append(f"Strong proficiency in {skill} ({star_rating}/5 stars)")
            elif star_rating <= 2:
                recommendations["improvement_areas"].append(f"{skill} needs development ({star_rating}/5 stars)")
            
            # Add specific focus suggestions based on proficiency
            if data["proficiency_level"] == "Expert":
                recommendations["focus_suggestions"].append(f"Consider mentoring others in {skill}")
            elif data["proficiency_level"] == "Beginner":
                recommendations["focus_suggestions"].append(f"Invest time in foundational learning for {skill}")
            elif data["proficiency_level"] == "Intermediate":
                recommendations["focus_suggestions"].append(f"Practice advanced applications of {skill}")
        
        return recommendations

    # Legacy compatibility methods
    def create_interview_for_skills(self, candidate_name: str, skills: str, skill_area: str = "general") -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        return self.create_skill_based_interview(candidate_name, skills, skill_area)

    def create_skill_based_resume(self, skills: str, skill_area: str = "general") -> Dict[str, Any]:
        """
        Create a mock resume based on entered skills (for legacy compatibility)
        """
        skill_list = [s.strip() for s in skills.split(',') if s.strip()]
        
        mock_resume = {
            "skills": skill_list,
            "experience": f"Professional experience in {skill_area}" if skill_area != "general" else "General professional experience",
            "education": "Relevant education and training",
            "categorized_skills": {skill_area: skill_list}
        }
        
        return mock_resume

    def generate_questions_for_skills(
        self, 
        skills: str, 
        skill_area: str = "general",
        questions_per_skill: int = 3
    ) -> Dict[str, List[str]]:
        """
        Generate interview questions based on user-entered skills (legacy compatibility)
        
        Args:
            skills: Skills entered by user
            skill_area: General skill area category
            questions_per_skill: Number of questions per skill
            
        Returns:
            Dictionary with categorized questions
        """
        # Create mock resume and job description
        mock_resume = self.create_skill_based_resume(skills, skill_area)
        job_description = self._create_job_description_for_skills(skills, skill_area)
        
        # Generate questions using the new skill-based approach
        question_result = self.question_generator.generate_questions_for_skills_assessment(
            skills, 
            job_description, 
            questions_per_skill
        )
        
        # Convert to legacy format
        technical_questions = [q["question"] for q in question_result["questions"]]
        behavioral_questions = ["Tell me about a time when you had to work under pressure.", 
                               "How do you handle feedback and criticism?"]
        job_specific_questions = ["Why are you interested in this role?"]
        
        return {
            "technical": technical_questions,
            "behavioral": behavioral_questions,
            "job_specific": job_specific_questions,
            "all": technical_questions + behavioral_questions + job_specific_questions,
            "skills_metadata": question_result["skills_metadata"],
            "skills_assessed": question_result["skills_assessed"]
        }