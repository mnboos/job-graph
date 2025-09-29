import asyncio
import random

import httpx

from . import BaseScraper


def _parenthesize(val: str):
    return f"({val})"


class OstjobScraper(BaseScraper):
    API_URL = "https://api.ostjob.ch/public/vacancy/search/"

    def _get_query_params(self, page: int):
        query = " | ".join(map(_parenthesize, self.query))
        return {
            "search": _parenthesize(query),
            "page": page,
            "pageSize": 10,
            # "place": "Thurgau",
            # "placeType": "kanton",
            # "placeCode": "",
            # "placeValue": "Thurgau",
            # "pt": "kanton",
            "order": "by_relevance",
            "relatedWords": "",
        }

    async def _fetch_page(self, client: httpx.AsyncClient, page: int) -> dict | None:
        """Asynchronously fetches a single page of results."""
        params = self._get_query_params(page)
        try:
            response = await client.get(self.API_URL, params=params, timeout=15.0)
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            print(f"Error fetching page {page}: {e}")
            return None

    async def scrape(self) -> list[dict]:
        all_jobs = []

        async with httpx.AsyncClient(verify=False) as client:
            resp = await self._fetch_page(client, 1)
            if resp:
                all_jobs.extend(resp.get("items", []))
                total_pages = resp.get("pages")
                if total_pages > 1:
                    tasks = []
                    max_parallel_requests = 3
                    for i, page_num in enumerate(range(2, total_pages + 1)):
                        if not i % max_parallel_requests:
                            sleep_time = random.randint(100, 1000) / 1000
                            print(f"[{i}]: sleeping: ", sleep_time, "s")
                            await asyncio.sleep(sleep_time)
                        tasks.append(self._fetch_page(client, page_num))

                    print(f"Fetching remaining {len(tasks)} pages concurrently...")
                    other_pages_results = await asyncio.gather(*tasks)
                    for page_data in other_pages_results:
                        if page_data and page_data.get("items"):
                            all_jobs.extend(page_data.get("items"))
        return all_jobs
