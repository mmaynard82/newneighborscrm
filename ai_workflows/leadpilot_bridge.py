"""Opt-in New Neighbors -> LeadPilot server bridge (no browser cookies).

No background automation or remote approval. A user initiates a review and the
CRM retrieves draft output for manual inspection.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from django.core.exceptions import ImproperlyConfigured


class LeadPilotBridgeError(Exception):
    pass


def _config(workspace_id):
    base = os.environ.get("LEADPILOT_BRIDGE_URL", "").rstrip("/")
    token = os.environ.get("LEADPILOT_BRIDGE_TOKEN", "")
    allowed_workspace = os.environ.get("LEADPILOT_CRM_WORKSPACE_ID", "")
    if not base or len(token) < 32 or not allowed_workspace:
        raise LeadPilotBridgeError("LeadPilot integration is not configured. Ask a CRM administrator to configure the bridge.")
    if str(workspace_id) != allowed_workspace:
        raise LeadPilotBridgeError("This CRM workspace is not connected to LeadPilot.")
    url = urlsplit(base)
    if url.scheme != "https" or not url.netloc or url.username or url.password or url.query or url.fragment:
        raise ImproperlyConfigured("LeadPilot must be configured with a secure HTTPS URL.")
    return base, token


def _call(*, workspace_id, method, path, payload=None):
    base, token = _config(workspace_id)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        base + "/integrations/new-neighbors/" + path,
        data=data, method=method,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=12) as response:
            result = json.load(response)
    except HTTPError as exc:
        if exc.code in (401, 403):
            raise LeadPilotBridgeError("LeadPilot rejected integration access. Check the matching API tokens.") from exc
        if exc.code == 409:
            raise LeadPilotBridgeError("Required LeadPilot real estate team is unavailable, disabled or awaiting review. Verify its setup.") from exc
        raise LeadPilotBridgeError("LeadPilot could not accept the review (HTTP {}). Check both applications.".format(exc.code)) from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise LeadPilotBridgeError("LeadPilot is unreachable or returned an invalid response. Check LeadPilot before retrying.") from exc
    if not isinstance(result, dict) or not isinstance(result.get("run_id"), str):
        raise LeadPilotBridgeError("LeadPilot returned an incomplete response. Check its dashboard.")
    return result


def start_review(review, subject):
    if review.lead_id:
        lead = subject
        payload = {
            "kind": "lead",
            "reference": review.reference,
            "title": "New Neighbors lead review #" + str(lead.pk),
            "summary": "Review this real estate sales lead and prepare a professional follow-up plan for agent approval. Do not send messages. Current status: " + lead.status,
            "details": {
                "lead_type": lead.lead_type,
                "client_name": (lead.person.first_name + " " + lead.person.last_name).strip(),
                "inquiry_notes": (lead.notes or "Not provided")[:300],
                "next_step": (lead.next_step or "Not provided")[:200],
                "follow_up_date": lead.next_follow_up_date.isoformat() if lead.next_follow_up_date else "Not set",
            },
        }
    else:
        case = subject
        payload = {
            "kind": "transaction",
            "reference": review.reference,
            "title": "New Neighbors transaction: " + case.title[:160],
            "summary": "Provide a contract-to-close checklist, milestone verification questions, and recommended next actions for agent approval only. Do not invent contract dates or send documents.",
            "details": {
                "stage": case.stage,
                "inspection_deadline": case.inspection_deadline.isoformat() if case.inspection_deadline else "Not verified",
                "financing_deadline": case.financing_deadline.isoformat() if case.financing_deadline else "Not verified",
                "closing_date": case.closing_date.isoformat() if case.closing_date else "Not verified",
                "transaction_notes": (case.notes or "None")[:300],
            },
        }
    return _call(workspace_id=review.workspace_id, method="POST", path="reviews", payload=payload)


def check_review(review):
    if not review.remote_run_id:
        raise LeadPilotBridgeError("No LeadPilot review has been started.")
    return _call(workspace_id=review.workspace_id, method="GET", path="reviews/" + review.remote_run_id)
