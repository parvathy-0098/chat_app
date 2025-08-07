import random
import string
from datetime import datetime, timedelta
from flask_mail import Message
import logging

class IdentityVerifier:
    """Handle email-based identity verification"""
    
    def __init__(self, mail_instance):
        self.mail = mail_instance
        self.code_expiry_minutes = 15
    
    def generate_verification_code(self):
        """Generate 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_verification_email(self, email, verification_codes_storage):
        """Send verification code via email"""
        try:
            # Generate verification code
            code = self.generate_verification_code()
            expires_at = datetime.now() + timedelta(minutes=self.code_expiry_minutes)
            
            # Store verification code
            verification_codes_storage[email] = {
                'code': code,
                'expires_at': expires_at
            }
            
            # Create email message
            msg = Message(
                subject='SecureChat - Email Verification',
                recipients=[email],
                body=f'''Hello,

Your email verification code for SecureChat is: {code}

This code will expire in {self.code_expiry_minutes} minutes.

If you did not request this verification code, please ignore this email.

Best regards,
SecureChat Team''',
                html=f'''
                <html>
                    <body>
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <h2 style="color: #333;">SecureChat - Email Verification</h2>
                            <p>Hello,</p>
                            <p>Your email verification code for SecureChat is:</p>
                            <div style="background-color: #f8f9fa; padding: 20px; text-align: center; margin: 20px 0;">
                                <h1 style="color: #007bff; font-size: 36px; margin: 0; letter-spacing: 5px;">{code}</h1>
                            </div>
                            <p>This code will expire in {self.code_expiry_minutes} minutes.</p>
                            <p>If you did not request this verification code, please ignore this email.</p>
                            <hr style="margin: 30px 0;">
                            <p style="color: #666; font-size: 12px;">
                                Best regards,<br>
                                SecureChat Team
                            </p>
                        </div>
                    </body>
                </html>
                '''
            )
            
            # Send email
            self.mail.send(msg)
            logging.info(f"Verification email sent to {email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send verification email to {email}: {str(e)}")
            return False
    
    def verify_code(self, email, submitted_code, verification_codes_storage):
        """Verify submitted code against stored code"""
        try:
            if email not in verification_codes_storage:
                logging.warning(f"No verification code found for {email}")
                return False
            
            stored_data = verification_codes_storage[email]
            stored_code = stored_data['code']
            expires_at = stored_data['expires_at']
            
            # Check if code has expired
            if datetime.now() > expires_at:
                logging.warning(f"Verification code expired for {email}")
                # Clean up expired code
                del verification_codes_storage[email]
                return False
            
            # Check if codes match
            if submitted_code.strip() == stored_code:
                logging.info(f"Email verification successful for {email}")
                # Clean up used code
                del verification_codes_storage[email]
                return True
            else:
                logging.warning(f"Invalid verification code submitted for {email}")
                return False
                
        except Exception as e:
            logging.error(f"Error verifying code for {email}: {str(e)}")
            return False
    
    def cleanup_expired_codes(self, verification_codes_storage):
        """Clean up expired verification codes"""
        try:
            now = datetime.now()
            expired_emails = []
            
            for email, data in verification_codes_storage.items():
                if now > data['expires_at']:
                    expired_emails.append(email)
            
            for email in expired_emails:
                del verification_codes_storage[email]
                logging.debug(f"Cleaned up expired verification code for {email}")
                
        except Exception as e:
            logging.error(f"Error cleaning up expired codes: {str(e)}")