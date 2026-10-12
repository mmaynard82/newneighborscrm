from django import forms
from .models import LandingPage


class LandingPageForm(forms.ModelForm):
    class Meta:
        model = LandingPage
        fields = ["title", "slug", "template", "headline", "description", "button_text"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class LandingInquiryForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=50, required=False)
    message = forms.CharField(max_length=2000, required=False, widget=forms.Textarea)
