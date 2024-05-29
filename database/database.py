from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database.config import settings, redis_port, redis_host
from redis.asyncio import ConnectionPool



# redis conn
pool = ConnectionPool(host=redis_host, port=redis_port, db=1, decode_responses=True,)

#pool = ConnectionPool.from_url(f"redis://{redis_host}:{redis_port}")
redis_url = f"redis://{redis_host}:{redis_port}"


# postgres engine
async_engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=False,
)

async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)