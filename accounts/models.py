from django.conf import settings
from django.db import models


class Workspace(models.Model):
    """A data boundary for one solo agent or one brokerage."""
    SOLO = "solo"
    BROKERAGE = "brokerage"
    KINDS = [(SOLO, "Individual Agent"), (BROKERAGE, "Brokerage")]

    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=KINDS)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    OWNER = "owner"
    ADMIN = "admin"
    AGENT = "agent"
    ROLES = [(OWNER, "Owner"), (ADMIN, "Administrator"), (AGENT, "Agent")]

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="crm_memberships")
    role = models.CharField(max_length=20, choices=ROLES, default=AGENT)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["workspace", "user"], name="unique_crm_workspace_member"),
        ]

    def __str__(self):
        return f"{self.user} — {self.workspace} ({self.role})"
