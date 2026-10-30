from django.urls import path
from . import views

urlpatterns = [
    path("", views.workbench, name="ai_workbench"),
    path("lead/<int:lead_id>/review/", views.review_lead, name="ai_review_lead"),
    path("paperwork/templates/", views.paperwork_templates, name="brokerage_paperwork_templates"),
    path("paperwork/templates/new/", views.new_paperwork_template, name="brokerage_new_paperwork_template"),
    path("paperwork/packets/<int:packet_id>/", views.contract_packet, name="brokerage_contract_packet"),
    path("paperwork/packets/<int:packet_id>/edit/", views.edit_contract_packet, name="brokerage_edit_contract_packet"),
    path("paperwork/packets/<int:packet_id>/send/", views.send_contract_packet, name="brokerage_send_contract_packet"),
    path("transactions/<int:case_id>/paperwork/new/", views.new_contract_packet, name="brokerage_new_contract_packet"),
    path("transactions/new/", views.create_transaction, name="ai_create_transaction"),
    path("transactions/<int:case_id>/edit/", views.edit_transaction, name="ai_edit_transaction"),
    path("transactions/<int:case_id>/", views.transaction_detail, name="ai_transaction_detail"),
    path("transactions/<int:case_id>/review/", views.review_transaction, name="ai_review_transaction"),
    path("recommendations/<int:recommendation_id>/<str:action>/", views.update_recommendation, name="ai_update_recommendation"),
]
