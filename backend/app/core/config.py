from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./backend/db.sqlite3"
    secret_key: str = "change-this-secret"
    access_token_expire_minutes: int = 60 * 24
    media_dir: str = "backend/media"
    default_location: str = "Main Office"
    otp_expiry_minutes: int = 30
    cors_origins: list[str] = ["*"]
    
    # FastHub TZ BlkSMS Configuration
    blksms_base_url: str = "https://bulksms.fasthub.co.tz"
    blksms_client_id: str = ""
    blksms_client_secret: str = ""
    blksms_sender_id: str = "REAL DEAL"
    blksms_enabled: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
