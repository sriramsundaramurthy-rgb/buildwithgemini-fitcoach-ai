"""Firestore tools for FitCoach AI exercises catalog."""

import json
from google.cloud import firestore

# Hardcoded project ID as string per requirements (prevents Agent Platform project number issue)
PROJECT_ID = "qwiklabs-gcp-02-7f6f16f4aa3e"


def _get_firestore_client():
    return firestore.Client(project=PROJECT_ID)


def list_exercises(muscle_group: str = "", equipment: str = "") -> str:
    """Lists exercises from the Firestore database, optionally filtering by muscle group or equipment.

    Args:
        muscle_group: Optional string to filter exercises by target muscle group (e.g., 'Legs', 'Chest', 'Back', 'Core', 'Arms').
        equipment: Optional string to filter exercises by equipment type (e.g., 'Barbell', 'Dumbbells', 'Bodyweight').

    Returns:
        JSON string containing the list of matching exercise documents.
    """
    db = _get_firestore_client()
    docs = db.collection("exercises").stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        # Apply optional filters (case-insensitive substring match)
        if muscle_group and muscle_group.lower() not in data.get("muscle_group", "").lower():
            continue
        if equipment and equipment.lower() not in data.get("equipment", "").lower():
            continue

        results.append(data)

    if not results:
        return f"No exercises found matching muscle_group='{muscle_group}' and equipment='{equipment}'."

    return json.dumps(results, indent=2)


def get_exercise_details(exercise_id: str) -> str:
    """Gets detailed information for a specific exercise by its exercise ID from Firestore.

    Args:
        exercise_id: The unique identifier of the exercise (e.g., 'barbell-squat', 'pull-up', 'plank').

    Returns:
        JSON string containing the exercise details, or an error message if not found.
    """
    db = _get_firestore_client()
    doc_ref = db.collection("exercises").document(exercise_id)
    doc = doc_ref.get()

    if not doc.exists:
        return f"Exercise with ID '{exercise_id}' not found in database."

    data = doc.to_dict()
    data["id"] = doc.id
    return json.dumps(data, indent=2)


def add_exercise(
    exercise_id: str,
    name: str,
    muscle_group: str,
    equipment: str,
    difficulty: str,
    description: str,
    sets_reps: str,
) -> str:
    """Adds a new exercise or updates an existing exercise in the Firestore database.

    Args:
        exercise_id: Unique slug identifier for the exercise (e.g., 'kettlebell-swing').
        name: Display name of the exercise (e.g., 'Kettlebell Swing').
        muscle_group: Primary muscle group targeted (e.g., 'Glutes', 'Legs', 'Full Body').
        equipment: Equipment required (e.g., 'Kettlebell', 'Dumbbell', 'Bodyweight').
        difficulty: Difficulty level ('Beginner', 'Intermediate', 'Advanced').
        description: A short explanation of proper form and execution.
        sets_reps: Recommended set and rep scheme (e.g., '3 sets of 15 reps').

    Returns:
        A confirmation message with the added exercise ID.
    """
    db = _get_firestore_client()
    data = {
        "name": name,
        "muscle_group": muscle_group,
        "equipment": equipment,
        "difficulty": difficulty,
        "description": description,
        "sets_reps": sets_reps,
    }
    db.collection("exercises").document(exercise_id).set(data)
    return f"Successfully saved exercise '{name}' (ID: {exercise_id}) to Firestore."
