from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from accounts.access import single_workspace_for
from accounts.models import Membership
from django.views.decorators.http import require_POST
from django.core.exceptions import ImproperlyConfigured
from .wordpress import sync_draft
from .forms import LandingPageForm, LandingInquiryForm
from .intake import create_landing_inquiry
from .models import LandingPage


@login_required
def list_pages(request):
    workspace = single_workspace_for(request.user)
    return render(request, "landing_pages/list.html", {
        "pages": LandingPage.objects.filter(workspace=workspace).order_by("-updated_at"),
        "can_sync_wordpress": Membership.objects.filter(workspace=workspace, user=request.user, is_active=True, role__in=["owner", "admin"]).exists(),
    })


@login_required
def create_page(request):
    workspace = single_workspace_for(request.user)
    form = LandingPageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        page = form.save(commit=False)
        page.workspace = workspace
        page.save()
        return redirect("landing_pages_list")
    return render(request, "landing_pages/form.html", {"form": form})


@login_required
def edit_page(request, page_id):
    workspace = single_workspace_for(request.user)
    page = get_object_or_404(LandingPage, pk=page_id, workspace=workspace)
    form = LandingPageForm(request.POST or None, instance=page)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("landing_pages_list")
    return render(request, "landing_pages/form.html", {"form": form, "page": page})


@login_required
def preview_page(request, page_id):
    workspace = single_workspace_for(request.user)
    page = get_object_or_404(LandingPage, pk=page_id, workspace=workspace)
    form = LandingInquiryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        create_landing_inquiry(page, form.cleaned_data)
        return render(request, 'landing_pages/received.html')
    return render(request, 'landing_pages/preview.html', {'page': page, 'form': form})


@login_required
@require_POST
def sync_wordpress_page(request, page_id):
    workspace = single_workspace_for(request.user)
    page = get_object_or_404(LandingPage, pk=page_id, workspace=workspace)
    if not Membership.objects.filter(workspace=workspace, user=request.user, is_active=True, role__in=["owner", "admin"]).exists():
        return HttpResponseForbidden("Only a workspace owner or administrator can sync WordPress drafts.")
    try:
        sync_draft(page)
    except (RuntimeError, ImproperlyConfigured) as exc:
        cause = exc.__cause__
        status_code = getattr(cause, "code", None)
        detail = {
            401: "WordPress rejected the credentials. Check the username and Application Password.",
            403: "WordPress denied page editing permission or blocked the API request.",
            404: "The WordPress Pages API endpoint was not found.",
        }.get(status_code, "Check Render credentials and WordPress REST API access.")
        return render(request, "landing_pages/sync_result.html", {
            "ok": False, "page": page, "detail": detail,
        }, status=502)
    return render(request, "landing_pages/sync_result.html", {
        "ok": True, "page": page,
    })
