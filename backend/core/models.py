from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models.functions import Cast


# Create your models here.


class JobOpening(models.Model):
    class Meta:
        unique_together = (("company_name", "title", "workplace_zip"),)

    company_name = models.CharField(max_length=255, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()

    location = models.PointField(srid=4326, blank=True)
    workplace_zip = models.CharField(max_length=20, blank=True)
    workplace_city = models.CharField(max_length=255, blank=True)

    urls = ArrayField(models.URLField(max_length=500), default=list)

    first_seen_date = models.DateTimeField(auto_now_add=True)
    last_seen_date = models.DateTimeField(auto_now=True)

    home_office = models.GeneratedField(
        expression=Cast("raw_data__homeOffice", models.BooleanField()),
        output_field=models.BooleanField(),
        db_persist=True,
    )

    raw_data = models.JSONField(
        default=list, help_text="A list of the raw JSON objects from each source, in the same order as the URLs."
    )

    def __str__(self):
        return f"{self.title} at {self.company_name}"
