from django.contrib.gis.db import models
from django.db.models.functions import Cast


class JobOpening(models.Model):
    class Meta:
        unique_together = (
            (
                "company_name",
                "title",
                "zip",
            ),
        )

    company_name = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()

    location = models.PointField(srid=4326, blank=True, null=True)

    zip = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=64, blank=True)

    phone = models.CharField(max_length=32, blank=True)

    url_application = models.URLField(max_length=500, blank=True)
    url_description = models.URLField(max_length=500, blank=True)

    first_published_at = models.DateTimeField(null=True, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    home_office = models.GeneratedField(
        expression=Cast("raw_data__homeOffice", models.BooleanField()),
        output_field=models.BooleanField(),
        db_persist=True,
    )

    platform_id = models.GeneratedField(
        expression=Cast("raw_data__id", models.IntegerField()),
        output_field=models.IntegerField(),
        db_persist=True,
    )

    raw_data = models.JSONField(
        default=dict, help_text="A list of the raw JSON objects from each source, in the same order as the URLs."
    )

    def __str__(self):
        return f"{self.title} at {self.company_name}"
