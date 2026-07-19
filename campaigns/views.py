import csv

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from leads.models import Lead
from tags.models import PersonTag
from dashboard.access import filter_leads_for_user, require_lead_access
from .forms import CampaignForm
from .models import Campaign, CampaignMember


@login_required
def campaign_list(request):
    campaigns = Campaign.objects.all().order_by("-created_at")

    context = {
        "campaigns": campaigns,
    }

    return render(request, "campaigns/campaign_list.html", context)


@login_required
def add_campaign(request):
    if request.method == "POST":
        form = CampaignForm(request.POST)

        if form.is_valid():
            campaign = form.save()
            return redirect("campaign_detail", campaign_id=campaign.id)

    else:
        form = CampaignForm()

    context = {
        "form": form,
    }

    return render(request, "campaigns/add_campaign.html", context)


@login_required
def campaign_detail(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)

    members = CampaignMember.objects.filter(
        campaign=campaign,
    ).exclude(
        status="removed",
    ).select_related(
        "lead",
        "lead__person",
        "lead__related_property",
    )

    members = members.filter(
        lead__in=filter_leads_for_user(Lead.objects.all(), request.user)
    )

    context = {
        "campaign": campaign,
        "members": members,
        "member_count": members.count(),
    }

    return render(request, "campaigns/campaign_detail.html", context)


@login_required
def build_campaign_audience(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)

    leads = Lead.objects.select_related(
        "person",
        "related_property",
    ).all()

    leads = filter_leads_for_user(leads, request.user)

    if campaign.audience_lead_type:
        leads = leads.filter(lead_type=campaign.audience_lead_type)

    if campaign.audience_lead_status:
        leads = leads.filter(status=campaign.audience_lead_status)

    if campaign.audience_tag:
        tagged_person_ids = PersonTag.objects.filter(
            tag=campaign.audience_tag,
        ).values_list(
            "person_id",
            flat=True,
        )

        leads = leads.filter(person_id__in=tagged_person_ids)

    leads = leads.filter(
        person__email_opt_in=True,
        person__do_not_contact=False,
    )

    for lead in leads:
        member, created = CampaignMember.objects.get_or_create(
            campaign=campaign,
            lead=lead,
        )

        if not created and member.status == "removed":
            member.status = "queued"
            member.save()

    campaign.status = "audience_built"
    campaign.save()

    return redirect("campaign_detail", campaign_id=campaign.id)


@login_required
def remove_campaign_member(request, campaign_id, member_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)

    member = get_object_or_404(
        CampaignMember,
        id=member_id,
        campaign=campaign,
    )

    require_lead_access(request.user, member.lead)

    member.status = "removed"
    member.save()

    return redirect("campaign_detail", campaign_id=campaign.id)


@login_required
def export_campaign_audience(request, campaign_id):
    campaign = get_object_or_404(Campaign, id=campaign_id)

    members = CampaignMember.objects.filter(
        campaign=campaign,
    ).exclude(
        status="removed",
    ).select_related(
        "lead",
        "lead__person",
        "lead__related_property",
    )

    members = members.filter(
        lead__in=filter_leads_for_user(Lead.objects.all(), request.user)
    )

    filename = f"{campaign.name}_audience.csv".replace(" ", "_")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    writer.writerow([
        "first_name",
        "last_name",
        "email",
        "phone",
        "lead_type",
        "lead_status",
        "source",
        "related_property",
        "next_step",
        "next_follow_up_date",
        "tags",
        "campaign_member_status",
    ])

    for member in members:
        lead = member.lead
        person = lead.person

        tag_names = PersonTag.objects.filter(
            person=person,
        ).select_related(
            "tag",
        ).values_list(
            "tag__name",
            flat=True,
        )

        writer.writerow([
            person.first_name,
            person.last_name,
            person.email,
            person.phone,
            lead.get_lead_type_display(),
            lead.get_status_display(),
            lead.source,
            lead.related_property if lead.related_property else "",
            lead.next_step,
            lead.next_follow_up_date if lead.next_follow_up_date else "",
            ", ".join(tag_names),
            member.get_status_display(),
        ])

    return response