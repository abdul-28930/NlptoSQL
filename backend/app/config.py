from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "NL to SQL API"
    debug: bool = True

    # SQLite database file in project root by default
    database_url: str = "sqlite:///./nl_to_sql.db"

    # Hugging Face model configuration (small, local SLM)
    hf_model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"
    max_new_tokens: int = 256
    temperature: float = 0.2
    top_p: float = 0.9

    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

