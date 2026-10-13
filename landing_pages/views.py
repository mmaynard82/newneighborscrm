from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger(__name__)
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.core.cache import cache
from django.http import HttpResponse
import hashlib
from accounts.access import single_workspace_for
from accounts.models import Membership
from django.views.decorators.http import require_POST
from django.core.exceptions import ImproperlyConfigured
from .wordpress import sync_draft, publish_existing_draft
from .forms import LandingPageForm, LandingInquiryForm
from .intake import create_landing_inquiry
from .models import LandingPage
from leads.models import Lead
from django.db.models import Count


@login_required
def list_pages(request):
    workspace = single_workspace_for(request.user)
    pages = list(LandingPage.objects.filter(workspace=workspace).select_related("assigned_agent").order_by("-updated_at"))
    counts = dict(
        Lead.objects.filter(
            workspace=workspace,
            source__in=["landing_page:" + str(page.id) for page in pages],
        ).values("source").annotate(count=Count("id")).values_list("source", "count")
    )
    for page in pages:
        page.inquiry_count = counts.get("landing_page:" + str(page.id), 0)
    return render(request, "landing_pages/list.html", {
        "pages": pages,
        "can_sync_wordpress": Membership.objects.filter(workspace=workspace, user=request.user, is_active=True, role__in=["owner", "admin"]).exists(),
    })


@login_required
def create_page(request):
    workspace = single_workspace_for(request.user)
    form = LandingPageForm(request.POST or None, workspace=workspace)
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
    form = LandingPageForm(request.POST or None, instance=page, workspace=workspace)
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
    except Exception:
        logger.exception("Unexpected WordPress draft sync failure (page_id=%s)", page.id)
        return render(request, "landing_pages/sync_result.html", {
            "ok": False, "page": page,
            "detail": "An unexpected server error occurred. Check Render logs for the WordPress draft sync traceback.",
        }, status=502)
    return render(request, "landing_pages/sync_result.html", {
        "ok": True, "page": page,
    })


@never_cache
def public_inquiry(request, token):
    """Public contact form linked from a WordPress draft; never reveals tenant details."""
    page = get_object_or_404(LandingPage, public_form_token=token)
    if request.method not in ("GET", "POST"):
        return HttpResponse(status=405)
    form = LandingInquiryForm(request.POST or None)
    if request.method == "POST":
        # Limit per form and client address; cache may be per-process on basic Render.
        address = request.META.get("REMOTE_ADDR", "")
        fingerprint = hashlib.sha256((token + "|" + address).encode()).hexdigest()
        key = "landing_form_hits:" + fingerprint
        if cache.get(key, 0) >= 5:
            return render(request, "landing_pages/public_form.html", {
                "page": page, "form": form, "limited": True,
            }, status=429)
        if form.is_valid():
            cache.add(key, 0, timeout=3600)
            try:
                cache.incr(key)
            except ValueError:
                cache.set(key, 1, timeout=3600)
            if not form.cleaned_data.get("website"):
                create_landing_inquiry(page, form.cleaned_data)
            return render(request, "landing_pages/received.html")
    return render(request, "landing_pages/public_form.html", {"page": page, "form": form})


@login_required
def publish_wordpress_page(request, page_id):
    workspace = single_workspace_for(request.user)
    page = get_object_or_404(LandingPage, pk=page_id, workspace=workspace)
    if not Membership.objects.filter(
        workspace=workspace, user=request.user, is_active=True, role__in=["owner", "admin"]
    ).exists():
        return HttpResponseForbidden("Only a workspace owner or administrator can publish.")
    if request.method == "GET":
        return render(request, "landing_pages/publish_confirm.html", {"page": page})
    if request.method != "POST":
        return HttpResponse(status=405)
    if request.POST.get("confirm") != "publish":
        return HttpResponse(status=400)
    try:
        publish_existing_draft(page)
    except (RuntimeError, ImproperlyConfigured):
        return render(request, "landing_pages/publish_result.html", {
            "ok": False, "page": page,
            "detail": "WordPress did not confirm publication. Check that the draft exists and the WordPress account can publish pages.",
        }, status=502)
    except Exception:
        logger.exception("Unexpected WordPress publication failure (page_id=%s)", page.id)
        return render(request, "landing_pages/publish_result.html", {
            "ok": False, "page": page,
            "detail": "A server error occurred. Check Render logs before retrying.",
        }, status=502)
    return render(request, "landing_pages/publish_result.html", {"ok": True, "page": page})
