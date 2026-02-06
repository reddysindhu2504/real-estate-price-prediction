from django import forms

class LandForm(forms.Form):
    state = forms.CharField()
    district = forms.CharField()

    land_area = forms.FloatField(label="Land Area (sq.ft)")
    soil_type = forms.CharField()
    road_width = forms.FloatField()
    land_shape = forms.CharField()
