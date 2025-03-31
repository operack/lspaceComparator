import enum
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition
from django_extensions.db.models import TimeStampedModel


class ReportType(enum.Enum):
    OPEN_ORDERS = 'OPEN'
    SHIPPED_ORDERS = 'SHIPPED'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.replace('_', ' ').title()) for tag in cls]


class ReportStatus(enum.Enum):
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.title()) for tag in cls]


class Report(TimeStampedModel):
    name = models.CharField(max_length=255, blank=True)
    type = models.CharField(max_length=10, choices=ReportType.choices())
    date = models.DateField()
    status = FSMField(default=ReportStatus.OPEN.value, choices=ReportStatus.choices(), protected=True)
    is_manual = models.BooleanField(default=False)  # ✅ NEW FIELD

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['type', 'date'],
                name='unique_type_date_for_automated',
                condition=models.Q(is_manual=False)  # Only applies to automated reports
            )
        ]
        ordering = ['-date']

    def __str__(self):
        return f"[{self.type}] {self.name} ({self.date})"

    @transition(field=status, source=ReportStatus.OPEN.value, target=ReportStatus.CLOSED.value)
    def close(self):
        """
        Mark the report as closed — to be triggered when both required files are received.
        """
        pass

    def get_main_comparison_report(self):
        """
        Finds the opposite-source report of the same type and date.
        e.g., If this is OPEN from WMS, compare to OPEN from Full Circle.
        """
        current_source = self.infer_source()
        if not current_source:
            return None

        opposite_source = {
            "WMS": "FULL_CIRCLE",
            "FULL_CIRCLE": "WMS"
        }.get(current_source)

        if not opposite_source:
            return None

        return Report.objects.filter(
            type=self.type,
            date=self.date,
            items__source=opposite_source
        ).exclude(id=self.id).distinct().first()

    def infer_source(self):
        """
        Tries to infer the source of the report by checking the source of its items.
        Assumes all items come from the same source.
        """
        return self.items.values_list("source", flat=True).first()


class ItemSource(enum.Enum):
    FULL_CIRCLE = 'FULL_CIRCLE'
    WMS = 'WMS'

    @classmethod
    def choices(cls):
        return [(tag.value, tag.name.replace('_', ' ').title()) for tag in cls]


class Item(models.Model):
    pick_number = models.CharField(max_length=100)
    source = models.CharField(max_length=20, choices=ItemSource.choices())
    type = models.CharField(max_length=10, choices=ReportType.choices())
    report = models.ForeignKey(Report, related_name='items', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.pick_number} ({self.source})"
