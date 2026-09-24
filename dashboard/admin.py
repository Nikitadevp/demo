from django.contrib import admin
from .models import Ticket
from .models import (
    QCProject, QCSite, ChecklistTemplate, ChecklistTemplateItem,
    ChecklistInstance, ChecklistItemResult, QCIssue, QCAuditLog,
)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_no", "name", "department", "priority", "status", "created_at")
    

# ---- QC Checklist models ----


admin.site.register(QCProject)
admin.site.register(QCSite)
admin.site.register(ChecklistTemplate)
admin.site.register(ChecklistTemplateItem)
admin.site.register(ChecklistInstance)
admin.site.register(ChecklistItemResult)
admin.site.register(QCIssue)
admin.site.register(QCAuditLog)