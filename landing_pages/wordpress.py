"""WordPress draft integration. No public publishing from this module."""
import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.exceptions import ImproperlyConfigured


WORDPRESS_PAGES_API = "https://newneighborsinc.com/?rest_route=/wp/v2/pages"


def sync_draft(page):
    """Save or update a PRIVATE-TO-EDITORS WordPress draft; never publish."""
    username = os.environ.get("NEWNEIGHBORS_WP_USERNAME", "").strip()
    password = os.environ.get("NEWNEIGHBORS_WP_APP_PASSWORD", "").strip()
    if not username or not password:
        raise ImproperlyConfigured("WordPress application credentials are not configured.")

    # Escaped text avoids storing executable HTML supplied via the CRM editor.
    from django.utils.html import escape
    content = "<h1>{}</h1><p>{}</p>".format(
        escape(page.headline), escape(page.description).replace("\n", "<br>"),
    )
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
