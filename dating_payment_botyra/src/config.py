from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/payment_db"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    eth_rpc_url: str = ""
    usdt_contract_address: str = "0xdAC17F958D2ee523a2206206994597C13D831ec7"  
    payment_factory_address: str = ""
    treasury_address: str = ""
    factory_owner_private_key: str = ""  
    crypto_payment_timeout_minutes: int = 15
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
