from django import forms
from .models import LandingPage


class LandingPageForm(forms.ModelForm):
    class Meta:
        model = LandingPage
        fields = ["title", "slug", "template", "headline", "description", "button_text"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
