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
def transaction_detail(request, case_id):
    workspace = single_workspace_for(request.user)
    item = get_object_or_404(TransactionCase, pk=case_id, workspace=workspace)
    return render(request, "ai_workflows/detail.html", {
        "case": item,
        "recommendations": AgentRecommendation.objects.filter(workspace=workspace, transaction=item).order_by("-created_at"),
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
