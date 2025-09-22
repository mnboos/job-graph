from async_lru import alru_cache
from django.http import HttpRequest
from ninja import NinjaAPI
import httpx

api = NinjaAPI()


@api.get("/generate_isochrone")
async def generate_isochrone(request: HttpRequest, travel_time_minutes: int) -> dict:
    travel_time_seconds = travel_time_minutes * 60
    return await retrieve_isochrone(travel_time_seconds=travel_time_seconds)


@alru_cache(maxsize=32)
async def retrieve_isochrone(*, travel_time_seconds: int) -> dict:
    async with httpx.AsyncClient() as client:
        params = {
            "point": "47.521889,9.252317",
            "key": "",
            "profile": "bike",
            "time_limit": travel_time_seconds,
        }
        resp = await client.get("http://localhost:8989/isochrone", params=params)
    return resp.json()


@api.get("/search")
async def search(request: HttpRequest, query: str) -> list[str]:
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://photon:2322", params={"q": query})
    return resp.json()["results"]
