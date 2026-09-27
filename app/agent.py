# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.db_tools import add_exercise, get_exercise_details, list_exercises
from app.fitness_tools import (
    calculate_workout_metrics,
    fetch_online_exercises,
    generate_exercise_video,
    generate_workout_visual,
)
from app.maps_tools import find_nearby_places, geocode_address

# Load Agent Engine resource name from deployment_metadata.json
metadata_path = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
agent_engine_id = None
if metadata_path.exists():
    try:
        with open(metadata_path) as f:
            meta = json.load(f)
            agent_engine_id = meta.get("remote_agent_runtime_id")
    except Exception:
        pass

if not agent_engine_id:
    agent_engine_id = "projects/1001085889930/locations/us-central1/reasoningEngines/1808964358772883456"

memory_bank_id = agent_engine_id.split("/")[-1]

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_id
)


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: After each turn, send the session events to Memory Bank for fact extraction."""
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None


def memory_bank_service_builder():
    """Memory service builder configured for deployment on Agent Runtime."""
    return VertexAiMemoryBankService(
        project=os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-02-7f6f16f4aa3e"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        agent_engine_id=memory_bank_id,
    )


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description="You are FitCoach AI, an intelligent fitness assistant that helps users find exercises, log workouts, compute training metrics, locate nearby gyms and fitness centers, generate workout visual illustrations, run Python code analysis in a sandbox, and manage workout plans. Always remember, record, and strictly account for user allergies, dietary restrictions, and stated health preferences across conversations to personalize all fitness and nutrition advice.",
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
    tools=[
        PreloadMemoryTool(),
        generate_exercise_video,
        generate_workout_visual,
        geocode_address,
        find_nearby_places,
        fetch_online_exercises,
        calculate_workout_metrics,
        list_exercises,
        get_exercise_details,
        add_exercise,
        get_weather,
        get_current_time,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
