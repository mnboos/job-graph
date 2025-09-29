import importlib

from django_tasks import task

from .models import JobOpening
from django.contrib.gis.geos import Point
import traceback
import json


@task
async def run_scraper_task(scraper_name: str, search_query: list[str]):
    print("running scraper: ", scraper_name)
    try:
        try:
            parts = scraper_name.split(".")
            module_name = ".".join(parts[:-1])
            class_name = parts[-1]
            scraper_module = importlib.import_module(module_name)
            scraper_class = getattr(scraper_module, class_name)
        except ModuleNotFoundError:
            traceback.print_exc()
            raise
        print("Imported: ", scraper_name)
        scraper = scraper_class(query=search_query)

        scraped_jobs = await scraper.scrape()

        for job_data in scraped_jobs:
            print("got job: ", json.dumps(job_data, indent=4))
            # uniqueness_hash = create_job_fingerprint(
            #     company_name=job_data["company_name"], title=job_data["title"], description=job_data["description"]
            # )

            coords = job_data.get("coordinates", [])
            if coords and "latitude" in coords[0] and "longitude" in coords[0]:
                location = Point(x=coords[0]["longitude"], y=coords[0]["latitude"], srid=4326)
            else:
                location = None

            company = job_data["company"]["name"]
            title = job_data["title"]

            # Get or create the canonical JobOpening
            opening, created = await JobOpening.objects.aget_or_create(
                company_name=company,
                title=title,
                location=location,
                defaults={
                    "company_name": company,
                    "title": title,
                    "description": job_data["activity"],
                    # Add the new fields to the defaults
                    "workplace_zip": job_data.get("workplaceZip"),
                    "workplace_city": job_data.get("workplaceCity"),
                    "location": location,
                    "raw_data": job_data,
                },
            )

            # Add the URL and save (this logic remains the same)
            new_url = job_data.get("url")
            if new_url and new_url not in opening.urls:
                opening.urls.append(new_url)

            await opening.asave()
    except:
        traceback.print_exc()
        raise
