import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from app.api.routes import ingest
from app.core.database import engine, Base

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # We could also dispose of the engine here if needed

app = FastAPI(
    lifespan=lifespan
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="GitHub to GCS Ingestion Service",
        description="Service to ingest GitHub repos to Google Cloud Storage.",
        version="1.0.0",
        routes=app.routes,
    )
    # Add servers based on current environment
    openapi_schema["servers"] = [
        {"url": "https://iw-ingestion-svc-428871167882.us-central1.run.app", "description": "AppMod Ingestion Service Server"},
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

if os.environ.get("LOCAL_TESTING", "false") != "true":
    app.openapi = custom_openapi

app.include_router(ingest.router)
