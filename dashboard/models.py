
from django.db import models
import uuid
from django.utils import timezone


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



class LeaveRequest(models.Model):
    leave_id = models.CharField(
        max_length=20,
        primary_key=True,
        editable=False
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)

    department = models.CharField(max_length=100)
    department_email = models.EmailField(blank=True, null=True)
    department_phone = models.CharField(max_length=15, blank=True, null=True)

    leave_type = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()

    # supports 0.5 for half day
    leave_days = models.FloatField(default=1)

    reason = models.TextField()

    request_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default="Pending")
    manager_reason = models.TextField(blank=True, null=True)

    approved_rejected_date = models.DateTimeField(blank=True, null=True)
    resolved_date = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # auto leave id
        if not self.leave_id:
            self.leave_id = f"LR-{uuid.uuid4().hex[:8].upper()}"

        leave_type_clean = (self.leave_type or "").strip().lower()

        #  half day
        if "half" in leave_type_clean:
            self.leave_days = 0.5

        #  same logic as Google Sheet
        elif self.start_date and self.end_date:
            diff_days = (self.end_date - self.start_date).days
            self.leave_days = diff_days + 1

        else:
            self.leave_days = 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.leave_id} - {self.name}"