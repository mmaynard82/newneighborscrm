# Sales Brokerage CRM: Contracts and E-Signatures

This CRM now focuses its default navigation and dashboard on buyers, sellers, listings/properties, leads, sales transactions, offers/paperwork and closings. Existing service/maintenance records remain in the database for historical retention; the change is not a data deletion.

## How paperwork works

1. Brokerage owner/admin creates an approved, fillable real-estate form template in **Dropbox Sign**, including named buyer/seller signer roles and optional merge/custom fields.
2. Owner/admin opens **Sales Transactions → Contracts & E-Sign → Register approved form** and saves the *actual Dropbox Sign template ID*, the matching signer role names and any matching merge field names. This does not upload or change a legal form.
3. Agent opens **Sales Transactions**, selects a transaction, chooses **Prepare contract or disclosure**, and fills buyer/seller contact details and any deal terms supported by that approved template.
4. Owner/admin reviews the packet, the recipients and the exact values to be inserted, then explicitly clicks **I verified this paperwork — send to Dropbox Sign**.
5. The provider receives a request using the preconfigured legal template; the CRM stores the returned signature request ID. The signed PDF, signer identity verification, signature audit trail, completion status, cancellations and archiving must be monitored and handled in Dropbox Sign until a separately implemented authenticated webhook/file retrieval workflow is deployed.

**Important:** This is *template field prefill*; it is not a general PDF editor, generic contract generator, or legal agreement drafting system. Only use forms licensed and reviewed by the brokerage and the appropriate CT/MA real estate/legal professionals.

### Render environment

- `DROPBOX_SIGN_API_KEY` — secret API key for the brokerage's Dropbox Sign account.
- `CRM_ESIGN_LIVE_SEND_ENABLED` — **false by default**. With false, provider requests use test mode and are not legally binding. Set to `true` only after confirming templates, account billing, permission controls and test runs.

Dropbox Sign template IDs, role labels and merge-field names are account-specific. Paid plan limits apply; check Dropbox Sign API eligibility and pricing. Sending via the provider API may incur charges. A failed/timeout response may be ambiguous; **check Dropbox Sign before retrying**. No automatic retry is performed.

### Security and operational limits

- Every packet and associated transaction belongs to exactly one CRM workspace.
- Owners/admins can configure approved form templates and authorize external sends; agents can prepare packets.
- A send requires a separate confirmation POST, and a successful packet cannot be resent.
- Recipient names and email addresses are sent to Dropbox Sign only after approval.
- A provider acceptance is **not** proof of signed completion. Provider dashboard and executed PDF/audit trail remain authoritative.
- Existing records and WordPress pages are preserved; don't delete historical data without a retention review.
- Real estate offers/agreements may require additional signers or multiple forms; currently each packet supports one Buyer and one Seller role. Expand after selecting actual brokerage forms.
