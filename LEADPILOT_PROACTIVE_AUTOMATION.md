# New Neighbors CRM — Proactive LeadPilot AI (Phases 1 and 2)

## New agent experience

**Phase 1: Lead conversion.** When a new sales lead is saved (including a website inquiry), New Neighbors records one pending LeadPilot review. The review is submitted to the existing Real Estate Lead Conversion Team when the scheduled worker runs. The CRM displays a readable readiness score and draft action plan under Agent Field Desk. Agents inspect and approve their own follow-up; nothing is automatically emailed, texted or added to an e-signature packet.

**Phase 2: Transaction coordination.** A new sales transaction creates one pending LeadPilot review. A daily scan identifies active deals with recorded inspection, financing or closing dates inside the next seven days (or already past). It creates conservative CRM reminders and may queue one LeadPilot review per transaction/day. The AI Transaction Coordination Team drafts an action checklist. The CRM shows recommendations directly on the transaction.

Only recorded dates are treated as confirmed. Missing contract terms are marked unverified; AI does not invent deadlines or change executed documents.

## Activation checklist (administrator)

1. Merge and deploy the existing LeadPilot service bridge (LeadPilot AI PR #16) and Agent Field Desk (CRM PR #20), if not already deployed.
2. Enable both real-estate LeadPilot teams in the chosen LeadPilot workspace and require **final human approval** on each.
3. Configure both services with the same random 32+-character API token and pinned workspace mapping as outlined in `LEADPILOT_FIELD_AGENT_SETUP.md`. Do not put credentials in GitHub or share them with agents.
4. Configure these CRM Render environment values:
   - `LEADPILOT_BRIDGE_URL` = HTTPS base URL of LeadPilot
   - `LEADPILOT_BRIDGE_TOKEN` = shared secret
   - `LEADPILOT_CRM_WORKSPACE_ID` = *numeric* New Neighbors CRM workspace ID
   - `LEADPILOT_AUTOMATION_DAILY_CAP=10` (change only after checking billing)
   - `LEADPILOT_AUTOMATION_ENABLED=true` (leave `false` until ready)
5. Create a **Render Cron Job**, using the same deployment commit, Python environment, database URL, and integration environment settings as the CRM web service. Command:
   ```
   python manage.py process_leadpilot_automation
   ```
   Recommended schedule: `*/15 * * * *` (every 15 minutes). Use only **one** scheduled worker for a brokerage workspace. Do not run multiple copies at the same time. Set the cron service to use the same production PostgreSQL database as the web app. It must not use an ephemeral local SQLite database. Check Render's cron job plan and billing.
6. Run a test: create one new buyer lead, run the worker, verify the queued AI review appears, wait for the LeadPilot worker to process it, then run the CRM worker again to retrieve recommendations. Repeat with an example transaction that has a verified inspection date in the next seven days.
7. Confirm AI output is a **draft recommendation**, not sent communication. Check user permissions before giving agents access.

## Safety and usage rules

- Automation defaults **off** and is blocked for any CRM workspace other than the exact workspace in `LEADPILOT_CRM_WORKSPACE_ID`.
- Property-management leads and closed/lost leads are not submitted.
- New sale lead submissions deduplicate by CRM lead ID. Repeat transaction review scans are limited to one review per eligible transaction/day.
- Daily outbound submissions are capped (10 by default, hard maximum setting 50). The per-command dispatch limit defaults to 5.
- Sending to LeadPilot occurs **only from the scheduled command**; saving a lead does not make an external network call.
- If a remote send is unavailable or times out, the record is marked `unavailable` and is not automatically retried, preventing accidental duplicate AI charges. Administrators should inspect the LeadPilot dashboard before attempting a new review.
- Review results are stored in the brokerage's CRM and only visible through authenticated, workspace-scoped views. Data is shared with the configured LeadPilot workspace; consult your brokerage data/privacy policy and obtain needed consents.
- Every action and email or SMS recommendation is displayed **for human review only**. No AI-generated legal agreement edits, e-sign sends, or CRM status changes are performed by this worker.
- The scheduled job and LeadPilot background worker must both be running for automatic AI results to arrive.

## Current limitations

- The CRM is not an autonomous messaging tool. Automated *analysis* is supported, not automatic client outreach.
- The included worker is a scheduled task, not a 24/7 streaming queue. Results will appear after the next successful worker invocation.
- AI costs/quotas depend on the connected LeadPilot workspace.
- Historical leads are not bulk-backfilled automatically; manual review remains available.
- A provider failure can leave a job in `submitting`; an administrator must inspect the remote provider before resubmitting to avoid duplicate work.
- AI readiness scores and action plans can be wrong; agents must verify identity, property details, financial assertions and contract deadlines.
