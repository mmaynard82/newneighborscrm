from django.db import models
from people.models import Person


class Tag(models.Model):
    TAG_CATEGORIES = [
        ("buyer", "Buyer"),
        ("seller", "Seller"),
        ("property_management", "Property Management"),
        ("home_management", "Home Management"),
        ("referral", "Referral"),
        ("priority", "Priority"),
        ("marketing", "Marketing"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, choices=TAG_CATEGORIES, default="other")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class PersonTag(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="person_tags")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("person", "tag")

    def __str__(self):
        return f"{self.person} - {self.tag}"