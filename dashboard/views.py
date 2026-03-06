from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta, time
from .models import Ticket



#  Office Time Settings
OFFICE_START = time(9, 30)
OFFICE_END = time(18, 30)


#  TAT Calculation (Office Hours Based)
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



#  Raise Ticket View
def raise_ticket(request):
    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        department = request.POST.get("department")
        issue_type = request.POST.get("issue_type")
        priority = request.POST.get("priority")

        #  Calculate TAT Deadline
        tat_deadline = calculate_tat_deadline(priority)

        # Save Ticket
        ticket = Ticket.objects.create(
            name=name,
            email=email,
            phone=phone,
            department=department,
            issue_type=issue_type,
            priority=priority,
            tat_deadline=tat_deadline,
        )

        # Resolve URL (Safe way)
        resolve_url = request.build_absolute_uri(
            reverse("resolve_ticket", args=[ticket.ticket_no])
        )

        # Department Email Mapping
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

A new Help Desk ticket has been created.

Ticket ID   : {ticket.ticket_no}
Department  : {department}
Priority    : {priority}
Issue Type  : {issue_type}

Resolution Time: {tat_deadline.strftime('%d-%m-%Y %I:%M %p')}

Resolve Link:
{resolve_url}

-- Help Desk System
"""

        if dept_email:
            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [dept_email],
                    fail_silently=True,  # avoid 500 error in deploy
                )
            except Exception:
                pass

        return redirect(f"{reverse('raise_ticket')}?success=1")

    success = request.GET.get("success")
    return render(request, "ticket_form.html", {"success": success})


#resolve_ticket    


def resolve_ticket(request, ticket_no):
    ticket = get_object_or_404(Ticket, ticket_no=ticket_no)

    # Prevent re-resolving already closed tickets
    if ticket.status == "Closed":
        return render(request, "dashboard/resolve_ticket.html", {
            "ticket": ticket,
            "success": request.GET.get("success")
        })

    if request.method == "POST":

        problem_solver = request.POST.get("problem_solver")
        solution_provided = request.POST.get("solution_provided")

        if problem_solver and solution_provided:

            # Update Ticket
            ticket.status = "Closed"
            ticket.problem_solver = problem_solver
            ticket.solution_provided = solution_provided
            ticket.resolved_at = timezone.now()
            ticket.save()

            # Email Subject
            subject = f"Your Help Desk Ticket {ticket.ticket_no} Has Been Resolved"

            # Email Message
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

Resolved On   : {ticket.resolved_at.strftime('%d-%m-%Y %I:%M %p')}

---------------------------------------

Solution Provided:
{ticket.solution_provided}

If you have any further issues, please feel free to raise a new ticket.

Regards,
Help Desk Team
"""

            # Send Email
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [ticket.email],
                fail_silently=False,
            )

            return redirect(f"/resolve-ticket/{ticket.ticket_no}/?success=1")

    return render(request, "dashboard/resolve_ticket.html", {
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
    }

    #  Correct according to your structure
    return render(request, 'dashboard.html', context)




