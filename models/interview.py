"""
Interview models for interview assistant
"""
import json

class Interview:
    """Interview model for managing candidate interviews"""
    
    def __init__(self, id=None, candidate_id=None, status="pending", score=None, 
                 feedback=None, created_at=None, completed_at=None):
        self.id = id
        self.candidate_id = candidate_id
        self.status = status  # pending, questions_generated, in_progress, completed
        self.score = score
        self.feedback = feedback
        self.created_at = created_at
        self.completed_at = completed_at
    
    def to_dict(self):
        """Convert interview object to dictionary"""
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "score": self.score,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

class InterviewQuestion:
    """Interview question model for storing questions and responses"""
    
    def __init__(self, id=None, interview_id=None, question=None, response=None, 
                 evaluation=None, score=None):
        self.id = id
        self.interview_id = interview_id
        self.question = question
        self.response = response
        self.evaluation = evaluation  # JSON string for evaluation data
        self.score = score
    
    def to_dict(self):
        """Convert interview question object to dictionary"""
        evaluation_data = None
        if self.evaluation:
            try:
                if isinstance(self.evaluation, str) and '{' in self.evaluation:
                    evaluation_data = json.loads(self.evaluation)
                else:
                    evaluation_data = self.evaluation
            except:
                evaluation_data = self.evaluation
            
        return {
            "id": self.id,
            "interview_id": self.interview_id,
            "question": self.question,
            "response": self.response,
            "evaluation": evaluation_data,
            "score": self.score
        }