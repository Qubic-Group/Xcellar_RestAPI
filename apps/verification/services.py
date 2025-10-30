import logging
from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class TwilioService:
    """
    Service wrapper for Twilio Verify API.
    Handles OTP sending via SMS, WhatsApp, and Voice.
    """
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.verify_service_sid = getattr(settings, 'TWILIO_VERIFY_SERVICE_SID', '')
        self.whatsapp_number = getattr(settings, 'TWILIO_WHATSAPP_NUMBER', '')
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            logger.warning("Twilio credentials not configured. Verification will be disabled.")
    
    def send_otp(self, phone_number, method='SMS'):
        """
        Send OTP via Twilio Verify API.
        
        Args:
            phone_number: Phone number in E.164 format
            method: Verification method (SMS, WHATSAPP, or VOICE)
        
        Returns:
            tuple: (success: bool, message: str, verification_sid: str or None)
        """
        if not self.client or not self.verify_service_sid:
            logger.error("Twilio not configured properly")
            return False, "Verification service not configured", None
        
        try:
            # Map method to Twilio channel
            channel_map = {
                'SMS': 'sms',
                'WHATSAPP': 'whatsapp',
                'VOICE': 'call',
            }
            channel = channel_map.get(method.upper(), 'sms')
            
            # Send verification code via Twilio Verify API
            verification = self.client.verify.v2.services(
                self.verify_service_sid
            ).verifications.create(
                to=phone_number,
                channel=channel
            )
            
            logger.info(f"OTP sent to {phone_number} via {method}. SID: {verification.sid}")
            return True, "OTP sent successfully", verification.sid
            
        except TwilioRestException as e:
            logger.error(f"Twilio error: {e.msg}")
            return False, f"Failed to send OTP: {e.msg}", None
        except Exception as e:
            logger.error(f"Unexpected error sending OTP: {str(e)}")
            return False, "Failed to send OTP", None
    
    def verify_otp(self, phone_number, code):
        """
        Verify OTP code using Twilio Verify API.
        
        Args:
            phone_number: Phone number in E.164 format
            code: OTP code to verify
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.client or not self.verify_service_sid:
            logger.error("Twilio not configured properly")
            return False, "Verification service not configured"
        
        try:
            verification_check = self.client.verify.v2.services(
                self.verify_service_sid
            ).verification_checks.create(
                to=phone_number,
                code=code
            )
            
            if verification_check.status == 'approved':
                logger.info(f"OTP verified successfully for {phone_number}")
                return True, "OTP verified successfully"
            else:
                logger.warning(f"OTP verification failed for {phone_number}: {verification_check.status}")
                return False, "Invalid or expired OTP code"
                
        except TwilioRestException as e:
            logger.error(f"Twilio verification error: {e.msg}")
            return False, f"Verification failed: {e.msg}"
        except Exception as e:
            logger.error(f"Unexpected error verifying OTP: {str(e)}")
            return False, "Failed to verify OTP"


# Singleton instance
twilio_service = TwilioService()

