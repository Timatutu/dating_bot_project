from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/payment_db"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5673/"
    eth_rpc_url: str = ""
    usdt_contract_address: str = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    payment_factory_address: str = ""
    treasury_address: str = ""
    factory_owner_private_key: str = ""

    ton_api_url: str = "https://toncenter.com/api/v2"
    ton_api_key: str = ""
    ton_usdt_master_address: str = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"
    ton_payment_factory_address: str = ""
    ton_treasury_address: str = ""
    ton_factory_owner_mnemonic: str = ""
    ton_deposit_wallet_code_boc: str = ""

    solana_rpc_url: str = "https://api.devnet.solana.com"
    solana_program_id: str = ""
    solana_usdc_mint: str = ""
    solana_treasury_address: str = ""
    solana_owner_keypair_path: str = ""

    crypto_payment_timeout_minutes: int = 15
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
