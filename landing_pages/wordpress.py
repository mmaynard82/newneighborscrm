"""WordPress draft integration. No public publishing from this module."""
import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.conf import settings
from .design import render_wordpress_content


WORDPRESS_PAGES_API = "https://newneighborsinc.com/?rest_route=/wp/v2/pages"


def sync_draft(page):
    """Save or update a PRIVATE-TO-EDITORS WordPress draft; never publish."""
    if page.status == "published":
        raise RuntimeError("Published pages cannot be overwritten by draft sync.")
    username = os.environ.get("NEWNEIGHBORS_WP_USERNAME", "").strip()
    password = os.environ.get("NEWNEIGHBORS_WP_APP_PASSWORD", "").strip()
    if not username or not password:
        raise ImproperlyConfigured("WordPress application credentials are not configured.")

    # Escaped text avoids storing executable HTML supplied via the CRM editor.
    form_url = settings.CRM_PUBLIC_BASE_URL.rstrip("/") + reverse(
        "landing_pages_public_inquiry", kwargs={"token": page.public_form_token}
    )
    content = render_wordpress_content(page, form_url)
    payload = json.dumps({
        "title": page.title,
        "slug": page.slug,
        "content": content,
        "status": "draft",
    }).encode("utf-8")
    url = WORDPRESS_PAGES_API
    if page.wordpress_page_id:
        url += "/{}".format(page.wordpress_page_id)
    token = base64.b64encode("{}:{}".format(username, password).encode()).decode()
    request = Request(
        url, data=payload, method="POST",
        headers={
            "Authorization": "Basic " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("WordPress draft sync failed; check API credentials and connectivity.") from exc

    if result.get("status") != "draft" or not isinstance(result.get("id"), int):
        raise RuntimeError("WordPress did not confirm a draft; CRM metadata was not updated.")
    page.wordpress_page_id = result["id"]
    page.wordpress_url = result.get("link", "")
    page.save(update_fields=["wordpress_page_id", "wordpress_url", "updated_at"])
    return page


def publish_existing_draft(page):
    """Publish only a previously linked WordPress draft after explicit CRM approval."""
    if not page.wordpress_page_id:
        raise RuntimeError("Save a WordPress draft before publishing.")
    if page.status == "published":
        raise RuntimeError("This page is already marked as published.")
    username = os.environ.get("NEWNEIGHBORS_WP_USERNAME", "").strip()
    password = os.environ.get("NEWNEIGHBORS_WP_APP_PASSWORD", "").strip()
    if not username or not password:
        raise ImproperlyConfigured("WordPress application credentials are not configured.")
    url = WORDPRESS_PAGES_API + "/" + str(page.wordpress_page_id)
    token = base64.b64encode("{}:{}".format(username, password).encode()).decode()
    request = Request(
        url, data=json.dumps({"status": "publish"}).encode("utf-8"), method="POST",
        headers={"Authorization": "Basic " + token, "Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            result = json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError("WordPress did not confirm publication.") from exc
    if not isinstance(result, dict) or result.get("status") != "publish" or result.get("id") != page.wordpress_page_id:
        raise RuntimeError("WordPress did not confirm publication.")
    page.status = "published"
    page.wordpress_url = result.get("link") or page.wordpress_url
    page.save(update_fields=["status", "wordpress_url", "updated_at"])
    return page
