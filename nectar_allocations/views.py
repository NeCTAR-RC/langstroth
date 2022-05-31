from django.conf import settings
from django.shortcuts import render


def index_page(request):
    context = {
        "title": "Allocations",
        "tagline": "",
        "allocation_url": settings.ALLOCATION_API_URL,
        "forcode_series": settings.FOR_CODE_SERIES,
    }
    print (context)
    return render(request, "allocation_visualisation.html", context)


def project_details_page(request, allocation_request_id):
    context = {
        "title": 'Allocation: %s' % allocation_request_id,
        "tagline": "",
        "allocation_url": settings.ALLOCATION_API_URL,
        "forcode_series": settings.FOR_CODE_SERIES,
        "allocation_request_id": allocation_request_id}
    return render(request, "project_details.html", context)
