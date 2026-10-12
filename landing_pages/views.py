from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from accounts.access import single_workspace_for
from .forms import LandingPageForm, LandingInquiryForm
from .intake import create_landing_inquiry
from .models import LandingPage


@login_required
def list_pages(request):
    workspace = single_workspace_for(request.user)
    return render(request, "landing_pages/list.html", {
        "pages": LandingPage.objects.filter(workspace=workspace).order_by("-updated_at"),
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
