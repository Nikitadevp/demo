from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta, time
from .models import Ticket
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
    plt.bar(["Open", "Closed"], [open_count, closed_count], color=["blue", "orange"])
    plt.title("Status")
    plt.tight_layout()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    status_chart = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    # -------- PRIORITY CHART --------
    buffer2 = io.BytesIO()
    plt.figure(figsize=(4,3))
    plt.bar(["Urgent", "Normal"], [urgent_count, normal_count], color=["blue", "orange"])
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