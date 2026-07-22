from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="dashboard_home"),

    path(
        "setup-admin/<str:token>/",
        views.setup_admin_user,
        name="setup_admin_user",
    ),

    path("pipeline/", views.pipeline, name="pipeline"),
    path("search/", views.global_search, name="global_search"),
    path("import-leads/", views.import_leads, name="import_leads"),

    path("people/", views.person_list, name="person_list"),
    path("people/add/", views.add_contact, name="add_contact"),
    path("people/<int:person_id>/", views.person_detail, name="person_detail"),
    path("people/<int:person_id>/edit/", views.edit_contact, name="edit_contact"),

    path("properties/", views.property_list, name="property_list"),
    path("properties/add/", views.add_property, name="add_property"),
    path("properties/<int:property_id>/", views.property_detail, name="property_detail"),
    path("properties/<int:property_id>/edit/", views.edit_property, name="edit_property"),

    path("tasks/", views.task_list, name="task_list"),
    path("tasks/add/", views.add_general_task, name="add_general_task"),
    path("tasks/<int:task_id>/edit/", views.edit_general_task, name="edit_general_task"),
    path("tasks/<int:task_id>/complete/", views.complete_general_task, name="complete_general_task"),

    path("users/", views.user_access_list, name="user_access_list"),
    path("users/add/", views.add_crm_user, name="add_crm_user"),
    path(
        "users/<int:user_id>/edit-access/",
        views.edit_crm_user_access,
        name="edit_crm_user_access",
    ),

    path("add-lead/", views.add_lead, name="add_lead"),
    path("lead/<int:lead_id>/", views.lead_detail, name="lead_detail"),
    path("lead/<int:lead_id>/edit/", views.edit_lead, name="edit_lead"),

    path(
        "lead/<int:lead_id>/log-communication/",
        views.log_communication,
        name="log_communication",
    ),

    path(
        "lead/<int:lead_id>/add-task/",
        views.add_task,
        name="add_task",
    ),

    path(
        "lead/<int:lead_id>/update-status/",
        views.update_lead_status,
        name="update_lead_status",
    ),

    path(
        "lead/<int:lead_id>/move-stage/<str:new_status>/",
        views.move_lead_stage,
        name="move_lead_stage",
    ),

    path(
        "lead/<int:lead_id>/task/<int:task_id>/complete/",
        views.complete_task,
        name="complete_task",
    ),
]