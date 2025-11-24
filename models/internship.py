from datetime import datetime
from typing import Optional

class Internship:
    def __init__(
        self,
        id: Optional[int] = None,
        company: str = "",
        title: str = "",
        location: str = "",
        url: str = "",
        posted_date: datetime = None,
        description: str = "",
        requirements: list = None,
        created_at: datetime = None,
        notified: bool = False
    ):
        self.id = id
        self.company = company
        self.title = title
        self.location = location
        self.url = url
        self.posted_date = posted_date or datetime.now()
        self.description = description
        self.requirements = requirements or []
        self.created_at = created_at or datetime.now()
        self.notified = notified
    
    def to_dict(self):
        return {
            'id': self.id,
            'company': self.company,
            'title': self.title,
            'location': self.location,
            'url': self.url,
            'posted_date': self.posted_date.isoformat(),
            'description': self.description,
            'requirements': self.requirements,
            'created_at': self.created_at.isoformat(),
            'notified': self.notified
        }