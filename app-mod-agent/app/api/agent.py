import os
from dotenv.main import load_dotenv
from urllib.parse import quote
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.adk.sessions import InMemorySessionService
from google.adk.errors.session_not_found_error import SessionNotFoundError
from google.adk.utils.context_utils import Aclosing
from app import root_agent
from google.adk import Runner
from google.adk.cli.adk_web_server import RunAgentRequest
from google.adk.events.event import Event
from fastapi import APIRouter, HTTPException
import logging

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

db_user = os.environ.get("DB_USER", "postgres")
db_name = os.environ.get("DB_NAME", "postgres")
db_pass = quote(os.environ.get("DB_PASS"), safe='')
instance_conn_name = os.environ.get("INSTANCE_CONNECTION_NAME")

SESSION_SERVICE_URI = f"postgresql+asyncpg://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{instance_conn_name}"

router = APIRouter(prefix="/app-mod", tags=["Agent"])
session_service = DatabaseSessionService(db_url=SESSION_SERVICE_URI)

async def get_or_create_session(session_id: str, uuid: str, app_name: str):
  try:
    logger.info("Inside get_or_create_session")
    logger.info(f"session_id: {session_id}, user_id: {uuid}")
    session = await session_service.get_session(app_name=app_name, session_id=session_id, user_id=uuid)
    if session is not None:
      logger.info("Session already exists")
      return
  except Exception as e:
    logger.exception("Exception occurred while getting session or session doesn't exist")

  try:
    logger.info("Session not found, creating session")
    return await session_service.create_session(
        user_id=uuid,
        app_name=app_name,
        session_id=session_id
    )
  except Exception as e:
    logger.exception("Exception occurred while creating session")
    raise

@router.post("/run", response_model_exclude_none=True)
async def invoke_appmod_agent_endpoint(request: RunAgentRequest) -> list[Event]:
  logger.info("Invoking appmod agent with request: %s", request)
  runner = Runner(
    agent=root_agent,
    app_name=request.app_name,
    session_service=session_service,
  )
  await get_or_create_session(request.session_id, request.user_id, request.app_name)
  # _set_telemetry_context_if_needed(runner)
  try:
    async with Aclosing(
        runner.run_async(
            user_id=request.user_id,
            session_id=request.session_id,
            new_message=request.new_message,
            state_delta=request.state_delta,
            invocation_id=request.invocation_id,
        )
    ) as agen:
      events = [event async for event in agen]
  except SessionNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e)) from e
  logger.info("Generated %s events in agent run", len(events))
  logger.debug("Events generated: %s", events)
  return events