from django.urls import path

from . import views


urlpatterns = [
    path("", views.campaign_list, name="campaign_list"),
    path("add/", views.add_campaign, name="add_campaign"),
    path("<int:campaign_id>/", views.campaign_detail, name="campaign_detail"),
    path(
        "<int:campaign_id>/build-audience/",
        views.build_campaign_audience,
        name="build_campaign_audience",
    ),
    path(
        "<int:campaign_id>/export/",
        views.export_campaign_audience,
        name="export_campaign_audience",
    ),
    path(
        "<int:campaign_id>/member/<int:member_id>/remove/",
        views.remove_campaign_member,
        name="remove_campaign_member",
    ),
]