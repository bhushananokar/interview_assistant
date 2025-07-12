# Groq API client
"""
Groq API client for LLM integration
Handles communication with Groq API for LLM tasks
"""
import os
import json
import time
import logging
import requests
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Available models
AVAILABLE_MODELS = {
    "llama": "meta-llama/llama-4-scout-17b-16e-instruct",
    "mixtral": "mistral-saba-24b"
}

class GroqClient:
    """
    Client for interacting with Groq API
    """
    def __init__(self, model: str = "mixtral"):
        """
        Initialize the Groq client
        
        Args:
            model: Model to use, either "llama" or "mixtral"
        """
        if not GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not found in environment variables")
            
        self.api_key = GROQ_API_KEY
        self.model = AVAILABLE_MODELS.get(model, AVAILABLE_MODELS["mixtral"])
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a response using the Groq API
        
        Args:
            messages: List of message dictionaries with role and content
            temperature: Control randomness (0.0 to 1.0)
            max_tokens: Maximum tokens in the response
            stream: Whether to stream the response
            
        Returns:
            Dictionary with the API response
        """
        if not self.api_key:
            return {"error": "GROQ_API_KEY not configured"}
            
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream
            }
            
            response = requests.post(
                GROQ_API_URL,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code}"}
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {"error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
            
    def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Analyze resume text to extract structured information
        
        Args:
            resume_text: Text content of the resume
            
        Returns:
            Dictionary with structured resume information
        """
        prompt = [
            {"role": "system", "content": "You are an expert resume analyzer. Extract key information from the resume in a structured format."},
            {"role": "user", "content": f"Analyze this resume and extract the following information in JSON format:\n1. Contact Information\n2. Education\n3. Work Experience\n4. Skills\n5. Projects\n6. Certifications\n\nResume text:\n{resume_text}"}
        ]
        
        response = self.generate_response(prompt, temperature=0.1)
        
        if "error" in response:
            return {"error": response["error"]}
            
        try:
            # Extract JSON content from the response
            content = response["choices"][0]["message"]["content"]
            
            # Try to parse the JSON
            try:
                # First attempt - direct parsing
                result = json.loads(content)
            except:
                # Second attempt - try to extract JSON if surrounded by markdown or text
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Last resort - just return the text
                    return {"parsed_text": content}
            
            return result
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return {"error": "Failed to parse response", "raw_response": content}
            
    def generate_interview_questions(self, resume_data: Dict[str, Any], job_description: str, num_questions: int = 5) -> List[str]:
        """
        Generate interview questions based on resume and job description
        
        Args:
            resume_data: Structured resume data
            job_description: Job description text
            num_questions: Number of questions to generate
            
        Returns:
            List of interview questions
        """
        # Convert resume data to string format for the prompt
        resume_str = json.dumps(resume_data, indent=2)
        
        prompt = [
            {"role": "system", "content": "You are an expert HR interviewer. Generate relevant interview questions based on the candidate's resume and job description."},
            {"role": "user", "content": f"Generate {num_questions} insightful interview questions based on this resume and job description. Focus on technical skills, experience, and fit for the role.\n\nRESUME DATA:\n{resume_str}\n\nJOB DESCRIPTION:\n{job_description}\n\nProvide the questions in a JSON list format."}
        ]
        
        response = self.generate_response(prompt, temperature=0.7)
        
        if "error" in response:
            return [f"Error generating questions: {response['error']}"]
            
        try:
            content = response["choices"][0]["message"]["content"]
            
            # Try to extract JSON array of questions
            try:
                # Direct parsing if it's a clean JSON
                questions = json.loads(content)
                if isinstance(questions, list):
                    return questions
                elif isinstance(questions, dict) and "questions" in questions:
                    return questions["questions"]
            except:
                # Extract from markdown if wrapped
                json_match = re.search(r'```(?:json)?\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    try:
                        questions = json.loads(json_match.group(1))
                        if isinstance(questions, list):
                            return questions
                        elif isinstance(questions, dict) and "questions" in questions:
                            return questions["questions"]
                    except:
                        pass
                
                # Fallback: Try to parse line by line for questions
                lines = content.split('\n')
                questions = []
                for line in lines:
                    # Look for numbered or bullet point questions
                    if re.match(r'^(\d+\.|\*|\-)\s+', line):
                        question = re.sub(r'^(\d+\.|\*|\-)\s+', '', line).strip()
                        if question:
                            questions.append(question)
                
                if questions:
                    return questions
                
                # Last resort - return the raw text
                return [content]
                
        except Exception as e:
            logger.error(f"Error parsing questions response: {str(e)}")
            return [f"Error generating questions: {str(e)}"]