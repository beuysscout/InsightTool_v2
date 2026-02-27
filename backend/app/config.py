from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Insight Tool"
    debug: bool = False

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Anthropic
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # File storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
