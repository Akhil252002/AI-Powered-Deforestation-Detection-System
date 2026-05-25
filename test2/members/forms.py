from django import forms
from .models import Region, Town

# Region Form
class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['name', 'region_type']

# Town Form
class TownForm(forms.ModelForm):
    class Meta:
        model = Town
        fields = ['name']