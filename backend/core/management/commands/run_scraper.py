import djclick as click
from core.tasks import run_scraper_task


@click.command()
def command():
    scrapers = ["core.scraper.ostjob_scraper.OstjobScraper"]

    query = [
        "vue",
        "react",
        "python",
        "java",
        ".net",
        "Software Developer",
        "Software Engineer",
        "Software Entwickler",
        "Software Ingenieur",
        "Software Architekt",
    ]

    for s in scrapers:
        run_scraper_task.enqueue(scraper_name=s, search_query=query)

    print("Running scraper...")
