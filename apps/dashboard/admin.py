from django.contrib import admin
from .models import Report, Item


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'type', 'status', 'created', 'modified')
    list_filter = ('type', 'status', 'date')
    search_fields = ('type',)
    ordering = ('-date',)
    readonly_fields = ('created', 'modified', 'status')  # status is now read-only


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('pick_number', 'source', 'report', 'created')
    list_filter = ('source', 'report__type', 'report__date')
    search_fields = ('pick_number',)
    ordering = ('-created',)

    autocomplete_fields = ('report',)