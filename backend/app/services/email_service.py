"""
Email service for sending contact support and demo scheduling emails
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import structlog
from datetime import datetime

from app.core.config import settings

logger = structlog.get_logger()


class EmailService:
    """Service for sending emails via SMTP"""

    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.admin_email = settings.ADMIN_EMAIL

    def send_contact_support_email(self, contact_data: Dict[str, Any]) -> bool:
        """Send contact support email to admin"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.admin_email
            msg['Subject'] = f"New Contact Support Request from {contact_data.get('name', 'Unknown')}"

            # Create email body
            body = f"""
New contact support request received:

Name: {contact_data.get('name', 'Not provided')}
Organization: {contact_data.get('organization', 'Not provided')}
Email: {contact_data.get('email', 'Not provided')}
Question: {contact_data.get('question', 'Not provided')}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please respond to the user at: {contact_data.get('email', 'No email provided')}
            """

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            return self._send_email(msg)

        except Exception as e:
            logger.error(f"Failed to send contact support email: {e}")
            return False

    def send_demo_request_email(self, demo_data: Dict[str, Any]) -> bool:
        """Send demo request email to admin"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.admin_email
            msg['Subject'] = f"New Demo Request from {demo_data.get('name', 'Unknown')}"

            # Create email body
            body = f"""
New demo request received:

Name: {demo_data.get('name', 'Not provided')}
Organization: {demo_data.get('organization', 'Not provided')}
Email: {demo_data.get('email', 'Not provided')}
Phone: {demo_data.get('phone', 'Not provided')}

Demo Details:
Preferred Date: {demo_data.get('preferredDate', 'Not provided')}
Preferred Time: {demo_data.get('preferredTime', 'Not provided')}
Timezone: {demo_data.get('timezone', 'Not provided')}

Company Information:
Company Size: {demo_data.get('companySize', 'Not provided')}
Use Case: {demo_data.get('useCase', 'Not provided')}
Additional Notes: {demo_data.get('additionalNotes', 'None')}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please contact the user at: {demo_data.get('email', 'No email provided')}
Phone: {demo_data.get('phone', 'No phone provided')}
            """

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            return self._send_email(msg)

        except Exception as e:
            logger.error(f"Failed to send demo request email: {e}")
            return False

    def send_confirmation_email(self, email: str, email_type: str, data: Dict[str, Any]) -> bool:
        """Send confirmation email to user"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = email

            if email_type == 'contact_support':
                msg['Subject'] = "Thank you for contacting CustomerCareGPT Support"
                body = f"""
Hi {data.get('name', 'there')},

Thank you for reaching out to CustomerCareGPT support. We've received your message and will get back to you within 24 hours during business days.

Your question: {data.get('question', '')}

If you have any urgent matters, please don't hesitate to contact us directly.

Best regards,
CustomerCareGPT Support Team
                """
            elif email_type == 'demo_request':
                msg['Subject'] = "Demo Request Confirmation - CustomerCareGPT"
                body = f"""
Hi {data.get('name', 'there')},

Thank you for your interest in CustomerCareGPT! We've received your demo request and will contact you within 24 hours to confirm your demo session.

Demo Details:
- Preferred Date: {data.get('preferredDate', '')}
- Preferred Time: {data.get('preferredTime', '')}
- Timezone: {data.get('timezone', '')}

We'll review your requirements and get back to you soon to schedule your personalized demo.

Best regards,
CustomerCareGPT Team
                """
            else:
                return False

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            return self._send_email(msg)

        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")
            return False

    def _send_email(self, msg: MIMEMultipart) -> bool:
        """Send email via SMTP"""
        try:
            # Create SMTP session
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                
                # Send email
                text = msg.as_string()
                server.sendmail(self.from_email, msg['To'], text)
                
            logger.info(f"Email sent successfully to {msg['To']}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_test_email(self, to_email: str) -> bool:
        """Send test email to verify SMTP configuration"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "CustomerCareGPT - Test Email"

            body = """
This is a test email from CustomerCareGPT.

If you're receiving this email, the email service is working correctly.

Best regards,
CustomerCareGPT Team
            """

            msg.attach(MIMEText(body, 'plain'))

            return self._send_email(msg)

        except Exception as e:
            logger.error(f"Failed to send test email: {e}")
            return False
