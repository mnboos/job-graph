import importlib

from django_tasks import task

from .models import JobOpening
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

            company = job_data["company"]
            title = job_data["title"]

            workplace_zip = job_data.get("workplaceZip")
            if workplace_zip == company.get("zip"):
                address = " ".join([company.get("street", ""), company.get("houseNumber", "")]).strip()
                country = company.get("country")
            else:
                address = ""
                country_codes = job_data.get("countryCode")
                if country_codes:
                    country = country_codes[0]
                else:
                    country = ""
                if country and country.lower() not in ["ch", "schweiz", "suisse", "svizzera"]:
                    continue

            # Get or create the canonical JobOpening
            opening, created = await JobOpening.objects.aget_or_create(
                company_name=company.get("name"),
                title=title,
                defaults={
                    "company_name": company.get("name"),
                    "title": title,
                    "description": job_data.get("activity"),
                    # Add the new fields to the defaults
                    "zip": job_data.get("workplaceZip"),
                    "city": job_data.get("workplaceCity"),
                    "address": address,
                    "country": country,
                    "raw_data": job_data,
                    "first_published_at": job_data.get("firstPublishedAt"),
                    "url_application": job_data.get("urlApplication", ""),
                    "url_description": job_data.get("urlDescription", ""),
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
