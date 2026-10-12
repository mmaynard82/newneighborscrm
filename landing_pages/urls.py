from django.urls import path
from . import views

urlpatterns = [
    path("", views.list_pages, name="landing_pages_list"),
    path("new/", views.create_page, name="landing_pages_create"),
    path("<int:page_id>/preview/", views.preview_page, name="landing_pages_preview"),
    path("<int:page_id>/edit/", views.edit_page, name="landing_pages_edit"),
]
