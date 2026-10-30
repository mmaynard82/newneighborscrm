"""Explicit operator-approved Dropbox Sign template requests.

Templates and signer roles must already exist in the brokerage's Dropbox Sign account.
This module never generates legal agreements or claims that signatures are completed.
"""
import base64
import json
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

DROPBOX_SIGN_SEND_URL = "https://api.hellosign.com/v3/signature_request/send_with_template"


class SignatureSendError(Exception):
    pass


def prepare_request(packet):
    template = packet.template
    signers = []
    if template.buyer_role:
        if not packet.buyer_name or not packet.buyer_email:
            raise SignatureSendError("Buyer name and email are required.")
        signers.append({"role": template.buyer_role, "name": packet.buyer_name, "email_address": packet.buyer_email})
    if template.seller_role:
        if not packet.seller_name or not packet.seller_email:
            raise SignatureSendError("Seller name and email are required.")
        signers.append({"role": template.seller_role, "name": packet.seller_name, "email_address": packet.seller_email})
    if not signers:
        raise SignatureSendError("Template has no configured signer roles.")

    values = [
        ("property_address_field", packet.property_address),
        ("purchase_price_field", str(packet.purchase_price) if packet.purchase_price is not None else ""),
        ("deposit_field", str(packet.deposit) if packet.deposit is not None else ""),
        ("closing_date_field", packet.closing_date.isoformat() if packet.closing_date else ""),
        ("additional_terms_field", packet.additional_terms),
    ]
    custom_fields = []
    for attr, value in values:
        name = getattr(template, attr)
        if name:
            if not value.strip():
                raise SignatureSendError("Missing required packet value for configured field: " + attr)
            custom_fields.append({"name": name, "value": value})
    return {
        "template_ids": [template.provider_template_id],
        "title": packet.template.name + " - " + packet.transaction.title,
        "subject": "New Neighbors - document signature request",
        "message": "Please review the document carefully before signing. Contact your real estate agent with questions.",
        "signers": signers,
        "custom_fields": custom_fields,
        "metadata": {"crm_packet_id": str(packet.pk), "crm_workspace_id": str(packet.workspace_id)},
    }


def send_request(packet):
    key = os.environ.get("DROPBOX_SIGN_API_KEY", "").strip()
    if not key:
        raise SignatureSendError("Dropbox Sign API key has not been configured on Render.")
    payload = prepare_request(packet)
    test_mode = os.environ.get("CRM_ESIGN_LIVE_SEND_ENABLED", "false").lower() != "true"
    payload["test_mode"] = test_mode
    authorization = base64.b64encode((key + ":").encode("utf-8")).decode("ascii")
    request = Request(
        DROPBOX_SIGN_SEND_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Authorization": "Basic " + authorization, "Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            result = json.load(response)
    except HTTPError as exc:
        logger.warning("Dropbox Sign rejected signature request for packet %s (HTTP %s)", packet.pk, exc.code)
        raise SignatureSendError("E-sign provider rejected the request. Verify the template ID, signer roles and fields in Dropbox Sign.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        logger.exception("E-sign request connection error for packet %s", packet.pk)
        raise SignatureSendError("E-sign provider connection failed. Check the provider dashboard before trying again; the request may have been delivered.") from exc
    except (ValueError, TypeError) as exc:
        raise SignatureSendError("Unexpected e-sign provider response. Check the provider dashboard before retrying.") from exc

    request_id = result.get("signature_request", {}).get("signature_request_id")
    if not isinstance(request_id, str) or not request_id:
        raise SignatureSendError("Provider did not return a signature request ID. Check the provider dashboard before retrying.")
    return request_id, test_mode
