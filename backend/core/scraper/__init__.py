from abc import ABC, abstractmethod


class BaseScraper(ABC):
    def __init__(self, query: list[str]):
        self.query = query

    @abstractmethod
    async def scrape(self) -> list[dict]:
        pass
