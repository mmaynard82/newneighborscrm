from django.contrib import admin
from .models import LandingPage


@admin.register(LandingPage)
class LandingPageAdmin(admin.ModelAdmin):
    list_display = ("title", "workspace", "template", "status", "wordpress_url")
    list_filter = ("status", "template")
    readonly_fields = ("wordpress_page_id", "wordpress_url")
