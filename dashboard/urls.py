
#aap url
from django.urls import path
from . import views
from .views import export_leave_csv



urlpatterns = [
    #path('', views.dashboard, name='dashboard'),
   # path("", views.ticket_form, name="home"),   # 👈 Ye line change karo
    #path("dashboard/", views.dashboard, name="dashboard"),
    #path("raise-ticket/", views.raise_ticket, name="raise_ticket"),
    #path("", views.dashboard, name="home"),
    path("", views.dashboard, name="home"),   # homepage
    path("raise-ticket/", views.raise_ticket, name="raise_ticket"),
    path("resolve-ticket/<str:ticket_no>/", views.resolve_ticket, name="resolve_ticket"),
    path('leave/',views.leave_form),
   
    
    path("dme-dashboard/", views.dme_dashboard, name="dme_dashboard"),
    path("leave-csv/", export_leave_csv, name="leave_csv"),
    path("jrdme-dashboard/", views.jrdme_dashboard, name="jrdme_dashboard"),
    path("accounts-dashboard/", views.accounts_dashboard, name="accounts_dashboard"),
    path("review/<str:leave_id>/", views.review_leave, name="review_leave"),
    path("leave-admin/", views.leave_admin_dashboard, name="leave_admin_dashboard"),
    path("finance-leave-dashboard/", views.finance_leave_dashboard, name="finance_leave_dashboard"),
    path("engineering-leave-dashboard/", views.engineering_leave_dashboard, name="engineering_leave_dashboard"),
    path("dme-leave/", views.dme_leave, name="dme_leave"),
    path("hr-admin-leave/", views.hr_admin_leave_dashboard, name="hr_admin_leave_dashboard"),
    path("purchase-leave/", views.purchase_leave_dashboard, name="purchase_leave_dashboard"),
    path("sales-leave/", views.sales_leave_dashboard, name="sales_leave_dashboard"),
    path("mdo-leave/", views.mdo_leave_dashboard, name="mdo_leave_dashboard"),
    path("mdo-sales-leave/", views.mdo_sales_leave_dashboard, name="mdo_sales_leave_dashboard"),
    path("construction-dashboard/", views.construction_dashboard, name="construction_dashboard"),
    path("crm-ho-dashboard/", views.crm_ho_dashboard, name="crm_ho_dashboard"),
    path("hr-dashboard/", views.hr_dashboard, name="hr_dashboard"),
    path("it-admin-dashboard/", views.it_admin_dashboard, name="it_admin_dashboard"),
    path("project-planning-dashboard/", views.project_planning_dashboard, name="project_planning_dashboard"),
    path("purchase-security-dashboard/", views.purchase_security_dashboard, name="purchase_security_dashboard"),
    path("customer-form/", views.customer_query_form, name="customer_form"),
    path('maintenance-scope/<int:query_id>/', views.maintenance_scope_form, name='maintenance_scope_form'),
    path('site-inspection/<int:query_id>/', views.site_inspection_form, name='site_inspection_form'),
    path('estimate-form/<int:query_id>/', views.estimate_form, name='estimate_form'),
    path('customer-approval/<int:query_id>/', views.customer_approval_form, name='customer_approval_form'),
    path('advance-collection/<int:query_id>/', views.advance_collection_form, name='advance_collection_form'),
    path('material-availability/<int:query_id>/', views.material_availability_form, name='material_availability_form'),
    path('raise-indent/<int:query_id>/', views.raise_indent_form, name='raise_indent_form'),
    path('issue-material/<int:query_id>/', views.issue_material_form, name='issue_material_form'),
    path('receive-material/<int:query_id>/', views.receive_material_form, name='receive_material_form'),
    path('query-closer/<int:query_id>/', views.query_closer_form, name='query_closer_form'),





    
]
    

