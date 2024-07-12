from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SALT: str
    JWT_ALGORITHM: str
    JWT_EXP_MINUTES: int
    MAILGUN_API_KEY: str
    NEXT_PUBLIC_URL: str
    OPENAI_API_KEY: str
    STRIPE_API_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ID: str

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()