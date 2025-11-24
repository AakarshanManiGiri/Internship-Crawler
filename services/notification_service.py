from typing import List
from services.email_service import EmailService
from models.internship import Internship
from typing import Dict

class NotificationService:
    def __init__(self):
        self.email_service = EmailService()
    
    def notify_new_internships(self, internships: List[Internship], users: List[Dict]):
        """Send notifications about new internships to all users"""
        
        if not internships:
            return
        
        for user in users:
            # Check user preferences (e.g., companies, locations)
            filtered_internships = self._filter_for_user(internships, user)
            
            if filtered_internships:
                self.email_service.send_notification(user, filtered_internships)
    
    def _filter_for_user(self, internships: List[Internship], user: Dict) -> List[Internship]:
        """Filter internships based on user preferences"""
        # Implement filtering logic based on user preferences
        return internships