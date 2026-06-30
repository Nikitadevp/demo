from django.contrib import admin
from .models import Ticket, MasterDashboard

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_no", "name", "department", "priority", "status", "created_at")
    

@admin.register(MasterDashboard)
class MasterDashboardAdmin(admin.ModelAdmin):

    list_display = (
        "ticket_id",
        "customer_name",
        "current_stage",
        "current_status",
        "priority",
        "created_at"
    )

    list_filter = (
        "current_stage",
        "current_status",
        "priority"
    )

    search_fields = (
        "ticket_id",
        "customer_name",
        "contact"
    )
    