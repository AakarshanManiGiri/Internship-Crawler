import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from models.internship import Internship


logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL", "").strip()
        self.sender_password = os.getenv("SENDER_PASSWORD", "").strip()

    def is_configured(self) -> bool:
        return bool(self.sender_email and self.sender_password)
    
    def send_notification(self, user: Dict, internships: List[Internship]):
        """Send email notification about new internships"""

        if not self.is_configured():
            logger.warning("Skipping email notification because sender credentials are not configured.")
            return
        
        subject = f"🚀 {len(internships)} New Internship(s) Posted!"
        body = self._create_email_body(internships)
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = user['email']
        
        html_part = MIMEText(body, "html")
        message.attach(html_part)
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email,
                    user['email'],
                    message.as_string()
                )
            logger.info("Email sent to %s", user['email'])
        
        except Exception as e:
            logger.error("Error sending email to %s: %s", user['email'], e)
    
    def _create_email_body(self, internships: List[Internship]) -> str:
        """Create HTML email body"""
        html = """
        <html>
        <body>
            <h2>New Internship Opportunities!</h2>
            <p>The following internships have just been posted:</p>
        """
        
        for internship in internships:
            html += f"""
            <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                <h3>{internship.company} - {internship.title}</h3>
                <p><strong>Location:</strong> {internship.location}</p>
                <p><strong>Posted:</strong> {internship.posted_date.strftime('%Y-%m-%d')}</p>
                <a href="{internship.url}" style="display: inline-block; padding: 10px 20px; 
                   background-color: #4CAF50; color: white; text-decoration: none; 
                   border-radius: 5px;">Apply Now</a>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html