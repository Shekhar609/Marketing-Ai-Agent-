import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)

# Engine configuration with connection pooling
is_sqlite = "sqlite" in settings.DATABASE_URL.lower()
engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
}

if not is_sqlite:
    # High-throughput PostgreSQL connection pool
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_timeout": 30,
    })
else:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# Async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing database sessions to request handlers."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables and pgvector extension."""
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        try:
            from sqlalchemy import text
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info("pgvector extension enabled.")
        except Exception as exc:
            logger.debug(f"pgvector check note: {exc}")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified and ready.")
