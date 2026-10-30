from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from accounts.access import single_workspace_for
from leads.models import Lead
from .engine import lead_review, transaction_review
from .forms import TransactionCaseForm
from .models import AgentRecommendation, TransactionCase

@login_required
def workbench(request):
    workspace = single_workspace_for(request.user)
    return render(request, "ai_workflows/workbench.html", {
        "leads": Lead.objects.filter(workspace=workspace).select_related("person").order_by("-created_at")[:40],
        "cases": TransactionCase.objects.filter(workspace=workspace).order_by("-created_at")[:50],
        "recommendations": AgentRecommendation.objects.filter(workspace=workspace).order_by("-created_at")[:30],
    })

@login_required
@require_POST
def review_lead(request, lead_id):
    workspace = single_workspace_for(request.user)
    lead = get_object_or_404(Lead, pk=lead_id, workspace=workspace)
    with db_transaction.atomic():
        for title, explanation in lead_review(lead):
            AgentRecommendation.objects.get_or_create(
                workspace=workspace, kind="lead", lead=lead, status="proposed", title=title,
                defaults={"explanation": explanation, "created_by": request.user},
            )
    return redirect("ai_workbench")

@login_required
def create_transaction(request):
    workspace = single_workspace_for(request.user)
    form = TransactionCaseForm(request.POST or None, workspace=workspace)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.workspace = workspace
        item.save()
        return redirect("ai_transaction_detail", case_id=item.pk)
    return render(request, "ai_workflows/create.html", {"form": form})

@login_required
def edit_transaction(request, case_id):
    workspace = single_workspace_for(request.user)
    item = get_object_or_404(TransactionCase, pk=case_id, workspace=workspace)
    form = TransactionCaseForm(request.POST or None, instance=item, workspace=workspace)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("ai_transaction_detail", case_id=item.pk)
    return render(request, "ai_workflows/create.html", {"form": form, "case": item})

@login_required
def transaction_detail(request, case_id):
    workspace = single_workspace_for(request.user)
    item = get_object_or_404(TransactionCase, pk=case_id, workspace=workspace)
    return render(request, "ai_workflows/detail.html", {
        "case": item,
        "recommendations": AgentRecommendation.objects.filter(workspace=workspace, transaction=item).order_by("-created_at"),
        "packets": item.contract_packets.select_related("template").order_by("-created_at"),
    })

@login_required
@require_POST
def review_transaction(request, case_id):
    workspace = single_workspace_for(request.user)
    item = get_object_or_404(TransactionCase, pk=case_id, workspace=workspace)
    with db_transaction.atomic():
        for title, explanation in transaction_review(item):
            AgentRecommendation.objects.get_or_create(
                workspace=workspace, kind="transaction", transaction=item, status="proposed", title=title,
                defaults={"explanation": explanation, "created_by": request.user},
            )
    return redirect("ai_transaction_detail", case_id=case_id)

@login_required
@require_POST
def update_recommendation(request, recommendation_id, action):
    if action not in ("acknowledged", "dismissed"):
        return HttpResponseBadRequest("Invalid action")
    workspace = single_workspace_for(request.user)
    item = get_object_or_404(AgentRecommendation, pk=recommendation_id, workspace=workspace)
    item.status = action
    item.save(update_fields=["status"])
    if item.transaction_id:
        return redirect("ai_transaction_detail", case_id=item.transaction_id)
    return redirect("ai_workbench")


# Brokerage paperwork: workspace-scoped preparation and owner/admin approved sends.
from django.contrib import messages
from django.utils import timezone
from accounts.models import Membership
from .forms import BrokerageSignatureTemplateForm, BrokerageContractPacketForm
from .models import BrokerageSignatureTemplate, BrokerageContractPacket
from .esign import SignatureSendError, prepare_request, send_request


def _can_send(user, workspace):
    return Membership.objects.filter(
        user=user, workspace=workspace, is_active=True,
        role__in=("owner", "admin")
    ).exists()


@login_required
def paperwork_templates(request):
    workspace = single_workspace_for(request.user)
    return render(request, "ai_workflows/templates_list.html", {
        "templates": BrokerageSignatureTemplate.objects.filter(workspace=workspace).order_by("name"),
        "can_manage": _can_send(request.user, workspace),
    })


@login_required
def new_paperwork_template(request):
    workspace = single_workspace_for(request.user)
    if not _can_send(request.user, workspace):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Only brokerage owners and admins can configure e-sign templates.")
    form = BrokerageSignatureTemplateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        template = form.save(commit=False)
        template.workspace = workspace
        template.save()
        return redirect("brokerage_paperwork_templates")
    return render(request, "ai_workflows/template_form.html", {"form": form})


@login_required
def new_contract_packet(request, case_id):
    workspace = single_workspace_for(request.user)
    case = get_object_or_404(TransactionCase, pk=case_id, workspace=workspace)
    form = BrokerageContractPacketForm(request.POST or None, workspace=workspace)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.workspace = workspace
        item.transaction = case
        item.created_by = request.user
        item.save()
        return redirect("brokerage_contract_packet", packet_id=item.pk)
    return render(request, "ai_workflows/packet_form.html", {"form": form, "case": case})


@login_required
def contract_packet(request, packet_id):
    workspace = single_workspace_for(request.user)
    packet = get_object_or_404(
        BrokerageContractPacket.objects.select_related("transaction", "template"),
        pk=packet_id, workspace=workspace,
    )
    return render(request, "ai_workflows/packet_detail.html", {
        "packet": packet,
        "can_send": _can_send(request.user, workspace),
        "live_enabled": __import__("os").environ.get("CRM_ESIGN_LIVE_SEND_ENABLED", "false").lower() == "true",
    })


@login_required
def edit_contract_packet(request, packet_id):
    workspace = single_workspace_for(request.user)
    packet = get_object_or_404(BrokerageContractPacket, pk=packet_id, workspace=workspace)
    if packet.status != "draft":
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Sent packets cannot be edited. Prepare a new packet.")
    form = BrokerageContractPacketForm(request.POST or None, instance=packet, workspace=workspace)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("brokerage_contract_packet", packet_id=packet.pk)
    return render(request, "ai_workflows/packet_form.html", {"form": form, "case": packet.transaction, "packet": packet})


@login_required
def send_contract_packet(request, packet_id):
    workspace = single_workspace_for(request.user)
    if not _can_send(request.user, workspace):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Only brokerage owners or admins can authorize e-sign sending.")
    packet = get_object_or_404(
        BrokerageContractPacket.objects.select_related("transaction", "template"),
        pk=packet_id, workspace=workspace,
    )
    if packet.status != "draft" or packet.provider_request_id:
        messages.error(request, "This packet has already been sent; it cannot be sent again.")
        return redirect("brokerage_contract_packet", packet_id=packet.pk)
    if not packet.template.is_active:
        messages.error(request, "This e-sign template is inactive.")
        return redirect("brokerage_contract_packet", packet_id=packet.pk)
    try:
        preview = prepare_request(packet)
    except SignatureSendError as exc:
        messages.error(request, str(exc))
        return redirect("brokerage_contract_packet", packet_id=packet.pk)
    if request.method == "GET":
        return render(request, "ai_workflows/packet_send_confirm.html", {
            "packet": packet, "preview": preview,
            "live_enabled": __import__("os").environ.get("CRM_ESIGN_LIVE_SEND_ENABLED", "false").lower() == "true",
        })
    if request.method != "POST":
        return HttpResponseBadRequest("Unsupported method")
    if request.POST.get("confirmation") != "send":
        return HttpResponseBadRequest("Explicit confirmation required.")
    with db_transaction.atomic():
        locked = get_object_or_404(BrokerageContractPacket.objects.select_for_update().select_related("template", "transaction"), pk=packet.pk, workspace=workspace)
        if locked.status != "draft" or locked.provider_request_id:
            messages.error(request, "This packet was already sent.")
            return redirect("brokerage_contract_packet", packet_id=packet.pk)
        try:
            request_id, test_mode = send_request(locked)
        except SignatureSendError as exc:
            messages.error(request, str(exc))
            return redirect("brokerage_contract_packet", packet_id=packet.pk)
        locked.provider_request_id = request_id
        locked.sent_test_mode = test_mode
        locked.sent_at = timezone.now()
        locked.status = "sent"
        locked.save(update_fields=["provider_request_id", "sent_test_mode", "sent_at", "status", "updated_at"])
    messages.success(request, "Dropbox Sign accepted the signature request. Check provider status for completion.")
    return redirect("brokerage_contract_packet", packet_id=packet.pk)
