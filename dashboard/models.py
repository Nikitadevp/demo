
from django.db import models
import uuid


def generate_ticket_no():
    return "TCKT-" + uuid.uuid4().hex[:8].upper()


class Ticket(models.Model):

    STATUS_CHOICES = [
        ("Open", "Open"),
        ("In Progress", "In Progress"),
        ("Resolved", "Resolved"),
        ("Closed", "Closed"),
    ]

    PRIORITY_CHOICES = [
        ("Urgent", "Urgent"),
        ("Normal", "Normal"),
    ]

    ticket_no = models.CharField(
        max_length=20,
        unique=True,
        default=generate_ticket_no,
        editable=False
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    department = models.CharField(max_length=100)
    issue_type = models.CharField(max_length=200)

    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Open"
    )

    tat_deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    problem_solver = models.CharField(max_length=100, null=True, blank=True)

    solution_provided = models.TextField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.ticket_no
# from django.db import models
# import uuid
# from django.contrib.auth.models import User


# def generate_ticket_no():
#     return "TCKT-" + uuid.uuid4().hex[:8].upper()


# class Ticket(models.Model):

#     STATUS_CHOICES = [
#         ("Open", "Open"),
#         ("In Progress", "In Progress"),
#         ("Resolved", "Resolved"),
#         ("Closed", "Closed"),
#     ]

#     PRIORITY_CHOICES = [
#         ("Urgent", "Urgent"),
#         ("Normal", "Normal"),
#     ]

#     ticket_no = models.CharField(
#         max_length=20,
#         unique=True,
#         default=generate_ticket_no,
#         editable=False
#     )

#     name = models.CharField(max_length=100)
#     email = models.EmailField()
#     phone = models.CharField(max_length=20)
#     department = models.CharField(max_length=100)
#     issue_type = models.CharField(max_length=200)

#     priority = models.CharField(
#         max_length=20,
#         choices=PRIORITY_CHOICES
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="Open"
#     )

#     tat_deadline = models.DateTimeField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     problem_solver = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )

#     solution_provided = models.TextField(null=True, blank=True)
#     resolved_at = models.DateTimeField(null=True, blank=True)

#     def __str__(self):
#         return self.ticket_no


class LeaveRequest(models.Model):

    # ✅ UNIQUE LEAVE ID
    leave_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        editable=False
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)

    department = models.CharField(max_length=100)
    leave_type = models.CharField(max_length=50)

    start_date = models.DateField()
    end_date = models.DateField()

    reason = models.TextField()

    status = models.CharField(max_length=20, default="Pending")
    manager_reason = models.TextField(blank=True, null=True)

    #  AUTO GENERATE LEAVE ID
    def save(self, *args, **kwargs):
        if not self.leave_id:
            self.leave_id = f"LR-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.leave_id if self.leave_id else self.name