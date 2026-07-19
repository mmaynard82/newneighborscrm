from django.db import models


class Person(models.Model):
    PERSON_TYPES = [
        ("lead", "Lead"),
        ("buyer", "Buyer"),
        ("seller", "Seller"),
        ("owner", "Owner"),
        ("tenant", "Tenant"),
        ("vendor", "Vendor"),
        ("agent", "Agent"),
        ("attorney", "Attorney"),
        ("lender", "Lender"),
        ("family_contact", "Family Contact"),
        ("referral_partner", "Referral Partner"),
        ("other", "Other"),
    ]

    PREFERRED_CONTACT_METHODS = [
        ("email", "Email"),
        ("phone", "Phone"),
        ("text", "Text"),
        ("facebook", "Facebook Message"),
        ("other", "Other"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    person_type = models.CharField(
        max_length=50,
        choices=PERSON_TYPES,
        default="lead",
    )

    preferred_contact_method = models.CharField(
        max_length=50,
        choices=PREFERRED_CONTACT_METHODS,
        blank=True,
    )

    email_opt_in = models.BooleanField(default=True)
    sms_opt_in = models.BooleanField(default=False)
    do_not_contact = models.BooleanField(default=False)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else "Unnamed Person"