# listings/forms.py
import os
import json
from django import forms
from django.conf import settings

def load_state_districts():
    """Load JSON mapping of states -> districts (list)."""
    path = os.path.join(settings.BASE_DIR, "listings", "static", "listings", "data", "india_states_districts.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        print("State/District JSON missing:", path)
        return {}
    except Exception as e:
        print("Error loading state JSON:", e)
        return {}

class PropertyForm(forms.Form):
    state = forms.ChoiceField(choices=[("", "Select State")], required=True,
                              widget=forms.Select(attrs={"class": "form-control", "id": "id_state"}))
    district = forms.ChoiceField(choices=[("", "Select District")], required=True,
                                 widget=forms.Select(attrs={"class": "form-control", "id": "id_district"}))

    city = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "City (optional)"}))
    locality = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Locality / Area"}))

    size_sqft = forms.FloatField(widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 1200"}))
    bedrooms = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    bathrooms = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    age = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))

    amenities_score = forms.FloatField(required=False, initial=5.0, widget=forms.NumberInput(attrs={"class": "form-control"}))
    monthly_income = forms.FloatField(required=False, widget=forms.NumberInput(attrs={"class": "form-control"}))
    country = forms.CharField(widget=forms.HiddenInput(), initial="India")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sd = load_state_districts()
        state_choices = [("", "Select State")]
        for s in sd.keys():
            state_choices.append((s, s))
        self.fields["state"].choices = state_choices

        posted_state = None
        data = kwargs.get("data") or (args[0] if args else None)
        try:
            if data and hasattr(data, "get"):
                posted_state = data.get("state")
        except:
            posted_state = None

        district_choices = [("", "Select District")]
        if posted_state and posted_state in sd:
            for d in sd[posted_state]:
                district_choices.append((d, d))
        self.fields["district"].choices = district_choices


