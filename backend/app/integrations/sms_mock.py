from app.core.config import settings
from app.core.logging import safe_logger


class MockSMSDelivery:
    """Mock SMS Delivery Adapter for patient consent OTPs.
    Enforces zero-leakage logging policy in production environments.
    """

    async def send_otp(self, phone_masked: str, otp: str, challenge_id: str) -> dict:
        if settings.app_env == "production":
            safe_logger.info(f"OTP dispatch requested for recipient {phone_masked} (challenge {challenge_id})")
            message = "OTP dispatched via telecommunications gateway"
        else:
            safe_logger.info(f"[DEV ONLY] OTP challenge {challenge_id} generated for {phone_masked}")
            message = f"DEMO OTP: {otp}"

        return {
            "delivered": True,
            "recipient": phone_masked,
            "challenge_id": challenge_id,
            "message": message
        }


sms_gateway = MockSMSDelivery()
