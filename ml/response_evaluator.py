# Response evaluation
"""
Response Evaluator
Analyzes and scores candidate responses to interview questions
"""
import os
import json
import logging
from typing import Dict, List, Any, Tuple

from llm.groq_client import GroqClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseEvaluator:
    """
    Evaluates candidate responses to interview questions
    """
    def __init__(self):
        # Initialize the Groq client for LLM-based evaluation
        self.groq_client = GroqClient()
        
    def evaluate_response(
        self, 
        question: str, 
        response: str,
        job_description: str = "",
        question_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Evaluate a candidate's response to an interview question
        
        Args:
            question: The interview question
            response: Candidate's response
            job_description: Job description for context
            question_type: Type of question (technical, behavioral, job_specific)
            
        Returns:
            Dictionary with evaluation results
        """
        # Create appropriate system prompt based on question type
        if question_type == "technical":
            system_prompt = "You are an expert technical interviewer. Evaluate the candidate's response to a technical interview question, focusing on accuracy, depth of knowledge, problem-solving skills, and clarity."
        elif question_type == "behavioral":
            system_prompt = "You are an expert behavioral interviewer. Evaluate the candidate's response to a behavioral question, focusing on the STAR method (Situation, Task, Action, Result), communication skills, and relevant experience."
        elif question_type == "job_specific":
            system_prompt = "You are an expert job interviewer. Evaluate the candidate's response to a job-specific question, focusing on their understanding of the role, relevant experience, and alignment with job requirements."
        else:
            system_prompt = "You are an expert interviewer. Evaluate the candidate's response to an interview question, focusing on content, clarity, and relevance."
        
        # Create context for evaluation
        context = ""
        if job_description:
            context = f"JOB DESCRIPTION:\n{job_description}\n\n"
            
        # Build the prompt
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{context}QUESTION:\n{question}\n\nCANDIDATE RESPONSE:\n{response}\n\nPlease evaluate this response on a scale of 1-10 and provide feedback. Return a JSON object with the following structure:\n{{\n  \"score\": <score between 1-10>,\n  \"strengths\": [<list of strengths>],\n  \"weaknesses\": [<list of areas for improvement>],\n  \"feedback\": \"<detailed feedback>\"\n}}"}
        ]
        
        try:
            # Get response from LLM
            response = self.groq_client.generate_response(prompt, temperature=0.3)
            
            if "error" in response:
                logger.error(f"Error in LLM evaluation: {response['error']}")
                return self._default_evaluation(question, response)
                
            content = response["choices"][0]["message"]["content"]
            
            # Parse JSON response
            try:
                result = json.loads(content)
                
                # Ensure required fields are present
                if "score" not in result:
                    result["score"] = 5  # Default middle score
                if "strengths" not in result:
                    result["strengths"] = []
                if "weaknesses" not in result:
                    result["weaknesses"] = []
                if "feedback" not in result:
                    result["feedback"] = "No detailed feedback available."
                    
                return result
                
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code block
                import re
                json_match = re.search(r'```(?:json)?\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                        
                        # Ensure required fields are present
                        if "score" not in result:
                            result["score"] = 5  # Default middle score
                        if "strengths" not in result:
                            result["strengths"] = []
                        if "weaknesses" not in result:
                            result["weaknesses"] = []
                        if "feedback" not in result:
                            result["feedback"] = "No detailed feedback available."
                            
                        return result
                    except:
                        pass
                
                # Fall back to default evaluation
                logger.error(f"Error parsing evaluation response: {str(e)}")
                return self._default_evaluation(question, response, content)
                
        except Exception as e:
            logger.error(f"Error evaluating response: {str(e)}")
            return self._default_evaluation(question, response)
            
    def _default_evaluation(self, question: str, response: str, raw_llm_response: str = "") -> Dict[str, Any]:
        """
        Provide a default evaluation when LLM-based evaluation fails
        
        Args:
            question: The interview question
            response: Candidate's response
            raw_llm_response: Raw LLM response if available
            
        Returns:
            Dictionary with default evaluation
        """
        # Calculate a basic score based on response length and complexity
        response_len = len(response.split())
        
        # Basic scoring - very simple
        if response_len < 10:
            score = 2  # Very short response
        elif response_len < 25:
            score = 4  # Short response
        elif response_len < 50:
            score = 6  # Medium response
        elif response_len < 100:
            score = 7  # Decent length response
        else:
            score = 8  # Long response
            
        return {
            "score": score,
            "strengths": ["Response provided"],
            "weaknesses": ["Unable to perform detailed analysis"],
            "feedback": "The system was unable to perform a detailed analysis of this response. Basic evaluation provided based on response length and structure.",
            "error": "LLM evaluation failed",
            "raw_llm_response": raw_llm_response
        }
        
    def evaluate_multiple_responses(
        self, 
        question_responses: List[Dict[str, str]],
        job_description: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple interview responses
        
        Args:
            question_responses: List of dictionaries with questions and responses
            job_description: Job description for context
            
        Returns:
            List of evaluation results
        """
        results = []
        
        for item in question_responses:
            question = item.get("question", "")
            response = item.get("response", "")
            question_type = item.get("type", "general")
            
            evaluation = self.evaluate_response(
                question, 
                response, 
                job_description,
                question_type
            )
            
            results.append({
                "question": question,
                "response": response,
                "type": question_type,
                "evaluation": evaluation
            })
            
        return results
        
    def calculate_overall_score(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate overall interview score from individual question evaluations
        
        Args:
            evaluations: List of evaluation results
            
        Returns:
            Dictionary with overall score and summary
        """
        if not evaluations:
            return {
                "overall_score": 0,
                "average_score": 0,
                "count": 0,
                "key_strengths": [],
                "key_weaknesses": [],
                "summary": "No evaluations provided."
            }
            
        # Calculate average score
        scores = [e.get("evaluation", {}).get("score", 0) for e in evaluations]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Collect all strengths and weaknesses
        all_strengths = []
        all_weaknesses = []
        
        for eval_item in evaluations:
            eval_data = eval_item.get("evaluation", {})
            all_strengths.extend(eval_data.get("strengths", []))
            all_weaknesses.extend(eval_data.get("weaknesses", []))
            
        # Find most common strengths and weaknesses
        from collections import Counter
        
        # Get top 3 strengths and weaknesses
        strength_counter = Counter(all_strengths)
        weakness_counter = Counter(all_weaknesses)
        
        key_strengths = [s for s, _ in strength_counter.most_common(3)]
        key_weaknesses = [w for w, _ in weakness_counter.most_common(3)]
        
        # Calculate overall score (weighted toward technical questions if available)
        technical_evals = [e for e in evaluations if e.get("type") == "technical"]
        behavioral_evals = [e for e in evaluations if e.get("type") == "behavioral"]
        job_specific_evals = [e for e in evaluations if e.get("type") == "job_specific"]
        
        if technical_evals and (behavioral_evals or job_specific_evals):
            # If we have technical and other questions, weight technical more
            technical_avg = sum([e.get("evaluation", {}).get("score", 0) for e in technical_evals]) / len(technical_evals) if technical_evals else 0
            other_avg = sum([e.get("evaluation", {}).get("score", 0) for e in evaluations if e.get("type") != "technical"]) / (len(evaluations) - len(technical_evals)) if len(evaluations) > len(technical_evals) else 0
            
            # 60% technical, 40% other
            overall_score = (technical_avg * 0.6) + (other_avg * 0.4)
        else:
            # Otherwise just use average
            overall_score = avg_score
            
        # Round scores
        overall_score = round(overall_score, 1)
        avg_score = round(avg_score, 1)
        
        return {
            "overall_score": overall_score,
            "average_score": avg_score,
            "count": len(evaluations),
            "key_strengths": key_strengths,
            "key_weaknesses": key_weaknesses,
            "summary": f"Overall interview performance score: {overall_score}/10"
        }