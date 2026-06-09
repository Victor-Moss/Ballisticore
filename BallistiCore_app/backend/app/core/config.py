from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    # Public base URL used to build PDF links Twilio can fetch (e.g. https://abc123.ngrok.io).
    # Leave blank to fall back to text-only WhatsApp messages.
    PUBLIC_BASE_URL: str = ""
    PERMIT_LINK_TTL_MINUTES: int = 1440  # 24h — Twilio fetches the media shortly after send

    PDF_STORAGE_PATH: str = "permits/"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"  # comma-separated in production

    # Path to the built React frontend (dist/). When set and present, the backend
    # serves the UI itself so a single process delivers both API and app — used by
    # the self-hosted installer. Left blank in dev, where Vite serves the UI.
    FRONTEND_DIST: str = ""

    def get_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
