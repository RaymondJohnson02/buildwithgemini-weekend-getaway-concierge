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
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore
from google.genai import types


MODEL = "gemini-3.8-flash"
PROJECT_ID = "qwiklabs-gcp-04-9c93db10a08a"


def _get_firestore_client() -> firestore.Client:
    """Return a Firestore client configured with the hardcoded GCP Project ID."""
    return firestore.Client(project=PROJECT_ID)


def list_getaway_packages(
    city: Optional[str] = None,
    cuisine: Optional[str] = None,
    max_budget_usd: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """List or search weekend getaway packages and food tours from Firestore.

    Args:
        city: Optional city name to filter packages (e.g., 'San Francisco', 'New York', 'Austin').
        cuisine: Optional cuisine keyword to filter packages (e.g., 'Seafood', 'Mexican', 'BBQ', 'Italian').
        max_budget_usd: Optional maximum estimated budget in USD.

    Returns:
        A list of matching getaway package dictionaries.
    """
    db = _get_firestore_client()
    docs = db.collection("getaway_packages").stream()
    results = []

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        if city and city.strip().lower() not in data.get("city", "").lower():
            continue

        if cuisine:
            cuisine_lower = cuisine.strip().lower()
            cuisines = [c.lower() for c in data.get("cuisines", [])]
            if not any(cuisine_lower in c for c in cuisines):
                continue

        if max_budget_usd is not None and data.get("estimated_budget_usd", 0) > max_budget_usd:
            continue

        results.append(data)

    return results


def get_getaway_package_details(package_id: str) -> Dict[str, Any]:
    """Retrieve complete itinerary and details for a specific getaway package ID.

    Args:
        package_id: The ID of the getaway package (e.g., 'sf-fog-foodie', 'austin-tacos-smoke').

    Returns:
        The getaway package dictionary if found, or an error dictionary.
    """
    db = _get_firestore_client()
    doc_ref = db.collection("getaway_packages").document(package_id)
    doc = doc_ref.get()

    if not doc.exists:
        return {"error": f"Package with ID '{package_id}' not found."}

    data = doc.to_dict()
    data["id"] = doc.id
    return data


def save_getaway_package(
    package_id: str,
    title: str,
    city: str,
    state: str,
    estimated_budget_usd: int,
    cuisines: List[str],
    highlights: List[str],
    theme: str = "Food & Culture",
    duration_hours: int = 48,
) -> Dict[str, Any]:
    """Create or update a curated weekend getaway package in Firestore.

    Args:
        package_id: A unique identifier slug (e.g., 'chicago-deep-dish-tour').
        title: The display title of the weekend package.
        city: Destination city.
        state: State abbreviation or name.
        estimated_budget_usd: Estimated total cost per person in USD.
        cuisines: List of cuisines featured on the tour.
        highlights: Key activities and food tastings included.
        theme: Theme of the package.
        duration_hours: Length of the getaway in hours (default: 48).

    Returns:
        A dictionary confirming the package was saved with its ID.
    """
    db = _get_firestore_client()
    package_data = {
        "id": package_id,
        "title": title,
        "city": city,
        "state": state,
        "estimated_budget_usd": estimated_budget_usd,
        "cuisines": cuisines,
        "highlights": highlights,
        "theme": theme,
        "duration_hours": duration_hours,
    }
    db.collection("getaway_packages").document(package_id).set(package_data, merge=True)
    return {"status": "success", "package_id": package_id, "package": package_data}


def get_live_weekend_weather(city: str) -> Dict[str, Any]:
    """Fetch live multi-day weather forecast for any destination city using the free Open-Meteo API.

    Args:
        city: Name of the destination city (e.g. 'San Francisco', 'Austin', 'New York', 'Portland', 'Tokyo').

    Returns:
        A dictionary containing real forecast metrics (dates, max/min temperatures in Fahrenheit, precipitation probability).
    """
    import json
    import urllib.parse
    import urllib.request

    try:
        # Step 1: Geocode city name to lat/lon
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=en&format=json"
        req = urllib.request.Request(geo_url, headers={"User-Agent": "WeekendGetawayAgent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            geo_data = json.loads(response.read().decode())

        if not geo_data.get("results"):
            return {"error": f"Could not find coordinates for city '{city}'."}

        place = geo_data["results"][0]
        lat, lon = place["latitude"], place["longitude"]
        resolved_name = f"{place.get('name')}, {place.get('admin1', '')} {place.get('country', '')}".strip()

        # Step 2: Fetch forecast from Open-Meteo
        forecast_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            "&temperature_unit=fahrenheit&timezone=auto"
        )
        req_forecast = urllib.request.Request(forecast_url, headers={"User-Agent": "WeekendGetawayAgent/1.0"})
        with urllib.request.urlopen(req_forecast, timeout=5) as response:
            forecast_data = json.loads(response.read().decode())

        daily = forecast_data.get("daily", {})
        dates = daily.get("time", [])[:3]
        max_temps = daily.get("temperature_2m_max", [])[:3]
        min_temps = daily.get("temperature_2m_min", [])[:3]
        precip = daily.get("precipitation_probability_max", [])[:3]

        forecast_summary = [
            {
                "date": d,
                "high_f": high,
                "low_f": low,
                "rain_probability_percent": pop,
            }
            for d, high, low, pop in zip(dates, max_temps, min_temps, precip)
        ]

        return {
            "city": resolved_name,
            "forecast": forecast_summary,
            "source": "Open-Meteo Public API (free, no key required)",
        }
    except Exception as e:
        return {"error": f"Failed to retrieve weather for {city}: {str(e)}"}


def calculate_trip_budget(
    base_cost_per_person: float,
    num_people: int = 1,
    dining_tip_percent: float = 20.0,
    hotel_nights: int = 2,
    hotel_nightly_rate: float = 0.0,
    transportation_usd: float = 0.0,
) -> Dict[str, Any]:
    """Calculate the estimated total and per-person cost for a weekend getaway.

    Args:
        base_cost_per_person: Base estimated budget per person for food and activities.
        num_people: Number of travelers in the group (default: 1).
        dining_tip_percent: Estimated tip percentage for dining/tours (default: 20%).
        hotel_nights: Number of hotel nights (default: 2 for a weekend).
        hotel_nightly_rate: Total nightly rate for shared lodging in USD (default: 0).
        transportation_usd: Total estimated transit / rideshare / flight cost in USD.

    Returns:
        A breakdown dictionary with total cost, total per person, and line items.
    """
    people = max(1, num_people)
    food_and_activities = base_cost_per_person * people
    tips = food_and_activities * (dining_tip_percent / 100.0)
    lodging = hotel_nightly_rate * hotel_nights
    total_trip_cost = round(food_and_activities + tips + lodging + transportation_usd, 2)
    cost_per_person = round(total_trip_cost / people, 2)

    return {
        "num_people": people,
        "food_and_activities_subtotal": round(food_and_activities, 2),
        "estimated_tips": round(tips, 2),
        "lodging_total": round(lodging, 2),
        "transportation_total": round(transportation_usd, 2),
        "total_group_cost_usd": total_trip_cost,
        "cost_per_person_usd": cost_per_person,
    }


def geocode_address(address: str) -> Dict[str, Any]:
    """Turn an address or city name into latitude and longitude coordinates using Google Maps Geocoding API.

    Args:
        address: The address, landmark, or city name (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'Austin, TX').

    Returns:
        A dictionary containing the formatted address and latitude/longitude coordinates.
    """
    import json
    import os
    import urllib.parse
    import urllib.request

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    encoded_address = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        if data.get("status") != "OK" or not data.get("results"):
            error_msg = data.get("error_message", data.get("status", "Unknown geocoding error"))
            return {"error": f"Geocoding failed for '{address}': {error_msg}"}

        first_result = data["results"][0]
        location = first_result.get("geometry", {}).get("location", {})
        return {
            "formatted_address": first_result.get("formatted_address"),
            "latitude": location.get("lat"),
            "longitude": location.get("lng"),
            "place_id": first_result.get("place_id"),
        }
    except Exception as e:
        return {"error": f"Geocoding request failed: {str(e)}"}


def search_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "restaurant",
    radius_meters: float = 1500.0,
    max_results: int = 5,
) -> Dict[str, Any]:
    """Find nearby places (restaurants, cafes, attractions, bakeries) using Google Places API (New).

    Args:
        latitude: Latitude coordinate.
        longitude: Longitude coordinate.
        place_type: Type of place to search (e.g. 'restaurant', 'cafe', 'bakery', 'bar', 'tourist_attraction').
        radius_meters: Search radius in meters (default: 1500 meters).
        max_results: Maximum number of places to return (1-20, default: 5).

    Returns:
        A dictionary with a list of matching places including name, address, and location.
    """
    import json
    import os
    import urllib.request

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating,places.types",
    }
    payload = json.dumps({
        "includedTypes": [place_type],
        "maxResultCount": min(20, max(1, max_results)),
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": float(radius_meters),
            }
        },
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        places_raw = data.get("places", [])
        results = []
        for p in places_raw:
            display_name = p.get("displayName", {}).get("text", "")
            address = p.get("formattedAddress", "")
            location = p.get("location", {})
            results.append({
                "name": display_name,
                "address": address,
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "rating": p.get("rating"),
                "types": p.get("types", []),
            })

        return {
            "count": len(results),
            "places": results,
        }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {"error": f"Places API returned HTTP {e.code}: {error_body}"}
BUCKET_NAME = "weekend-getaway-assets-qwiklabs-gcp-04-9c93db10a08a"


async def generate_getaway_postcard(
    prompt: str,
    destination_city: str,
    tool_context: Any,
) -> Dict[str, Any]:
    """Generate an AI visual postcard or dish mood board for a weekend getaway using gemini-3.1-flash-lite-image.

    The generated image is saved to the Playground Artifacts and uploaded directly to Cloud Storage.

    Args:
        prompt: Description of the scene or food dishes to visualize (e.g. 'Austin Texas craft smoked brisket and taco platter at sunset patio').
        destination_city: The name of the city (e.g. 'Austin', 'San Francisco', 'New York').

    Returns:
        A dictionary containing the public Cloud Storage image URL, artifact filename, and prompt.
    """
    import uuid
    from google import genai
    from google.cloud import storage
    from google.genai.types import GenerateContentConfig, Modality, Part

    image_gen_client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    full_prompt = (
        f"A beautiful, high-quality digital travel postcard and culinary mood board for a weekend getaway in {destination_city}. "
        f"{prompt}. Vibrant food photography and aesthetic scenery, travel magazine style."
    )

    try:
        response = image_gen_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=full_prompt,
            config=GenerateContentConfig(
                response_modalities=[Modality.IMAGE],
            ),
        )

        image_bytes = None
        mime_type = "image/jpeg"
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.inline_data and part.inline_data.data:
                        image_bytes = part.inline_data.data
                        if part.inline_data.mime_type:
                            mime_type = part.inline_data.mime_type
                        break
            if image_bytes:
                break

        if not image_bytes:
            return {"error": "No image was returned by the image generation model."}

        # (1) Save artifact with tool_context.save_artifact for Playground Artifacts panel
        safe_city = destination_city.lower().replace(" ", "_").replace(",", "")
        artifact_filename = f"postcard_{safe_city}_{uuid.uuid4().hex[:6]}.jpg"
        artifact_part = Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=artifact_filename, artifact=artifact_part)

        # (2) Upload directly to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(artifact_filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{artifact_filename}"

        return {
            "status": "success",
            "destination_city": destination_city,
            "public_image_url": public_url,
            "artifact_filename": artifact_filename,
            "prompt": prompt,
        }
    except Exception as e:
        return {"error": f"Failed to generate getaway postcard: {str(e)}"}


# Load Agent Engine resource name from deployment_metadata.json if available
def _get_agent_engine_resource_name() -> Optional[str]:
    metadata_path = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("remote_agent_runtime_id")
        except Exception:
            pass
    return None


_agent_engine_id = _get_agent_engine_resource_name()
_code_executor = (
    AgentEngineSandboxCodeExecutor(agent_engine_resource_name=_agent_engine_id)
    if _agent_engine_id
    else None
)

async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session to Memory Bank for extraction."""
    await callback_context.add_session_to_memory()
    return None


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the Weekend Getaway & Food Tour Concierge, an expert travel assistant specializing in "
        "curating 48-hour culinary escapes, food tours, and weekend micro-vacations. "
        "You remember the user's dietary preferences, favorite cuisines, budget ranges, and travel history across conversations to personalize recommendations. "
        "Use your Firestore tools to search and retrieve packages (`list_getaway_packages`, `get_getaway_package_details`), "
        "save new custom packages (`save_getaway_package`), calculate group trip budgets (`calculate_trip_budget`), "
        "fetch real-time multi-day weather forecasts (`get_live_weekend_weather`), "
        "convert addresses to coordinates (`geocode_address`), discover nearby spots (`search_nearby_places`), "
        "generate visual getaway postcards (`generate_getaway_postcard`), "
        "and execute Python code for data analysis, complex math, or customized itineraries in the Agent Engine sandbox."
    ),
    code_executor=_code_executor,
    tools=[
        PreloadMemoryTool(),
        list_getaway_packages,
        get_getaway_package_details,
        save_getaway_package,
        calculate_trip_budget,
        get_live_weekend_weather,
        geocode_address,
        search_nearby_places,
        generate_getaway_postcard,
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)


