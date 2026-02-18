from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "NL to SQL API"
    debug: bool = True

    # SQLite database file in project root by default
    database_url: str = "sqlite:///./nl_to_sql.db"

    # Hugging Face model configuration (small, local SLM).
    # Default to a slightly larger but still CPU-friendly instruction model
    # for better SQL generation quality.
    hf_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    max_new_tokens: int = 256
    temperature: float = 0.2
    top_p: float = 0.9

    # Comma-separated list of allowed frontend origins for CORS.
    # Defaults include local dev (Vite) and the deployed Vercel app.
    cors_origins: str = "http://localhost:5173,https://nlpto-sql.vercel.app"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

