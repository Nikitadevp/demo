from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta, time
from .models import Ticket
from django.urls import reverse
import matplotlib.pyplot as plt
import io
import base64
from .models import LeaveRequest
from django.http import HttpResponse
import re



#  Office Time Settings

# Office Time
OFFICE_START = time(9, 30)
OFFICE_END = time(18, 30)


def is_weekend(dt):
    # 5 = Saturday, 6 = Sunday
    return dt.weekday() in [5, 6]


def next_working_day(dt):
    while is_weekend(dt):
        dt = dt + timedelta(days=1)
    return dt


def calculate_tat_deadline(priority):

    now = timezone.localtime(timezone.now())

    if priority == "Urgent":
        remaining_hours = 6
    else:
        remaining_hours = 24

    current_datetime = now

    while remaining_hours > 0:

        # Weekend skip
        if is_weekend(current_datetime):
            current_datetime = next_working_day(current_datetime)
            current_datetime = current_datetime.replace(
                hour=9, minute=30, second=0, microsecond=0
            )
            continue

        current_time = current_datetime.time()

        if current_time < OFFICE_START:
            current_datetime = current_datetime.replace(
                hour=9, minute=30, second=0, microsecond=0
            )

        elif current_time >= OFFICE_END:
            next_day = current_datetime + timedelta(days=1)
            next_day = next_working_day(next_day)

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
                next_day = next_working_day(next_day)

                current_datetime = next_day.replace(
                    hour=9, minute=30, second=0, microsecond=0
                )

    return current_datetime

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

    department = request.GET.get('department')
    priority = request.GET.get('priority')
    status = request.GET.get('status')

    tickets = Ticket.objects.all()

    # -------- FILTERS --------
    if department:
        tickets = tickets.filter(department=department)

    if priority:
        tickets = tickets.filter(priority=priority)

    if status:
        tickets = tickets.filter(status=status)

    # -------- COUNTS --------
    open_count = tickets.filter(status="Open").count()
    closed_count = tickets.filter(status="Closed").count()
    urgent_count = tickets.filter(priority="Urgent").count()
    normal_count = tickets.filter(priority="Normal").count()

    # ================================
    # STATUS CHART (Open vs Closed)
    # ================================

    buffer = io.BytesIO()

    plt.figure(figsize=(4,3))
    plt.bar(["Open", "Closed"], [open_count, closed_count])
    plt.title("Status Wise Tickets")
    plt.tight_layout()

    plt.savefig(buffer, format="png")
    buffer.seek(0)

    status_chart = base64.b64encode(buffer.getvalue()).decode()

    plt.close()

    # ================================
    # PRIORITY CHART (Urgent vs Normal)
    # ================================

    buffer2 = io.BytesIO()

    plt.figure(figsize=(4,3))
    plt.bar(["Urgent", "Normal"], [urgent_count, normal_count])
    plt.title("Priority Wise Tickets")
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

        'total_tickets': tickets.count(),
        'open_tickets': open_count,
        'closed_tickets': closed_count,
        'urgent_tickets': urgent_count,
        'normal_tickets': normal_count,

        'recent_tickets': tickets.order_by('-created_at')[:10],

        # charts
        'status_chart': status_chart,
        'priority_chart': priority_chart,
    }

    return render(request, "dashboard.html", context)




#This for leave application     

    
department_emails={

"Accounts and Finance":"alok.agrawal@rajat-group.com",
"HR and Admin":"ea.rbpl@rajat-group.com",
"Engineering":"bagga.rbpl@rajat-group.com",
"MDO":"mrinal.golechha1@rajat-group.com",
"Sales":"vinod.mishra@rajat-group.com",
"Purchase":"ravi.jain@rajat-group.com",
"DME":"dme.rbpl@rajat-group.com",
"coordinator":"pc1.rbpl@rajat-group.com",
"jrdme":"jrdme.rbpl@rajat-group.com",
"MDO Sales":"prakhar.golechha@rajat-group.com"


}





def leave_form(request):

    if request.method == "POST":

        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        department = request.POST.get('department')
        leave_type = request.POST.get('leave_type')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        reason = request.POST.get('reason')

        #  EMAIL FORMAT VALIDATION (IMPORTANT)
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(pattern, email):
            return HttpResponse(" Please enter valid email like example@gmail.com")

        # SAVE DATA
        leave = LeaveRequest.objects.create(
            name=name,
            email=email,
            phone=phone,
            department=department,
            leave_type=leave_type,
            start_date=start,
            end_date=end,
            reason=reason
        )

        #  DYNAMIC DOMAIN (Render ke liye)
        domain = request.build_absolute_uri('/')[:-1]

        review_link = f"{domain}/review/{leave.id}/"
        

        #  MESSAGE FOR MANAGER
        message = f"""
New Leave Request



Employee: {name}
Department: {department}

Review Request:
{review_link}
"""

        #  OPTIONAL: DEPARTMENT MAIL (agar hai to)
        manager_email = department_emails.get(department)

        if manager_email:
            send_mail(
                "Leave Request Approval",
                message,
                settings.EMAIL_HOST_USER,
                [manager_email],
                fail_silently=True
            )

        #  MAIL TO USER (IMPORTANT)
        send_mail(
            "Leave Request Submitted",
            "Your leave request has been sent for approval.\n\nIf you do not receive updates, please check your email ID.",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=True
        )

        return render(request, "leave_form.html", {"success": True})

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


def review_leave(request, id):

    leave = get_object_or_404(LeaveRequest, id=id)

    if leave.status != "Pending":
        return HttpResponse("This request is already processed.")

    if request.method == "POST":

        action = request.POST.get("action")

        # APPROVE
        if action == "approve":
            leave.status = "Approved"
            leave.save()

            send_mail(
                "Leave Approved",
                f"Your leave has been approved.\nFrom {leave.start_date} to {leave.end_date}",
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
            leave.reject_reason = reason
            leave.save()

            send_mail(
                "Leave Rejected",
                f"Your leave has been rejected.\nReason: {reason}",
                settings.EMAIL_HOST_USER,
                [leave.email],
                fail_silently=True
            )

        return HttpResponse("Action completed successfully")

    return render(request, "review_leave.html", {"leave": leave})