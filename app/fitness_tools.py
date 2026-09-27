"""Fitness metrics calculation and public API tools for FitCoach AI."""

import base64
import json
import os
import re
import urllib.request
import uuid
from google import genai
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

# Hardcoded bucket name per prompt instructions
BUCKET_NAME = "fitcoach-ai-public-qwiklabs-gcp-02-7f6f16f4aa3e"


def calculate_workout_metrics(
    weight_kg: float,
    duration_minutes: int,
    exercise_type: str = "running",
    intensity: str = "moderate",
    age: int = 30,
) -> str:
    """Calculates estimated calories burned and target heart rate zones for a workout.

    Args:
        weight_kg: User's body weight in kilograms (e.g. 70.0).
        duration_minutes: Duration of the workout session in minutes (e.g. 45).
        exercise_type: Type of exercise (e.g. 'running', 'cycling', 'swimming', 'weightlifting', 'walking').
        intensity: Workout intensity level ('low', 'moderate', 'high').
        age: User's age in years (used to estimate max heart rate, default 30).

    Returns:
        JSON string with calculated calories burned, MET value, and heart rate training zones.
    """
    # MET (Metabolic Equivalent of Task) table
    met_table = {
        "running": {"low": 7.0, "moderate": 10.0, "high": 12.5},
        "cycling": {"low": 6.0, "moderate": 8.0, "high": 10.0},
        "swimming": {"low": 6.0, "moderate": 8.0, "high": 10.0},
        "weightlifting": {"low": 3.5, "moderate": 5.0, "high": 6.0},
        "walking": {"low": 3.0, "moderate": 4.0, "high": 5.0},
    }

    ex_key = exercise_type.lower()
    intens_key = intensity.lower() if intensity.lower() in ["low", "moderate", "high"] else "moderate"

    # Default to walking/general exercise if type not found
    exercise_mets = met_table.get(ex_key, met_table["walking"])
    met = exercise_mets.get(intens_key, 4.0)

    # Calorie calculation formula: Calories = MET * weight_kg * hours
    calories_burned = round(met * weight_kg * (duration_minutes / 60.0), 1)

    # Heart Rate Zones (Max HR = 220 - age)
    max_hr = max(100, 220 - age)
    hr_zones = {
        "max_heart_rate": max_hr,
        "fat_burn_zone_bpm": f"{round(max_hr * 0.60)}-{round(max_hr * 0.70)} bpm (60-70%)",
        "cardio_zone_bpm": f"{round(max_hr * 0.70)}-{round(max_hr * 0.80)} bpm (70-80%)",
        "peak_zone_bpm": f"{round(max_hr * 0.80)}-{round(max_hr * 0.90)} bpm (80-90%)",
    }

    result = {
        "exercise_type": exercise_type,
        "intensity": intens_key,
        "duration_minutes": duration_minutes,
        "weight_kg": weight_kg,
        "calories_burned": calories_burned,
        "met_value": met,
        "heart_rate_zones": hr_zones,
    }

    return json.dumps(result, indent=2)


def fetch_online_exercises(category: str = "", limit: int = 5) -> str:
    """Fetches real exercise data from the free public wger Exercise API.

    Args:
        category: Optional category filter (e.g. 'Legs', 'Abs', 'Arms', 'Shoulders', 'Chest', 'Back').
        limit: Maximum number of exercise items to return (default 5).

    Returns:
        JSON string containing matching exercise names, categories, equipment, and descriptions.
    """
    url = "https://wger.de/api/v2/exerciseinfo/?limit=50"
    headers = {"User-Agent": "FitCoachAI/1.0 (contact@fitcoach.ai)"}

    # Optional API key read from environment variable per prompt instructions
    api_key = os.environ.get("WGER_API_KEY")
    if api_key:
        headers["Authorization"] = f"Token {api_key}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for item in data.get("results", []):
                translations = item.get("translations", [])
                # Prefer English (language id 2) translation if available
                name = next(
                    (t.get("name") for t in translations if t.get("language") == 2 and t.get("name")),
                    next((t.get("name") for t in translations if t.get("name")), None),
                )
                if not name:
                    continue

                cat_name = item.get("category", {}).get("name", "General")
                if category and category.lower() not in cat_name.lower():
                    continue

                equipment_list = [eq.get("name") for eq in item.get("equipment", []) if eq.get("name")]
                description = next((t.get("description", "") for t in translations if t.get("description")), "")
                clean_desc = re.sub(r"<[^<]+?>", "", description).strip()[:150]

                results.append({
                    "id": item.get("id"),
                    "name": name,
                    "category": cat_name,
                    "equipment": equipment_list if equipment_list else ["Bodyweight"],
                    "description": clean_desc,
                })
                if len(results) >= limit:
                    break

            if not results:
                return f"No online exercises found matching category '{category}'."

            return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error fetching exercises from wger public API: {str(e)}"


def generate_workout_visual(
    prompt: str,
    tool_context: ToolContext = None,
) -> str:
    """Generates an image visual for a workout or exercise using gemini-3.1-flash-lite-image model, saves it as an ADK artifact, and uploads it to Cloud Storage.

    Args:
        prompt: Description of the exercise or workout image to generate (e.g. 'An energetic illustration of a person doing barbell squats in a gym').
        tool_context: ToolContext object provided automatically by the agent framework.

    Returns:
        The public HTTPS URL of the uploaded image on Cloud Storage.
    """
    client = genai.Client(vertexai=True, project="qwiklabs-gcp-02-7f6f16f4aa3e", location="global")

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        image_bytes = None
        mime_type = "image/png"
        for candidate in response.candidates:
            if not candidate.content or not candidate.content.parts:
                continue
            for part in candidate.content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/png"
                    break
            if image_bytes:
                break

        if not image_bytes:
            return "Failed to generate image bytes from model response."

        ext = "jpg" if "jpeg" in mime_type.lower() else "png"
        filename = f"workout_visual_{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save artifact with tool_context.save_artifact if available
        if tool_context:
            try:
                artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                tool_context.save_artifact(filename=filename, artifact=artifact_part)
            except Exception as e:
                # Log/ignore save_artifact errors in fallback modes
                pass

        # 2. Upload image bytes directly to public Cloud Storage bucket
        storage_client = storage.Client(project="qwiklabs-gcp-02-7f6f16f4aa3e")
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        return f"Error generating or uploading workout visual: {str(e)}"


def generate_exercise_video(
    prompt: str,
    tool_context: ToolContext = None,
) -> str:
    """Generates a short exercise demonstration or workout video using gemini-omni-flash-preview model in the global region, saves it as an ADK artifact, and uploads it to Cloud Storage.

    Args:
        prompt: Description of the exercise or workout video to generate (e.g. 'A short 3-second video showing proper form for a barbell squat in a gym').
        tool_context: ToolContext object provided automatically by the agent framework.

    Returns:
        The public HTTPS URL of the uploaded MP4 video on Cloud Storage.
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-02-7f6f16f4aa3e")
    client = genai.Client(vertexai=True, project=project_id, location="global")

    try:
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )

        video_bytes = None
        if hasattr(interaction, "output_video") and interaction.output_video and getattr(interaction.output_video, "data", None):
            data = interaction.output_video.data
            video_bytes = base64.b64decode(data) if isinstance(data, str) else data
        elif hasattr(interaction, "steps") and interaction.steps:
            for step in interaction.steps:
                if getattr(step, "type", None) == "model_output" and getattr(step, "content", None):
                    for part in step.content:
                        if getattr(part, "type", None) == "video" and getattr(part, "data", None):
                            data = part.data
                            video_bytes = base64.b64decode(data) if isinstance(data, str) else data
                            break
                if video_bytes:
                    break

        if not video_bytes:
            return "Failed to generate video bytes from model response."

        filename = f"exercise_video_{uuid.uuid4().hex[:8]}.mp4"
        mime_type = "video/mp4"

        # 1. Save artifact with tool_context.save_artifact if available
        if tool_context:
            try:
                artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
                tool_context.save_artifact(filename=filename, artifact=artifact_part)
            except Exception:
                # Log/ignore save_artifact errors in fallback modes
                pass

        # 2. Upload video bytes directly to public Cloud Storage bucket
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        return f"Error generating or uploading exercise video: {str(e)}"

