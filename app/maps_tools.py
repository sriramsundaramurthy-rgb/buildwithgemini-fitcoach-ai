"""Google Maps Geocoding and Places (New) API tools for FitCoach AI."""

import json
import os
from pathlib import Path
import urllib.parse
import urllib.request
from dotenv import load_dotenv

# Ensure .env variables are loaded in local dev
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


def _get_maps_api_key() -> str:
    """Reads Google Maps API key from environment variable."""
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable is not set.")
    return key



def geocode_address(address: str) -> str:
    """Converts a street address or location name into geographic latitude and longitude coordinates using Geocoding API.

    Args:
        address: The address or place name to geocode (e.g., '1600 Amphitheatre Parkway, Mountain View, CA').

    Returns:
        JSON string with formatted_address, latitude, and longitude.
    """
    api_key = _get_maps_api_key()
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={api_key}"

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") != "OK" or not data.get("results"):
                return f"Geocoding failed for address '{address}': {data.get('error_message', data.get('status'))}"

            first_result = data["results"][0]
            location = first_result["geometry"]["location"]
            result = {
                "address": address,
                "formatted_address": first_result.get("formatted_address"),
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
            }
            return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error executing Geocoding request: {str(e)}"


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "gym",
    radius_meters: float = 3000.0,
) -> str:
    """Finds nearby places of a given type around a location using Google Places API (New) searchNearby.

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Type of place to search for (e.g. 'gym', 'park', 'sports_complex', 'health').
        radius_meters: Search radius in meters (default 3000.0).

    Returns:
        JSON string listing nearby places with name, formatted address, and location coordinates.
    """
    api_key = _get_maps_api_key()
    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
        "Content-Type": "application/json",
    }

    body = {
        "includedTypes": [place_type.lower()],
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": radius_meters,
            }
        },
    }

    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            places = data.get("places", [])
            if not places:
                return f"No nearby places of type '{place_type}' found within {radius_meters}m of ({latitude}, {longitude})."

            results = []
            for p in places:
                results.append({
                    "name": p.get("displayName", {}).get("text", "Unknown"),
                    "address": p.get("formattedAddress", "N/A"),
                    "location": {
                        "latitude": p.get("location", {}).get("latitude"),
                        "longitude": p.get("location", {}).get("longitude"),
                    },
                })
            return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error executing Places searchNearby request: {str(e)}"
