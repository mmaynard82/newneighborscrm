from django.db import models
from people.models import Person
from leads.models import Lead


class CommunicationLog(models.Model):
    COMMUNICATION_TYPES = [
        ("call", "Call"),
        ("email", "Email"),
        ("text", "Text"),
        ("meeting", "Meeting"),
        ("voicemail", "Voicemail"),
        ("facebook_message", "Facebook Message"),
        ("website_inquiry", "Website Inquiry"),
        ("referral_note", "Referral Note"),
        ("other", "Other"),
    ]

    OUTCOMES = [
        ("connected", "Connected"),
        ("left_message", "Left Message"),
        ("no_response", "No Response"),
        ("scheduled_consult", "Scheduled Consult"),
        ("sent_info", "Sent Information"),
        ("follow_up_needed", "Follow-Up Needed"),
        ("not_interested", "Not Interested"),
        ("converted", "Converted"),
        ("other", "Other"),
    ]

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True)
    communication_type = models.CharField(max_length=100, choices=COMMUNICATION_TYPES)
    communication_date = models.DateField()
    subject = models.CharField(max_length=255, blank=True)
    summary = models.TextField()
    outcome = models.CharField(max_length=100, choices=OUTCOMES, blank=True)
    next_step = models.CharField(max_length=255, blank=True)
    next_follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.person} - {self.get_communication_type_display()} - {self.communication_date}"