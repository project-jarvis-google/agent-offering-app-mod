import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from urllib.parse import quote

load_dotenv()

if os.environ.get("LOCAL_TESTING", "false") == "true":
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)
else:
    db_user = os.environ["DB_USER"]
    db_pass = os.environ["DB_PASS"]
    db_name = os.environ["DB_NAME"]
    instance_conn_name = os.environ["INSTANCE_CONNECTION_NAME"]
    DATABASE_URL = f"postgresql+asyncpg://{db_user}:{quote(db_pass, safe='')}@/{db_name}?host=/cloudsql/{instance_conn_name}"
    engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
