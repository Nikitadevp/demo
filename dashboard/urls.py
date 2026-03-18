
#aap url
from django.urls import path
from . import views

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
   
    path('review/<int:id>/', views.review_leave, name='review_leave'),
    
    
]