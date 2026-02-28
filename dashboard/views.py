from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta, time
from .models import Ticket



# 🔹 Office Time Settings
OFFICE_START = time(9, 30)
OFFICE_END = time(18, 30)


# 🔹 TAT Calculation (Office Hours Based)
def calculate_tat_deadline(priority):
    now = timezone.localtime(timezone.now())

    if priority == "Urgent":
        remaining_hours = 6
    else:
        remaining_hours = 24

    current_datetime = now

    while remaining_hours > 0:
        current_time = current_datetime.time()

        if current_time < OFFICE_START:
            current_datetime = current_datetime.replace(
                hour=9, minute=30, second=0, microsecond=0
            )

        elif current_time >= OFFICE_END:
            next_day = current_datetime + timedelta(days=1)
            current_datetime = next_day.replace(
                hour=9, minute=30, second=0, microsecond=0
            )

        else:
            office_end_today = current_datetime.replace(
                hour=18, minute=30, second=0, microsecond=0
            )

            remaining_today_seconds = (
                office_end_today - current_datetime
            ).total_seconds()

            remaining_today_hours = remaining_today_seconds / 3600

            if remaining_today_hours >= remaining_hours:
                current_datetime = current_datetime + timedelta(
                    hours=remaining_hours
                )
                remaining_hours = 0
            else:
                remaining_hours -= remaining_today_hours
                next_day = current_datetime + timedelta(days=1)
                current_datetime = next_day.replace(
                    hour=9, minute=30, second=0, microsecond=0
                )

    return current_datetime


# 🔹 Raise Ticket View
def raise_ticket(request):
    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        department = request.POST.get("department")
        issue_type = request.POST.get("issue_type")
        priority = request.POST.get("priority")

        tat_deadline = calculate_tat_deadline(priority)

        ticket = Ticket.objects.create(
            name=name,
            email=email,
            phone=phone,
            department=department,
            issue_type=issue_type,
            priority=priority,
            tat_deadline=tat_deadline,
        )

        # resolve_url = request.build_absolute_uri(
        #     f"/resolve-ticket/{ticket.ticket_no}/"
        # )

        department_emails = {
            "Accounts and Finance": "alok.agrawal@rajat-group.com",
            "Construction": "bagga.rbpl@rajat-group.com",
            "CRM HO": "crm.rbpl@rajat-group.com",
            "DME": "dme.rbpl@rajat-group.com",
            "Electrical and Plumbing": "saurav.rbpl@gmail.com",
            "Engineering Highpark": "highpark@rajat-group.com",
            "Engineering Sampoorna": "dipesh.chaudhary@rajat-group.com",
            "Finishing Sampoorna": "narendra04081994@gmail.com",
            "HR": "ea.rbpl@rajat-group.com",
            "IT and Admin": "it.rbpl@rajat-group.com",
            "Maintenance Highpark": "mainteam.hp@gmail.com",
            "Maintenance Sampoorna": "mainteam.sh@gmail.com",
            "Project Planning": "planning.rbpl@rajat-group.com",
            "Purchase and Security": "ravi.jain@rajat-group.com",
            "Sales and Marketing": "vinod.mishra@rajat-group.com",
            "CRM Sampoorna": "crm3.rbpl@gmail.com",
            "CRM Highpark": "crm2.rbpl@gmail.com",
            "JNRDME": "jrdme.rbpl@rajat-group.com",
        }

        dept_email = department_emails.get(department)

        subject = f"New Help Desk Ticket - {ticket.ticket_no}"

        message = f"""
Dear Team,

A new Help Desk ticket has been successfully created and assigned to your department.

Ticket ID   : {ticket.ticket_no}
Department  : {department}
Priority    : {priority}
Issue Type  : {issue_type}

Resolution Time: {tat_deadline.strftime('%d-%m-%Y %I:%M %p')}



-- Help Desk System
"""

        if dept_email:
            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [dept_email],
                    fail_silently=True,  # ✅ Prevent 500 error in deploy
                )
            except Exception:
                pass

        return redirect("/raise-ticket/?success=1")

    success = request.GET.get("success")
    return render(request, "forms/ticket_form.html", {"success": success})

#dashboard    

def dashboard(request):

    context = {
        "total": 20,
        "open": 5,
        "closed": 10,
        "urgent": 2,
        "tickets": [
            {
                "no": 1,
                "name": "Printer Issue",
                "department": "IT",
                "priority": "High",
                "status": "Open",
                "date": "2026-02-28"
            }
        ]
    }

    return render(request, "dashboard.html", context)




