from django.shortcuts import render

def home(request):

    tickets = [
        {"no":"TCKT-486B8036","name":"vijay","department":"JNRDME","priority":"Normal","status":"Closed","date":"30 Jan 2026"},
        {"no":"TCKT-D70E2285","name":"namita","department":"JNRDME","priority":"Urgent","status":"Closed","date":"29 Jan 2026"},
    ]

    context = {
        "total": 28,
        "open": 16,
        "closed": 6,
        "urgent": 22,
        "tickets": tickets
    }

    return render(request, "dashboard/dashboard.html", context)