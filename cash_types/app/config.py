from dataclasses import dataclass
import os


VALID_STRATEGIES = {"cache_aside", "write_through", "write_back"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return float(raw)


@dataclass(frozen=True)
class Settings:
    cache_strategy: str
    cache_prefix: str
    redis_host: str
    redis_port: int
    redis_db: int
    database_url: str
    db_schema: str
    write_back_flush_interval: float
    write_back_batch_size: int
    startup_seed_size: int


def get_settings() -> Settings:
    strategy = os.getenv("CACHE_STRATEGY", "cache_aside").strip().lower()
    if strategy not in VALID_STRATEGIES:
        raise ValueError(
            f"Unknown CACHE_STRATEGY={strategy!r}. "
            f"Expected one of: {', '.join(sorted(VALID_STRATEGIES))}"
        )

    return Settings(
        cache_strategy=strategy,
        cache_prefix=os.getenv("CACHE_PREFIX", strategy),
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=_int_env("REDIS_PORT", 6379),
        redis_db=_int_env("REDIS_DB", 0),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/cache_practice",
        ),
        db_schema=os.getenv("DB_SCHEMA", strategy),
        write_back_flush_interval=_float_env("WRITE_BACK_FLUSH_INTERVAL", 2.0),
        write_back_batch_size=_int_env("WRITE_BACK_BATCH_SIZE", 100),
        startup_seed_size=_int_env("STARTUP_SEED_SIZE", 1000),
    )
