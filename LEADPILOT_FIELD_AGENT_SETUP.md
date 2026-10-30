# New Neighbors Agent Field Desk + LeadPilot AI

## Field agent daily flow

1. **Connect:** open a buyer or seller lead, assign an agent, log the conversation and follow-up.
2. **Meet:** schedule a buyer consult, listing appointment, property showing or open house.
3. **Negotiate:** organize the offer review and set up the sales transaction.
4. **Contract:** record confirmed contract contingencies; prepare approved brokerage document templates.
5. **Close:** schedule inspections, appraisal, final walk-through and closing.
6. **AI assistance:** explicitly request LeadPilot's existing Real Estate Lead Conversion Team or Real Estate Transaction Coordination Team. AI drafts are read-only in this CRM and require human review. They do not automatically send texts, emails, legal documents or change contract fields.

## Separate deployment required

Two pull requests are required:
- `mmaynard82/aiagent`: authenticated New Neighbors bridge API for LeadPilot agent team reviews.
- `mmaynard82/newneighborscrm`: field-agent experience and secure bridge client.

Merge and deploy both repositories, then configure **both Render services**. The integration is deliberately disabled until it is explicitly configured.

### LeadPilot Render service settings

```
NEW_NEIGHBORS_BRIDGE_TOKEN=<same randomly generated secret, 32+ characters>
NEW_NEIGHBORS_BRIDGE_WORKSPACE_ID=<exact UUID for the LeadPilot workspace used by this brokerage>
```

Within that LeadPilot workspace, enable both prebuilt teams:
- `real-estate-lead-conversion-team`
- `real-estate-transaction-team`

**Require final human approval** for both teams. A disabled team or unattended team is rejected by the bridge. A running LeadPilot worker and any required AI provider/billing configuration are necessary for actual output.

### New Neighbors CRM Render service settings

```
LEADPILOT_BRIDGE_URL=https://<your-leadpilot-application-hostname>
LEADPILOT_BRIDGE_TOKEN=<same randomly generated secret, 32+ characters>
LEADPILOT_CRM_WORKSPACE_ID=<exact numeric workspace ID for the New Neighbors brokerage>
```

Use an HTTPS service origin without a trailing slash; do not append the API path. The remote workspace ID is **not** derived from a public request and is pinned to the workspace configured on LeadPilot. This first integration connects **one CRM brokerage workspace to one LeadPilot workspace**. Other brokerage workspaces are intentionally blocked, not silently mapped.

## What happens on review

- A signed-in CRM user requests a review via POST; no passive CRM browsing triggers a remote run.
- The CRM sends a limited sales lead or transaction summary to the workspace-pinned LeadPilot service. This is data sharing; obtain the brokerage's appropriate disclosures/authorizations before use.
- LeadPilot creates a work item and queues its existing real estate agent team. It returns a run ID.
- The CRM saves this reference. An operator clicks **Refresh AI result** to retrieve the draft analysis.
- All AI output remains informational. Review it for accuracy; no CRM contracts, lead statuses, appointments or outbound messages are altered by the response.
- Existing CRM-only checklist remains available when the LeadPilot bridge is not configured.

## Remaining production work

- This is an explicit *request and review* integration, not unattended continuous automation.
- A queued LeadPilot run requires a functioning worker and available AI credits/provider.
- The workbench currently renders the returned structured analysis in a readable raw JSON section; a richer AI briefing/approve-draft UI can be added later.
- Appointment records are not yet synced with Google Calendar.
- For legally binding contracts use approved templates and verify status/audit trail at your e-sign provider. AI is not allowed to create or change legal agreements autonomously.
