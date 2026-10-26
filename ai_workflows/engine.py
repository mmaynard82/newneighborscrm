"""Conservative pre-integration review rules. No LLM or LeadAIAgent API invocation."""
from datetime import timedelta
from django.utils import timezone

def lead_review(lead):
    ideas = []
    if lead.status == "new":
        ideas.append(("First-contact follow-up", "This lead is marked new. Review the inquiry and prepare a personalized response for human approval."))
    if not lead.assigned_agent_id:
        ideas.append(("Assign an agent", "No agent is assigned. Select an active agent in this workspace before outreach."))
    if not lead.next_follow_up_date:
        ideas.append(("Schedule follow-up", "No follow-up date is recorded. Set one based on the client's request and team process."))
    if not ideas:
        ideas.append(("Review next step", "Review the lead status, latest communications and follow-up task before proceeding."))
    return ideas

def transaction_review(case):
    today = timezone.localdate()
    ideas = []
    for label, value in (("Inspection", case.inspection_deadline), ("Financing", case.financing_deadline), ("Closing", case.closing_date)):
        if value is None:
            ideas.append((label + " date unconfirmed", "No " + label.lower() + " date is recorded. Verify signed documents before entering a deadline."))
        elif value < today:
            ideas.append((label + " date passed", label + " date recorded as " + value.isoformat() + ". Confirm status promptly; do not infer a default extension."))
        elif value <= today + timedelta(days=7):
            ideas.append((label + " approaching", label + " date recorded as " + value.isoformat() + ". Verify required documents and responsible parties."))
    if not ideas:
        ideas.append(("Transaction status review", "Review the documents, contingencies and next confirmed milestones."))
    return ideas
