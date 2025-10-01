from collections import defaultdict

from asgiref.sync import sync_to_async
from async_lru import alru_cache
from django.contrib.gis.geos import Polygon
from django.http import HttpRequest
from ninja import NinjaAPI
import httpx
from .models import JobOpening
from .schemas import DistanceCalculation, PlacesSearchResult, IsochroneOut, JobOpeningOut

api = NinjaAPI()


@api.post("/jobs/calc_distance", response=float)
async def calc_distance(request: HttpRequest, params: DistanceCalculation):
    job = await sync_to_async(JobOpening.objects.get)(pk=params.job_id)
    async with httpx.AsyncClient() as client:
        request_params = {
            "profile": params.profile,
            "points": [
                [params.abfahrtsort.lon, params.abfahrtsort.lat],
                job.location.coords,
            ],
            "instructions": False,
            "calc_points": False,
            "details": [
                "time",
            ],
        }
        resp = await client.post("http://localhost:8989/route", json=request_params, timeout=30000)
        resp.raise_for_status()
        data = resp.json()
    distance = data.get("paths", [{"distance": 0}])[0]["distance"]
    return round(distance / 1000, 1)


@api.get("/jobs", response=list[JobOpeningOut])
async def jobs(request: HttpRequest, travel_time_minutes: int, lat: float, lon: float, profile: str):
    travel_time_seconds = travel_time_minutes * 60
    isochrone = await retrieve_isochrone(travel_time_seconds=travel_time_seconds, lat=lat, lon=lon, profile=profile)

    polygons = isochrone.get("polygons", [])
    all_polygons = []
    for p in polygons:
        rings = p.get("geometry", {}).get("coordinates", [])

        all_polygons.append(Polygon(*rings))

    def load_jobs_sync():
        return list(JobOpening.objects.filter(location__isnull=False, location__within=all_polygons).all())

    return await sync_to_async(load_jobs_sync, thread_sensitive=True)()


@api.get("/generate_isochrone", response=IsochroneOut)
async def generate_isochrone(request: HttpRequest, travel_time_minutes: int, lat: float, lon: float, profile: str):
    travel_time_seconds = travel_time_minutes * 60
    resp = await retrieve_isochrone(travel_time_seconds=travel_time_seconds, lat=lat, lon=lon, profile=profile)
    polygons = resp.get("polygons", [])
    results = []
    for p in polygons:
        rings = p.get("geometry", {}).get("coordinates", [])

        results.append({"rings": rings})
    return {"polygons": results}


@alru_cache(maxsize=32)
async def retrieve_isochrone(*, travel_time_seconds: int, lat: float, lon: float, profile: str) -> dict:
    async with httpx.AsyncClient() as client:
        params = {
            "point": f"{lat},{lon}",
            "key": "",
            "profile": profile,
            "time_limit": travel_time_seconds,
        }
        resp = await client.get("http://localhost:8989/isochrone", params=params, timeout=30000)
        resp.raise_for_status()
        data = resp.json()
    return data


def process_features_for_ambiguity(features: list[dict]) -> list[dict]:
    """
    Analyzes a list of Photon features to determine if the canton
    should be shown to resolve ambiguity.

    This function adds a `show_canton: bool` flag to each feature's
    properties.
    """
    if not features:
        return []

    # Step 1: Group all features by their city name.
    city_groups = defaultdict(list)
    for feature in features:
        properties = feature.get("properties", {})
        # Use the city, but fall back to the feature's name if city is missing.
        city_name = properties.get("city") or properties.get("name")
        if city_name:
            city_groups[city_name].append(feature)

    # Step 2: Identify which city names are ambiguous (appear in multiple cantons).
    ambiguous_city_names = set()
    for city_name, features_in_group in city_groups.items():
        # Create a set of unique canton names for this city group.
        # We discard None in case a feature is missing a state.
        cantons_in_group = {f.get("properties", {}).get("state") for f in features_in_group}
        cantons_in_group.discard(None)

        if len(cantons_in_group) > 1:
            ambiguous_city_names.add(city_name)

    # Step 3: Augment the original features with the `show_canton` flag.
    for feature in features:
        properties = feature.get("properties", {})
        city_name = properties.get("city") or properties.get("name")

        # The canton should be shown if its city name is in our ambiguous set.
        show_canton = city_name in ambiguous_city_names
        properties["show_canton"] = show_canton

    return features


@api.get("/search", response=list[PlacesSearchResult])
async def search(request: HttpRequest, query: str, zoom: int, lat: float, lon: float):
    raw_places = await retrieve_places(query=query, zoom=zoom, lat=lat, lon=lon)
    return process_features_for_ambiguity(raw_places)


@alru_cache(maxsize=32)
async def retrieve_places(*, query: str, lat: float, lon: float, zoom: int) -> list:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "http://localhost:2322/api",
            params={
                "q": query,
                "limit": 5,
                "lat": lat,
                "lon": lon,
                "location_bias_scale": 0.2,
                "zoom": zoom,
                "layer": ["city", "locality"],
            },
            timeout=30000,
        )

    data = resp.raise_for_status().json()
    return data.get("features", [])
