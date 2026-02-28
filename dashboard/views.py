from django.shortcuts import render

def dashboard(request):

    context = {
        "total": 20,
        "open": 5,
        "closed": 10,
        "urgent": 2,
        "tickets": [
            {
                "no": 1,
                "name": "Printer Issue",
                "department": "IT",
                "priority": "High",
                "status": "Open",
                "date": "2026-02-28"
            }
        ]
    }

    return render(request, "dashboard.html", context)