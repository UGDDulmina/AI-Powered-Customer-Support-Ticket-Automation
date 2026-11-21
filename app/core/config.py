from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "AI Customer Support API"
    APP_ENV: str = "development"
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    APP_ENV: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()