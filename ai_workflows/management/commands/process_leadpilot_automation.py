"""Run from a scheduled Render Cron Job, NOT on every web request.

Usage: python manage.py process_leadpilot_automation
Defaults: daily outbound cap 10, max 5 dispatches and 20 polls per invocation.
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ai_workflows.automation import enabled_for, queue_transaction
from ai_workflows.engine import transaction_review
from ai_workflows.leadpilot_bridge import LeadPilotBridgeError, check_review, start_review
from ai_workflows.models import AgentRecommendation, LeadPilotReview, TransactionCase


class Command(BaseCommand):
    help = "Queue & poll opt-in LeadPilot AI sales reviews; never sends messages or contracts."

    def add_arguments(self, parser):
        parser.add_argument("--dispatch-limit", type=int, default=5)
        parser.add_argument("--poll-limit", type=int, default=20)

    def handle(self, *args, **options):
        workspace = getattr(settings, "LEADPILOT_CRM_WORKSPACE_ID", "")
        if not enabled_for(workspace):
            self.stdout.write("LeadPilot proactive automation disabled or integration not configured.")
            return

        today = timezone.localdate()
        # No stale/closed cases: due milestones trigger a review at most once daily.
        cases = TransactionCase.objects.filter(workspace_id=workspace).exclude(stage__in=["closed", "cancelled"])
        for case in cases.iterator():
            if not case.workspace_id:
                continue
            queue_transaction(case, today=today)
            # Deterministic CRM-only reminders, no hallucinated dates or legal decisions.
            if any(date and date <= today + timezone.timedelta(days=7) for date in (
                case.inspection_deadline, case.financing_deadline, case.closing_date,
            )):
                for title, explanation in transaction_review(case):
                    if title.endswith("approaching") or title.endswith("date passed"):
                        AgentRecommendation.objects.get_or_create(
                            workspace=case.workspace, kind="transaction", transaction=case,
                            title=title, status="proposed",
                            defaults={"explanation": explanation},
                        )

        dispatched = LeadPilotReview.objects.filter(
            workspace_id=workspace, created_at__date=today,
        ).exclude(remote_run_id="").count()
        allowance = max(0, settings.LEADPILOT_AUTOMATION_DAILY_CAP - dispatched)
        dispatch_limit = max(0, min(allowance, options["dispatch_limit"], 20))
        sent = 0
        # Claim a queued review per transaction; don't repeat an ambiguous remote call.
        pending_ids = list(
            LeadPilotReview.objects.filter(workspace_id=workspace, status="pending")
            .order_by("created_at").values_list("pk", flat=True)[:dispatch_limit]
        )
        for review_id in pending_ids:
            with transaction.atomic():
                review = LeadPilotReview.objects.select_for_update().get(pk=review_id, workspace_id=workspace)
                if review.status != "pending" or review.remote_run_id:
                    continue
                # Never make a remote request for closed/lost leads or closed/cancelled deals.
                subject = review.lead if review.lead_id else review.transaction
                if subject is None or (
                    review.lead_id and subject.status in ("lost", "closed")
                ) or (
                    review.transaction_id and subject.stage in ("closed", "cancelled")
                ):
                    review.status = "skipped"
                    review.save(update_fields=["status", "updated_at"])
                    continue
                review.status = "submitting"
                review.save(update_fields=["status", "updated_at"])
            try:
                result = start_review(review, subject)
            except LeadPilotBridgeError as exc:
                review.status = "unavailable"
                review.error_message = str(exc)[:300]
                review.save(update_fields=["status", "error_message", "updated_at"])
                self.stderr.write("LeadPilot request unavailable for review {}".format(review.pk))
                continue
            review.remote_run_id = result["run_id"]
            review.status = str(result.get("status") or "queued")[:30]
            review.error_message = ""
            review.save(update_fields=["remote_run_id", "status", "error_message", "updated_at"])
            sent += 1

        polled = 0
        for review in LeadPilotReview.objects.filter(
            workspace_id=workspace,
            status__in=("queued", "running", "retrying", "submitting", "pending"),
        ).exclude(remote_run_id="").order_by("updated_at")[:max(0, min(options["poll_limit"], 100))]:
            try:
                result = check_review(review)
            except LeadPilotBridgeError:
                continue
            review.status = str(result.get("status") or "running")[:30]
            outcome = result.get("result")
            if isinstance(outcome, (dict, list)):
                review.result_json = outcome
            review.error_message = str(result.get("error") or "")[:300]
            review.save(update_fields=["status", "result_json", "error_message", "updated_at"])
            polled += 1

        self.stdout.write("Submitted {} LeadPilot reviews, refreshed {} statuses; daily cap {}.".format(
            sent, polled, settings.LEADPILOT_AUTOMATION_DAILY_CAP
        ))
