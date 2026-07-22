import csv
import io
import os
from collections import OrderedDict
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from people.models import Person
from properties.models import Property
from leads.models import Lead
from services.models import Service
from tasks.models import Task
from maintenance.models import MaintenanceRequest
from inspections.models import HomeInspection
from documents.models import Document
from tags.models import Tag, PersonTag
from communications.models import CommunicationLog
from campaigns.models import Campaign

from .access import (
    FULL_ACCESS_GROUP_NAME,
    REAL_ESTATE_ONLY_GROUP_NAME,
    get_allowed_lead_type_choices,
    filter_leads_for_user,
    require_lead_access,
)

from .forms import (
    AddLeadForm,
    LogCommunicationForm,
    AddTaskForm,
    ImportLeadsForm,
    CRMUserCreationForm,
    CRMUserAccessForm,
    EditLeadForm,
    AddContactForm,
    EditContactForm,
    AddPropertyForm,
    EditPropertyForm,
    GeneralTaskForm,
)


def setup_admin_user(request, token):
    expected_token = os.environ.get("SETUP_ADMIN_TOKEN", "").strip()

    if not expected_token:
        return HttpResponse(
            "SETUP_ADMIN_TOKEN is not configured.",
            status=500,
        )

    if token != expected_token:
        return HttpResponse(
            "Invalid setup token.",
            status=403,
        )

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "").strip()

    if not username or not email or not password:
        return HttpResponse(
            "Missing DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, or DJANGO_SUPERUSER_PASSWORD.",
            status=500,
        )

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )

    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.set_password(password)
    user.save()

    if created:
        return HttpResponse(
            f"Admin user '{username}' was created. You can now log in at /admin/."
        )

    return HttpResponse(
        f"Admin user '{username}' already existed. Password was reset. You can now log in at /admin/."
    )


@login_required
def home(request):
    allowed_leads = filter_leads_for_user(Lead.objects.all(), request.user)

    today = timezone.localdate()

    total_people = Person.objects.count()
    total_properties = Property.objects.count()
    new_leads = allowed_leads.filter(status="new").count()
    active_services = Service.objects.filter(status="active").count()

    tasks_due_today = Task.objects.filter(
        due_date=today
    ).exclude(
        status="completed"
    ).count()

    overdue_tasks = Task.objects.filter(
        due_date__lt=today
    ).exclude(
        status="completed"
    ).count()

    high_priority_tasks = Task.objects.filter(
        priority__in=["high", "urgent"]
    ).exclude(
        status="completed"
    ).count()

    open_maintenance = MaintenanceRequest.objects.exclude(
        status__in=["completed", "cancelled"]
    ).count()

    emergency_maintenance = MaintenanceRequest.objects.filter(
        priority="emergency"
    ).exclude(
        status__in=["completed", "cancelled"]
    ).count()

    inspections_due = HomeInspection.objects.filter(
        next_inspection_date__lte=today
    ).count()

    recent_leads = allowed_leads.select_related(
        "person",
        "related_property",
    ).order_by("-created_at")[:8]

    upcoming_tasks = Task.objects.select_related(
        "related_person",
        "related_property",
    ).exclude(
        status="completed"
    ).order_by("due_date", "-created_at")[:8]

    recent_maintenance = MaintenanceRequest.objects.select_related(
        "property",
        "assigned_vendor",
    ).order_by("-date_reported")[:5]

    upcoming_inspections = HomeInspection.objects.select_related(
        "property",
    ).order_by("next_inspection_date")[:5]

    recent_documents = Document.objects.select_related(
        "related_person",
        "related_property",
    ).order_by("-uploaded_at")[:5]

    context = {
        "total_people": total_people,
        "total_properties": total_properties,
        "new_leads": new_leads,
        "active_services": active_services,
        "tasks_due_today": tasks_due_today,
        "overdue_tasks": overdue_tasks,
        "high_priority_tasks": high_priority_tasks,
        "open_maintenance": open_maintenance,
        "emergency_maintenance": emergency_maintenance,
        "inspections_due": inspections_due,
        "recent_leads": recent_leads,
        "upcoming_tasks": upcoming_tasks,
        "recent_maintenance": recent_maintenance,
        "upcoming_inspections": upcoming_inspections,
        "recent_documents": recent_documents,
    }

    return render(request, "dashboard/home.html", context)


@login_required
def pipeline(request):
    selected_type = request.GET.get("type", "all")

    leads = Lead.objects.select_related(
        "person",
        "related_property",
    ).order_by("next_follow_up_date", "-created_at")

    leads = filter_leads_for_user(leads, request.user)

    if selected_type != "all":
        leads = leads.filter(lead_type=selected_type)

    stages = OrderedDict()

    for status_key, status_label in Lead.LEAD_STATUSES:
        stages[status_key] = {
            "label": status_label,
            "leads": [],
        }

    for lead in leads:
        if lead.status in stages:
            stages[lead.status]["leads"].append(lead)

    context = {
        "stages": stages,
        "selected_type": selected_type,
        "lead_type_choices": get_allowed_lead_type_choices(request.user),
    }

    return render(request, "dashboard/pipeline.html", context)


@login_required
def global_search(request):
    query = request.GET.get("q", "").strip()

    people = Person.objects.none()
    properties = Property.objects.none()
    leads = Lead.objects.none()
    tasks = Task.objects.none()

    if query:
        people = Person.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(notes__icontains=query)
        )[:20]

        properties = Property.objects.filter(
            Q(address__icontains=query)
            | Q(city__icontains=query)
            | Q(state__icontains=query)
            | Q(zip_code__icontains=query)
            | Q(notes__icontains=query)
        )[:20]

        leads = Lead.objects.select_related(
            "person",
            "related_property",
        ).filter(
            Q(person__first_name__icontains=query)
            | Q(person__last_name__icontains=query)
            | Q(person__email__icontains=query)
            | Q(source__icontains=query)
            | Q(next_step__icontains=query)
            | Q(notes__icontains=query)
            | Q(related_property__address__icontains=query)
        )

        leads = filter_leads_for_user(leads, request.user)[:20]

        tasks = Task.objects.select_related(
            "related_person",
            "related_property",
        ).filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(related_person__first_name__icontains=query)
            | Q(related_person__last_name__icontains=query)
            | Q(related_property__address__icontains=query)
        )[:20]

    context = {
        "query": query,
        "people": people,
        "properties": properties,
        "leads": leads,
        "tasks": tasks,
    }

    return render(request, "dashboard/global_search.html", context)


@login_required
def person_list(request):
    query = request.GET.get("q", "").strip()
    person_type = request.GET.get("type", "all")

    people = Person.objects.all()

    if query:
        people = people.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(notes__icontains=query)
        )

    if person_type != "all":
        people = people.filter(person_type=person_type)

    context = {
        "people": people,
        "query": query,
        "person_type": person_type,
        "person_types": Person.PERSON_TYPES,
    }

    return render(request, "dashboard/person_list.html", context)


@login_required
def add_contact(request):
    if request.method == "POST":
        form = AddContactForm(request.POST)

        if form.is_valid():
            person = Person.objects.create(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
                phone=form.cleaned_data["phone"],
                person_type=form.cleaned_data["person_type"],
                preferred_contact_method=form.cleaned_data["preferred_contact_method"],
                email_opt_in=form.cleaned_data["email_opt_in"],
                sms_opt_in=form.cleaned_data["sms_opt_in"],
                do_not_contact=form.cleaned_data["do_not_contact"],
                notes=form.cleaned_data["notes"],
            )

            for tag in form.cleaned_data["tags"]:
                PersonTag.objects.get_or_create(
                    person=person,
                    tag=tag,
                )

            return redirect("person_detail", person_id=person.id)
    else:
        form = AddContactForm()

    return render(
        request,
        "dashboard/add_contact.html",
        {
            "form": form,
        },
    )


@login_required
def person_detail(request, person_id):
    person = get_object_or_404(Person, id=person_id)

    leads = filter_leads_for_user(
        Lead.objects.filter(person=person).select_related("related_property"),
        request.user,
    )

    owned_properties = Property.objects.filter(owner=person)

    related_tasks = Task.objects.filter(
        Q(related_person=person) | Q(related_property__in=owned_properties)
    ).select_related(
        "related_person",
        "related_property",
    ).order_by("due_date", "-created_at")

    communications = CommunicationLog.objects.filter(
        Q(person=person) | Q(lead__person=person)
    ).select_related(
        "lead",
    ).order_by("-communication_date", "-created_at")

    documents = Document.objects.filter(
        Q(related_person=person) | Q(related_property__in=owned_properties)
    ).select_related(
        "related_person",
        "related_property",
    ).order_by("-uploaded_at")

    person_tags = PersonTag.objects.filter(person=person).select_related("tag")

    context = {
        "person": person,
        "leads": leads,
        "owned_properties": owned_properties,
        "related_tasks": related_tasks,
        "communications": communications,
        "documents": documents,
        "person_tags": person_tags,
    }

    return render(request, "dashboard/person_detail.html", context)


@login_required
def edit_contact(request, person_id):
    person = get_object_or_404(Person, id=person_id)

    if request.method == "POST":
        form = EditContactForm(request.POST)

        if form.is_valid():
            person.first_name = form.cleaned_data["first_name"]
            person.last_name = form.cleaned_data["last_name"]
            person.email = form.cleaned_data["email"]
            person.phone = form.cleaned_data["phone"]
            person.person_type = form.cleaned_data["person_type"]
            person.preferred_contact_method = form.cleaned_data["preferred_contact_method"]
            person.email_opt_in = form.cleaned_data["email_opt_in"]
            person.sms_opt_in = form.cleaned_data["sms_opt_in"]
            person.do_not_contact = form.cleaned_data["do_not_contact"]
            person.notes = form.cleaned_data["notes"]
            person.save()

            PersonTag.objects.filter(person=person).delete()

            for tag in form.cleaned_data["tags"]:
                PersonTag.objects.get_or_create(
                    person=person,
                    tag=tag,
                )

            return redirect("person_detail", person_id=person.id)
    else:
        current_tags = Tag.objects.filter(persontag__person=person)

        form = EditContactForm(
            initial={
                "first_name": person.first_name,
                "last_name": person.last_name,
                "email": person.email,
                "phone": person.phone,
                "person_type": person.person_type,
                "preferred_contact_method": person.preferred_contact_method,
                "email_opt_in": person.email_opt_in,
                "sms_opt_in": person.sms_opt_in,
                "do_not_contact": person.do_not_contact,
                "tags": current_tags,
                "notes": person.notes,
            }
        )

    return render(
        request,
        "dashboard/edit_contact.html",
        {
            "form": form,
            "person": person,
        },
    )


@login_required
def property_list(request):
    query = request.GET.get("q", "").strip()

    properties = Property.objects.select_related("owner").all()

    if query:
        properties = properties.filter(
            Q(address__icontains=query)
            | Q(city__icontains=query)
            | Q(state__icontains=query)
            | Q(zip_code__icontains=query)
            | Q(owner__first_name__icontains=query)
            | Q(owner__last_name__icontains=query)
            | Q(notes__icontains=query)
        )

    context = {
        "properties": properties,
        "query": query,
    }

    return render(request, "dashboard/property_list.html", context)


@login_required
def add_property(request):
    if request.method == "POST":
        form = AddPropertyForm(request.POST)

        if form.is_valid():
            property_obj = Property.objects.create(
                address=form.cleaned_data["address"],
                city=form.cleaned_data["city"],
                state=form.cleaned_data["state"],
                zip_code=form.cleaned_data["zip_code"],
                property_type=form.cleaned_data["property_type"],
                bedrooms=form.cleaned_data["bedrooms"],
                bathrooms=form.cleaned_data["bathrooms"],
                square_feet=form.cleaned_data["square_feet"],
                owner=form.cleaned_data["owner"],
                notes=form.cleaned_data["notes"],
            )

            return redirect("property_detail", property_id=property_obj.id)
    else:
        form = AddPropertyForm()

    return render(
        request,
        "dashboard/add_property.html",
        {
            "form": form,
        },
    )


@login_required
def property_detail(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)

    leads = filter_leads_for_user(
        Lead.objects.filter(related_property=property_obj).select_related("person"),
        request.user,
    )

    tasks = Task.objects.filter(
        related_property=property_obj
    ).select_related(
        "related_person",
        "related_property",
    ).order_by("due_date", "-created_at")

    maintenance_requests = MaintenanceRequest.objects.filter(
        property=property_obj
    ).select_related(
        "assigned_vendor",
    ).order_by("-date_reported")

    inspections = HomeInspection.objects.filter(
        property=property_obj
    ).order_by("-inspection_date")

    documents = Document.objects.filter(
        related_property=property_obj
    ).select_related(
        "related_person",
        "related_property",
    ).order_by("-uploaded_at")

    context = {
        "property_obj": property_obj,
        "leads": leads,
        "tasks": tasks,
        "maintenance_requests": maintenance_requests,
        "inspections": inspections,
        "documents": documents,
    }

    return render(request, "dashboard/property_detail.html", context)


@login_required
def edit_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)

    if request.method == "POST":
        form = EditPropertyForm(request.POST)

        if form.is_valid():
            property_obj.address = form.cleaned_data["address"]
            property_obj.city = form.cleaned_data["city"]
            property_obj.state = form.cleaned_data["state"]
            property_obj.zip_code = form.cleaned_data["zip_code"]
            property_obj.property_type = form.cleaned_data["property_type"]
            property_obj.bedrooms = form.cleaned_data["bedrooms"]
            property_obj.bathrooms = form.cleaned_data["bathrooms"]
            property_obj.square_feet = form.cleaned_data["square_feet"]
            property_obj.owner = form.cleaned_data["owner"]
            property_obj.notes = form.cleaned_data["notes"]
            property_obj.save()

            return redirect("property_detail", property_id=property_obj.id)
    else:
        form = EditPropertyForm(
            initial={
                "address": property_obj.address,
                "city": property_obj.city,
                "state": property_obj.state,
                "zip_code": property_obj.zip_code,
                "property_type": property_obj.property_type,
                "bedrooms": property_obj.bedrooms,
                "bathrooms": property_obj.bathrooms,
                "square_feet": property_obj.square_feet,
                "owner": property_obj.owner,
                "notes": property_obj.notes,
            }
        )

    return render(
        request,
        "dashboard/edit_property.html",
        {
            "form": form,
            "property_obj": property_obj,
        },
    )


@login_required
def add_lead(request):
    if request.method == "POST":
        form = AddLeadForm(request.POST)

        form.fields["lead_type"].choices = get_allowed_lead_type_choices(request.user)

        if form.is_valid():
            person = Person.objects.create(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
                phone=form.cleaned_data["phone"],
                person_type="lead",
                preferred_contact_method=form.cleaned_data["preferred_contact_method"],
                email_opt_in=form.cleaned_data["email_opt_in"],
                sms_opt_in=form.cleaned_data["sms_opt_in"],
                do_not_contact=form.cleaned_data["do_not_contact"],
                notes=form.cleaned_data["notes"],
            )

            lead = Lead.objects.create(
                person=person,
                lead_type=form.cleaned_data["lead_type"],
                source=form.cleaned_data["source"],
                referred_by=form.cleaned_data["referred_by"],
                status=form.cleaned_data["status"],
                related_property=form.cleaned_data["related_property"],
                last_contact_date=form.cleaned_data["last_contact_date"],
                next_follow_up_date=form.cleaned_data["next_follow_up_date"],
                next_step=form.cleaned_data["next_step"],
                notes=form.cleaned_data["notes"],
            )

            for tag in form.cleaned_data["tags"]:
                PersonTag.objects.get_or_create(
                    person=person,
                    tag=tag,
                )

            if form.cleaned_data["create_follow_up_task"] and lead.next_step:
                Task.objects.create(
                    title=lead.next_step,
                    description=f"Follow up for lead: {lead}",
                    related_person=person,
                    related_property=lead.related_property,
                    due_date=lead.next_follow_up_date,
                    status="open",
                    priority="normal",
                )

            return redirect("lead_detail", lead_id=lead.id)
    else:
        form = AddLeadForm()
        form.fields["lead_type"].choices = get_allowed_lead_type_choices(request.user)

    return render(
        request,
        "dashboard/add_lead.html",
        {
            "form": form,
        },
    )


@login_required
def lead_detail(request, lead_id):
    lead = get_object_or_404(
        Lead.objects.select_related(
            "person",
            "related_property",
            "referred_by",
        ),
        id=lead_id,
    )

    require_lead_access(request.user, lead)

    communications = CommunicationLog.objects.filter(
        Q(lead=lead) | Q(person=lead.person)
    ).order_by("-communication_date", "-created_at")

    tasks = Task.objects.filter(
        related_person=lead.person
    ).select_related(
        "related_person",
        "related_property",
    ).order_by("due_date", "-created_at")

    documents = Document.objects.filter(
        Q(related_person=lead.person) | Q(related_property=lead.related_property)
    ).select_related(
        "related_person",
        "related_property",
    ).order_by("-uploaded_at")

    person_tags = PersonTag.objects.filter(
        person=lead.person
    ).select_related("tag")

    context = {
        "lead": lead,
        "communications": communications,
        "tasks": tasks,
        "documents": documents,
        "person_tags": person_tags,
    }

    return render(request, "dashboard/lead_detail.html", context)


@login_required
def edit_lead(request, lead_id):
    lead = get_object_or_404(
        Lead.objects.select_related("person", "related_property"),
        id=lead_id,
    )

    require_lead_access(request.user, lead)

    if request.method == "POST":
        form = EditLeadForm(request.POST)
        form.fields["lead_type"].choices = get_allowed_lead_type_choices(request.user)

        if form.is_valid():
            person = lead.person

            person.first_name = form.cleaned_data["first_name"]
            person.last_name = form.cleaned_data["last_name"]
            person.email = form.cleaned_data["email"]
            person.phone = form.cleaned_data["phone"]
            person.preferred_contact_method = form.cleaned_data["preferred_contact_method"]
            person.email_opt_in = form.cleaned_data["email_opt_in"]
            person.sms_opt_in = form.cleaned_data["sms_opt_in"]
            person.do_not_contact = form.cleaned_data["do_not_contact"]
            person.notes = form.cleaned_data["person_notes"]
            person.save()

            lead.lead_type = form.cleaned_data["lead_type"]
            lead.source = form.cleaned_data["source"]
            lead.status = form.cleaned_data["status"]
            lead.related_property = form.cleaned_data["related_property"]
            lead.last_contact_date = form.cleaned_data["last_contact_date"]
            lead.next_follow_up_date = form.cleaned_data["next_follow_up_date"]
            lead.next_step = form.cleaned_data["next_step"]
            lead.notes = form.cleaned_data["lead_notes"]
            lead.save()

            return redirect("lead_detail", lead_id=lead.id)
    else:
        form = EditLeadForm(
            initial={
                "first_name": lead.person.first_name,
                "last_name": lead.person.last_name,
                "email": lead.person.email,
                "phone": lead.person.phone,
                "preferred_contact_method": lead.person.preferred_contact_method,
                "email_opt_in": lead.person.email_opt_in,
                "sms_opt_in": lead.person.sms_opt_in,
                "do_not_contact": lead.person.do_not_contact,
                "lead_type": lead.lead_type,
                "source": lead.source,
                "status": lead.status,
                "related_property": lead.related_property,
                "last_contact_date": lead.last_contact_date,
                "next_follow_up_date": lead.next_follow_up_date,
                "next_step": lead.next_step,
                "person_notes": lead.person.notes,
                "lead_notes": lead.notes,
            }
        )

        form.fields["lead_type"].choices = get_allowed_lead_type_choices(request.user)

    return render(
        request,
        "dashboard/edit_lead.html",
        {
            "form": form,
            "lead": lead,
        },
    )


@login_required
def log_communication(request, lead_id):
    lead = get_object_or_404(
        Lead.objects.select_related("person", "related_property"),
        id=lead_id,
    )

    require_lead_access(request.user, lead)

    if request.method == "POST":
        form = LogCommunicationForm(request.POST)

        if form.is_valid():
            CommunicationLog.objects.create(
                person=lead.person,
                lead=lead,
                communication_type=form.cleaned_data["communication_type"],
                communication_date=form.cleaned_data["communication_date"],
                subject=form.cleaned_data["subject"],
                summary=form.cleaned_data["summary"],
                outcome=form.cleaned_data["outcome"],
                next_step=form.cleaned_data["next_step"],
                next_follow_up_date=form.cleaned_data["next_follow_up_date"],
            )

            lead.last_contact_date = form.cleaned_data["communication_date"]

            if form.cleaned_data["next_step"]:
                lead.next_step = form.cleaned_data["next_step"]

            if form.cleaned_data["next_follow_up_date"]:
                lead.next_follow_up_date = form.cleaned_data["next_follow_up_date"]

            lead.save()

            if form.cleaned_data["create_follow_up_task"] and form.cleaned_data["next_step"]:
                Task.objects.create(
                    title=form.cleaned_data["next_step"],
                    description=f"Follow-up from communication with {lead.person}",
                    related_person=lead.person,
                    related_property=lead.related_property,
                    due_date=form.cleaned_data["next_follow_up_date"],
                    status="open",
                    priority="normal",
                )

            return redirect("lead_detail", lead_id=lead.id)
    else:
        form = LogCommunicationForm(
            initial={
                "communication_date": timezone.localdate(),
            }
        )

    return render(
        request,
        "dashboard/log_communication.html",
        {
            "form": form,
            "lead": lead,
        },
    )


@login_required
def add_task(request, lead_id):
    lead = get_object_or_404(
        Lead.objects.select_related("person", "related_property"),
        id=lead_id,
    )

    require_lead_access(request.user, lead)

    if request.method == "POST":
        form = AddTaskForm(request.POST)

        if form.is_valid():
            task = Task.objects.create(
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                related_person=lead.person,
                related_property=form.cleaned_data["related_property"],
                due_date=form.cleaned_data["due_date"],
                status=form.cleaned_data["status"],
                priority=form.cleaned_data["priority"],
            )

            if form.cleaned_data["update_lead_next_step"]:
                lead.next_step = task.title
                lead.next_follow_up_date = task.due_date
                lead.save()

            return redirect("lead_detail", lead_id=lead.id)
    else:
        form = AddTaskForm(
            initial={
                "related_property": lead.related_property,
                "due_date": lead.next_follow_up_date,
            }
        )

    return render(
        request,
        "dashboard/add_task.html",
        {
            "form": form,
            "lead": lead,
        },
    )


@login_required
@require_POST
def update_lead_status(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)

    require_lead_access(request.user, lead)

    new_status = request.POST.get("status")

    valid_statuses = [
        status_key
        for status_key, status_label in Lead.LEAD_STATUSES
    ]

    if new_status in valid_statuses:
        lead.status = new_status
        lead.save()

    return redirect("lead_detail", lead_id=lead.id)


@login_required
@require_POST
def move_lead_stage(request, lead_id, new_status):
    lead = get_object_or_404(Lead, id=lead_id)

    require_lead_access(request.user, lead)

    valid_statuses = [
        status_key
        for status_key, status_label in Lead.LEAD_STATUSES
    ]

    if new_status in valid_statuses:
        lead.status = new_status
        lead.save()

    selected_type = request.POST.get("selected_type", "all")

    if selected_type and selected_type != "all":
        return redirect(f"/pipeline/?type={selected_type}")

    return redirect("pipeline")


@login_required
@require_POST
def complete_task(request, lead_id, task_id):
    lead = get_object_or_404(Lead, id=lead_id)

    require_lead_access(request.user, lead)

    task = get_object_or_404(Task, id=task_id)
    task.status = "completed"
    task.save()

    return redirect("lead_detail", lead_id=lead.id)


@login_required
def task_list(request):
    status_filter = request.GET.get("status", "open")
    priority_filter = request.GET.get("priority", "all")

    tasks = Task.objects.select_related(
        "related_person",
        "related_property",
    ).order_by("due_date", "-created_at")

    if status_filter != "all":
        tasks = tasks.filter(status=status_filter)

    if priority_filter != "all":
        tasks = tasks.filter(priority=priority_filter)

    open_tasks_count = Task.objects.filter(status="open").count()

    in_progress_tasks_count = Task.objects.filter(status="in_progress").count()

    overdue_tasks_count = Task.objects.filter(
        due_date__lt=timezone.localdate()
    ).exclude(
        status="completed"
    ).count()

    context = {
        "tasks": tasks,
        "status_filter": status_filter,
        "priority_filter": priority_filter,
        "open_tasks_count": open_tasks_count,
        "in_progress_tasks_count": in_progress_tasks_count,
        "overdue_tasks_count": overdue_tasks_count,
        "task_statuses": Task.TASK_STATUSES,
        "task_priorities": Task.PRIORITIES,
    }

    return render(request, "dashboard/task_list.html", context)


@login_required
def add_general_task(request):
    if request.method == "POST":
        form = GeneralTaskForm(request.POST)

        if form.is_valid():
            Task.objects.create(
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                related_person=form.cleaned_data["related_person"],
                related_property=form.cleaned_data["related_property"],
                due_date=form.cleaned_data["due_date"],
                status=form.cleaned_data["status"],
                priority=form.cleaned_data["priority"],
            )

            return redirect("task_list")
    else:
        form = GeneralTaskForm()

    return render(
        request,
        "dashboard/task_form.html",
        {
            "form": form,
            "page_title": "Add Task",
            "button_text": "Save Task",
        },
    )


@login_required
def edit_general_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        form = GeneralTaskForm(request.POST)

        if form.is_valid():
            task.title = form.cleaned_data["title"]
            task.description = form.cleaned_data["description"]
            task.related_person = form.cleaned_data["related_person"]
            task.related_property = form.cleaned_data["related_property"]
            task.due_date = form.cleaned_data["due_date"]
            task.status = form.cleaned_data["status"]
            task.priority = form.cleaned_data["priority"]
            task.save()

            return redirect("task_list")
    else:
        form = GeneralTaskForm(
            initial={
                "title": task.title,
                "description": task.description,
                "related_person": task.related_person,
                "related_property": task.related_property,
                "due_date": task.due_date,
                "status": task.status,
                "priority": task.priority,
            }
        )

    return render(
        request,
        "dashboard/task_form.html",
        {
            "form": form,
            "task": task,
            "page_title": "Edit Task",
            "button_text": "Update Task",
        },
    )


@login_required
@require_POST
def complete_general_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.status = "completed"
    task.save()

    return redirect("task_list")


@login_required
def import_leads(request):
    if request.method == "POST":
        form = ImportLeadsForm(request.POST, request.FILES)

        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]
            decoded_file = csv_file.read().decode("utf-8-sig")
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            imported_count = 0
            skipped_count = 0

            allowed_lead_types = [
                value
                for value, label in get_allowed_lead_type_choices(request.user)
            ]

            valid_statuses = [
                value
                for value, label in Lead.LEAD_STATUSES
            ]

            for row in reader:
                first_name = row.get("first_name", "").strip()
                last_name = row.get("last_name", "").strip()
                email = row.get("email", "").strip()
                phone = row.get("phone", "").strip()
                lead_type = row.get("lead_type", "buyer").strip()
                source = row.get("source", "").strip()
                status = row.get("status", "new").strip()
                next_step = row.get("next_step", "").strip()
                next_follow_up_date_raw = row.get("next_follow_up_date", "").strip()
                notes = row.get("notes", "").strip()
                tags_raw = row.get("tags", "").strip()

                if not first_name:
                    skipped_count += 1
                    continue

                if lead_type not in allowed_lead_types:
                    skipped_count += 1
                    continue

                if status not in valid_statuses:
                    status = "new"

                next_follow_up_date = None

                if next_follow_up_date_raw:
                    try:
                        next_follow_up_date = datetime.strptime(
                            next_follow_up_date_raw,
                            "%Y-%m-%d",
                        ).date()
                    except ValueError:
                        next_follow_up_date = None

                person = Person.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    person_type="lead",
                    notes=notes,
                )

                lead = Lead.objects.create(
                    person=person,
                    lead_type=lead_type,
                    source=source,
                    status=status,
                    next_step=next_step,
                    next_follow_up_date=next_follow_up_date,
                    notes=notes,
                )

                if tags_raw:
                    tag_names = [
                        tag_name.strip()
                        for tag_name in tags_raw.split(",")
                        if tag_name.strip()
                    ]

                    for tag_name in tag_names:
                        tag, created = Tag.objects.get_or_create(
                            name=tag_name,
                            defaults={
                                "category": "Imported",
                            },
                        )

                        PersonTag.objects.get_or_create(
                            person=person,
                            tag=tag,
                        )

                imported_count += 1

            return render(
                request,
                "dashboard/import_leads.html",
                {
                    "form": ImportLeadsForm(),
                    "imported_count": imported_count,
                    "skipped_count": skipped_count,
                },
            )
    else:
        form = ImportLeadsForm()

    return render(
        request,
        "dashboard/import_leads.html",
        {
            "form": form,
        },
    )


@staff_member_required
def user_access_list(request):
    users = User.objects.all().order_by("username")

    context = {
        "users": users,
        "full_access_group_name": FULL_ACCESS_GROUP_NAME,
        "real_estate_only_group_name": REAL_ESTATE_ONLY_GROUP_NAME,
    }

    return render(request, "dashboard/user_access_list.html", context)


@staff_member_required
def add_crm_user(request):
    full_access_group, created = Group.objects.get_or_create(
        name=FULL_ACCESS_GROUP_NAME
    )

    real_estate_group, created = Group.objects.get_or_create(
        name=REAL_ESTATE_ONLY_GROUP_NAME
    )

    if request.method == "POST":
        form = CRMUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = form.cleaned_data["is_active"]
            user.is_staff = False
            user.is_superuser = False
            user.save()

            user.groups.clear()

            if form.cleaned_data["access_level"] == "crm_full_access":
                user.groups.add(full_access_group)
            else:
                user.groups.add(real_estate_group)

            return redirect("user_access_list")
    else:
        form = CRMUserCreationForm()

    return render(
        request,
        "dashboard/add_crm_user.html",
        {
            "form": form,
        },
    )


@staff_member_required
def edit_crm_user_access(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    full_access_group, created = Group.objects.get_or_create(
        name=FULL_ACCESS_GROUP_NAME
    )

    real_estate_group, created = Group.objects.get_or_create(
        name=REAL_ESTATE_ONLY_GROUP_NAME
    )

    if user_obj.groups.filter(name=FULL_ACCESS_GROUP_NAME).exists():
        current_access_level = "crm_full_access"
    else:
        current_access_level = "real_estate_only"

    if request.method == "POST":
        form = CRMUserAccessForm(request.POST)

        if form.is_valid():
            user_obj.is_active = form.cleaned_data["is_active"]

            if not user_obj.is_superuser:
                user_obj.is_staff = False

            user_obj.groups.clear()

            if form.cleaned_data["access_level"] == "crm_full_access":
                user_obj.groups.add(full_access_group)
            else:
                user_obj.groups.add(real_estate_group)

            user_obj.save()

            return redirect("user_access_list")
    else:
        form = CRMUserAccessForm(
            initial={
                "access_level": current_access_level,
                "is_active": user_obj.is_active,
            }
        )

    return render(
        request,
        "dashboard/edit_crm_user_access.html",
        {
            "form": form,
            "user_obj": user_obj,
        },
    )