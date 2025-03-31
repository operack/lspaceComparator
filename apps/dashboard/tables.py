import django_tables2 as tables
from .models import Report
from django.urls import reverse
from django.utils.html import format_html


class ReportTable(tables.Table):
    view = tables.Column(empty_values=(), verbose_name="")

    class Meta:
        model = Report
        template_name = "django_tables2/bootstrap5.html"
        fields = ("date", "type", "name", "status", "created", "modified")

    def render_view(self, record):
        url = reverse("dashboard:report-detail", args=[record.pk])
        return format_html('<a class="btn btn-sm btn-outline-primary" href="{}">View</a>', url)