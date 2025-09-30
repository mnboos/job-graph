import djclick as click
import httpx
from django.contrib.gis.geos import Point
from django.db import transaction

from core.models import JobOpening


@click.command()
def command():
    queryset = JobOpening.objects.filter(location__isnull=True)
    while queryset.exists():
        with transaction.atomic():
            o: JobOpening = queryset.select_for_update(skip_locked=True).first()

            print("geocoding: ", o)
            parts_for_geocoding = [o.company_name, o.address, o.zip, o.city]

            while parts_for_geocoding:
                full_address = ", ".join(filter(lambda p: len(p), parts_for_geocoding))
                resp = httpx.get("http://localhost:2322/api/", params={"q": full_address}).raise_for_status()
                data = resp.json()
                features = data["features"]
                if features:
                    geom = features[0]["geometry"]
                    o.location = Point(*geom["coordinates"], srid=4326)
                    break
                else:
                    parts_for_geocoding = parts_for_geocoding[1:]
            if not o.location:
                o.location = Point(0, 0)
            o.save()
