from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = "Nena AI API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    supabase_url: str = "https://nena-ai-demo.supabase.co"
    supabase_anon_key: str = "synthetic-anon-key-placeholder"
    supabase_service_role_key: str = "synthetic-service-role-key-placeholder"
    supabase_jwt_secret: str | None = None

    # Keyed HMAC secret for patient reference & device fingerprint hashing
    app_hmac_secret: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5

    anomaly_manual_review_threshold: int = 40
    anomaly_reject_threshold: int = 85

    mpesa_mode: str = "mock"
    mpesa_callback_secret: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    mock_mpesa_latency_ms: int = 0
    mock_mpesa_failure_rate: float = 0.0

    @field_validator("app_hmac_secret")
    @classmethod
    def validate_hmac_secret(cls, value: str) -> str:
        if len(value) < 32 or value.startswith("REPLACE"):
            raise ValueError("APP_HMAC_SECRET must be a unique secret of at least 32 characters")
        return value

    @field_validator("mpesa_mode")
    @classmethod
    def validate_mpesa_mode(cls, value: str) -> str:
        if value not in {"mock"}:
            raise ValueError("Only MPESA_MODE=mock is implemented in this MVP")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
