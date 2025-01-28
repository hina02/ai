from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_access_token: str | None = None
    supabase_dev_email: str
    supabase_dev_password: str
    tavily_api_key: str | None = None
    openai_api_key: str
    gemini_api_key: str
    anthropic_api_key: str
    neo4j_uri: str
    neo4j_auth: str

    class Config:
        env_file = ".env"


settings = Settings()
