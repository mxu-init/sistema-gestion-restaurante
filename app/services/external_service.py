import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1"
COCKTAILDB_BASE = "https://www.thecocktaildb.com/api/json/v1/1"
USER_AGENT = "RestaurantManager/1.0 (contact@example.com)"
TIMEOUT_SECONDS = 10

CACHE_TTL_SECONDS = 60
_search_cache: dict[str, tuple[float, list[dict]]] = {}


class ExternalApiError(Exception):
    """The external recipe API could not be reached or returned an error."""


def _request_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read()
    except urllib.error.HTTPError as error:
        raise ExternalApiError(f"external api returned http {error.code}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ExternalApiError(f"external api unreachable: {error}") from error
    try:
        return json.loads(payload.decode("utf-8", "replace"))
    except json.JSONDecodeError as error:
        raise ExternalApiError("external api returned invalid json") from error


def _cached_search(cache_key: str, url: str) -> list[dict]:
    cached = _search_cache.get(cache_key)
    if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]
    payload = _request_json(url)
    _search_cache.clear()
    _search_cache[cache_key] = (time.monotonic(), payload)
    return payload


def _normalize_meal(meal: dict) -> dict:
    return {
        "source": "mealdb",
        "source_id": str(meal.get("idMeal") or ""),
        "name": (meal.get("strMeal") or "").strip(),
        "description": (meal.get("strInstructions") or "").strip() or None,
        "category": (meal.get("strCategory") or "").strip() or None,
        "image_url": (meal.get("strMealThumb") or "").strip() or None,
    }


def _normalize_drink(drink: dict) -> dict:
    return {
        "source": "cocktaildb",
        "source_id": str(drink.get("idDrink") or ""),
        "name": (drink.get("strDrink") or "").strip(),
        "description": (drink.get("strInstructions") or "").strip() or None,
        "category": (drink.get("strCategory") or "").strip() or None,
        "image_url": (drink.get("strDrinkThumb") or "").strip() or None,
    }


def search_meals(query: str, limit: int = 10) -> list[dict]:
    encoded = urllib.parse.quote(query)
    url = f"{MEALDB_BASE}/search.php?s={encoded}"
    payload = _cached_search(f"meals:{query.lower()}", url)
    meals = payload.get("meals") or []
    return [_normalize_meal(meal) for meal in meals[:limit] if meal.get("idMeal")]


def search_drinks(query: str, limit: int = 10) -> list[dict]:
    encoded = urllib.parse.quote(query)
    url = f"{COCKTAILDB_BASE}/search.php?s={encoded}"
    payload = _cached_search(f"drinks:{query.lower()}", url)
    drinks = payload.get("drinks") or []
    return [_normalize_drink(drink) for drink in drinks[:limit] if drink.get("idDrink")]


def lookup_product(source: str, source_id: str) -> Optional[dict]:
    encoded = urllib.parse.quote(source_id)
    if source == "mealdb":
        url = f"{MEALDB_BASE}/lookup.php?i={encoded}"
        payload = _request_json(url)
        meals = payload.get("meals") or []
        return _normalize_meal(meals[0]) if meals else None
    if source == "cocktaildb":
        url = f"{COCKTAILDB_BASE}/lookup.php?i={encoded}"
        payload = _request_json(url)
        drinks = payload.get("drinks") or []
        return _normalize_drink(drinks[0]) if drinks else None
    raise ValueError(f"unknown source: {source}")
