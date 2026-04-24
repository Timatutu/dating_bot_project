from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    bot_token: str
    database_url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/dating_bot"
    redis_url: str = "redis://127.0.0.1:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@127.0.0.1:5672/"
    minio_endpoint: str = "127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "photos"
    minio_use_ssl: bool = False
    payment_service_host: str = "localhost"
    payment_service_grpc_port: int = 50051

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = BotSettings()
