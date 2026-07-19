import csv
import io
from collections import OrderedDict
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.http import Http404
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

from .forms import (
    AddLeadForm,
    LogCommunicationForm,
    AddTaskForm,
    ImportLeadsForm,
    CRMUserCreationForm,
    CRMUserAccessForm,
    EditLeadForm,
    EditContactForm,
    AddContactForm,
    AddPropertyForm,
    EditPropertyForm,
)

from .access import (
    filter_leads_for_user,
    get_allowed_lead_type_choices,
    get_allowed_lead_type_keys,
    require_lead_access,
    user_has_full_crm_access,
)


@login_required
def home(request):
    today = timezone.now().date()
    allowed_lead_types = get_allowed_lead_type_keys(request.user)

    visible_leads = Lead.objects.filter(
        lead_type__in=allowed_lead_types,
    )

    visible_people_ids = visible_leads.values_list(
        "person_id",
        flat=True,
    )

    context = {
        "total_people": Person.objects.filter(
            id__in=visible_people_ids,
        ).distinct().count(),

        "total_properties": Property.objects.count(),

        "new_leads": visible_leads.filter(
            status="new",
        ).count(),

        "active_services": Service.objects.filter(
            status="active",
        ).count(),

        "tasks_due_today": Task.objects.filter(
            due_date=today,
            status__in=["open", "in_progress"],
            related_person_id__in=visible_people_ids,
        ).count(),

        "overdue_tasks": Task.objects.filter(
            due_date__lt=today,
            status__in=["open", "in_progress"],
            related_person_id__in=visible_people_ids,
        ).count(),

        "high_priority_tasks": Task.objects.filter(
            priority__in=["high", "urgent"],
            status__in=["open", "in_progress"],
            related_person_id__in=visible_people_ids,
        ).count(),

        "open_maintenance": MaintenanceRequest.objects.exclude(
            status__in=["completed", "cancelled"],
        ).count(),

        "emergency_maintenance": MaintenanceRequest.objects.filter(
            priority="emergency",
        ).exclude(
            status__in=["completed", "cancelled"],
        ).count(),

        "inspections_due": HomeInspection.objects.filter(
            next_inspection_date__lte=today,
        ).count(),

        "recent_leads": visible_leads.select_related(
            "person",
            "related_property",
        ).order_by(
            "-created_at",
        )[:5],

        "upcoming_tasks": Task.objects.filter(
            status__in=["open", "in_progress"],
            related_person_id__in=visible_people_ids,
        ).order_by(
            "due_date",
        )[:10],

        "recent_maintenance": MaintenanceRequest.objects.exclude(
            status__in=["completed", "cancelled"],
        ).order_by(
            "-date_reported",
        )[:5],

        "upcoming_inspections": HomeInspection.objects.filter(
            next_inspection_date__isnull=False,
        ).order_by(
            "next_inspection_date",
        )[:5],

        "recent_documents": Document.objects.order_by(
            "-uploaded_at",
        )[:5],
    }

    return render(request, "dashboard/home.html", context)


@login_required
def pipeline(request):
    selected_type = request.GET.get("type", "all")

    stages = OrderedDict([
        ("new", "New"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified"),
        ("consult_scheduled", "Consult Scheduled"),
        ("proposal_sent", "Proposal Sent"),
        ("active_client", "Active Client"),
        ("closed", "Closed"),
        ("lost", "Lost"),
        ("nurture", "Nurture"),
    ])

    allowed_lead_type_keys = get_allowed_lead_type_keys(request.user)

    lead_type_filters = [
        ("all", "All"),
    ] + get_allowed_lead_type_choices(request.user)

    if selected_type != "all" and selected_type not in allowed_lead_type_keys:
        selected_type = "all"

    pipeline_data = []

    for status_key, status_label in stages.items():
        leads = Lead.objects.filter(
            status=status_key,
            lead_type__in=allowed_lead_type_keys,
        )

        if selected_type != "all":
            leads = leads.filter(
                lead_type=selected_type,
            )

        leads = leads.select_related(
            "person",
            "related_property",
            "referred_by",
        ).order_by(
            "-created_at",
        )

        pipeline_data.append({
            "status_key": status_key,
            "status_label": status_label,
            "leads": leads,
            "count": leads.count(),
        })

    context = {
        "pipeline_data": pipeline_data,
        "lead_type_filters": lead_type_filters,
        "selected_type": selected_type,
    }

    return render(request, "dashboard/pipeline.html", context)


@login_required
def global_search(request):
    query = request.GET.get("q", "").strip()
    allowed_lead_type_keys = get_allowed_lead_type_keys(request.user)

    people_results = []
    lead_results = []
    property_results = []
    task_results = []

    visible_leads = Lead.objects.filter(
        lead_type__in=allowed_lead_type_keys,
    )

    visible_people_ids = visible_leads.values_list(
        "person_id",
        flat=True,
    )

    if query:
        people_results = Person.objects.filter(
            id__in=visible_people_ids,
        ).filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(notes__icontains=query)
        ).distinct().order_by(
            "last_name",
            "first_name",
        )[:25]

        lead_results = Lead.objects.filter(
            lead_type__in=allowed_lead_type_keys,
        ).filter(
            Q(person__first_name__icontains=query)
            | Q(person__last_name__icontains=query)
            | Q(person__email__icontains=query)
            | Q(person__phone__icontains=query)
            | Q(source__icontains=query)
            | Q(notes__icontains=query)
            | Q(next_step__icontains=query)
            | Q(related_property__address__icontains=query)
            | Q(related_property__city__icontains=query)
        ).select_related(
            "person",
            "related_property",
            "referred_by",
        ).order_by(
            "-created_at",
        )[:25]

        property_results = Property.objects.filter(
            Q(address__icontains=query)
            | Q(city__icontains=query)
            | Q(state__icontains=query)
            | Q(zip_code__icontains=query)
            | Q(notes__icontains=query)
            | Q(owner__first_name__icontains=query)
            | Q(owner__last_name__icontains=query)
        ).select_related(
            "owner",
        ).order_by(
            "address",
        )[:25]

        task_results = Task.objects.filter(
            related_person_id__in=visible_people_ids,
        ).filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(related_person__first_name__icontains=query)
            | Q(related_person__last_name__icontains=query)
            | Q(related_property__address__icontains=query)
            | Q(related_property__city__icontains=query)
        ).select_related(
            "related_person",
            "related_property",
        ).order_by(
            "due_date",
            "-created_at",
        )[:25]

    context = {
        "query": query,
        "people_results": people_results,
        "lead_results": lead_results,
        "property_results": property_results,
        "task_results": task_results,
        "total_results": (
            len(people_results)
            + len(lead_results)
            + len(property_results)
            + len(task_results)
        ),
    }

    return render(request, "dashboard/search.html", context)


def get_visible_contact_queryset(user):
    if user_has_full_crm_access(user):
        return Person.objects.all()

    allowed_lead_type_keys = get_allowed_lead_type_keys(user)

    visible_people_ids = Lead.objects.filter(
        lead_type__in=allowed_lead_type_keys,
    ).values_list(
        "person_id",
        flat=True,
    )

    return Person.objects.filter(
        id__in=visible_people_ids,
    ).distinct()


def user_can_view_property_record(user, property_obj):
    if user_has_full_crm_access(user):
        return True

    allowed_lead_type_keys = get_allowed_lead_type_keys(user)

    visible_leads = Lead.objects.filter(
        lead_type__in=allowed_lead_type_keys,
    )

    visible_property_ids = list(
        visible_leads.exclude(
            related_property__isnull=True,
        ).values_list(
            "related_property_id",
            flat=True,
        )
    )

    visible_people_ids = list(
        visible_leads.values_list(
            "person_id",
            flat=True,
        )
    )

    return (
        property_obj.id in visible_property_ids
        or property_obj.owner_id in visible_people_ids
    )


@login_required
def property_list(request):
    query = request.GET.get("q", "").strip()

    if user_has_full_crm_access(request.user):
        properties = Property.objects.all()
    else:
        allowed_lead_type_keys = get_allowed_lead_type_keys(request.user)

        visible_leads = Lead.objects.filter(
            lead_type__in=allowed_lead_type_keys,
        )

        visible_property_ids = visible_leads.exclude(
            related_property__isnull=True,
        ).values_list(
            "related_property_id",
            flat=True,
        )

        visible_people_ids = visible_leads.values_list(
            "person_id",
            flat=True,
        )

        properties = Property.objects.filter(
            Q(id__in=visible_property_ids)
            | Q(owner_id__in=visible_people_ids)
        ).distinct()

    if query:
        properties = properties.filter(
            Q(address__icontains=query)
            | Q(city__icontains=query)
            | Q(state__icontains=query)
            | Q(zip_code__icontains=query)
            | Q(owner__first_name__icontains=query)
            | Q(owner__last_name__icontains=query)
            | Q(notes__icontains=query)
        ).distinct()

    properties = properties.select_related(
        "owner",
    ).order_by(
        "address",
    )

    context = {
        "properties": properties,
        "query": query,
        "property_count": properties.count(),
    }

    return render(request, "dashboard/property_list.html", context)


@login_required
def add_property(request):
    if request.method == "POST":
        form = AddPropertyForm(request.POST)
        form.fields["owner"].queryset = get_visible_contact_queryset(request.user)

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
        form.fields["owner"].queryset = get_visible_contact_queryset(request.user)

    context = {
        "form": form,
    }

    return render(request, "dashboard/add_property.html", context)


@login_required
def property_detail(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)

    if not user_can_view_property_record(request.user, property_obj):
        raise Http404("Property not found.")

    related_leads = filter_leads_for_user(
        Lead.objects.filter(
            related_property=property_obj,
        ),
        request.user,
    ).select_related(
        "person",
    ).order_by(
        "-created_at",
    )

    related_tasks = Task.objects.filter(
        related_property=property_obj,
    ).select_related(
        "related_person",
    ).order_by(
        "due_date",
        "-created_at",
    )

    maintenance_requests = MaintenanceRequest.objects.filter(
        property=property_obj,
    ).order_by(
        "-date_reported",
    )

    inspections = HomeInspection.objects.filter(
        property=property_obj,
    ).order_by(
        "next_inspection_date",
    )

    documents = Document.objects.filter(
        related_property=property_obj,
    ).order_by(
        "-uploaded_at",
    )

    context = {
        "property": property_obj,
        "related_leads": related_leads,
        "related_tasks": related_tasks,
        "maintenance_requests": maintenance_requests,
        "inspections": inspections,
        "documents": documents,
    }

    return render(request, "dashboard/property_detail.html", context)


@login_required
def edit_property(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)

    if not user_can_view_property_record(request.user, property_obj):
        raise Http404("Property not found.")

    if request.method == "POST":
        form = EditPropertyForm(request.POST)
        form.fields["owner"].queryset = get_visible_contact_queryset(request.user)

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

        form.fields["owner"].queryset = get_visible_contact_queryset(request.user)

    context = {
        "form": form,
        "property": property_obj,
    }

    return render(request, "dashboard/edit_property.html", context)


@login_required
def person_list(request):
    query = request.GET.get("q", "").strip()

    if user_has_full_crm_access(request.user):
        people = Person.objects.all()
    else:
        allowed_lead_type_keys = get_allowed_lead_type_keys(request.user)

        visible_leads = Lead.objects.filter(
            lead_type__in=allowed_lead_type_keys,
        )

        visible_people_ids = visible_leads.values_list(
            "person_id",
            flat=True,
        )

        people = Person.objects.filter(
            id__in=visible_people_ids,
        ).distinct()

    if query:
        people = people.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(notes__icontains=query)
        ).distinct()

    people = people.order_by(
        "last_name",
        "first_name",
    )

    context = {
        "people": people,
        "query": query,
        "person_count": people.count(),
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
                PersonTag.objects.create(
                    person=person,
                    tag=tag,
                )

            return redirect("person_detail", person_id=person.id)

    else:
        form = AddContactForm()

    context = {
        "form": form,
    }

    return render(request, "dashboard/add_contact.html", context)


@login_required
def person_detail(request, person_id):
    person = get_object_or_404(Person, id=person_id)

    if not user_has_full_crm_access(request.user):
        allowed_lead_type_keys = get_allowed_lead_type_keys(request.user)

        user_can_view_person = Lead.objects.filter(
            person=person,
            lead_type__in=allowed_lead_type_keys,
        ).exists()

        if not user_can_view_person:
            raise Http404("Contact not found.")

    related_leads = filter_leads_for_user(
        Lead.objects.filter(
            person=person,
        ),
        request.user,
    ).select_related(
        "related_property",
        "referred_by",
    ).order_by(
        "-created_at",
    )

    related_tasks = Task.objects.filter(
        related_person=person,
    ).select_related(
        "related_property",
    ).order_by(
        "due_date",
        "-created_at",
    )

    communications = CommunicationLog.objects.filter(
        person=person,
    ).select_related(
        "lead",
    ).order_by(
        "-communication_date",
        "-created_at",
    )

    person_tags = PersonTag.objects.filter(
        person=person,
    ).select_related(
        "tag",
    )

    owned_properties = Property.objects.filter(
        owner=person,
    ).order_by(
        "address",
    )

    related_property_ids = related_leads.exclude(
        related_property__isnull=True,
    ).values_list(
        "related_property_id",
        flat=True,
    )

    lead_related_properties = Property.objects.filter(
        id__in=related_property_ids,
    ).order_by(
        "address",
    )

    services = Service.objects.filter(
        client=person,
    ).select_related(
        "property",
    ).order_by(
        "status",
        "service_type",
    )

    property_documents = Document.objects.filter(
        related_property__in=owned_properties,
    ).order_by(
        "-uploaded_at",
    )

    context = {
        "person": person,
        "related_leads": related_leads,
        "related_tasks": related_tasks,
        "communications": communications,
        "person_tags": person_tags,
        "owned_properties": owned_properties,
        "lead_related_properties": lead_related_properties,
        "services": services,
        "property_documents": property_documents,
    }

    return render(request, "dashboard/person_detail.html", context)


@login_required
def edit_contact(request, person_id):
    person = get_object_or_404(Person, id=person_id)

    if not user_has_full_crm_access(request.user):
        allowed_lead_type_keys = get_allowed_lead_type_keys(request.user)

        user_can_view_person = Lead.objects.filter(
            person=person,
            lead_type__in=allowed_lead_type_keys,
        ).exists()

        if not user_can_view_person:
            raise Http404("Contact not found.")

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

            PersonTag.objects.filter(
                person=person,
            ).delete()

            for tag in form.cleaned_data["tags"]:
                PersonTag.objects.create(
                    person=person,
                    tag=tag,
                )

            return redirect("person_detail", person_id=person.id)

    else:
        current_tags = PersonTag.objects.filter(
            person=person,
        ).values_list(
            "tag_id",
            flat=True,
        )

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
                "tags": list(current_tags),
                "notes": person.notes,
            }
        )

    context = {
        "form": form,
        "person": person,
    }

    return render(request, "dashboard/edit_contact.html", context)


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

            lead_type = form.cleaned_data["lead_type"]
            allowed_lead_type_keys = get_allowed_lead_type_keys(request.user)

            if lead_type not in allowed_lead_type_keys:
                lead_type = "other"

            lead = Lead.objects.create(
                person=person,
                lead_type=lead_type,
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
                PersonTag.objects.create(
                    person=person,
                    tag=tag,
                )

            if (
                form.cleaned_data["create_follow_up_task"]
                and form.cleaned_data["next_follow_up_date"]
            ):
                Task.objects.create(
                    title=f"Follow up with {person}",
                    description=(
                        f"Follow up regarding {lead.get_lead_type_display()} lead. "
                        f"Next step: {lead.next_step}"
                    ),
                    related_person=person,
                    related_property=form.cleaned_data["related_property"],
                    due_date=form.cleaned_data["next_follow_up_date"],
                    status="open",
                    priority="normal",
                )

            return redirect("pipeline")

    else:
        form = AddLeadForm()
        form.fields["lead_type"].choices = get_allowed_lead_type_choices(request.user)

    context = {
        "form": form,
    }

    return render(request, "dashboard/add_lead.html", context)


@login_required
def import_leads(request):
    import_results = None
    errors = []

    allowed_lead_type_keys = get_allowed_lead_type_keys(request.user)

    if request.method == "POST":
        form = ImportLeadsForm(request.POST, request.FILES)

        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]

            if not csv_file.name.lower().endswith(".csv"):
                errors.append("Please upload a .csv file.")
            else:
                try:
                    decoded_file = csv_file.read().decode("utf-8-sig")
                    io_string = io.StringIO(decoded_file)
                    reader = csv.DictReader(io_string)

                    created_people = 0
                    updated_people = 0
                    created_leads = 0
                    updated_leads = 0
                    created_tags = 0
                    tagged_people = 0
                    skipped_rows = 0
                    restricted_rows = 0

                    valid_lead_types = [value for value, label in Lead.LEAD_TYPES]
                    valid_statuses = [value for value, label in Lead.LEAD_STATUSES]

                    required_headers = [
                        "first_name",
                        "last_name",
                        "email",
                        "phone",
                        "lead_type",
                        "source",
                        "status",
                        "next_step",
                        "next_follow_up_date",
                        "notes",
                        "tags",
                    ]

                    missing_headers = []

                    if reader.fieldnames is None:
                        errors.append("The CSV file appears to be empty or missing headers.")
                    else:
                        normalized_headers = [
                            header.strip() for header in reader.fieldnames
                        ]

                        for header in required_headers:
                            if header not in normalized_headers:
                                missing_headers.append(header)

                        if missing_headers:
                            errors.append(
                                "Missing required column header(s): "
                                + ", ".join(missing_headers)
                            )

                    if not errors:
                        for row_number, row in enumerate(reader, start=2):
                            first_name = row.get("first_name", "").strip()
                            last_name = row.get("last_name", "").strip()
                            email = row.get("email", "").strip()
                            phone = row.get("phone", "").strip()
                            lead_type = row.get("lead_type", "other").strip()
                            source = row.get("source", "").strip()
                            status = row.get("status", "new").strip()
                            next_step = row.get("next_step", "").strip()
                            next_follow_up_date_raw = row.get(
                                "next_follow_up_date",
                                "",
                            ).strip()
                            notes = row.get("notes", "").strip()
                            tags_raw = row.get("tags", "").strip()

                            if not first_name and not last_name and not email and not phone:
                                skipped_rows += 1
                                continue

                            if not first_name:
                                first_name = "Unknown"

                            if lead_type not in valid_lead_types:
                                lead_type = "other"

                            if lead_type not in allowed_lead_type_keys:
                                restricted_rows += 1
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
                                    errors.append(
                                        f"Row {row_number}: Invalid next_follow_up_date. Use YYYY-MM-DD."
                                    )

                            person = None

                            if email:
                                person = Person.objects.filter(
                                    email__iexact=email,
                                ).first()

                            if person is None and phone:
                                person = Person.objects.filter(
                                    phone=phone,
                                ).first()

                            if person:
                                updated_people += 1

                                person.first_name = first_name
                                person.last_name = last_name
                                person.email = email
                                person.phone = phone
                                person.person_type = "lead"

                                if notes:
                                    person.notes = notes

                                person.save()

                            else:
                                person = Person.objects.create(
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=email,
                                    phone=phone,
                                    person_type="lead",
                                    email_opt_in=True,
                                    sms_opt_in=False,
                                    do_not_contact=False,
                                    notes=notes,
                                )

                                created_people += 1

                            existing_lead = Lead.objects.filter(
                                person=person,
                                lead_type=lead_type,
                                source=source,
                            ).first()

                            if existing_lead:
                                lead = existing_lead
                                lead.status = status
                                lead.next_step = next_step
                                lead.next_follow_up_date = next_follow_up_date

                                if notes:
                                    lead.notes = notes

                                lead.save()
                                updated_leads += 1

                            else:
                                Lead.objects.create(
                                    person=person,
                                    lead_type=lead_type,
                                    source=source,
                                    status=status,
                                    next_step=next_step,
                                    next_follow_up_date=next_follow_up_date,
                                    notes=notes,
                                )

                                created_leads += 1

                            if tags_raw:
                                tag_names = [
                                    tag_name.strip()
                                    for tag_name in tags_raw.split(",")
                                    if tag_name.strip()
                                ]

                                for tag_name in tag_names:
                                    tag, tag_created = Tag.objects.get_or_create(
                                        name=tag_name,
                                        defaults={
                                            "category": "marketing",
                                        },
                                    )

                                    if tag_created:
                                        created_tags += 1

                                    person_tag, person_tag_created = (
                                        PersonTag.objects.get_or_create(
                                            person=person,
                                            tag=tag,
                                        )
                                    )

                                    if person_tag_created:
                                        tagged_people += 1

                        import_results = {
                            "created_people": created_people,
                            "updated_people": updated_people,
                            "created_leads": created_leads,
                            "updated_leads": updated_leads,
                            "created_tags": created_tags,
                            "tagged_people": tagged_people,
                            "skipped_rows": skipped_rows,
                            "restricted_rows": restricted_rows,
                        }

                except UnicodeDecodeError:
                    errors.append(
                        "Could not read the file. Please save it as a standard UTF-8 CSV file and try again."
                    )

                except csv.Error:
                    errors.append(
                        "There was a problem reading the CSV file. Please check the formatting."
                    )

    else:
        form = ImportLeadsForm()

    context = {
        "form": form,
        "import_results": import_results,
        "errors": errors,
    }

    return render(request, "dashboard/import_leads.html", context)


@login_required
def lead_detail(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    require_lead_access(request.user, lead)

    person = lead.person

    person_tags = PersonTag.objects.filter(
        person=person,
    ).select_related(
        "tag",
    )

    communications = CommunicationLog.objects.filter(
        person=person,
    ).order_by(
        "-communication_date",
        "-created_at",
    )

    related_tasks = Task.objects.filter(
        related_person=person,
    ).order_by(
        "due_date",
        "-created_at",
    )

    context = {
        "lead": lead,
        "person": person,
        "person_tags": person_tags,
        "communications": communications,
        "related_tasks": related_tasks,
        "lead_status_choices": Lead.LEAD_STATUSES,
    }

    return render(request, "dashboard/lead_detail.html", context)


@login_required
def edit_lead(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    require_lead_access(request.user, lead)

    person = lead.person
    allowed_lead_type_choices = get_allowed_lead_type_choices(request.user)
    allowed_lead_type_keys = get_allowed_lead_type_keys(request.user)

    if request.method == "POST":
        form = EditLeadForm(request.POST)
        form.fields["lead_type"].choices = allowed_lead_type_choices

        if form.is_valid():
            new_lead_type = form.cleaned_data["lead_type"]

            if new_lead_type not in allowed_lead_type_keys:
                new_lead_type = lead.lead_type

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

            lead.lead_type = new_lead_type
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
                "first_name": person.first_name,
                "last_name": person.last_name,
                "email": person.email,
                "phone": person.phone,
                "preferred_contact_method": person.preferred_contact_method,
                "email_opt_in": person.email_opt_in,
                "sms_opt_in": person.sms_opt_in,
                "do_not_contact": person.do_not_contact,
                "lead_type": lead.lead_type,
                "source": lead.source,
                "status": lead.status,
                "related_property": lead.related_property,
                "last_contact_date": lead.last_contact_date,
                "next_follow_up_date": lead.next_follow_up_date,
                "next_step": lead.next_step,
                "person_notes": person.notes,
                "lead_notes": lead.notes,
            }
        )

        form.fields["lead_type"].choices = allowed_lead_type_choices

    context = {
        "form": form,
        "lead": lead,
        "person": person,
    }

    return render(request, "dashboard/edit_lead.html", context)


@login_required
def log_communication(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    require_lead_access(request.user, lead)

    person = lead.person
    today = timezone.now().date()

    if request.method == "POST":
        form = LogCommunicationForm(request.POST)

        if form.is_valid():
            communication = CommunicationLog.objects.create(
                person=person,
                lead=lead,
                communication_type=form.cleaned_data["communication_type"],
                communication_date=form.cleaned_data["communication_date"],
                subject=form.cleaned_data["subject"],
                summary=form.cleaned_data["summary"],
                outcome=form.cleaned_data["outcome"],
                next_step=form.cleaned_data["next_step"],
                next_follow_up_date=form.cleaned_data["next_follow_up_date"],
            )

            lead.last_contact_date = communication.communication_date

            if communication.next_step:
                lead.next_step = communication.next_step

            if communication.next_follow_up_date:
                lead.next_follow_up_date = communication.next_follow_up_date

            lead.save()

            if (
                form.cleaned_data["create_follow_up_task"]
                and communication.next_follow_up_date
            ):
                Task.objects.create(
                    title=f"Follow up with {person}",
                    description=(
                        f"Follow up after {communication.get_communication_type_display().lower()} "
                        f"on {communication.communication_date}. "
                        f"Next step: {communication.next_step}"
                    ),
                    related_person=person,
                    related_property=lead.related_property,
                    due_date=communication.next_follow_up_date,
                    status="open",
                    priority="normal",
                )

            return redirect("lead_detail", lead_id=lead.id)

    else:
        form = LogCommunicationForm(
            initial={
                "communication_date": today,
                "next_step": lead.next_step,
                "next_follow_up_date": lead.next_follow_up_date,
            }
        )

    context = {
        "form": form,
        "lead": lead,
        "person": person,
    }

    return render(request, "dashboard/log_communication.html", context)


@login_required
def add_task(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    require_lead_access(request.user, lead)

    person = lead.person

    if request.method == "POST":
        form = AddTaskForm(request.POST)

        if form.is_valid():
            related_property = form.cleaned_data["related_property"]

            if related_property is None:
                related_property = lead.related_property

            task = Task.objects.create(
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                related_person=person,
                related_property=related_property,
                due_date=form.cleaned_data["due_date"],
                status=form.cleaned_data["status"],
                priority=form.cleaned_data["priority"],
            )

            if form.cleaned_data["update_lead_next_step"]:
                lead.next_step = task.title

                if task.due_date:
                    lead.next_follow_up_date = task.due_date

                lead.save()

            return redirect("lead_detail", lead_id=lead.id)

    else:
        form = AddTaskForm(
            initial={
                "related_property": lead.related_property,
                "title": lead.next_step,
                "due_date": lead.next_follow_up_date,
            }
        )

    context = {
        "form": form,
        "lead": lead,
        "person": person,
    }

    return render(request, "dashboard/add_task.html", context)


@login_required
@require_POST
def update_lead_status(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    require_lead_access(request.user, lead)

    new_status = request.POST.get("status")
    valid_statuses = [status_key for status_key, status_label in Lead.LEAD_STATUSES]

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

    task = get_object_or_404(
        Task,
        id=task_id,
        related_person=lead.person,
    )

    task.status = "completed"
    task.save()

    return redirect("lead_detail", lead_id=lead.id)


def ensure_crm_groups_exist():
    real_estate_group, created = Group.objects.get_or_create(
        name="Real Estate Only",
    )

    full_access_group, created = Group.objects.get_or_create(
        name="CRM Full Access",
    )

    return real_estate_group, full_access_group


@staff_member_required
def user_access_list(request):
    ensure_crm_groups_exist()

    users = User.objects.all().order_by(
        "username",
    )

    context = {
        "users": users,
    }

    return render(request, "dashboard/user_access_list.html", context)


@staff_member_required
def add_crm_user(request):
    ensure_crm_groups_exist()

    if request.method == "POST":
        form = CRMUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            user.is_active = form.cleaned_data["is_active"]
            user.is_staff = False
            user.is_superuser = False
            user.save()

            real_estate_group, full_access_group = ensure_crm_groups_exist()

            access_level = form.cleaned_data["access_level"]

            user.groups.remove(
                real_estate_group,
                full_access_group,
            )

            if access_level == "crm_full_access":
                user.groups.add(
                    full_access_group,
                )
            else:
                user.groups.add(
                    real_estate_group,
                )

            return redirect("user_access_list")

    else:
        form = CRMUserCreationForm()

    context = {
        "form": form,
    }

    return render(request, "dashboard/add_crm_user.html", context)


@staff_member_required
def edit_crm_user_access(request, user_id):
    ensure_crm_groups_exist()

    crm_user = get_object_or_404(User, id=user_id)

    real_estate_group, full_access_group = ensure_crm_groups_exist()

    if crm_user.groups.filter(name="CRM Full Access").exists():
        current_access_level = "crm_full_access"
    else:
        current_access_level = "real_estate_only"

    if request.method == "POST":
        form = CRMUserAccessForm(request.POST)

        if form.is_valid():
            crm_user.is_active = form.cleaned_data["is_active"]
            crm_user.save()

            access_level = form.cleaned_data["access_level"]

            crm_user.groups.remove(
                real_estate_group,
                full_access_group,
            )

            if access_level == "crm_full_access":
                crm_user.groups.add(
                    full_access_group,
                )
            else:
                crm_user.groups.add(
                    real_estate_group,
                )

            return redirect("user_access_list")

    else:
        form = CRMUserAccessForm(
            initial={
                "access_level": current_access_level,
                "is_active": crm_user.is_active,
            }
        )

    context = {
        "form": form,
        "crm_user": crm_user,
    }

    return render(request, "dashboard/edit_crm_user_access.html", context)