"""Seed script to populate Firestore with sample exercise data for FitCoach AI."""

from google.cloud import firestore

# Hardcode project ID as a string per requirements (prevents Agent Platform project number issue)
PROJECT_ID = "qwiklabs-gcp-02-7f6f16f4aa3e"

SEED_EXERCISES = [
    {
        "id": "barbell-squat",
        "name": "Barbell Squat",
        "muscle_group": "Legs",
        "equipment": "Barbell",
        "difficulty": "Intermediate",
        "description": "A foundational compound leg exercise targeting quadriceps, glutes, and hamstrings.",
        "sets_reps": "4 sets of 8-10 reps",
    },
    {
        "id": "dumbbell-bench-press",
        "name": "Dumbbell Bench Press",
        "muscle_group": "Chest",
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "description": "Flat bench dumbbell pressing exercise for pectorals, front deltoids, and triceps.",
        "sets_reps": "3 sets of 10-12 reps",
    },
    {
        "id": "pull-up",
        "name": "Pull-Up",
        "muscle_group": "Back",
        "equipment": "Bodyweight",
        "difficulty": "Intermediate",
        "description": "Bodyweight compound pulling movement targeting the lats, upper back, and biceps.",
        "sets_reps": "3 sets of max reps",
    },
    {
        "id": "plank",
        "name": "Plank",
        "muscle_group": "Core",
        "equipment": "Bodyweight",
        "difficulty": "Beginner",
        "description": "Isometric core exercise that builds endurance in abdominals and lower back.",
        "sets_reps": "3 sets of 60 seconds hold",
    },
    {
        "id": "dumbbell-bicep-curl",
        "name": "Dumbbell Bicep Curl",
        "muscle_group": "Arms",
        "equipment": "Dumbbells",
        "difficulty": "Beginner",
        "description": "Isolation exercise targeting the biceps brachii for arm strength.",
        "sets_reps": "3 sets of 12 reps",
    },
]


def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("exercises")

    print(f"Seeding Firestore collection 'exercises' in project '{PROJECT_ID}'...")
    for exercise in SEED_EXERCISES:
        doc_id = exercise["id"]
        data = {k: v for k, v in exercise.items() if k != "id"}
        collection_ref.document(doc_id).set(data)
        print(f"  ✓ Added exercise: {exercise['name']} ({doc_id})")

    print("Seeding complete!")


if __name__ == "__main__":
    seed_database()
