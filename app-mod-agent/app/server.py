# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Agent App"""

import os
from dotenv import load_dotenv
from urllib.parse import quote
import google.auth
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, export

from app.api import agent
from app.utils.tracing import CloudTraceLoggingSpanExporter

load_dotenv()

_, project_id = google.auth.default()
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "*").split(",") if os.getenv("ALLOW_ORIGINS") else ["*"]
)

provider = TracerProvider()
processor = export.BatchSpanProcessor(CloudTraceLoggingSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# AlloyDB session configuration
db_user = os.environ.get("DB_USER", "postgres")
db_name = os.environ.get("DB_NAME", "postgres")
db_pass = quote(os.environ.get("DB_PASS"), safe='')
instance_conn_name = os.environ.get("INSTANCE_CONNECTION_NAME")

SESSION_SERVICE_URI = f"postgresql+asyncpg://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{instance_conn_name}"
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    allow_origins=allow_origins,
    session_service_uri=SESSION_SERVICE_URI,
)
app.title = "app-mod-agent-app"
app.description = "API for interacting with the Agent app-mod-agent-app"
app.include_router(agent.router)

# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
