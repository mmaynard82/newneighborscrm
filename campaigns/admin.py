from django.contrib import admin

from .models import Campaign, CampaignMember


class CampaignMemberInline(admin.TabularInline):
    model = CampaignMember
    extra = 0
    autocomplete_fields = ["lead"]


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "campaign_type",
        "status",
        "audience_lead_type",
        "audience_lead_status",
        "audience_tag",
        "created_at",
    )

    search_fields = (
        "name",
        "subject",
        "message",
        "notes",
    )

    list_filter = (
        "campaign_type",
        "status",
        "audience_lead_type",
        "audience_lead_status",
        "audience_tag",
        "created_at",
    )

    inlines = [CampaignMemberInline]


@admin.register(CampaignMember)
class CampaignMemberAdmin(admin.ModelAdmin):
    list_display = (
        "campaign",
        "lead",
        "status",
        "added_at",
    )

    search_fields = (
        "campaign__name",
        "lead__person__first_name",
        "lead__person__last_name",
        "lead__person__email",
        "lead__person__phone",
    )

    list_filter = (
        "campaign",
        "status",
        "added_at",
    )