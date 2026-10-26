from django import forms
from .models import TransactionCase
from leads.models import Lead

class TransactionCaseForm(forms.ModelForm):
    class Meta:
        model = TransactionCase
        fields = ["title", "lead", "stage", "inspection_deadline", "financing_deadline", "closing_date", "notes"]
        widgets = {key: forms.DateInput(attrs={"type": "date"}) for key in ("inspection_deadline", "financing_deadline", "closing_date")}
    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lead"].queryset = Lead.objects.filter(workspace=workspace) if workspace else Lead.objects.none()
        self.fields["lead"].required = False
