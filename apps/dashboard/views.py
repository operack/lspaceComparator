import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponse
from django.views.generic import TemplateView, DetailView

from .forms import UploadReportForm, ManualReportForm
from .models import Report, Item
from .tables import ReportTable
from .utils import extract_pick_numbers_from_excel  # Assuming function is in utils.py


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def post(self, request, *args, **kwargs):
        if "create_report" in request.POST:
            report_form = ManualReportForm(request.POST)
            if report_form.is_valid():
                try:
                    report = report_form.save(commit=False)
                    report.is_manual = True
                    report.save()
                    messages.success(request, f"Report created: {report}")
                except IntegrityError:
                    messages.error(request, "Only one report is allowed per type and date.")
            else:
                error_details = "; ".join(
                    [f"{field}: {', '.join(errors)}" for field, errors in report_form.errors.items()]
                )
                messages.error(request, f"Could not create report. Errors: {error_details}")

            return self.get(request, *args, report_form=report_form, **kwargs)
        form = UploadReportForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Please correct the errors below.")
            return self.get(request, *args, form=form, **kwargs)

        report = form.cleaned_data['report']
        excel_file = form.cleaned_data['file']

        try:
            result = extract_pick_numbers_from_excel(excel_file)
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return self.get(request, *args, form=form, **kwargs)

        count = 0
        for pick_number in result['pick_numbers']:
            Item.objects.create(
                pick_number=pick_number,
                source=result['source'],
                type=report.type,
                report=report
            )
            count += 1

        messages.success(request, f"Uploaded {count} items to report: {report}")
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get('form') or UploadReportForm()
        context["report_form"] = ManualReportForm()
        return context


class ReportListView(LoginRequiredMixin, TemplateView):
    template_name = "report_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Report.objects.all().order_by("-date")
        table = ReportTable(queryset)
        context["table"] = table
        return context

class ReportDetailView(LoginRequiredMixin, DetailView):
    model = Report
    template_name = "report_detail.html"
    context_object_name = "report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.object
        items = report.items.all()

        fc_items = items.filter(source="FULL_CIRCLE")
        wms_items = items.filter(source="WMS")

        fc_pick_numbers = set(fc_items.values_list("pick_number", flat=True))
        wms_pick_numbers = set(wms_items.values_list("pick_number", flat=True))

        if report.type == "OPEN":
            # Base: FULL_CIRCLE — check what’s missing from WMS
            missing_items = fc_items.filter(pick_number__in=fc_pick_numbers - wms_pick_numbers)
            missing_source_label = "WMS"
        elif report.type == "SHIPPED":
            # Base: WMS — check what’s missing from FULL_CIRCLE
            missing_items = wms_items.filter(pick_number__in=wms_pick_numbers - fc_pick_numbers)
            missing_source_label = "Full Circle"
        else:
            missing_items = []
            missing_source_label = "Other"

        context["items"] = items
        context["missing_items"] = missing_items
        context["missing_source_label"] = missing_source_label
        return context


def download_missing_csv(request, pk):
    report = Report.objects.get(pk=pk)
    items = report.items.all()

    # logic must match your context
    fc = set(items.filter(source="FULL_CIRCLE").values_list("pick_number", flat=True))
    wms = set(items.filter(source="WMS").values_list("pick_number", flat=True))

    if report.type == "OPEN":
        base = fc
        compare = wms
    else:
        base = wms
        compare = fc

    missing_picks = base - compare
    missing_items = items.filter(pick_number__in=missing_picks)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="missing_{report.pk}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Pick Number", "Source", "Created"])
    for item in missing_items:
        writer.writerow([item.pick_number, item.source, item.created])
    return response


def download_source_csv(request, pk, source):
    report = Report.objects.get(pk=pk)
    items = report.items.filter(source=source.upper())

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{source.lower()}_{report.pk}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Pick Number", "Source", "Created"])
    for item in items:
        writer.writerow([item.pick_number, item.source, item.created])
    return response