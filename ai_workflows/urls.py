from django.urls import path
from . import views

urlpatterns = [
    path("", views.workbench, name="ai_workbench"),
    path("lead/<int:lead_id>/review/", views.review_lead, name="ai_review_lead"),
    path("transactions/new/", views.create_transaction, name="ai_create_transaction"),
    path("transactions/<int:case_id>/edit/", views.edit_transaction, name="ai_edit_transaction"),
    path("transactions/<int:case_id>/", views.transaction_detail, name="ai_transaction_detail"),
    path("transactions/<int:case_id>/review/", views.review_transaction, name="ai_review_transaction"),
    path("recommendations/<int:recommendation_id>/<str:action>/", views.update_recommendation, name="ai_update_recommendation"),
]
