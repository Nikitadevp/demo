
from datetime import timedelta

from django.db import models
import uuid
from django.utils import timezone
import random
import string
from django.contrib.auth.hashers import make_password, check_password

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




class CustomerQuery(models.Model):

    # ====================================
    
    # TOWER CHOICES
    # ====================================

    TOWER_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('Non Tower', 'Non Tower'),
        ('Amenities', 'Amenities'),
        ('Other', 'Other'),
    ]

    # ====================================
    # AREA CHOICES
    # ====================================

    AREA_CHOICES = [
        ('STP Area', 'STP Area'),
        ('Parking Area', 'Parking Area'),
        ('Temple Area', 'Temple Area'),
        ('Club House', 'Club House'),
        ('Other', 'Other'),
    ]

    # ====================================
    # ISSUE CHOICES
    # ====================================

    ISSUE_CHOICES = [
        ('Civil Work', 'Civil Work'),
        ('Plumbing Work', 'Plumbing Work'),
        ('Waterproofing Work', 'Waterproofing Work'),
        ('Door and Windows', 'Door and Windows'),
        ('Flooring Work', 'Flooring Work'),
        ('Painting Work', 'Painting Work'),
        ('Electrical Work', 'Electrical Work'),
        ('Other', 'Other'),
    ]

    # ====================================
    # STATUS CHOICES
    # ====================================

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    # ====================================
    # TICKET DETAILS
    # ====================================

    ticket_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='Open'
    )

    # ====================================
    # CUSTOMER DETAILS
    # ====================================

    email = models.EmailField()

    name = models.CharField(
        max_length=100
    )

    contact = models.CharField(
        max_length=10
    )

    
    # ====================================
    # LOCATION DETAILS
    # ====================================

    tower = models.CharField(
        max_length=50,
        choices=TOWER_CHOICES
    )

    other_tower = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    


    area = models.CharField(
        max_length=50,
        choices=AREA_CHOICES
    )

    other_area = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # ====================================
    # ISSUE DETAILS
    # ====================================

    issue = models.CharField(
        max_length=100,
        choices=ISSUE_CHOICES
    )

    

    problem = models.TextField()

    # ====================================
    # PHOTO UPLOAD
    # ====================================

    photo = models.ImageField(
        upload_to='customer_photos/',
        blank=True,
        null=True
    )

    # ====================================
    # TIME
    # ====================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    @property
    def sla_due_time(self):
        return self.created_at + timedelta(hours=3)
    
    @property
    def is_overdue(self):
        return (
             self.status == "Open" and timezone.now() > self.sla_due_time
        )


    # ====================================
    # AUTO TICKET ID
    # ====================================

    def save(self, *args, **kwargs):

        if not self.ticket_id:

            last_ticket = CustomerQuery.objects.all().order_by('id').last()

            if last_ticket:

                last_id = int(last_ticket.ticket_id[2:])

                new_id = last_id + 1

            else:

                new_id = 1

            self.ticket_id = f"MT{new_id:04d}"

        super().save(*args, **kwargs)

    # ====================================
    # SHOW IN ADMIN PANEL
    # ====================================

    def __str__(self):

        return f"{self.ticket_id} - {self.name}"  

class MaintenanceScope(models.Model):

    SCOPE_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]

    customer_query = models.OneToOneField(
        CustomerQuery,
        on_delete=models.CASCADE,
        related_name='scope_form'
    )

    # Prefilled Data
    email = models.EmailField(
        blank=True,
        null=True
    )

    uid = models.IntegerField(
        blank=True,
        null=True
    )

    case_id = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    customer_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    customer_contact = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    block = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    location = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    issue_related = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    issue_description = models.TextField(
        blank=True,
        null=True
    )

    # Scope Decision
    scope_status = models.CharField(
        max_length=10,
        choices=SCOPE_CHOICES
    )

    reason = models.TextField(
        blank=True,
        null=True
    )

    # ====================================
    # TIME
    # ====================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    @property
    def sla_due_time(self):
        return self.customer_query.created_at + timedelta(hours=3)

    @property
    def is_overdue(self):
        return timezone.now() > self.sla_due_time

    def __str__(self):
        return f"{self.case_id} - {self.scope_status}"
    

class SiteInspection(models.Model):

    CATEGORY_CHOICES = [
        ('Chargeable', 'Chargeable'),
        ('Non Chargeable', 'Non Chargeable'),
    ]

    YES_NO_VENDOR = [
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Vendor Side', 'Vendor Side'),
    ]

    YES_NO = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]

    unique_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer_query = models.OneToOneField(
        CustomerQuery,
        on_delete=models.CASCADE
    )

    engineer_email = models.EmailField()
    engineer_name = models.CharField(max_length=100)

    uid = models.IntegerField()
    case_id = models.CharField(max_length=50)

    customer_name = models.CharField(max_length=100)

    block = models.CharField(
        max_length=100
    )

    area = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    issue_found_remark = models.TextField()

    issue_found_area = models.TextField()

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )
    

    photo1 = models.ImageField(upload_to='inspection_photos/', blank=True, null=True)
    photo2 = models.ImageField(upload_to='inspection_photos/', blank=True, null=True)
    

    material_required = models.CharField(
        max_length=20,
        choices=YES_NO_VENDOR
    )

    details_of_material_required = models.TextField(
    blank=True,
    null=True
    
    )

    days_required = models.IntegerField()

    under_scope = models.CharField(
        max_length=10,
        choices=YES_NO
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def generate_unique_id(self):

        while True:

            code = ''.join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=8
                )
            )

            if not SiteInspection.objects.filter(
                unique_id=code
            ).exists():

                return code

    def save(self, *args, **kwargs):

        if not self.unique_id:

            self.unique_id = self.generate_unique_id()

        super().save(*args, **kwargs)

    def __str__(self):

        return f"{self.unique_id} - {self.case_id}"
    








class EstimateForm(models.Model):

    unique_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer_query = models.OneToOneField(
        CustomerQuery,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    your_name = models.CharField(
        max_length=100
    )

    uid = models.IntegerField()

    customer_name = models.CharField(
        max_length=100
    )

    contact_number = models.CharField(
        max_length=20
    )

    block = models.CharField(
        max_length=100
    )

    area = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    case_id = models.CharField(
        max_length=50
    )

    advance_amount_mentioned = models.CharField(
        max_length=3,
        choices=[
            ('Yes', 'Yes'),
            ('No', 'No')
        ]
    )

    invoice_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    proforma_invoice = models.FileField(
        upload_to='proforma_invoice/'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def generate_unique_id(self):

        while True:

            code = "EF" + ''.join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=10
                )
            )

            if not EstimateForm.objects.filter(
                unique_id=code
            ).exists():

                return code

    def save(self, *args, **kwargs):

        if not self.unique_id:

            self.unique_id = self.generate_unique_id()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.unique_id
    



#CustomerApproval

class CustomerApproval(models.Model):

    APPROVAL_CHOICES = [
        ('Approve', 'Approve'),
        ('Reject', 'Reject'),
    ]

    unique_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer_query = models.OneToOneField(
        CustomerQuery,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    uid = models.IntegerField()

    customer_name = models.CharField(
        max_length=100
    )

    block = models.CharField(
        max_length=100
    )

    area = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    case_id = models.CharField(
        max_length=50
    )

    approval_type = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES
    )

    customer_remark = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def generate_unique_id(self):

        while True:

            code = "CA" + ''.join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=10
                )
            )

            if not CustomerApproval.objects.filter(
                unique_id=code
            ).exists():

                return code

    def save(self, *args, **kwargs):

        if not self.unique_id:

            self.unique_id = self.generate_unique_id()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.unique_id
    


class AdvanceCollection(models.Model):

    unique_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer_query = models.OneToOneField(
        CustomerQuery,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    uid = models.IntegerField()

    customer_name = models.CharField(
        max_length=100
    )

    block = models.CharField(
        max_length=100
    )

    area = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    case_id = models.CharField(
        max_length=50
    )

    advance_collected = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    collected_by = models.CharField(
        max_length=100
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def generate_unique_id(self):

        while True:

            code = "AC" + ''.join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=10
                )
            )

            if not AdvanceCollection.objects.filter(
                unique_id=code
            ).exists():

                return code

    def save(self, *args, **kwargs):

        if not self.unique_id:

            self.unique_id = self.generate_unique_id()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.unique_id
    



class MaterialAvailability(models.Model):

    unique_id = models.CharField(max_length=20, unique=True, blank=True)

    customer_query = models.OneToOneField(
        CustomerQuery,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    uid = models.IntegerField()

    customer_name = models.CharField(max_length=100)

    block = models.CharField(max_length=100)

    area = models.CharField(max_length=100)

    case_id = models.CharField(max_length=50)

    material_available = models.CharField(
        max_length=10,
        choices=[
            ('Yes', 'Yes'),
            ('No', 'No')
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def generate_unique_id(self):

        while True:

            code = "MA" + ''.join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=10
                )
            )

            if not MaterialAvailability.objects.filter(
                unique_id=code
            ).exists():

                return code

    def save(self, *args, **kwargs):

        if not self.unique_id:

            self.unique_id = self.generate_unique_id()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.unique_id
    





class RaiseIndent(models.Model):

    unique_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer_query = models.OneToOneField(
        CustomerQuery,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    uid = models.IntegerField()

    customer_name = models.CharField(
        max_length=100
    )

    block = models.CharField(
        max_length=100
    )

    area = models.CharField(
        max_length=100
    )

    case_id = models.CharField(
        max_length=50
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def generate_unique_id(self):

        while True:

            code = "RI" + ''.join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=10
                )
            )

            if not RaiseIndent.objects.filter(
                unique_id=code
            ).exists():

                return code

    def save(self, *args, **kwargs):

        if not self.unique_id:

            self.unique_id = self.generate_unique_id()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.unique_id
    




class IssueMaterial(models.Model):

    unique_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer_query = models.OneToOneField(
        CustomerQuery,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    uid = models.IntegerField()

    customer_name = models.CharField(
        max_length=100
    )

    block = models.CharField(
        max_length=100
    )

    area = models.CharField(
        max_length=100
    )

    case_id = models.CharField(
        max_length=50
    )

    issued_by = models.CharField(
        max_length=100
    )

    issue_material_details = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def generate_unique_id(self):

        while True:

            code = "IM" + ''.join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=10
                )
            )

            if not IssueMaterial.objects.filter(
                unique_id=code
            ).exists():

                return code

    def save(self, *args, **kwargs):

        if not self.unique_id:

            self.unique_id = self.generate_unique_id()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.unique_id
    




class ReceiveMaterial(models.Model):

    unique_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer_query = models.OneToOneField(
        CustomerQuery,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    uid = models.IntegerField()

    customer_name = models.CharField(
        max_length=100
    )

    block = models.CharField(
        max_length=100
    )

    area = models.CharField(
        max_length=100
    )

    case_id = models.CharField(
        max_length=50
    )

    received_by = models.CharField(
        max_length=100
    )

    remark = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def generate_unique_id(self):

        while True:

            code = "RM" + ''.join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=10
                )
            )

            if not ReceiveMaterial.objects.filter(
                unique_id=code
            ).exists():

                return code

    def save(self, *args, **kwargs):

        if not self.unique_id:

            self.unique_id = self.generate_unique_id()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.unique_id
    



class QueryCloser(models.Model):

    unique_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer_query = models.OneToOneField(
        CustomerQuery,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    uid = models.IntegerField()

    contact_number = models.CharField(
        max_length=20
    )

    customer_name = models.CharField(
        max_length=100
    )

    block = models.CharField(
        max_length=100
    )

    area = models.CharField(
        max_length=100
    )

    case_id = models.CharField(
        max_length=50
    )

    solution_provided = models.TextField()

    closer_report = models.FileField(
        upload_to='closer_reports/'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def generate_unique_id(self):

        while True:

            code = "QC" + ''.join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=10
                )
            )

            if not QueryCloser.objects.filter(
                unique_id=code
            ).exists():

                return code

    def save(self, *args, **kwargs):

        if not self.unique_id:

            self.unique_id = self.generate_unique_id()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.unique_id
    




class CustomerFeedback(models.Model):

    unique_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    customer_query = models.OneToOneField(
        CustomerQuery,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    uid = models.IntegerField()

    customer_name = models.CharField(
        max_length=100
    )

    contact_number = models.CharField(
        max_length=20
    )

    block = models.CharField(
        max_length=100
    )

    area = models.CharField(
        max_length=100
    )

    case_id = models.CharField(
        max_length=50
    )

    issue_resolved = models.CharField(
        max_length=10,
        choices=[
            ('Yes', 'Yes'),
            ('No', 'No')
        ]
    )

    customer_remark = models.TextField()

    service_satisfied = models.CharField(
        max_length=10,
        choices=[
            ('Yes', 'Yes'),
            ('No', 'No')
        ]
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def generate_unique_id(self):

        while True:

            code = "CF" + ''.join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=10
                )
            )

            if not CustomerFeedback.objects.filter(
                unique_id=code
            ).exists():

                return code

    def save(self, *args, **kwargs):

        if not self.unique_id:

            self.unique_id = self.generate_unique_id()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.unique_id
    



class AdminUser(models.Model):

    ROLE_CHOICES = (
        ("Admin", "Admin"),
        ("CRM", "CRM"),
        ("Site Engineer", "Site Engineer"),
        ("Store Keeper", "Store Keeper"),
        ("Maintenance", "Maintenance"),
    )

    username = models.CharField(
        max_length=50,
        unique=True
    )

    full_name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        unique=True
    )

    password = models.CharField(
        max_length=255
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default="Admin"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):

        # Password ko hash karega
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)

        super().save(*args, **kwargs)

    def verify_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username




"""
================================================================
QC CHECKLIST MODULE — add these classes to your demo/models.py
================================================================
Follows the same conventions already used in this file:
  - unique_id generated via random letters+digits with a prefix
  - save() override to auto-generate unique_id on first save
  - AdminUser reused for who-did-what (filled_by, verified_by, etc.)
  - ImageField(upload_to='inspection_photos/') — same folder you
    already use for SiteInspection photos

STEP 0 — first, add these 4 new choices to your existing
AdminUser.ROLE_CHOICES (near the top of models.py):

    ROLE_CHOICES = (
        ("Admin", "Admin"),
        ("CRM", "CRM"),
        ("Site Engineer", "Site Engineer"),
        ("Store Keeper", "Store Keeper"),
        ("Maintenance", "Maintenance"),
        ("L1 Inspector", "L1 Inspector"),
        ("L2 Verifier", "L2 Verifier"),
        ("L3 PM", "L3 PM"),
        ("Viewer", "Viewer"),
    )

Then run: python manage.py makemigrations && python manage.py migrate

ALSO NEEDED (separate files, given alongside this one):
  - authentication.py — bridges request.session["admin_id"] into
    request.user for DRF, without touching login_view/AdminUser
  - permissions.py — DRF permission classes using request.user.role
    (now that authentication.py populates it)
  - settings.py — add REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
    pointing at demo.authentication.SessionAdminAuthentication
"""








# ---------------------------------------------------------------------------
# PROJECT / SITE HIERARCHY
# ---------------------------------------------------------------------------
class QCProject(models.Model):
    unique_id = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_unique_id(self):
        while True:
            code = "PRJ" + "".join(
                random.choices(string.ascii_letters + string.digits, k=8)
            )
            if not QCProject.objects.filter(unique_id=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = self.generate_unique_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unique_id} - {self.name}"


class QCSite(models.Model):
    """A tower/block/site within a project — e.g. Tower A, Tower B."""
    unique_id = models.CharField(max_length=20, unique=True, blank=True)
    project = models.ForeignKey(
        QCProject, on_delete=models.CASCADE, related_name="sites"
    )
    name = models.CharField(max_length=100)  # "Tower A"

    def generate_unique_id(self):
        while True:
            code = "SITE" + "".join(
                random.choices(string.ascii_letters + string.digits, k=8)
            )
            if not QCSite.objects.filter(unique_id=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = self.generate_unique_id()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ("project", "name")

    def __str__(self):
        return f"{self.project.name} - {self.name}"


# ---------------------------------------------------------------------------
# CHECKLIST TEMPLATES (master data, admin-configurable)
# ---------------------------------------------------------------------------
class ChecklistTemplate(models.Model):
    ACTIVITY_CHOICES = [
        ("Structural", "Structural / Concrete Work"),
        ("Plastering", "Plastering"),
        ("Waterproofing", "Waterproofing"),
        ("Tiling", "Tiling"),
        ("Electrical", "Electrical"),
        ("Plumbing", "Plumbing"),
        ("Painting", "Painting"),
        ("Finishing", "Other Finishing"),
    ]

    unique_id = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=150)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "AdminUser", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_unique_id(self):
        while True:
            code = "QCT" + "".join(
                random.choices(string.ascii_letters + string.digits, k=8)
            )
            if not ChecklistTemplate.objects.filter(unique_id=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = self.generate_unique_id()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ("name", "version")

    def __str__(self):
        return f"{self.name} v{self.version}"


class ChecklistTemplateItem(models.Model):
    STAGE_CHOICES = [
        ("General", "General Inspection"),
        ("In-Process", "In-Process Inspection"),
        ("Post-Install", "After Installation Inspection"),
    ]

    template = models.ForeignKey(
        ChecklistTemplate, on_delete=models.CASCADE, related_name="items"
    )
    sequence = models.PositiveIntegerField(default=0)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default="General")
    question = models.CharField(max_length=300)
    requires_photo = models.BooleanField(default=True)
    requires_note = models.BooleanField(default=False)

    class Meta:
        ordering = ["sequence"]

    def __str__(self):
        return self.question


# ---------------------------------------------------------------------------
# CHECKLIST INSTANCES (filled on-site by L1)
# ---------------------------------------------------------------------------
class ChecklistInstance(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Process", "In Process"),
        ("Passed", "Passed"),
        ("Failed", "Failed"),
        ("Re-confirmation Required", "Re-confirmation Required"),
        ("Re-confirmed", "Re-confirmed & Approved"),
    ]

    unique_id = models.CharField(max_length=20, unique=True, blank=True)
    # client_uuid: generated on the phone/browser at creation time — lets the
    # offline-sync JS retry a failed upload without ever creating a duplicate
    client_uuid = models.CharField(max_length=64, unique=True, null=True, blank=True)

    template = models.ForeignKey(ChecklistTemplate, on_delete=models.PROTECT)
    template_version = models.PositiveIntegerField()  # snapshot, so a later
    # template edit never changes the meaning of an already-filled checklist
    project = models.ForeignKey(QCProject, on_delete=models.PROTECT)
    site = models.ForeignKey(QCSite, on_delete=models.PROTECT)

    filled_by = models.ForeignKey(
        "AdminUser", on_delete=models.PROTECT, related_name="qc_filled"
    )
    verified_by = models.ForeignKey(
        "AdminUser", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="qc_verified"
    )
    audited_by = models.ForeignKey(
        "AdminUser", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="qc_audited"
    )

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Pending")
    filled_at_device_time = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def generate_unique_id(self):
        while True:
            code = "QCI" + "".join(
                random.choices(string.ascii_letters + string.digits, k=8)
            )
            if not ChecklistInstance.objects.filter(unique_id=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = self.generate_unique_id()
        if not self.template_version and self.template_id:
            self.template_version = self.template.version
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unique_id} - {self.template.name} [{self.status}]"


class ChecklistItemResult(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Passed", "Passed"),
        ("Failed", "Failed"),
        ("NA", "Not Applicable"),
    ]

    instance = models.ForeignKey(
        ChecklistInstance, on_delete=models.CASCADE, related_name="item_results"
    )
    template_item = models.ForeignKey(ChecklistTemplateItem, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")
    note = models.TextField(blank=True, null=True)

    # same convention as SiteInspection — two photo slots, same media folder
    photo1 = models.ImageField(upload_to="inspection_photos/", blank=True, null=True)
    photo2 = models.ImageField(upload_to="inspection_photos/", blank=True, null=True)

    verified_by = models.ForeignKey(
        "AdminUser", on_delete=models.SET_NULL, null=True, blank=True
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("instance", "template_item")

    def __str__(self):
        return f"{self.template_item.question} - {self.status}"


# ---------------------------------------------------------------------------
# ISSUES (raised only by L2 during verify, or L3 during audit — never L1)
# ---------------------------------------------------------------------------
class QCIssue(models.Model):
    SOURCE_CHOICES = [
        ("verification", "Raised during L2 verification"),
        ("audit", "Raised during L3 audit"),
    ]
    STATUS_CHOICES = [
        ("Open", "Open"),
        ("In Correction", "Correction In Progress"),
        ("Re-inspection", "Resolved - Pending Re-check"),
        ("Closed", "Closed"),
    ]

    unique_id = models.CharField(max_length=20, unique=True, blank=True)
    checklist_item_result = models.ForeignKey(
        ChecklistItemResult, on_delete=models.CASCADE, related_name="issues"
    )
    raised_by = models.ForeignKey(
        "AdminUser", on_delete=models.PROTECT, related_name="qc_issues_raised"
    )
    assigned_to = models.ForeignKey(
        "AdminUser", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="qc_issues_assigned"
    )
    source = models.CharField(max_length=15, choices=SOURCE_CHOICES)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="Open")
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def generate_unique_id(self):
        while True:
            code = "ISS" + "".join(
                random.choices(string.ascii_letters + string.digits, k=8)
            )
            if not QCIssue.objects.filter(unique_id=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = self.generate_unique_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unique_id} - {self.status}"


# ---------------------------------------------------------------------------
# AUDIT LOG (every verify/reconfirm/audit action, for L3 compliance)
# ---------------------------------------------------------------------------
class QCAuditLog(models.Model):
    user = models.ForeignKey("AdminUser", on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    object_type = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    old_value = models.CharField(max_length=100, blank=True)
    new_value = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["object_type", "object_id"])]

    def __str__(self):
        return f"{self.action} on {self.object_type}#{self.object_id}"
    



