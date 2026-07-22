from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from people.models import Person
from properties.models import Property
from leads.models import Lead
from tasks.models import Task
from tags.models import Tag
from communications.models import CommunicationLog


class AddLeadForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        label="First Name",
    )

    last_name = forms.CharField(
        max_length=100,
        required=False,
        label="Last Name",
    )

    email = forms.EmailField(
        required=False,
        label="Email",
    )

    phone = forms.CharField(
        max_length=50,
        required=False,
        label="Phone",
    )

    preferred_contact_method = forms.ChoiceField(
        choices=[("", "---------")] + Person.PREFERRED_CONTACT_METHODS,
        required=False,
        label="Preferred Contact Method",
    )

    email_opt_in = forms.BooleanField(
        required=False,
        initial=True,
        label="Email Opt-In",
    )

    sms_opt_in = forms.BooleanField(
        required=False,
        initial=False,
        label="SMS Opt-In",
    )

    do_not_contact = forms.BooleanField(
        required=False,
        initial=False,
        label="Do Not Contact",
    )

    lead_type = forms.ChoiceField(
        choices=Lead.LEAD_TYPES,
        label="Lead Type",
    )

    source = forms.CharField(
        max_length=100,
        required=False,
        label="Lead Source",
    )

    referred_by = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        required=False,
        label="Referred By",
    )

    status = forms.ChoiceField(
        choices=Lead.LEAD_STATUSES,
        initial="new",
        label="Status",
    )

    related_property = forms.ModelChoiceField(
        queryset=Property.objects.all(),
        required=False,
        label="Related Property",
    )

    last_contact_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Last Contact Date",
    )

    next_follow_up_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Next Follow-Up Date",
    )

    next_step = forms.CharField(
        max_length=255,
        required=False,
        label="Next Step",
    )

    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Tags",
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
        label="Notes",
    )

    create_follow_up_task = forms.BooleanField(
        required=False,
        initial=False,
        label="Create Follow-Up Task",
    )


class LogCommunicationForm(forms.Form):
    communication_type = forms.ChoiceField(
        choices=CommunicationLog.COMMUNICATION_TYPES,
        label="Communication Type",
    )

    communication_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Communication Date",
    )

    subject = forms.CharField(
        max_length=255,
        required=False,
        label="Subject",
    )

    summary = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5}),
        label="Summary",
    )

    outcome = forms.ChoiceField(
        choices=[("", "---------")] + CommunicationLog.OUTCOMES,
        required=False,
        label="Outcome",
    )

    next_step = forms.CharField(
        max_length=255,
        required=False,
        label="Next Step",
    )

    next_follow_up_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Next Follow-Up Date",
    )

    create_follow_up_task = forms.BooleanField(
        required=False,
        initial=False,
        label="Create Follow-Up Task",
    )


class AddTaskForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        label="Task Title",
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
        label="Description",
    )

    related_property = forms.ModelChoiceField(
        queryset=Property.objects.all(),
        required=False,
        label="Related Property",
    )

    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Due Date",
    )

    status = forms.ChoiceField(
        choices=Task.TASK_STATUSES,
        initial="open",
        label="Status",
    )

    priority = forms.ChoiceField(
        choices=Task.PRIORITIES,
        initial="normal",
        label="Priority",
    )

    update_lead_next_step = forms.BooleanField(
        required=False,
        initial=True,
        label="Update Lead Next Step",
    )


class ImportLeadsForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV File",
    )


class CRMUserCreationForm(UserCreationForm):
    ACCESS_LEVELS = [
        ("real_estate_only", "Real Estate Only"),
        ("crm_full_access", "CRM Full Access"),
    ]

    first_name = forms.CharField(
        max_length=150,
        required=False,
        label="First Name",
    )

    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Last Name",
    )

    email = forms.EmailField(
        required=False,
        label="Email",
    )

    access_level = forms.ChoiceField(
        choices=ACCESS_LEVELS,
        initial="real_estate_only",
        label="Access Level",
    )

    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Active User",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "access_level",
            "is_active",
        ]


class CRMUserAccessForm(forms.Form):
    ACCESS_LEVELS = [
        ("real_estate_only", "Real Estate Only"),
        ("crm_full_access", "CRM Full Access"),
    ]

    access_level = forms.ChoiceField(
        choices=ACCESS_LEVELS,
        label="Access Level",
    )

    is_active = forms.BooleanField(
        required=False,
        label="Active User",
    )


class EditLeadForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        label="First Name",
    )

    last_name = forms.CharField(
        max_length=100,
        required=False,
        label="Last Name",
    )

    email = forms.EmailField(
        required=False,
        label="Email",
    )

    phone = forms.CharField(
        max_length=50,
        required=False,
        label="Phone",
    )

    preferred_contact_method = forms.ChoiceField(
        choices=[("", "---------")] + Person.PREFERRED_CONTACT_METHODS,
        required=False,
        label="Preferred Contact Method",
    )

    email_opt_in = forms.BooleanField(
        required=False,
        label="Email Opt-In",
    )

    sms_opt_in = forms.BooleanField(
        required=False,
        label="SMS Opt-In",
    )

    do_not_contact = forms.BooleanField(
        required=False,
        label="Do Not Contact",
    )

    lead_type = forms.ChoiceField(
        choices=Lead.LEAD_TYPES,
        label="Lead Type",
    )

    source = forms.CharField(
        max_length=100,
        required=False,
        label="Lead Source",
    )

    status = forms.ChoiceField(
        choices=Lead.LEAD_STATUSES,
        label="Status",
    )

    related_property = forms.ModelChoiceField(
        queryset=Property.objects.all(),
        required=False,
        label="Related Property",
    )

    last_contact_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Last Contact Date",
    )

    next_follow_up_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Next Follow-Up Date",
    )

    next_step = forms.CharField(
        max_length=255,
        required=False,
        label="Next Step",
    )

    person_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        label="Person Notes",
    )

    lead_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        label="Lead Notes",
    )


class AddContactForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        label="First Name",
    )

    last_name = forms.CharField(
        max_length=100,
        required=False,
        label="Last Name",
    )

    email = forms.EmailField(
        required=False,
        label="Email",
    )

    phone = forms.CharField(
        max_length=50,
        required=False,
        label="Phone",
    )

    person_type = forms.ChoiceField(
        choices=Person.PERSON_TYPES,
        label="Contact Type",
        initial="lead",
    )

    preferred_contact_method = forms.ChoiceField(
        choices=[("", "---------")] + Person.PREFERRED_CONTACT_METHODS,
        required=False,
        label="Preferred Contact Method",
    )

    email_opt_in = forms.BooleanField(
        required=False,
        initial=True,
        label="Email Opt-In",
    )

    sms_opt_in = forms.BooleanField(
        required=False,
        initial=False,
        label="SMS Opt-In",
    )

    do_not_contact = forms.BooleanField(
        required=False,
        initial=False,
        label="Do Not Contact",
    )

    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Tags",
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
        label="Contact Notes",
    )


class EditContactForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        label="First Name",
    )

    last_name = forms.CharField(
        max_length=100,
        required=False,
        label="Last Name",
    )

    email = forms.EmailField(
        required=False,
        label="Email",
    )

    phone = forms.CharField(
        max_length=50,
        required=False,
        label="Phone",
    )

    person_type = forms.ChoiceField(
        choices=Person.PERSON_TYPES,
        label="Contact Type",
    )

    preferred_contact_method = forms.ChoiceField(
        choices=[("", "---------")] + Person.PREFERRED_CONTACT_METHODS,
        required=False,
        label="Preferred Contact Method",
    )

    email_opt_in = forms.BooleanField(
        required=False,
        label="Email Opt-In",
    )

    sms_opt_in = forms.BooleanField(
        required=False,
        label="SMS Opt-In",
    )

    do_not_contact = forms.BooleanField(
        required=False,
        label="Do Not Contact",
    )

    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Tags",
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
        label="Contact Notes",
    )


class AddPropertyForm(forms.Form):
    address = forms.CharField(
        max_length=255,
        label="Street Address",
    )

    city = forms.CharField(
        max_length=100,
        label="City",
    )

    state = forms.CharField(
        max_length=50,
        initial="CT",
        label="State",
    )

    zip_code = forms.CharField(
        max_length=20,
        label="Zip Code",
    )

    property_type = forms.ChoiceField(
        choices=[("", "---------")] + Property.PROPERTY_TYPES,
        required=False,
        label="Property Type",
    )

    bedrooms = forms.IntegerField(
        required=False,
        label="Bedrooms",
    )

    bathrooms = forms.DecimalField(
        required=False,
        max_digits=4,
        decimal_places=1,
        label="Bathrooms",
    )

    square_feet = forms.IntegerField(
        required=False,
        label="Square Feet",
    )

    owner = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        required=False,
        label="Owner / Contact",
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
        label="Property Notes",
    )


class EditPropertyForm(forms.Form):
    address = forms.CharField(
        max_length=255,
        label="Street Address",
    )

    city = forms.CharField(
        max_length=100,
        label="City",
    )

    state = forms.CharField(
        max_length=50,
        label="State",
    )

    zip_code = forms.CharField(
        max_length=20,
        label="Zip Code",
    )

    property_type = forms.ChoiceField(
        choices=[("", "---------")] + Property.PROPERTY_TYPES,
        required=False,
        label="Property Type",
    )

    bedrooms = forms.IntegerField(
        required=False,
        label="Bedrooms",
    )

    bathrooms = forms.DecimalField(
        required=False,
        max_digits=4,
        decimal_places=1,
        label="Bathrooms",
    )

    square_feet = forms.IntegerField(
        required=False,
        label="Square Feet",
    )

    owner = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        required=False,
        label="Owner / Contact",
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
        label="Property Notes",
    )

class GeneralTaskForm(forms.Form):
        title = forms.CharField(max_length=255, label="Task Title")
        description = forms.CharField(
            required=False,
            widget=forms.Textarea(attrs={"rows": 5}),
            label="Description",
        )
        related_person = forms.ModelChoiceField(
            queryset=Person.objects.all(),
            required=False,
            label="Related Contact",
        )
        related_property = forms.ModelChoiceField(
            queryset=Property.objects.all(),
            required=False,
            label="Related Property",
        )
        due_date = forms.DateField(
            required=False,
            widget=forms.DateInput(attrs={"type": "date"}),
            label="Due Date",
        )
        status = forms.ChoiceField(
            choices=Task.TASK_STATUSES,
            initial="open",
            label="Status",
        )
        priority = forms.ChoiceField(
            choices=Task.PRIORITIES,
            initial="normal",
            label="Priority",
        )