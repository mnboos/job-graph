import djclick as click
import httpx
from django.db import transaction

from core.models import JobOpening


@click.command()
def command():
    queryset = JobOpening.objects.filter(location__isnull=True)
    while queryset.exists():
        with transaction.atomic():
            o: JobOpening = queryset.select_for_update(skip_locked=True).first()

            print("geocoding: ", o)

            full_address = ", ".join([o.company_name, o.address, f"{o.zip} {o.city}"])
            resp = httpx.get("http://localhost:2322/api/", params={"q": full_address}).raise_for_status()
            data = resp.json()
            print("response: ", data)
            # todo: get and save location
            break
