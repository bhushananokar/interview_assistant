"""
Simplified Candidate model for interview assistant
"""

class Candidate:
    """Simple candidate class for basic info storage"""
    
    def __init__(self, id=None, name=None, email=None, phone=None, created_at=None):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.created_at = created_at
    
    def to_dict(self):
        """Convert candidate object to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }