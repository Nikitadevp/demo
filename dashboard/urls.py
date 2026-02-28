
#aap url
from django.urls import path
from . import views

urlpatterns = [
    #path('', views.dashboard, name='dashboard'),
    path("", views.ticket_form, name="home"),   # 👈 Ye line change karo
    path("dashboard/", views.dashboard, name="dashboard"),
    path("raise-ticket/", views.raise_ticket, name="raise_ticket"),
   
]