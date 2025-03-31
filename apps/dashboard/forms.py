# forms.py
from django import forms
from .models import Report, ReportType


class UploadReportForm(forms.Form):
    report = forms.ModelChoiceField(
        queryset=Report.objects.filter(status="OPEN"),
        label="Select Report",
        required=True,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    file = forms.FileField(
        label="Upload Excel File",
        required=True,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )
# forms.py
class ManualReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["name", "type", "date"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional report name"})
    )

    type = forms.ChoiceField(
        choices=ReportType.choices(),
        widget=forms.Select(attrs={"class": "form-select"})
    )