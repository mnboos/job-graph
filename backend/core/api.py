from async_lru import alru_cache
from django.http import HttpRequest
from ninja import NinjaAPI
import httpx

api = NinjaAPI()


@api.get("/generate_isochrone")
async def generate_isochrone(request: HttpRequest, travel_time_minutes: int, point: str, profile: str) -> dict:
    travel_time_seconds = travel_time_minutes * 60
    return await retrieve_isochrone(travel_time_seconds=travel_time_seconds, point=point, profile=profile)


@alru_cache(maxsize=32)
async def retrieve_isochrone(*, travel_time_seconds: int, point: str, profile: str) -> dict:
    async with httpx.AsyncClient() as client:
        params = {
            "point": point,
            "key": "",
            "profile": profile,
            "time_limit": travel_time_seconds,
        }
        resp = await client.get("http://localhost:8989/isochrone", params=params, timeout=30000)
    return resp.json()


@api.get("/search")
async def search(request: HttpRequest, query: str, zoom: int, lat: float, lon: float) -> list[str]:
    return await retrieve_places(query=query, zoom=zoom, lat=lat, lon=lon)


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
        )
    return resp.json().get("features", [])
