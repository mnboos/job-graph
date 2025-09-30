from asgiref.sync import sync_to_async
from async_lru import alru_cache
from django.contrib.gis.geos import Polygon
from django.http import HttpRequest
from ninja import NinjaAPI, Schema, ModelSchema
import httpx
from ninja.errors import HttpError
from ninja.orm import register_field
from .models import JobOpening

api = NinjaAPI()


class FeatureProperties(Schema):
    name: str = None
    type: str = None

    street: str = None
    housenumber: str = None
    postcode: str = None
    city: str = None
    district: str = None
    county: str = None
    state: str = None
    country: str = None
    countrycode: str = None

    extent: tuple[float, float, float, float] = None

    osm_type: str = None
    osm_id: int = None
    osm_key: str = None
    osm_value: str = None


class Geometry(Schema):
    type: str
    coordinates: tuple[float, float]


class PlacesSearchResult(Schema):
    properties: FeatureProperties
    geometry: Geometry
    show_canton: bool


class IsoPolygon(Schema):
    rings: list[list[tuple[float, float]]]


class IsochroneOut(Schema):
    polygons: list[IsoPolygon]


register_field("PointField", tuple)


class JobOpeningOut(ModelSchema):
    id: int

    class Meta:
        model = JobOpening
        fields = ["id", "title", "company_name", "location", "description", "address", "city"]


class Point(Schema):
    lat: float
    lon: float


class DistanceCalculation(Schema):
    job_id: int
    abfahrtsort: Point
    profile: str


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


@api.get("/search", response=list[PlacesSearchResult])
async def search(request: HttpRequest, query: str, zoom: int, lat: float, lon: float):
    places = await retrieve_places(query=query, zoom=zoom, lat=lat, lon=lon)
    results = []
    for p in places:
        results.append({**p, "show_canton": False})
    return results


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
    data = resp.json()
    if resp.status_code != 200:
        raise HttpError(resp.status_code, data)
    return data.get("features", [])
