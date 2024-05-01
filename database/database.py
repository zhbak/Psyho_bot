import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import URL, create_engine, text
from database.config import settings, redis_port, redis_host
from redis.asyncio import ConnectionPool, Redis



# redis conn
pool = ConnectionPool(host=redis_host, port=redis_port, decode_responses=True)
redis_url = f"redis://{redis_host}:{redis_port}"


# postgres engine
async_engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=True,
)

async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)