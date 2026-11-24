from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "CampusFix AI"
    environment: str = "development"
    secret_key: str = "dev-only-change-this-secret"
    access_token_minutes: int = 90
    database_url: str = "sqlite:///./campusfix.db"
    cors_origins: str = "http://localhost:5173"
    upload_dir: str = "uploads"
    max_upload_mb: int = 12
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    groq_audio_model: str = "whisper-large-v3-turbo"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_document_secondary_model: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/free"
    openrouter_vision_model: str = ""
    ai_monthly_budget_usd: float = 1.0
    ai_estimated_cost_per_call_usd: float = 0.002
    ai_cost_per_million_tokens_usd: float = 0.50
    ai_max_input_chars: int = 10000
    ai_retry_attempts: int = 2
    campusfix_ca_bundle: str = ""
    duplicate_window_minutes: int = 10
    require_second_model: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
