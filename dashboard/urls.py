
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
    path("engineering-leave-dashboard/", views.engineering_leave_dashboard, name="engineering_leave_dashboard")


    
]
    
    
