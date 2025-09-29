from django.contrib import admin

from core.models import JobOpening

# Register your models here.


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_filter = ("home_office",)
    ordering = ("title",)
