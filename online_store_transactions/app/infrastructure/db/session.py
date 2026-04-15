import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings

database_url = settings.database_url
# Prefer psycopg async dialect for better stability on Windows hosts.
database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
if sys.platform.startswith("win"):
    database_url = database_url.replace("@localhost:", "@127.0.0.1:")

engine = create_async_engine(
    database_url,
    future=True,
    echo=False,
    pool_pre_ping=True,
    poolclass=NullPool,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
