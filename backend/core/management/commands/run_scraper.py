import djclick as click
from core.tasks import run_scraper_task


@click.command()
def command():
    scrapers = ["core.scraper.ostjob_scraper.OstjobScraper"]

    query = {
        "python",
        "vue",
        "react",
        "webentwickler",
        "Software Entwickler",
        "Software Engineer",
        "Software Developer",
        "Softwareingenieur",
        "Softwarearchitekt",
        "Leiter Softwareentwicklung",
        "Software Ingenieur",
        "Software Architekt",
        "Software Engineer",
        "Software Developer",
        "django",
        "devops",
        "devsecops",
        "java",
        ".net",
    }

    for s in scrapers:
        run_scraper_task.enqueue(scraper_name=s, search_query=list(query))

    print("Running scraper...")
