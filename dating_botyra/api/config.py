from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/dating_bot"
    redis_url: str = "redis://localhost:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "photos"
    secret_key: str = "change-me-in-production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
