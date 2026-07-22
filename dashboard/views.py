from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta, time

from dashboard.email_config import EMAILS
from .models import EstimateForm, QueryCloser, Ticket
from django.urls import reverse
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
import base64
from .models import LeaveRequest
from django.http import HttpResponse
import re
from django.http import HttpResponseForbidden
from django.db.models import Case, When, Value, IntegerField, Q
from datetime import datetime
from django.core.paginator import Paginator
from .models import CustomerQuery, MaintenanceScope
import csv
from .models import SiteInspection
from .models import  EstimateForm
from .models import CustomerApproval
from .models import AdvanceCollection
from .models import MaterialAvailability
from .models import RaiseIndent
from .models import IssueMaterial
from .models import ReceiveMaterial
from .models import QueryCloser
from .models import CustomerFeedback

from django.contrib import messages
from .models import AdminUser


from django.contrib.auth.decorators import login_required

from django.db.models import Count, Q







# Office Time
OFFICE_START = time(9, 30)
OFFICE_END = time(18, 30)


def calculate_tat_deadline(priority):
    now = timezone.localtime(timezone.now())

    # URGENT = 6 office hours only
    if priority == "Urgent":
        remaining_hours = 6
        current_datetime = now

        while remaining_hours > 0:
            current_time = current_datetime.time()

            # before office time
            if current_time < OFFICE_START:
                current_datetime = current_datetime.replace(
                    hour=9,
                    minute=30,
                    second=0,
                    microsecond=0
                )
                continue

            # after office close → next day start
            if current_time >= OFFICE_END:
                next_day = current_datetime + timedelta(days=1)
                current_datetime = next_day.replace(
                    hour=9,
                    minute=30,
                    second=0,
                    microsecond=0
                )
                continue

            # today's office available time
            office_end_today = current_datetime.replace(
                hour=18,
                minute=30,
                second=0,
                microsecond=0
            )

            available_today = (
                office_end_today - current_datetime
            ).total_seconds() / 3600

            if available_today >= remaining_hours:
                current_datetime += timedelta(hours=remaining_hours)
                remaining_hours = 0
            else:
                remaining_hours -= available_today
                next_day = current_datetime + timedelta(days=1)

                current_datetime = next_day.replace(
                    hour=9,
                    minute=30,
                    second=0,
                    microsecond=0
                )

        return timezone.localtime(current_datetime)

    # 📌 NORMAL = simple 24 real hours
    else:
        return timezone.localtime(now + timedelta(hours=24))

#raise_ticket
  
def raise_ticket(request):

    print("VIEW HIT")

    if request.method == "POST":

        print("POST REQUEST RECEIVED")
        print(request.POST)


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

        print("TICKET CREATED:", ticket.ticket_no)

        resolve_url = request.build_absolute_uri(
            reverse("resolve_ticket", args=[ticket.ticket_no])
        )

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

To resolve this ticket, please click the link below:
{resolve_url}

We kindly request you to review the above ticket and proceed with the required action at the earliest possible.
"""

        if dept_email:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [dept_email],
                fail_silently=True
            )

        return redirect(f"{reverse('raise_ticket')}?success=1")

    success = request.GET.get("success") == "1"
    return render(request, "ticket_form.html", {"success": success})


#resolve_ticket    

def resolve_ticket(request, ticket_no):

    ticket = get_object_or_404(Ticket, ticket_no=ticket_no)

    # If ticket already closed
    if ticket.status == "Closed":
        return render(request, "resolve_ticket.html", {
            "ticket": ticket,
            "success": request.GET.get("success")
        })

    if request.method == "POST":

        problem_solver = request.POST.get("problem_solver")
        solution_provided = request.POST.get("solution_provided")

        if problem_solver and solution_provided:

            ticket.status = "Closed"
            ticket.problem_solver = problem_solver
            ticket.solution_provided = solution_provided
            ticket.resolved_at = timezone.now()
            ticket.save()

            subject = f"Your Help Desk Ticket {ticket.ticket_no} Has Been Resolved"

            message = f"""
Dear {ticket.name},

We are pleased to inform you that your Help Desk ticket has been successfully resolved.

---------------------------------------
Ticket Details
---------------------------------------
Ticket ID     : {ticket.ticket_no}
Department    : {ticket.department}
Issue Type    : {ticket.issue_type}
Priority      : {ticket.priority}

Resolved On   : {timezone.localtime(ticket.resolved_at).strftime('%d-%m-%Y %I:%M %p')}

---------------------------------------

Solution Provided by:
{ticket.solution_provided}



If you have any further issues, please feel free to raise a new ticket.

Regards,
Help Desk Team
"""

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [ticket.email],
                fail_silently=False,
            )

            return redirect(f"/resolve-ticket/{ticket.ticket_no}/?success=1")

    return render(request, "resolve_ticket.html", {
        "ticket": ticket,
        "success": request.GET.get("success")
    })


DEPARTMENTS = [
    "Accounts and Finance",
    "Construction",
    "CRM HO",
    "DME",
    "Electrical and Plumbing",
    "Engineering Highpark",
    "Engineering Sampoorna",
    "Finishing Sampoorna",
    "HR",
    "IT and Admin",
    "Maintenance Highpark",
    "Maintenance Sampoorna",
    "Project Planning",
    "Purchase and Security",
    "Sales and Marketing",
    "CRM Sampoorna",
    "CRM Highpark",
    "JNRDME",
]    

    

#dashboard    

def dashboard(request):

    department = request.GET.get('department', '')
    priority = request.GET.get('priority', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')

    tickets = Ticket.objects.all()

    # -------- SEARCH --------
    if search:
        tickets = tickets.filter(
            Q(ticket_no__icontains=search) |
            Q(name__icontains=search) |
            Q(issue_type__icontains=search) |
            Q(department__icontains=search)
        )

    # -------- FILTERS --------
    if department:
        tickets = tickets.filter(department=department)   # ✅ FIXED

    if priority:
        tickets = tickets.filter(priority=priority)

    if status:
        tickets = tickets.filter(status=status)

    # -------- COUNTS --------
    open_count = tickets.filter(status="Open").count()
    closed_count = tickets.filter(status="Closed").count()
    urgent_count = tickets.filter(priority="Urgent").count()
    normal_count = tickets.filter(priority="Normal").count()

    # -------- SORT (OPEN FIRST, THEN CLOSED) --------
    tickets = tickets.annotate(
        status_order=Case(
            When(status="Open", then=Value(0)),
            When(status="Closed", then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by('status_order', '-created_at')

    # -------- PAGINATION (20 PER PAGE) --------
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # -------- STATUS CHART --------
    buffer = io.BytesIO()
    plt.figure(figsize=(4,3))
    plt.bar(["Open", "Closed"], [open_count, closed_count], color=["#60a5fa", "#fbbf24"])
    plt.title("Status")
    plt.tight_layout()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    status_chart = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    # -------- PRIORITY CHART --------
    buffer2 = io.BytesIO()
    plt.figure(figsize=(4,3))
    plt.bar(["Urgent", "Normal"], [urgent_count, normal_count], color=["#60a5fa", "#fbbf24"])
    plt.title("Priority")
    plt.tight_layout()
    plt.savefig(buffer2, format="png")
    buffer2.seek(0)
    priority_chart = base64.b64encode(buffer2.getvalue()).decode()
    plt.close()

    # -------- CONTEXT --------
    context = {
        'departments': DEPARTMENTS,
        'department': department,
        'priority': priority,
        'status': status,
        'search': search,

        'total_tickets': tickets.count(),
        'open_tickets': open_count,
        'closed_tickets': closed_count,
        'urgent_tickets': urgent_count,

        'page_obj': page_obj,

        'status_chart': status_chart,
        'priority_chart': priority_chart,
    }

    return render(request, "dashboard.html", context)


#This for leave application     

    
#  DEPARTMENT EMAILS
department_details = {
    "Accounts and Finance": {
        "email": "alok.agrawal@rajat-group.com",
        "phone": "8889799199"

    },
    "HR and Admin": {
        "email": "ea.rbpl@rajat-group.com",
        "phone": "8889102393"
    },
    "Engineering": {
        "email": "bagga.rbpl@rajat-group.com",
        "phone": "6262240006"
    },
    "MDO": {
        "email": "mrinal.golechha1@rajat-group.com",
        "phone": "9009923000"
    },
    "Sales": {
        "email": "vinod.mishra@rajat-group.com",
        "phone": "9644290004"
    },
    "Purchase": {
        "email": "ravi.jain@rajat-group.com",
        "phone": "9669425500"
    },
    "DME": {
        "email": "dme.rbpl@rajat-group.com",
        "phone": "8827740281"
    },
    "Jrdme": {
        "email": "jrdme.rbpl@rajat-group.com",
        "phone": "7974500140"
    },
    "MDO Sales": {
        "email": "prakhar.golechha@rajat-group.com",
        "phone": "9926193300"
    }
}
# LEAVE FORM
# LEAVE FORM
def leave_form(request):

    if request.method == "POST":

        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            department = request.POST.get('department').strip()
            leave_type = request.POST.get('leave_type')
            start = request.POST.get('start_date')
            end = request.POST.get('end_date')
            reason = request.POST.get('reason')

            # EMAIL FORMAT CHECK
            pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(pattern, email):
                return HttpResponse("Please enter valid email like example@gmail.com")

            # ✅ DATE FIX FOR POSTGRESQL
            try:
                start_date = datetime.strptime(start, "%Y-%m-%d").date()
                end_date = datetime.strptime(end, "%Y-%m-%d").date()
            except:
                start_date = datetime.strptime(start, "%d-%m-%Y").date()
                end_date = datetime.strptime(end, "%d-%m-%Y").date()

            # GET DEPARTMENT EMAIL + PHONE
            dept_data = department_details.get(department, {})
            manager_email = dept_data.get("email")
            manager_phone = dept_data.get("phone")

            if not manager_email:
                return HttpResponse(f"Department email not found: {department}")

            # SAVE DATA
            leave = LeaveRequest.objects.create(
                name=name,
                email=email,
                phone=phone,
                department=department,
                department_email=manager_email,
                department_phone=manager_phone,
                leave_type=leave_type,
                start_date=start_date,   # ✅ FIXED
                end_date=end_date,       # ✅ FIXED
                reason=reason
            )

            # DOMAIN
            domain = request.build_absolute_uri('/')[:-1]
            review_link = f"{domain}/review/{leave.leave_id}/"

            # MESSAGE
            message = f"""
New Leave Request

Leave ID: {leave.leave_id}
Employee: {name}
Email: {email}
Department: {department}
Department Phone: {manager_phone}
Leave Type: {leave_type}
From: {start}
To: {end}

Reason:
{reason}

Review Request:
{review_link}
"""

            # SEND TO DEPARTMENT
            send_mail(
                f"Leave Request Approval | ID: {leave.leave_id}",
                message,
                settings.EMAIL_HOST_USER,
                [manager_email],
                fail_silently=False
            )

            # SEND TO EMPLOYEE
            send_mail(
                f"Leave Request Submitted | ID: {leave.leave_id}",
                f"Your leave request has been sent for approval.\n\nLeave ID: {leave.leave_id}",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False
            )

            return render(request, "leave_form.html", {"success": True})

        except Exception as e:
            return HttpResponse(f"ERROR: {str(e)}")

    return render(request, "leave_form.html")
# # APPROVE
# def approve(request, id):

#     leave = LeaveRequest.objects.get(id=id)
#     leave.status = "Approved"
#     leave.save()

#     #  MAIL TO EMPLOYEE
#     send_mail(
#         "Leave Approved",
#         f"Your leave has been approved.\n\nFrom {leave.start_date} to {leave.end_date}",
#         settings.EMAIL_HOST_USER,
#         [leave.email],
#         fail_silently=False
#     )

#     return HttpResponse(" Leave Approved & Mail Sent")


# #  REJECT
# def reject(request, id):

#     leave = LeaveRequest.objects.get(id=id)
#     leave.status = "Rejected"
#     leave.save()

#     #  MAIL TO EMPLOYEE
#     send_mail(
#         "Leave Rejected",
#         "Your leave request has been rejected.",
#         settings.EMAIL_HOST_USER,
#         [leave.email],
#         fail_silently=False
#     )

#     return HttpResponse(" Leave Rejected & Mail Sent")



# review_leave
def review_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, leave_id=leave_id)

    if leave.status != "Pending":
        return HttpResponse("""
        <div style="display:flex; justify-content:center; align-items:center; height:100vh;">
            <h2 style="font-size:28px; text-align:center;">
                This request is already processed.
            </h2>
        </div>
        """)

    if request.method == "POST":
        action = request.POST.get("action")

        # APPROVE
        if action == "approve":
            leave.status = "Approved"
            leave.approved_rejected_date = timezone.now()
            leave.resolved_date = timezone.now()
            leave.save()

            send_mail(
                f"Leave Approved ✅ | ID: {leave.leave_id}",
                f"""Your leave has been approved.
From: {leave.start_date}
To: {leave.end_date}
Leave ID: {leave.leave_id}
""",
                settings.EMAIL_HOST_USER,
                [leave.email],
                fail_silently=True
            )

        # REJECT
        elif action == "reject":
            reason = request.POST.get("reject_reason")

            if not reason:
                return HttpResponse("Reject reason required")

            leave.status = "Rejected"
            leave.manager_reason = reason
            leave.approved_rejected_date = timezone.now()
            leave.resolved_date = timezone.now()
            leave.save()

            send_mail(
                f"Leave Rejected ❌ | ID: {leave.leave_id}",
                f"""Your leave has been rejected.
Reason: {reason}
Leave ID: {leave.leave_id}
""",
                settings.EMAIL_HOST_USER,
                [leave.email],
                fail_silently=True
            )

        return HttpResponse("""
        <h1 style="text-align:center; margin-top:100px; font-size:32px;">
            Action completed successfully
        </h1>
        """)

    return render(request, "review_leave.html", {"leave": leave})








#export_leave_csv


def export_leave_csv(request):
    rows = LeaveRequest.objects.all().values_list(
        "leave_id",
        "name",
        "email",
        "phone",
        "department",
        "leave_type",
        "start_date",
        "end_date",
        "reason",
        "status",
        "manager_reason"
    )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'inline; filename="leave_data.csv"'

    # Header row
    response.write(
        "Leave ID,Name,Email,Phone,Department,Leave Type,Start Date,End Date,Reason,Status,Manager Reason\n"
    )

    for row in rows:
        response.write(",".join(map(str, row)) + "\n")

    return response  




def jrdme_dashboard(request):
    tickets = Ticket.objects.filter(department__iexact="JNRDME")

    priority = request.GET.get("priority")
    status = request.GET.get("status")

    if priority:
        tickets = tickets.filter(priority=priority)

    if status:
        tickets = tickets.filter(status=status)

    context = {
        "recent_tickets": tickets.order_by("-created_at")[:20],
        "total_tickets": tickets.count(),
        "open_tickets": tickets.filter(status="Open").count(),
        "closed_tickets": tickets.filter(status="Closed").count(),
        "urgent_tickets": tickets.filter(priority="Urgent").count(),
        "priority": priority,
        "status": status,
    }

    return render(request, "jrdme_dashboard.html", context)


#dme_dashboard


def dme_dashboard(request):
    secret_key = request.GET.get("xid")

    #  Security
    if secret_key != "7_-BdJw3d9L432IN8tjgGNl3gdVpBwp8dOmpwOFIU":
        return HttpResponseForbidden("Access Denied")

    #  Base queryset
    tickets = Ticket.objects.filter(department="DME")

    #  Filters
    priority = request.GET.get("priority", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")
    search = request.GET.get("search", "")

    #  Search filter
    if search:
        tickets = tickets.filter(
            Q(ticket_no__icontains=search) |
            Q(name__icontains=search) |
            Q(issue_type__icontains=search)
        )

    #  Priority filter
    if priority:
        tickets = tickets.filter(priority=priority)

    #  Status filter
    if status:
        tickets = tickets.filter(status=status)

    #  Date filters
    if from_date:
        tickets = tickets.filter(created_at__date__gte=from_date)

    if to_date:
        tickets = tickets.filter(created_at__date__lte=to_date)

    #  Open tickets first
    recent_tickets = tickets.annotate(
        status_order=Case(
            When(status="Open", then=Value(0)),
            When(status="Closed", then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by("status_order", "-created_at")

    #  Context
    context = {
        "recent_tickets": recent_tickets,
        "total_tickets": tickets.count(),
        "open_tickets": tickets.filter(status="Open").count(),
        "closed_tickets": tickets.filter(status="Closed").count(),
        "urgent_tickets": tickets.filter(priority="Urgent").count(),
        "priority": priority,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
        "search": search,
    }

    return render(request, "dme_dashboard.html", context)




#accounts_dashboard

def accounts_dashboard(request):
    secret_key = request.GET.get("xid")

    #  Security
    if secret_key != "AC_92ksLxPq7ZtF3HjW8mR4vB1uN5yQ":
        return HttpResponseForbidden("Access Denied")

    # Base queryset
    tickets = Ticket.objects.filter(department="Accounts and Finance")

    # Filters
    priority = request.GET.get("priority", "")
    status = request.GET.get("status", "")
    search = request.GET.get("search", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    # Search
    if search:
        tickets = tickets.filter(
            Q(ticket_no__icontains=search) |
            Q(name__icontains=search) |
            Q(issue_type__icontains=search)
        )

    # Filters
    if priority:
        tickets = tickets.filter(priority=priority)

    if status:
        tickets = tickets.filter(status=status)

    if from_date:
        tickets = tickets.filter(created_at__date__gte=from_date)

    if to_date:
        tickets = tickets.filter(created_at__date__lte=to_date)

    # Open first
    recent_tickets = tickets.annotate(
        status_order=Case(
            When(status="Open", then=Value(0)),
            When(status="Closed", then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by("status_order", "-created_at")

    context = {
        "recent_tickets": recent_tickets,
        "total_tickets": tickets.count(),
        "open_tickets": tickets.filter(status="Open").count(),
        "closed_tickets": tickets.filter(status="Closed").count(),
        "urgent_tickets": tickets.filter(priority="Urgent").count(),
        "priority": priority,
        "status": status,
        "search": search,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "accounts_dashboard.html", context)



def construction_dashboard(request):
    secret_key = request.GET.get("xid")

    #  Security Key
    if secret_key != "CN_83KdlPq9XzT5LmR2Wv7N4bH1yQ":
        return HttpResponseForbidden("Access Denied")

    tickets = Ticket.objects.filter(department="Construction")

    # Filters
    priority = request.GET.get("priority", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")
    search = request.GET.get("search", "")

    # 🔍 Search
    if search:
        tickets = tickets.filter(
            Q(ticket_no__icontains=search) |
            Q(name__icontains=search) |
            Q(issue_type__icontains=search)
        )

    # Filters
    if priority:
        tickets = tickets.filter(priority=priority)

    if status:
        tickets = tickets.filter(status=status)

    if from_date:
        tickets = tickets.filter(created_at__date__gte=from_date)

    if to_date:
        tickets = tickets.filter(created_at__date__lte=to_date)

    # Open first
    recent_tickets = tickets.annotate(
        status_order=Case(
            When(status="Open", then=Value(0)),
            When(status="Closed", then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by("status_order", "-created_at")

    context = {
        "recent_tickets": recent_tickets,
        "total_tickets": tickets.count(),
        "open_tickets": tickets.filter(status="Open").count(),
        "closed_tickets": tickets.filter(status="Closed").count(),
        "urgent_tickets": tickets.filter(priority="Urgent").count(),
        "priority": priority,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
        "search": search,
    }

    return render(request, "construction_dashboard.html", context)



#crm_ho_dashboard

def crm_ho_dashboard(request):
    secret_key = request.GET.get("xid")

    # Security Key
    if secret_key != "CRM_91XkLpQ4ZtR7Wm2Hc8Bn5VYd3":
        return HttpResponseForbidden("Access Denied")

    tickets = Ticket.objects.filter(department="CRM HO")

    # Filters
    priority = request.GET.get("priority", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")
    search = request.GET.get("search", "")

    # 🔍 Search
    if search:
        tickets = tickets.filter(
            Q(ticket_no__icontains=search) |
            Q(name__icontains=search) |
            Q(issue_type__icontains=search)
        )

    # Filters
    if priority:
        tickets = tickets.filter(priority=priority)

    if status:
        tickets = tickets.filter(status=status)

    if from_date:
        tickets = tickets.filter(created_at__date__gte=from_date)

    if to_date:
        tickets = tickets.filter(created_at__date__lte=to_date)

    # Open first
    recent_tickets = tickets.annotate(
        status_order=Case(
            When(status="Open", then=Value(0)),
            When(status="Closed", then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by("status_order", "-created_at")

    context = {
        "recent_tickets": recent_tickets,
        "total_tickets": tickets.count(),
        "open_tickets": tickets.filter(status="Open").count(),
        "closed_tickets": tickets.filter(status="Closed").count(),
        "urgent_tickets": tickets.filter(priority="Urgent").count(),
        "priority": priority,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
        "search": search,
    }

    return render(request, "crm_ho_dashboard.html", context)




def hr_dashboard(request):
    secret_key = request.GET.get("xid")

    #  Security Key
    if secret_key != "HR_64LpQzT9XcW2mR8Bn5VyD3H7K":
        return HttpResponseForbidden("Access Denied")

    tickets = Ticket.objects.filter(department="HR")

    # Filters
    priority = request.GET.get("priority", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")
    search = request.GET.get("search", "")

    # 🔍 Search
    if search:
        tickets = tickets.filter(
            Q(ticket_no__icontains=search) |
            Q(name__icontains=search) |
            Q(issue_type__icontains=search)
        )

    # Filters
    if priority:
        tickets = tickets.filter(priority=priority)

    if status:
        tickets = tickets.filter(status=status)

    if from_date:
        tickets = tickets.filter(created_at__date__gte=from_date)

    if to_date:
        tickets = tickets.filter(created_at__date__lte=to_date)

    # Open first
    recent_tickets = tickets.annotate(
        status_order=Case(
            When(status="Open", then=Value(0)),
            When(status="Closed", then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by("status_order", "-created_at")

    context = {
        "recent_tickets": recent_tickets,
        "total_tickets": tickets.count(),
        "open_tickets": tickets.filter(status="Open").count(),
        "closed_tickets": tickets.filter(status="Closed").count(),
        "urgent_tickets": tickets.filter(priority="Urgent").count(),
        "priority": priority,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
        "search": search,
    }

    return render(request, "hr_dashboard.html", context)




def it_admin_dashboard(request):
    secret_key = request.GET.get("xid")

    # Security Key
    if secret_key != "IT_7LmQpR2XcV9zH4Bn8W5K3DyT":
        return HttpResponseForbidden("Access Denied")

    tickets = Ticket.objects.filter(department="IT and Admin")

    # Filters
    priority = request.GET.get("priority", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")
    search = request.GET.get("search", "")

    # 🔍 Search
    if search:
        tickets = tickets.filter(
            Q(ticket_no__icontains=search) |
            Q(name__icontains=search) |
            Q(issue_type__icontains=search)
        )

    # Filters
    if priority:
        tickets = tickets.filter(priority=priority)

    if status:
        tickets = tickets.filter(status=status)

    if from_date:
        tickets = tickets.filter(created_at__date__gte=from_date)

    if to_date:
        tickets = tickets.filter(created_at__date__lte=to_date)

    # Open first
    recent_tickets = tickets.annotate(
        status_order=Case(
            When(status="Open", then=Value(0)),
            When(status="Closed", then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by("status_order", "-created_at")

    context = {
        "recent_tickets": recent_tickets,
        "total_tickets": tickets.count(),
        "open_tickets": tickets.filter(status="Open").count(),
        "closed_tickets": tickets.filter(status="Closed").count(),
        "urgent_tickets": tickets.filter(priority="Urgent").count(),
        "priority": priority,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
        "search": search,
    }

    return render(request, "it_admin_dashboard.html", context)



def project_planning_dashboard(request):
    secret_key = request.GET.get("xid")

    if secret_key != "PP_92ksLxPq7ZtF3HjW8mR4vB1uN5yQ":
        return HttpResponseForbidden("Access Denied")

    tickets = Ticket.objects.filter(department="Project Planning")

    priority = request.GET.get("priority", "")
    status = request.GET.get("status", "")
    search = request.GET.get("search", "")

    if search:
        tickets = tickets.filter(
            Q(ticket_no__icontains=search) |
            Q(name__icontains=search) |
            Q(issue_type__icontains=search)
        )

    if priority:
        tickets = tickets.filter(priority=priority)

    if status:
        tickets = tickets.filter(status=status)

    recent_tickets = tickets.annotate(
        status_order=Case(
            When(status="Open", then=Value(0)),
            When(status="Closed", then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by("status_order", "-created_at")

    context = {
        "recent_tickets": recent_tickets,
        "total_tickets": tickets.count(),
        "open_tickets": tickets.filter(status="Open").count(),
        "closed_tickets": tickets.filter(status="Closed").count(),
        "urgent_tickets": tickets.filter(priority="Urgent").count(),
        "priority": priority,
        "status": status,
        "search": search,
    }

    return render(request, "project_planning_dashboard.html", context)





def purchase_security_dashboard(request):
    secret_key = request.GET.get("xid")

    if secret_key != "PS_92ksLxPq7ZtF3HjW8mR4vB1uN5yQ":
        return HttpResponseForbidden("Access Denied")

    tickets = Ticket.objects.filter(department="Purchase & Security")

    priority = request.GET.get("priority", "")
    status = request.GET.get("status", "")
    search = request.GET.get("search", "")

    if search:
        tickets = tickets.filter(
            Q(ticket_no__icontains=search) |
            Q(name__icontains=search) |
            Q(issue_type__icontains=search)
        )

    if priority:
        tickets = tickets.filter(priority=priority)

    if status:
        tickets = tickets.filter(status=status)

    recent_tickets = tickets.annotate(
        status_order=Case(
            When(status="Open", then=Value(0)),
            When(status="Closed", then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by("status_order", "-created_at")

    context = {
        "recent_tickets": recent_tickets,
        "total_tickets": tickets.count(),
        "open_tickets": tickets.filter(status="Open").count(),
        "closed_tickets": tickets.filter(status="Closed").count(),
        "urgent_tickets": tickets.filter(priority="Urgent").count(),
        "priority": priority,
        "status": status,
        "search": search,
    }

    return render(request, "purchase_security_dashboard.html", context)




#leave_admin_dashboard
# LEAVE KA HAI YAHA SE 


def leave_admin_dashboard(request):
    leave_requests = LeaveRequest.objects.all()

    status = request.GET.get("status", "")
    search = request.GET.get("search", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")
    department = request.GET.get("department", "")

    # SEARCH
    if search:
        leave_requests = leave_requests.filter(
            Q(leave_id__icontains=search) |
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(department__icontains=search)
        )

    # FILTERS
    if status:
        leave_requests = leave_requests.filter(status=status)

    if department:
        leave_requests = leave_requests.filter(department=department)

    if from_date:
        leave_requests = leave_requests.filter(request_date__date__gte=from_date)

    if to_date:
        leave_requests = leave_requests.filter(request_date__date__lte=to_date)

    # ✅ Pending first
    leave_requests = leave_requests.annotate(
        order_status=Case(
            When(status="Pending", then=0),
            When(status="Approved", then=1),
            When(status="Rejected", then=2),
            default=3,
            output_field=IntegerField(),
        )
    ).order_by("order_status", "-request_date")

    context = {
        "leave_requests": leave_requests,
        "total_requests": leave_requests.count(),
        "pending_requests": leave_requests.filter(status="Pending").count(),
        "approved_requests": leave_requests.filter(status="Approved").count(),
        "rejected_requests": leave_requests.filter(status="Rejected").count(),

        "status": status,
        "search": search,
        "from_date": from_date,
        "to_date": to_date,
        "department": department,
    }

    return render(request, "leave_admin_dashboard.html", context)


#finance_leave_dashboard

def finance_leave_dashboard(request):
    secret_key = request.GET.get("key")

    if secret_key != "leave123":
        return HttpResponseForbidden("Access Denied")

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    #  Accounts & Finance + Pending first
    leave_requests = LeaveRequest.objects.filter(
        department__iexact="Accounts and Finance"
    ).annotate(
        status_order=Case(
            When(status="Pending", then=Value(1)),
            When(status="Approved", then=Value(2)),
            When(status="Rejected", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    )

    # search
    if search:
        leave_requests = leave_requests.filter(
            Q(leave_id__icontains=search) |
            Q(name__icontains=search)
        )

    # status
    if status:
        leave_requests = leave_requests.filter(status=status)

    # date filters
    if from_date:
        leave_requests = leave_requests.filter(
            request_date__date__gte=from_date
        )

    if to_date:
        leave_requests = leave_requests.filter(
            request_date__date__lte=to_date
        )

    #  Pending first + latest first
    leave_requests = leave_requests.order_by("status_order", "-request_date")

    context = {
        "leave_requests": leave_requests,
        "total_requests": leave_requests.count(),
        "pending_requests": leave_requests.filter(status="Pending").count(),
        "approved_requests": leave_requests.filter(status="Approved").count(),
        "rejected_requests": leave_requests.filter(status="Rejected").count(),
        "search": search,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "ac_finance_leave.html", context)




 # engineering_leave_dashboard

def engineering_leave_dashboard(request):
    secret_key = request.GET.get("key")

    if secret_key != "eng123":
        return HttpResponseForbidden("Access Denied")

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    #  Engineering + Pending first
    leave_requests = LeaveRequest.objects.filter(
        department__iexact="Engineering"
    ).annotate(
        status_order=Case(
            When(status="Pending", then=Value(1)),
            When(status="Approved", then=Value(2)),
            When(status="Rejected", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    )

    #  Search
    if search:
        leave_requests = leave_requests.filter(
            Q(leave_id__icontains=search) |
            Q(name__icontains=search)
        )

    #  Status filter
    if status:
        leave_requests = leave_requests.filter(status=status)

    #  Date filters
    if from_date:
        leave_requests = leave_requests.filter(request_date__date__gte=from_date)

    if to_date:
        leave_requests = leave_requests.filter(request_date__date__lte=to_date)

    #  Final sorting → Pending first
    leave_requests = leave_requests.order_by("status_order", "-request_date")

    context = {
        "leave_requests": leave_requests,
        "total_requests": leave_requests.count(),
        "pending_requests": leave_requests.filter(status="Pending").count(),
        "approved_requests": leave_requests.filter(status="Approved").count(),
        "rejected_requests": leave_requests.filter(status="Rejected").count(),
        "search": search,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "eng_leave.html", context)


#dme_leave
def dme_leave(request):
    #  secure key check
    secret_key = request.GET.get("key")
    if secret_key != "dme123":
        return HttpResponseForbidden("Access Denied")

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    #  only DME + pending first
    leave_requests = LeaveRequest.objects.filter(
        department__iexact="DME"
    ).annotate(
        status_order=Case(
            When(status="Pending", then=Value(1)),
            When(status="Approved", then=Value(2)),
            When(status="Rejected", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    )

    #  search
    if search:
        leave_requests = leave_requests.filter(
            Q(leave_id__icontains=search) |
            Q(name__icontains=search)
        )

    #  status filter
    if status:
        leave_requests = leave_requests.filter(status=status)

    # date filters
    if from_date:
        leave_requests = leave_requests.filter(request_date__date__gte=from_date)

    if to_date:
        leave_requests = leave_requests.filter(request_date__date__lte=to_date)

    #  final sorting
    leave_requests = leave_requests.order_by("status_order", "-request_date")

    context = {
        "leave_requests": leave_requests,
        "total_requests": leave_requests.count(),
        "pending_requests": leave_requests.filter(status="Pending").count(),
        "approved_requests": leave_requests.filter(status="Approved").count(),
        "rejected_requests": leave_requests.filter(status="Rejected").count(),
        "search": search,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "dme_leave.html", context)




# hr_admin_leave_dashboard

def hr_admin_leave_dashboard(request):
    secret_key = request.GET.get("key")

    if secret_key != "hr123":
        return HttpResponseForbidden("Access Denied")

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    #  HR and Admin + Pending first
    leave_requests = LeaveRequest.objects.filter(
        department__iexact="HR and Admin"
    ).annotate(
        status_order=Case(
            When(status="Pending", then=Value(1)),
            When(status="Approved", then=Value(2)),
            When(status="Rejected", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    )

    # search
    if search:
        leave_requests = leave_requests.filter(
            Q(leave_id__icontains=search) |
            Q(name__icontains=search)
        )

    # status
    if status:
        leave_requests = leave_requests.filter(status=status)

    # date filters
    if from_date:
        leave_requests = leave_requests.filter(
            request_date__date__gte=from_date
        )

    if to_date:
        leave_requests = leave_requests.filter(
            request_date__date__lte=to_date
        )

    #  Pending first + latest first
    leave_requests = leave_requests.order_by("status_order", "-request_date")

    context = {
        "leave_requests": leave_requests,
        "total_requests": leave_requests.count(),
        "pending_requests": leave_requests.filter(status="Pending").count(),
        "approved_requests": leave_requests.filter(status="Approved").count(),
        "rejected_requests": leave_requests.filter(status="Rejected").count(),
        "search": search,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "hr_admin_leave.html", context)


 #purchase_leave_dashboard

def purchase_leave_dashboard(request):
    secret_key = request.GET.get("key")

    if secret_key != "pur123":
        return HttpResponseForbidden("Access Denied")

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    #  Purchase + Pending first
    leave_requests = LeaveRequest.objects.filter(
        department__iexact="Purchase"
    ).annotate(
        status_order=Case(
            When(status="Pending", then=Value(1)),
            When(status="Approved", then=Value(2)),
            When(status="Rejected", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    )

    # search
    if search:
        leave_requests = leave_requests.filter(
            Q(leave_id__icontains=search) |
            Q(name__icontains=search)
        )

    # status
    if status:
        leave_requests = leave_requests.filter(status=status)

    # date filters
    if from_date:
        leave_requests = leave_requests.filter(
            request_date__date__gte=from_date
        )

    if to_date:
        leave_requests = leave_requests.filter(
            request_date__date__lte=to_date
        )

    # Pending first + latest first
    leave_requests = leave_requests.order_by("status_order", "-request_date")

    context = {
        "leave_requests": leave_requests,
        "total_requests": leave_requests.count(),
        "pending_requests": leave_requests.filter(status="Pending").count(),
        "approved_requests": leave_requests.filter(status="Approved").count(),
        "rejected_requests": leave_requests.filter(status="Rejected").count(),
        "search": search,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "purchase_leave.html", context)



def sales_leave_dashboard(request):
    secret_key = request.GET.get("key")

    if secret_key != "sales123":
        return HttpResponseForbidden("Access Denied")

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    # Sales only + pending top
    leave_requests = LeaveRequest.objects.filter(
        department__iexact="Sales"
    ).annotate(
        status_order=Case(
            When(status="Pending", then=Value(1)),
            When(status="Approved", then=Value(2)),
            When(status="Rejected", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    )

    # Search
    if search:
        leave_requests = leave_requests.filter(
            Q(leave_id__icontains=search) |
            Q(name__icontains=search)
        )

    # Status
    if status:
        leave_requests = leave_requests.filter(status=status)

    # Date filters
    if from_date:
        leave_requests = leave_requests.filter(
            request_date__date__gte=from_date
        )

    if to_date:
        leave_requests = leave_requests.filter(
            request_date__date__lte=to_date
        )

    # Final sorting
    leave_requests = leave_requests.order_by(
        "status_order",
        "-request_date"
    )

    context = {
        "leave_requests": leave_requests,
        "total_requests": leave_requests.count(),
        "pending_requests": leave_requests.filter(status="Pending").count(),
        "approved_requests": leave_requests.filter(status="Approved").count(),
        "rejected_requests": leave_requests.filter(status="Rejected").count(),
        "search": search,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "sales_leave.html", context)



def mdo_leave_dashboard(request):
    secret_key = request.GET.get("key")

    if secret_key != "mdo123":
        return HttpResponseForbidden("Access Denied")

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    leave_requests = LeaveRequest.objects.filter(
        department__iexact="MDO"
    ).annotate(
        status_order=Case(
            When(status="Pending", then=Value(1)),
            When(status="Approved", then=Value(2)),
            When(status="Rejected", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    )

    if search:
        leave_requests = leave_requests.filter(
            Q(leave_id__icontains=search) |
            Q(name__icontains=search)
        )

    if status:
        leave_requests = leave_requests.filter(status=status)

    if from_date:
        leave_requests = leave_requests.filter(
            request_date__date__gte=from_date
        )

    if to_date:
        leave_requests = leave_requests.filter(
            request_date__date__lte=to_date
        )

    leave_requests = leave_requests.order_by(
        "status_order",
        "-request_date"
    )

    context = {
        "leave_requests": leave_requests,
        "total_requests": leave_requests.count(),
        "pending_requests": leave_requests.filter(status="Pending").count(),
        "approved_requests": leave_requests.filter(status="Approved").count(),
        "rejected_requests": leave_requests.filter(status="Rejected").count(),
        "search": search,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "mdo_leave.html", context)


def mdo_sales_leave_dashboard(request):
    secret_key = request.GET.get("key")

    if secret_key != "mdosales123":
        return HttpResponseForbidden("Access Denied")

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")

    # only MDO Sales + pending first
    leave_requests = LeaveRequest.objects.filter(
        department__iexact="MDO Sales"
    ).annotate(
        status_order=Case(
            When(status="Pending", then=Value(1)),
            When(status="Approved", then=Value(2)),
            When(status="Rejected", then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    )

    # search
    if search:
        leave_requests = leave_requests.filter(
            Q(leave_id__icontains=search) |
            Q(name__icontains=search)
        )

    # status
    if status:
        leave_requests = leave_requests.filter(status=status)

    # date
    if from_date:
        leave_requests = leave_requests.filter(
            request_date__date__gte=from_date
        )
        




        
    if to_date:
        leave_requests = leave_requests.filter(
            request_date__date__lte=to_date
        )

    # final sorting
    leave_requests = leave_requests.order_by(
        "status_order",
        "-request_date"
    )

    context = {
        "leave_requests": leave_requests,
        "total_requests": leave_requests.count(),
        "pending_requests": leave_requests.filter(status="Pending").count(),
        "approved_requests": leave_requests.filter(status="Approved").count(),
        "rejected_requests": leave_requests.filter(status="Rejected").count(),
        "search": search,
        "status": status,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "mdo_sales_leave.html", context)





#customer_query_form
def customer_query_form(request):

    if request.method == "POST":

        # =========================
        # TOWER LOGIC
        # =========================

        tower = request.POST.get("tower")

        other_tower = request.POST.get("other_tower")

        if tower == "Other":
            tower = other_tower

        # =========================
        # AREA LOGIC
        # =========================

        area = request.POST.get("area")

        other_area = request.POST.get("other_area")

        if area == "Other":
            area = other_area

        # =========================
        # ISSUE LOGIC
        # =========================

        issue = request.POST.get("issue")

        other_issue = request.POST.get("other_issue")

        if issue == "Other":
            issue = other_issue

        # =========================
        # PHOTO
        # =========================

        photo_file = request.FILES.get("photo")

        print("FILES:", request.FILES)

        print("PHOTO FILE:", photo_file)

        # =========================
        # SAVE DATA
        # =========================

        obj = CustomerQuery.objects.create(

            email=request.POST.get("email"),

            name=request.POST.get("name"),

            contact=request.POST.get("contact"),

            
            
            

            tower=tower,

            other_tower=other_tower,

            area=area,

            other_area=other_area,

            issue=issue,

            

            problem=request.POST.get("problem"),

            photo=photo_file

        )
        # =========================
        # SEND MAIL TO CRM
        # =========================

        send_mail(
            subject=f"New Customer Query Raised - {obj.ticket_id}",
            
            
            message=f"""
        New Customer Query Received
     
        Ticket ID: {obj.ticket_id}
        Customer Name: {obj.name}
        Email: {obj.email}
        Contact: {obj.contact}
        
        Block: {obj.tower}
        Location: {obj.area}                              

        Issue Related With: {obj.issue}

        Problem Description:
        {obj.problem}

        """,
            from_email=settings.EMAIL_HOST_USER,          
            recipient_list=[EMAILS[ "test"]],
            fail_silently=False,
        )       

        


        # =========================
        # DEBUG CHECK
        # =========================

        print("PHOTO PATH:", obj.photo)

        if obj.photo:

            print("PHOTO URL:", obj.photo.url)

        else:

            print("NO PHOTO SAVED")

        # =========================
        # SUCCESS REDIRECT
        # =========================

        return redirect("/customer-form/?success=1")

    # =========================
    # SUCCESS MESSAGE
    # =========================

    success = request.GET.get("success") == "1"

    return render(

        request,

        "customer_query_form.html",

        {
            "success": success
        }

    )


def export_customer_queries(request):

    response = HttpResponse(content_type='text/csv')

    response['Content-Disposition'] = 'attachment; filename="customer_queries.csv"'

    writer = csv.writer(response)

    # HEADER

    writer.writerow([
        'Ticket ID',
        'Name',
        'Contact',
        'Photo URL'
    ])

    # DATA

    queries = CustomerQuery.objects.all()

    for obj in queries:

        photo_url = ""

        if obj.photo:
            photo_url = request.build_absolute_uri(obj.photo.url)

        writer.writerow([
            obj.ticket_id,
            obj.name,
            obj.contact,
            photo_url
        ])

    return response


def maintenance_scope_form(request, query_id):

    customer = get_object_or_404(
        CustomerQuery,
        id=query_id
    )
    
    sla_due_time = customer.created_at + timedelta(hours=3)
    overdue = timezone.now() > sla_due_time

    if request.method == "POST":

        scope_status = request.POST.get("scope_status")

        MaintenanceScope.objects.create(

            customer_query=customer,

            email=customer.email,

            uid=customer.id,

            case_id=customer.ticket_id,

            customer_name=customer.name,

            customer_contact=customer.contact,

            block=customer.tower,

            location=customer.area,

            issue_related=customer.issue,

            issue_description=customer.problem,

            scope_status=scope_status,

            reason=request.POST.get("reason")

        )

        if scope_status == "Yes":

            customer.status = "In Progress"

            send_mail(

                subject="New Site Inspection Assigned",

                message=f"""
Hello Site Engineer,

A new Site Inspection has been assigned.

Case ID : {customer.ticket_id}

Customer : {customer.name}

Contact : {customer.contact}

Block : {customer.tower}

Area : {customer.area}

Issue : {customer.problem}

Please complete the Site Inspection as soon as possible.

Thank You.
""",

                from_email=settings.EMAIL_HOST_USER,

                recipient_list=[
                    EMAILS[ "test"]  #siteenginer ka mail aagyega baad me 
                ],

                fail_silently=False

            )

            popup_message = (
                "Form Submitted Successfully. "
                "Site Engineer Has Been Notified."
            )

        else:

            customer.status = "Closed"

            popup_message = (
                "Maintenance Ticket And Form Is Closed. "
                "Thank You."
            )

        customer.save()

        return render(
            request,
            "scope_success.html",
            {
                "popup_message": popup_message
            }
        )

    return render(
        request,
        "maintenance_scope.html",
        {
            "customer": customer
        }
    )


def site_inspection_form(request, query_id):

    customer = get_object_or_404(
        CustomerQuery,
        id=query_id
    )

    if request.method == "POST":

        issue_found_area = ",".join(
            request.POST.getlist("issue_found_area")
        )

        category = request.POST.get("category")

        SiteInspection.objects.create(

            customer_query=customer,

            engineer_email=request.POST.get("engineer_email"),

            engineer_name=request.POST.get("engineer_name"),

            uid=customer.id,

            case_id=customer.ticket_id,

            customer_name=customer.name,

            block=customer.tower,

            area=customer.area,

            issue_found_remark=request.POST.get(
                "issue_found_remark"
            ),

            issue_found_area=issue_found_area,

            category=category,

            

            photo1=request.FILES.get("photo1"),
            photo2=request.FILES.get("photo2"),
            

            material_required=request.POST.get(
                "material_required"
            ),

            material_reason=request.POST.get(
                "material_reason"
            ),

            days_required=request.POST.get(
                "days_required"
            ),

            under_scope=request.POST.get(
                "under_scope"
            )
        )

        if category == "Chargeable":

            customer.status = "Estimate Pending"

        else:

            customer.status = "Closer Pending"

        customer.save()

        return render(
            request,
            "site_inspection.html",
            {
                "popup_message": "Site Inspection Form Submitted Successfully"
            }
        )

    return render(
        request,
        "site_inspection.html",
        {
            "customer":customer
        }
    )





def estimate_form(request, query_id):

    customer = get_object_or_404(
        CustomerQuery,
        id=query_id
    )

    if request.method == "POST":

        try:

            EstimateForm.objects.create(

                customer_query=customer,

                email=request.POST.get("email"),

                your_name=request.POST.get("your_name"),

                uid=customer.id,

                customer_name=customer.name,

                contact_number=customer.contact,

                block=customer.tower,

                area=customer.area,

                case_id=customer.ticket_id,

                advance_amount_mentioned=request.POST.get(
                    "advance_amount_mentioned"
                ),

                invoice_amount=request.POST.get(
                    "invoice_amount"
                ),

                proforma_invoice=request.FILES.get(
                    "proforma_invoice"
                )
            )

            return HttpResponse("DATA SAVED")

        except Exception as e:

            return HttpResponse(
                f"ERROR = {e}"
            )

    return render(
        request,
        "estimate_form.html",
        {
            "customer": customer
        }
    )


# customer_approval_form

def customer_approval_form(request, query_id):

    customer = get_object_or_404(
        CustomerQuery,
        id=query_id
    )

    if request.method == "POST":

        approval_type = request.POST.get(
            "approval_type"
        )

        CustomerApproval.objects.create(

            customer_query=customer,

            email=request.POST.get("email"),

            uid=customer.id,

            customer_name=customer.name,

            block=customer.tower,

            area=customer.area,

            case_id=customer.ticket_id,

            approval_type=approval_type,

            customer_remark=request.POST.get(
                "customer_remark"
            )
        )

        if approval_type == "Reject":

            customer.status = "Closed"
            popup_message = "Customer Rejected. Form Closed Successfully."

        else:

            popup_message = "Customer Approved. Form Submitted Successfully."    

        customer.save()

        return render(
            request,
            "customer_approval.html",
            {
                "customer": customer,
                "success": True,
                "popup_message": popup_message
            }
        )

    return render(
        request,
        "customer_approval.html",
        {
            "customer": customer,
            "success": False
        }
    )



def advance_collection_form(request, query_id):

    customer = get_object_or_404(
        CustomerQuery,
        id=query_id
    )

    if request.method == "POST":

        AdvanceCollection.objects.create(

            customer_query=customer,

            email=request.POST.get(
                "email"
            ),

            uid=customer.id,

            customer_name=customer.name,

            block=customer.tower,

            area=customer.area,

            case_id=customer.ticket_id,

            advance_collected=request.POST.get(
                "advance_collected"
            ),

            collected_by=request.POST.get(
                "collected_by"
            )
        )

        return render(
            request,
            "advance_collection.html",
            {
                "customer": customer,
                "success": True,
                "popup_message":
                "Advance Collection Form Submitted Successfully"
            }
        )

    return render(
        request,
        "advance_collection.html",
        {
            "customer": customer,
            "success": False
        }
    )




def material_availability_form(request, query_id):

    customer = get_object_or_404(
        CustomerQuery,
        id=query_id
    )

    if request.method == "POST":

        material_available = request.POST.get(
            "material_available"
        )

        MaterialAvailability.objects.create(

            customer_query=customer,

            email=request.POST.get("email"),

            uid=customer.id,

            customer_name=customer.name,

            block=customer.tower,

            area=customer.area,

            case_id=customer.ticket_id,

            material_available=material_available
        )

        if material_available == "No":

            customer.status = "Indent Pending"

        else:

            customer.status = "Material Available"

        customer.save()

        return render(
            request,
            "material_availability.html",
            {
                "customer": customer,
                "popup_message":
                "Material Availability Form Submitted Successfully"
            }
        )

    return render(
        request,
        "material_availability.html",
        {
            "customer": customer
        }
    )


def raise_indent_form(request, query_id):

    customer = get_object_or_404(
        CustomerQuery,
        id=query_id
    )

    if request.method == "POST":

        RaiseIndent.objects.create(

            customer_query=customer,

            email=request.POST.get(
                "email"
            ),

            uid=customer.id,

            customer_name=customer.name,

            block=customer.tower,

            area=customer.area,

            case_id=customer.ticket_id
        )

        customer.status = "Purchase Pending"

        customer.save()

        return render(
            request,
            "raise_indent.html",
            {
                "customer": customer,
                "popup_message":
                "Raise Indent Form Submitted Successfully"
            }
        )

    return render(
        request,
        "raise_indent.html",
        {
            "customer": customer
        }
    )




def issue_material_form(request, query_id):

    customer = get_object_or_404(
        CustomerQuery,
        id=query_id
    )

    if request.method == "POST":

        IssueMaterial.objects.create(

            customer_query=customer,

            email=request.POST.get(
                "email"
            ),

            uid=customer.id,

            customer_name=customer.name,

            block=customer.tower,

            area=customer.area,

            case_id=customer.ticket_id,

            issued_by=request.POST.get(
                "issued_by"
            ),

            remark=request.POST.get(
                "remark"
            )
        )

        customer.status = "Material Issued"

        customer.save()

        return render(
            request,
            "issue_material.html",
            {
                "customer": customer,
                "popup_message":
                "Issue Material Form Submitted Successfully"
            }
        )

    return render(
        request,
        "issue_material.html",
        {
            "customer": customer
        }
    )






def receive_material_form(request, query_id):

    customer = get_object_or_404(
        CustomerQuery,
        id=query_id
    )

    if request.method == "POST":

        ReceiveMaterial.objects.create(

            customer_query=customer,

            email=request.POST.get(
                "email"
            ),

            uid=customer.id,

            customer_name=customer.name,

            block=customer.tower,

            area=customer.area,

            case_id=customer.ticket_id,

            received_by=request.POST.get(
                "received_by"
            ),

            remark=request.POST.get(
                "remark"
            )
        )

        customer.status = "Material Received"

        customer.save()

        return render(
            request,
            "receive_material.html",
            {
                "customer": customer,
                "popup_message":
                "Receive Material Form Submitted Successfully"
            }
        )

    return render(
        request,
        "receive_material.html",
        {
            "customer": customer
        }
    )


def query_closer_form(request, query_id):

    customer = get_object_or_404(
        CustomerQuery,
        id=query_id
    )

    if request.method == "POST":

        QueryCloser.objects.create(

            customer_query=customer,

            email=request.POST.get(
                "email"
            ),

            uid=customer.id,

            contact_number=customer.contact,

            customer_name=customer.name,

            block=customer.tower,

            area=customer.area,

            case_id=customer.ticket_id,

            solution_provided=request.POST.get(
                "solution_provided"
            ),

            closer_report=request.FILES.get(
                "closer_report"
            )
        )

        customer.status = "Closed"

        customer.save()

        return render(
            request,
            "query_closer.html",
            {
                "customer": customer,
                "popup_message":
                "Query Closed Successfully"
            }
        )

    return render(
        request,
        "query_closer.html",
        {
            "customer": customer
        }
    )



def customer_feedback_form(request, query_id):

    customer = get_object_or_404(
        CustomerQuery,
        id=query_id
    )

    if request.method == "POST":

        issue_resolved = request.POST.get(
            "issue_resolved"
        )

        service_satisfied = request.POST.get(
            "service_satisfied"
        )

        CustomerFeedback.objects.create(

            customer_query=customer,

            email=request.POST.get(
                "email"
            ),

            uid=customer.id,

            customer_name=customer.name,

            contact_number=customer.contact,

            block=customer.tower,

            area=customer.area,

            case_id=customer.ticket_id,

            issue_resolved=issue_resolved,

            customer_remark=request.POST.get(
                "customer_remark"
            ),

            service_satisfied=service_satisfied
        )

        if (
            issue_resolved == "Yes"
            and
            service_satisfied == "Yes"
        ):

            customer.status = "Closed"

        else:

            customer.status = "Pending"

        customer.save()

        return render(
            request,
            "customer_feedback.html",
            {
                "customer": customer,
                "popup_message":
                "Customer Feedback Submitted Successfully"
            }
        )

    return render(
        request,
        "customer_feedback.html",
        {
            "customer": customer
        }
    )






def login_view(request):

    # ==========================================
    # ALREADY LOGIN
    # ==========================================

    if request.session.get("admin_id"):

        role = request.session.get("admin_role")

        if role == "Admin":
            return redirect("admin_dashboard")

        elif role == "CRM":
            return redirect("crm_dashboard")

        elif role == "Site Engineer":
            return redirect("site_engineer_dashboard")

        elif role == "Store Keeper":
            return redirect("store_dashboard")

        elif role == "Maintenance":
            return redirect("maintenance_dashboard")

    # ==========================================
    # LOGIN
    # ==========================================

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:

            messages.error(
                request,
                "Please enter Username and Password."
            )

            return render(request, "login.html")

        try:

            admin = AdminUser.objects.get(

                username=username,
                is_active=True

            )

            # Password Verify
            if admin.verify_password(password):

                # =============================
                # CREATE SESSION
                # =============================

                request.session["admin_id"] = admin.id
                request.session["admin_name"] = admin.full_name
                request.session["admin_role"] = admin.role

                # =============================
                # ROLE WISE REDIRECT
                # =============================

                if admin.role == "Admin":
                    return redirect("admin_dashboard")

                elif admin.role == "CRM":
                    return redirect("crm_dashboard")

                elif admin.role == "Site Engineer":
                     return redirect("site_engineer_dashboard")

                elif admin.role == "Store Keeper":
                    return redirect("store_dashboard")

                elif admin.role == "Maintenance":
                    return redirect("maintenance_dashboard")

                else:

                    messages.error(
                        request,
                        "Role is not assigned."
                    )

                    return redirect("login")

            else:

                messages.error(
                    request,
                    "Invalid Password."
                )

        except AdminUser.DoesNotExist:

            messages.error(
                request,
                "Invalid Username."
            )

    return render(
        request,
        "login.html"
    )

# ==========================
# LOGOUT
# ==========================

def logout_view(request):

    request.session.flush()

    messages.success(
        request,
        "Logged out Successfully."
    )

    return redirect("login")





from .models import (
    CustomerQuery,
    MaintenanceScope,
    SiteInspection,
    EstimateForm,
    CustomerApproval,
    AdvanceCollection,
    MaterialAvailability,
    RaiseIndent,
    IssueMaterial,
    ReceiveMaterial,
    QueryCloser,
    CustomerFeedback,
)



def maintenance_dashboard(request):
    
    if "admin_id" not in request.session:
        return redirect("login")

    # ==========================================
    # DASHBOARD SUMMARY
    # ==========================================

    total_queries = CustomerQuery.objects.count()

    open_queries = SiteInspection.objects.filter(
    under_scope="Yes",
    customer_query__status="Open"
    ).count()

    pending_queries = CustomerQuery.objects.filter(
        status="Pending"
    ).count()

    in_progress_queries = CustomerQuery.objects.filter(
        status="In Progress"
    ).count()

    resolved_queries = CustomerQuery.objects.filter(
        status="Resolved"
    ).count()

    closed_queries = CustomerQuery.objects.filter(
        status="Closed"
    ).count()

    today_queries = CustomerQuery.objects.filter(
        created_at__date=timezone.now().date()
    ).count()


    # ==========================================
    # WORKFLOW COUNTS
    # ==========================================

    maintenance_scope = MaintenanceScope.objects.count()

    site_inspection = SiteInspection.objects.count()

    estimate_form = EstimateForm.objects.count()

    customer_approval = CustomerApproval.objects.count()

    advance_collection = AdvanceCollection.objects.count()

    material_availability = MaterialAvailability.objects.count()

    raise_indent = RaiseIndent.objects.count()

    issue_material = IssueMaterial.objects.count()

    receive_material = ReceiveMaterial.objects.count()

    query_closer = QueryCloser.objects.count()

    customer_feedback = CustomerFeedback.objects.count()


    # ==========================================
    # PENDING STAGE COUNTS
    # ==========================================

    scope_pending = max(
        total_queries - maintenance_scope,
        0
    )

    inspection_pending = max(
        maintenance_scope - site_inspection,
        0
    )

    estimate_pending = max(
        site_inspection - estimate_form,
        0
    )

    approval_pending = max(
        estimate_form - customer_approval,
        0
    )

    advance_pending = max(
        customer_approval - advance_collection,
        0
    )

    material_pending = max(
        advance_collection - material_availability,
        0
    )

    indent_pending = max(
        material_availability - raise_indent,
        0
    )

    issue_pending = max(
        raise_indent - issue_material,
        0
    )

    receive_pending = max(
        issue_material - receive_material,
        0
    )

    close_pending = max(
        receive_material - query_closer,
        0
    )

    feedback_pending = max(
        query_closer - customer_feedback,
        0
    )


    # ==========================================
    # LATEST COMPLAINTS
    # ==========================================

    all_complaints = CustomerQuery.objects.order_by(
        "-created_at"
    )


    # ==========================================
    # RECENT ESTIMATES
    # ==========================================

    recent_estimates = EstimateForm.objects.select_related(
        "customer_query"
    ).order_by("-id")[:5]


    # ==========================================
    # RECENT APPROVALS
    # ==========================================

    recent_approvals = CustomerApproval.objects.select_related(
        "customer_query"
    ).order_by("-id")[:5]
    

    # ==========================================
    # MATERIAL STATISTICS
    # ==========================================

    material_available_yes = MaterialAvailability.objects.filter(
        material_available="Yes"
    ).count()

    material_available_no = MaterialAvailability.objects.filter(
        material_available="No"
    ).count()

    total_material = (
        material_available_yes +
        material_available_no
    )

    if total_material:

        material_available_percent = round(
            (material_available_yes / total_material) * 100
        )

        material_pending_percent = round(
            (material_available_no / total_material) * 100
        )

    else:

        material_available_percent = 0
        material_pending_percent = 0


    # ==========================================
    # CHARGEABLE / NON CHARGEABLE
    # ==========================================

    chargeable = SiteInspection.objects.filter(
        category="Chargeable"
    ).count()

    non_chargeable = SiteInspection.objects.filter(
        category="Non Chargeable"
    ).count()

    total_category = chargeable + non_chargeable

    if total_category:

        chargeable_percent = round(
            (chargeable / total_category) * 100
        )

        non_chargeable_percent = round(
            (non_chargeable / total_category) * 100
        )

    else:

        chargeable_percent = 0
        non_chargeable_percent = 0


    # ==========================================
    # MONTHLY COMPLAINTS
    # ==========================================

    monthly_data = (
        CustomerQuery.objects
        .values("created_at__month")
        .annotate(total=Count("id"))
        .order_by("created_at__month")
    )

    month_names = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }

    months = []
    monthly_counts = []
    

    for item in monthly_data:

        months.append(
            month_names[item["created_at__month"]]
        )

        monthly_counts.append(
            item["total"]
        )

    monthly_report = zip(months, monthly_counts)


    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        # SUMMARY

        "total_queries": total_queries,
        "open_queries": open_queries,
        "pending_queries": pending_queries,
        "in_progress_queries": in_progress_queries,
        "resolved_queries": resolved_queries,
        "closed_queries": closed_queries,
        "today_queries": today_queries,

        # WORKFLOW

        "maintenance_scope": maintenance_scope,
        "site_inspection": site_inspection,
        "estimate_form": estimate_form,
        "customer_approval": customer_approval,
        "advance_collection": advance_collection,
        "material_availability": material_availability,
        "raise_indent": raise_indent,
        "issue_material": issue_material,
        "receive_material": receive_material,
        "query_closer": query_closer,
        "customer_feedback": customer_feedback,

        # PENDING

        "scope_pending": scope_pending,
        "inspection_pending": inspection_pending,
        "estimate_pending": estimate_pending,
        "approval_pending": approval_pending,
        "advance_pending": advance_pending,
        "material_pending": material_pending,
        "indent_pending": indent_pending,
        "issue_pending": issue_pending,
        "receive_pending": receive_pending,
        "close_pending": close_pending,
        "feedback_pending": feedback_pending,

        # TABLES

        "all_complaints": all_complaints,
        "recent_estimates": recent_estimates,
        "recent_approvals": recent_approvals,

        # CHART DATA

        "months": months,
        "monthly_counts": monthly_counts,
        "monthly_report": monthly_report,

        # PERCENTAGES

        "chargeable": chargeable,
        "non_chargeable": non_chargeable,
        "chargeable_percent": chargeable_percent,
        "non_chargeable_percent": non_chargeable_percent,

        "material_available_yes": material_available_yes,
        "material_available_no": material_available_no,
        "material_available_percent": material_available_percent,
        "material_pending_percent": material_pending_percent,

    }

    return render(
        request,
        "maintenance_dashboard.html",
        context
    )


def admin_dashboard(request):

    # ==========================================
    # LOGIN CHECK
    # ==========================================

    if "admin_id" not in request.session:
        return redirect("login")

    if request.session.get("admin_role") != "Admin":
        return redirect("login")


    # ==========================================
    # DASHBOARD SUMMARY
    # ==========================================

    total_queries = CustomerQuery.objects.count()

    open_queries = CustomerQuery.objects.filter(
        status="Open"
    ).count()

    pending_queries = CustomerQuery.objects.filter(
        status="Pending"
    ).count()

    in_progress_queries = CustomerQuery.objects.filter(
        status="In Progress"
    ).count()

    resolved_queries = CustomerQuery.objects.filter(
        status="Resolved"
    ).count()

    closed_queries = CustomerQuery.objects.filter(
        status="Closed"
    ).count()

    today_queries = CustomerQuery.objects.filter(
        created_at__date=timezone.now().date()
    ).count()


    # ==========================================
    # WORKFLOW COUNTS
    # ==========================================

    maintenance_scope = MaintenanceScope.objects.count()

    site_inspection = SiteInspection.objects.count()

    estimate_form = EstimateForm.objects.count()

    customer_approval = CustomerApproval.objects.count()

    advance_collection = AdvanceCollection.objects.count()

    material_availability = MaterialAvailability.objects.count()

    raise_indent = RaiseIndent.objects.count()

    issue_material = IssueMaterial.objects.count()

    receive_material = ReceiveMaterial.objects.count()

    query_closer = QueryCloser.objects.count()

    customer_feedback = CustomerFeedback.objects.count()
    # ==========================================
    # PENDING STAGE COUNTS
    # ==========================================

    scope_pending = max(
        total_queries - maintenance_scope,
        0
    )

    inspection_pending = max(
        maintenance_scope - site_inspection,
        0
    )

    estimate_pending = max(
        site_inspection - estimate_form,
        0
    )

    approval_pending = max(
        estimate_form - customer_approval,
        0
    )

    advance_pending = max(
        customer_approval - advance_collection,
        0
    )

    material_pending = max(
        advance_collection - material_availability,
        0
    )

    indent_pending = max(
        material_availability - raise_indent,
        0
    )

    issue_pending = max(
        raise_indent - issue_material,
        0
    )

    receive_pending = max(
        issue_material - receive_material,
        0
    )

    close_pending = max(
        receive_material - query_closer,
        0
    )

    feedback_pending = max(
        query_closer - customer_feedback,
        0
    )


    # ==========================================
    # ALL COMPLAINTS
    # (Admin will see every complaint)
    # ==========================================

    all_complaints = CustomerQuery.objects.order_by(
        "-created_at"
    )


    # ==========================================
    # CURRENT STAGE / PENDING WITH
    # ==========================================

    from datetime import timedelta
    
    STAGE_TIME = {

    "Maintenance Scope": 3,
    "Site Inspection": 3,
    "Estimate": 24,
    "Customer Approval": 24,
    "Advance Collection": 24,
    "Material Availability": 24,
    "Raise Indent": 24,
    "Issue Material": 24,
    "Receive Material": 24,
    "Query Closure": 24,
    "Customer Feedback": 24,

}
 



    for complaint in all_complaints:

        complaint.current_stage = "Completed"
        complaint.pending_with = "-"
        complaint.overdue = "No"

        if not MaintenanceScope.objects.filter(
            customer_query=complaint
        ).exists():

            complaint.current_stage = "Maintenance Scope"
            complaint.pending_with = "Dharmendra"

        elif not SiteInspection.objects.filter(
            customer_query=complaint
        ).exists():

            complaint.current_stage = "Site Inspection"
            complaint.pending_with = "Dipesh Chaudhary"

        elif not EstimateForm.objects.filter(
            customer_query=complaint
        ).exists():

            complaint.current_stage = "Estimate"
            complaint.pending_with = "Varsha Sahu"

        elif not CustomerApproval.objects.filter(
            customer_query=complaint
        ).exists():

            complaint.current_stage = "Customer Approval"
            complaint.pending_with = "Varsha Sahu"

        elif not AdvanceCollection.objects.filter(
            customer_query=complaint
        ).exists():

            complaint.current_stage = "Advance Collection"
            complaint.pending_with = "Varsha Sahu"

        elif not MaterialAvailability.objects.filter(
            customer_query=complaint
        ).exists():

            complaint.current_stage = "Material Availability"
            complaint.pending_with = "Bhola"

        elif not RaiseIndent.objects.filter(
            customer_query=complaint
        ).exists():

            complaint.current_stage = "Raise Indent"
            complaint.pending_with = "Bhola"

        elif not IssueMaterial.objects.filter(
            customer_query=complaint
        ).exists():

            complaint.current_stage = "Issue Material"
            complaint.pending_with = "Bhola"

        elif not ReceiveMaterial.objects.filter(
            customer_query=complaint
        ).exists():

            complaint.current_stage = "Receive Material"
            complaint.pending_with = "Dharmendra"

        elif not QueryCloser.objects.filter(
            customer_query=complaint
        ).exists():

            complaint.current_stage = "Query Closure"
            complaint.pending_with = "Dharmendra"

        elif not CustomerFeedback.objects.filter(
            customer_query=complaint
        ).exists():

            complaint.current_stage = "Customer Feedback"
            complaint.pending_with = "Varsha Sahu"    
    
        # ==========================================
        # OVERDUE CALCULATION
        # ==========================================
        
        
    # ==========================================
    # OVERDUE CALCULATION
    # ==========================================

    if complaint.current_stage == "Completed":

        complaint.overdue = "No"

    elif complaint.current_stage == "Maintenance Scope":

        due_time = complaint.created_at + timedelta(hours=2)

        complaint.overdue = (
            "Yes" if timezone.now() > due_time else "No"
        )

    elif complaint.current_stage == "Site Inspection":

        scope = MaintenanceScope.objects.filter(
            customer_query=complaint
        ).first()

        if scope:

            due_time = scope.created_at + timedelta(hours=24)

            complaint.overdue = (
                "Yes" if timezone.now() > due_time else "No"
            )

        else:

            complaint.overdue = "No"

    elif complaint.current_stage == "Estimate":

        inspection = SiteInspection.objects.filter(
            customer_query=complaint
        ).first()

        if inspection:

            due_time = inspection.created_at + timedelta(hours=48)

            complaint.overdue = (
                "Yes" if timezone.now() > due_time else "No"
            )

        else:

            complaint.overdue = "No"

    elif complaint.current_stage == "Customer Approval":

        estimate = EstimateForm.objects.filter(
            customer_query=complaint
        ).first()

        if estimate:

            due_time = estimate.created_at + timedelta(hours=24)

            complaint.overdue = (
                "Yes" if timezone.now() > due_time else "No"
            )

        else:

            complaint.overdue = "No"

    elif complaint.current_stage == "Advance Collection":

        approval = CustomerApproval.objects.filter(
            customer_query=complaint
        ).first()

        if approval:

            due_time = approval.created_at + timedelta(hours=24)

            complaint.overdue = (
                "Yes" if timezone.now() > due_time else "No"
            )

        else:

            complaint.overdue = "No"       
 
    elif complaint.current_stage == "Material Availability":

        advance = AdvanceCollection.objects.filter(
            customer_query=complaint
        ).first()

        if advance:

            due_time = advance.created_at + timedelta(hours=24)

            complaint.overdue = (
                "Yes" if timezone.now() > due_time else "No"
            )

        else:

            complaint.overdue = "No"
            
    elif complaint.current_stage == "Raise Indent":

        material = MaterialAvailability.objects.filter(
            customer_query=complaint
        ).first()

        if material:

            due_time = material.created_at + timedelta(hours=24)

            complaint.overdue = (
                "Yes" if timezone.now() > due_time else "No"
            )

        else:

            complaint.overdue = "No"    
            
    elif complaint.current_stage == "Issue Material":

        indent = RaiseIndent.objects.filter(
            customer_query=complaint
        ).first()

        if indent:

            due_time = indent.created_at + timedelta(hours=24)

            complaint.overdue = (
                "Yes" if timezone.now() > due_time else "No"
            )

        else:

            complaint.overdue = "No"    
            
    elif complaint.current_stage == "Receive Material":

        issue = IssueMaterial.objects.filter(
            customer_query=complaint
        ).first()

        if issue:

            due_time = issue.created_at + timedelta(hours=24)

            complaint.overdue = (
                "Yes" if timezone.now() > due_time else "No"
            )

        else:

            complaint.overdue = "No"
            
    elif complaint.current_stage == "Query Closure":

        receive = ReceiveMaterial.objects.filter(
            customer_query=complaint
        ).first()

        if receive:

            due_time = receive.created_at + timedelta(hours=24)

            complaint.overdue = (
                "Yes" if timezone.now() > due_time else "No"
            )

        else:

            complaint.overdue = "No"
            
    # ==========================================
    # COMPLETED CASE
    # ==========================================

    elif complaint.current_stage == "Completed":

        complaint.pending_with = "-"

        complaint.overdue = "No"

    # ==========================================
    # DEFAULT
    # ==========================================

    else:

        complaint.pending_with = "-"

        complaint.overdue = "No"

    # ==========================================
    # RECENT ESTIMATES
    # ==========================================

    recent_estimates = EstimateForm.objects.select_related(
        "customer_query"
    ).order_by(
        "-created_at"
    )[:10]


    # ==========================================
    # RECENT APPROVALS
    # ==========================================

    recent_approvals = CustomerApproval.objects.select_related(
        "customer_query"
    ).order_by(
        "-created_at"
    )[:10]


    # ==========================================
    # MATERIAL STATISTICS
    # ==========================================

    material_available_yes = MaterialAvailability.objects.filter(
        material_available="Yes"
    ).count()

    material_available_no = MaterialAvailability.objects.filter(
        material_available="No"
    ).count()

    total_material = (
        material_available_yes +
        material_available_no
    )

    if total_material > 0:

        material_available_percent = round(
            (material_available_yes / total_material) * 100
        )

        material_pending_percent = round(
            (material_available_no / total_material) * 100
        )

    else:

        material_available_percent = 0
        material_pending_percent = 0


    # ==========================================
    # CHARGEABLE / NON CHARGEABLE
    # ==========================================

    chargeable = SiteInspection.objects.filter(
        category="Chargeable"
    ).count()

    non_chargeable = SiteInspection.objects.filter(
        category="Non Chargeable"
    ).count()

    total_category = chargeable + non_chargeable

    if total_category > 0:

        chargeable_percent = round(
            (chargeable / total_category) * 100
        )

        non_chargeable_percent = round(
            (non_chargeable / total_category) * 100
        )

    else:

        chargeable_percent = 0
        non_chargeable_percent = 0


    # ==========================================
    # MONTHLY COMPLAINT REPORT
    # ==========================================

    monthly_data = (
        CustomerQuery.objects
        .values("created_at__month")
        .annotate(total=Count("id"))
        .order_by("created_at__month")
    )

    month_names = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }

    months = []
    monthly_counts = []

    for item in monthly_data:

        months.append(
            month_names[item["created_at__month"]]
        )

        monthly_counts.append(
            item["total"]
        )

    monthly_report = zip(
        months,
        monthly_counts
    )
    
    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        # ======================================
        # DASHBOARD SUMMARY
        # ======================================

        "total_queries": total_queries,
        "open_queries": open_queries,
        "pending_queries": pending_queries,
        "in_progress_queries": in_progress_queries,
        "resolved_queries": resolved_queries,
        "closed_queries": closed_queries,
        "today_queries": today_queries,

        # ======================================
        # WORKFLOW COUNTS
        # ======================================

        "maintenance_scope": maintenance_scope,
        "site_inspection": site_inspection,
        "estimate_form": estimate_form,
        "customer_approval": customer_approval,
        "advance_collection": advance_collection,
        "material_availability": material_availability,
        "raise_indent": raise_indent,
        "issue_material": issue_material,
        "receive_material": receive_material,
        "query_closer": query_closer,
        "customer_feedback": customer_feedback,

        # ======================================
        # PENDING STAGES
        # ======================================

        "scope_pending": scope_pending,
        "inspection_pending": inspection_pending,
        "estimate_pending": estimate_pending,
        "approval_pending": approval_pending,
        "advance_pending": advance_pending,
        "material_pending": material_pending,
        "indent_pending": indent_pending,
        "issue_pending": issue_pending,
        "receive_pending": receive_pending,
        "close_pending": close_pending,
        "feedback_pending": feedback_pending,

        # ======================================
        # TABLES
        # ======================================

        "all_complaints": all_complaints,
        "recent_estimates": recent_estimates,
        "recent_approvals": recent_approvals,

        # ======================================
        # CHART
        # ======================================

        "months": months,
        "monthly_counts": monthly_counts,
        "monthly_report": monthly_report,

        # ======================================
        # CHARGEABLE
        # ======================================

        "chargeable": chargeable,
        "non_chargeable": non_chargeable,
        "chargeable_percent": chargeable_percent,
        "non_chargeable_percent": non_chargeable_percent,

        # ======================================
        # MATERIAL
        # ======================================

        "material_available_yes": material_available_yes,
        "material_available_no": material_available_no,
        "material_available_percent": material_available_percent,
        "material_pending_percent": material_pending_percent,
        "all_complaints": all_complaints,

    }

    return render(

        request,

        "admin_dashboard.html",

        context

    )
















def site_engineer_dashboard(request):

    # ==========================================
    # LOGIN CHECK
    # ==========================================

    if "admin_id" not in request.session:
        return redirect("login")

    if request.session.get("admin_role") != "Site Engineer":
        return redirect("login")


    # ==========================================
    # CUSTOMER QUERY SUMMARY
    # ==========================================

    

    # ==========================================
    # MAINTENANCE SCOPE
    # ==========================================

    maintenance_scope = MaintenanceScope.objects.count()


    # ==========================================
    # SITE INSPECTION SUMMARY
    # ==========================================

    total_site_inspection = SiteInspection.objects.count()

    today_site_inspection = SiteInspection.objects.filter(
        created_at__date=timezone.now().date()
    ).count()

    chargeable = SiteInspection.objects.filter(
        category="Chargeable"
    ).count()

    non_chargeable = SiteInspection.objects.filter(
        category="Non Chargeable"
    ).count()

    material_required = SiteInspection.objects.filter(
        material_required="Yes"
    ).count()

    material_not_required = SiteInspection.objects.filter(
        material_required="No"
    ).count()

    vendor_side = SiteInspection.objects.filter(
        material_required="Vendor Side"
    ).count()

    

    # ==========================================
    # WORKFLOW
    # ==========================================

    site_inspection = total_site_inspection

    inspection_pending = max(
        maintenance_scope -
        site_inspection,
        0
    )




    # ==========================================
    # SEARCH
    # ==========================================

    search = request.GET.get("search", "")

    recent_site_inspections = SiteInspection.objects.filter(
        under_scope="Yes"
    )

    if search:
        recent_site_inspections = recent_site_inspections.filter(
            Q(case_id__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(engineer_name__icontains=search) |
            Q(block__icontains=search) |
            Q(area__icontains=search)
        )

    recent_site_inspections = recent_site_inspections.select_related(
        "customer_query"
    ).order_by("-created_at")[:10]


    # ==========================================
    # LATEST COMPLAINTS
    # ==========================================
    # ==========================================
    # LATEST COMPLAINTS
    # ==========================================

   


    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        # Complaint Summary

        

        # Workflow

        "maintenance_scope": maintenance_scope,
        "site_inspection": site_inspection,
        "inspection_pending": inspection_pending,

        # Site Inspection Summary

        "total_site_inspection": total_site_inspection,
        "today_site_inspection": today_site_inspection,

        "chargeable": chargeable,
        "non_chargeable": non_chargeable,

        "material_required": material_required,
        "material_not_required": material_not_required,
        "vendor_side": vendor_side,


        # Tables

        
        "recent_site_inspections": recent_site_inspections,
        "search": search,
       

        # Charts

       

    }

    return render(
        request,
        "site_engineer_dashboard.html",
        context
    )





# ==========================================================
# View dashbaoed 
# ==========================================================


# ==========================================================
# OFFICE TIMING
# ==========================================================

OFFICE_START = time(9, 30)     # 09:30 AM

OFFICE_END = time(18, 30)      # 06:30 PM


# ==========================================================
# STAGE TAT
# ==========================================================

STAGE_TAT = {

    "S1": ("hours", 3),

    "S2": ("days", 1),

    "S3": ("hours", 6),

    "S4": ("hours", 6),

    "S5": ("days", 1),

    "S6": ("hours", 2),

    "S7": ("days", 2),

    "S8": ("hours", 1),

    "S9": ("days", 1),

    "S10": ("days", 4),

    "S11": ("next_day_6pm", 1),

}


# ==========================================================
# SAFE RELATED OBJECT
# ==========================================================

def safe_related(obj, relation):

    try:

        return getattr(obj, relation)

    except:

        return None


# ==========================================================
# IS WORKING DAY
# Sunday = Holiday
# ==========================================================

def is_working_day(dt):

    return dt.weekday() != 6


# ==========================================================
# MOVE TO NEXT WORKING DAY
# ==========================================================

def next_working_day(dt):

    while not is_working_day(dt):

        dt += timedelta(days=1)

    return dt


# ==========================================================
# WORKING HOURS
# ==========================================================

def adjust_to_working_hours(dt):

    dt = timezone.localtime(dt)

    if dt.time() < OFFICE_START:

        dt = dt.replace(

            hour=OFFICE_START.hour,

            minute=OFFICE_START.minute,

            second=0,

            microsecond=0

        )

    elif dt.time() >= OFFICE_END:

        dt = dt + timedelta(days=1)

        dt = next_working_day(dt)

        dt = dt.replace(

            hour=OFFICE_START.hour,

            minute=OFFICE_START.minute,

            second=0,

            microsecond=0

        )

    dt = next_working_day(dt)

    return dt


# ==========================================================
# ADD WORKING HOURS
# ==========================================================

def add_working_hours(start_time, hours):

    current = adjust_to_working_hours(start_time)

    remaining = hours

    while remaining > 0:

        end_today = current.replace(

            hour=OFFICE_END.hour,

            minute=OFFICE_END.minute,

            second=0,

            microsecond=0

        )

        available = (end_today - current).total_seconds() / 3600

        if remaining <= available:

            current += timedelta(hours=remaining)

            remaining = 0

        else:

            remaining -= available

            current = current + timedelta(days=1)

            current = next_working_day(current)

            current = current.replace(

                hour=OFFICE_START.hour,

                minute=OFFICE_START.minute,

                second=0,

                microsecond=0

            )

    return current


# ==========================================================
# ADD WORKING DAYS
# ==========================================================

def add_working_days(start_time, days):

    current = adjust_to_working_hours(start_time)

    count = 0

    while count < days:

        current += timedelta(days=1)

        if is_working_day(current):

            count += 1

    return current


# ==========================================================
# NEXT WORKING DAY 6 PM
# ==========================================================

def next_day_6pm(start_time):

    current = adjust_to_working_hours(start_time)

    current += timedelta(days=1)

    current = next_working_day(current)

    return current.replace(

        hour=18,

        minute=0,

        second=0,

        microsecond=0

    )

# ==========================================================
# CALCULATE DUE TIME
# ==========================================================

def calculate_due_time(current_stage, stage_start):

    if not stage_start:
        return None

    if current_stage == "Completed":
        return None

    tat = STAGE_TAT.get(current_stage)

    if not tat:
        return None

    tat_type, tat_value = tat

    if tat_type == "hours":
        return add_working_hours(stage_start, tat_value)

    elif tat_type == "days":
        return add_working_days(stage_start, tat_value)

    elif tat_type == "next_day_6pm":
        return next_day_6pm(stage_start)

    return None


# ==========================================================
# REMAINING TIME / OVERDUE
# ==========================================================

def calculate_remaining_time(due_time):

    if not due_time:
        return "-", False

    now = timezone.localtime(timezone.now())

    due_time = timezone.localtime(due_time)

    diff = due_time - now

    seconds = int(diff.total_seconds())

    if seconds >= 0:

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        if days > 0:
            return f"{days}D {hours}H Left", False

        elif hours > 0:
            return f"{hours}H {minutes}M Left", False

        else:
            return f"{minutes} Minutes Left", False

    seconds = abs(seconds)

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    if days > 0:
        return f"Overdue by {days}D {hours}H", True

    elif hours > 0:
        return f"Overdue by {hours}H {minutes}M", True

    else:
        return f"Overdue by {minutes} Minutes", True


# ==========================================================
# PROGRESS
# ==========================================================

def get_progress(current_stage):

    if current_stage == "Completed":
        return "Closed"

    elif current_stage == "S1":
        return "Open"

    return "In Progress"


# ==========================================================
# PENDING WITH
# ==========================================================

def get_pending_with(current_stage):

    pending = {

        "S1": "CRM",
        "S2": "Site Engineer",
        "S3": "CRM",
        "S4": "CRM",
        "S5": "CRM",
        "S6": "Store Keeper",
        "S7": "Store Keeper",
        "S8": "Store Keeper",
        "S9": "Maintenance Incharge",
        "S10": "Maintenance Incharge",
        "S11": "CRM",
        "Completed": "-",

    }

    return pending.get(current_stage, "-")


# ==========================================================
# STAGE NAME
# ==========================================================

def get_stage_name(current_stage):

    names = {

        "S1": "Scope Check",
        "S2": "Site Inspection",
        "S3": "Estimate",
        "S4": "Customer Approval",
        "S5": "Advance Collection",
        "S6": "Material Availability",
        "S7": "Raise Indent",
        "S8": "Issue Material",
        "S9": "Receive Material",
        "S10": "Resolve Issue",
        "S11": "Customer Feedback",
        "Completed": "Completed",

    }

    return names.get(current_stage, "-")


# ==========================================================
# TIMELINE
# ==========================================================

def get_timeline(current_stage):

    return {

        "S0": current_stage != "S0",
        "S1": current_stage not in ["S0", "S1"],
        "S2": current_stage not in ["S0", "S1", "S2"],
        "S3": current_stage not in ["S0", "S1", "S2", "S3"],
        "S4": current_stage not in ["S0", "S1", "S2", "S3", "S4"],
        "S5": current_stage not in ["S0", "S1", "S2", "S3", "S4", "S5"],
        "S6": current_stage not in ["S0", "S1", "S2", "S3", "S4", "S5", "S6"],
        "S7": current_stage not in ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7"],
        "S8": current_stage not in ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"],
        "S9": current_stage not in ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"],
        "S10": current_stage not in ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"],
        "S11": current_stage == "Completed",

    }

# ==========================================================
# CRM MASTER DASHBOARD
# ==========================================================

def crm_dashboard(request):

    # ======================================================
    # LOGIN CHECK
    # ======================================================

    if "admin_id" not in request.session:
        return redirect("login")

    if request.session.get("admin_role") != "CRM":
        return redirect("login")

    # ======================================================
    # SEARCH
    # ======================================================

    search = request.GET.get("search", "").strip()

    # ======================================================
    # CUSTOMER QUERY
    # ======================================================

    queries = CustomerQuery.objects.all().order_by("-created_at")

    if search:
        queries = queries.filter(
            Q(ticket_id__icontains=search) |
            Q(name__icontains=search) |
            Q(contact__icontains=search) |
            Q(email__icontains=search) |
            Q(tower__icontains=search) |
            Q(area__icontains=search) |
            Q(issue__icontains=search)
        )

    # ======================================================
    # DASHBOARD COUNTS
    # ======================================================

    total_queries = queries.count()

    open_count = 0
    pending_count = 0
    in_progress_count = 0
    resolved_count = 0
    closed_count = 0

    overdue_count = 0
    due_today_count = 0

    # ======================================================
    # TABLE DATA
    # ======================================================

    customer_data = []
    overdue_customers = []
    due_today_customers = []

    today = timezone.localdate()

    # ======================================================
    # CUSTOMER LOOP
    # ======================================================

    for query in queries:

        # ==============================================
        # RELATED OBJECTS
        # ==============================================

        scope = safe_related(query, "scope_form")

        inspection = SiteInspection.objects.filter(
            customer_query=query
        ).first()

        estimate = EstimateForm.objects.filter(
            customer_query=query
        ).first()

        approval = CustomerApproval.objects.filter(
            customer_query=query
        ).first()

        advance = AdvanceCollection.objects.filter(
            customer_query=query
        ).first()

        material = MaterialAvailability.objects.filter(
            customer_query=query
        ).first()

        indent = RaiseIndent.objects.filter(
            customer_query=query
        ).first()

        issue_material = IssueMaterial.objects.filter(
            customer_query=query
        ).first()

        receive_material = ReceiveMaterial.objects.filter(
            customer_query=query
        ).first()

        closer = QueryCloser.objects.filter(
            customer_query=query
        ).first()

        feedback = CustomerFeedback.objects.filter(
            customer_query=query
        ).first()

        # ==============================================
        # CURRENT STAGE
        # ==============================================

        current_stage = "S1"
        stage_start = query.created_at

        if scope:
            current_stage = "S2"
            stage_start = scope.created_at

        if inspection:
            current_stage = "S3"
            stage_start = inspection.created_at

        if estimate:
            current_stage = "S4"
            stage_start = estimate.created_at

        if approval:
            current_stage = "S5"
            stage_start = approval.created_at

        if advance:
            current_stage = "S6"
            stage_start = advance.created_at

        if material:
            current_stage = "S7"
            stage_start = material.created_at

        if indent:
            current_stage = "S8"
            stage_start = indent.created_at

        if issue_material:
            current_stage = "S9"
            stage_start = issue_material.created_at

        if receive_material:
            current_stage = "S10"
            stage_start = receive_material.created_at

        if closer:
            current_stage = "S11"
            stage_start = closer.created_at

        if feedback:
            current_stage = "Completed"
            stage_start = feedback.created_at

        # ==============================================
        # STAGE DETAILS
        # ==============================================

        stage_name = get_stage_name(current_stage)
        pending_with = get_pending_with(current_stage)
        progress = get_progress(current_stage)
        timeline = get_timeline(current_stage)

        # ==============================================
        # DUE TIME
        # ==============================================

        due_time = calculate_due_time(
            current_stage,
            stage_start
        )
        
        # ==================================================
        # DUE TIME DISPLAY
        # ==================================================

        due_time_display = "-"
        remaining_time = "-"
        is_overdue = False

        if due_time:

            due_time_display = timezone.localtime(
                due_time
            ).strftime("%d-%m-%Y %I:%M %p")

            remaining_time, is_overdue = calculate_remaining_time(
                due_time
            )

        # ==================================================
        # QUERY RAISED
        # ==================================================

        query_raised = timezone.localtime(
            query.created_at
        ).strftime("%d-%m-%Y %I:%M %p")

        # ==================================================
        # DUE TODAY
        # ==================================================

        is_due_today = False

        if due_time and current_stage != "Completed":

            if timezone.localtime(due_time).date() == today:

                is_due_today = True
                due_today_count += 1

        # ==================================================
        # OVERDUE
        # ==================================================

        if is_overdue and current_stage != "Completed":

            overdue_count += 1

        # ==================================================
        # STATUS COUNT
        # ==================================================

        if query.status == "Open":

            open_count += 1

        elif query.status == "Pending":

            pending_count += 1

        elif query.status == "In Progress":

            in_progress_count += 1

        elif query.status == "Resolved":

            resolved_count += 1

        elif query.status == "Closed":

            closed_count += 1

        # ==================================================
        # PROGRESS
        # ==================================================

        if current_stage == "Completed":

            progress = "Closed"

        elif current_stage == "S1":

            progress = "Open"

        else:

            progress = "In Progress"

        # ==================================================
        # CUSTOMER DATA
        # ==================================================

        customer = {

            "id": query.id,

            "ticket": query.ticket_id,

            "customer": query.name,

            "contact": query.contact,

            "email": query.email,

            "tower": query.tower,

            "area": query.area,

            "issue": query.issue,

            "status": query.status,

            "query_raised": query_raised,

            "current_stage": current_stage,

            "stage_name": stage_name,

            "pending_with": pending_with,

            "progress": progress,

            "due_time": due_time_display,

            "remaining": remaining_time,

            "is_overdue": is_overdue,

            "timeline": timeline,

            "photo": query.photo,

        }

        customer_data.append(customer)

        # ==================================================
        # OVERDUE TABLE
        # ==================================================

        if is_overdue and current_stage != "Completed":

            overdue_customers.append(customer)

        # ==================================================
        # DUE TODAY TABLE
        # ==================================================

        if is_due_today and current_stage != "Completed":

            due_today_customers.append(customer)
            
    # ======================================================
    # CONTEXT
    # ======================================================

    context = {

        # Search
        "search": search,

        # Dashboard Counts
        "total_queries": total_queries,
        "open_count": open_count,
        "pending_count": pending_count,
        "in_progress_count": in_progress_count,
        "resolved_count": resolved_count,
        "closed_count": closed_count,
        "overdue_count": overdue_count,
        "due_today_count": due_today_count,

        # Main Table
        "customer_data": customer_data,

        # Overdue Table
        "overdue_customers": overdue_customers,

        # Due Today Table
        "due_today_customers": due_today_customers,

    }

    # ======================================================
    # RENDER
    # ======================================================

    return render(

        request,

        "crm_dashboard.html",

        context,

    )