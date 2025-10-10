import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://sensoruser:secret123@localhost:5432/sensordb")

engine = create_async_engine(
    DATABASE_URL,                      # 例: postgresql+asyncpg://user:pwd@localhost/db
    pool_size=50,                      # ↑ 连接池
    max_overflow=50,
    pool_timeout=30,
    pool_recycle=1800,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)  # ← 关键

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
