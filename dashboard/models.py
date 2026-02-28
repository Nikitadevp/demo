from django.db import models
import random

class Ticket(models.Model):
    ticket_no = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    department = models.CharField(max_length=100)
    issue_type = models.CharField(max_length=100)
    priority = models.CharField(max_length=50)
    tat_deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Open")

    def save(self, *args, **kwargs):
        if not self.ticket_no:
            self.ticket_no = f"TKT{random.randint(10000,99999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ticket_no