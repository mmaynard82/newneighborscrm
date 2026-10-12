from django.core.management.base import BaseCommand, CommandError
from landing_pages.models import LandingPage
from landing_pages.wordpress import sync_draft


class Command(BaseCommand):
    help = "Synchronize one CRM landing page to New Neighbors WordPress as a draft only."

    def add_arguments(self, parser):
        parser.add_argument("page_id", type=int)

    def handle(self, *args, **options):
        try:
            page = LandingPage.objects.get(pk=options["page_id"])
        except LandingPage.DoesNotExist as exc:
            raise CommandError("Landing page does not exist.") from exc
        try:
            sync_draft(page)
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS("WordPress draft synchronized (not published)."))
