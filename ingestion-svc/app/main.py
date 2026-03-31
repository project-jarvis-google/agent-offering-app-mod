from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import ingest
from app.core.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # We could also dispose of the engine here if needed

app = FastAPI(
    title="GitHub to GCS Ingestion Service",
    description="Enterprise-grade service to ingest GitHub repos to Google Cloud Storage.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(ingest.router)
