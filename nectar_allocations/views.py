from json import dumps
from django.http import HttpResponse
from django.shortcuts import render
from nectar_allocations.models.forcode import ForCode
from nectar_allocations.models.allocation import AllocationRequest

# Web pages

def index_page(request):
    return allocation_visualisation_page(request)

def allocation_visualisation_page(request):
    context = {
        "title": "Allocations",
        "tagline": ""}
    return render(request, "allocation_visualisation.html", context)

def project_details_page(request, allocation_request_id):
    context = {
        "title": "Project Details",
        "tagline": "",
        "allocation_request_id": allocation_request_id}
    return render(request, "project_details.html", context)

def project_allocations_page(request, allocation_request_id):
    context = {
        "title": "Project Allocations",
        "tagline": "",
        "allocation_request_id": allocation_request_id}
    return render(request, "project_allocations.html", context)


# Web services with JSON pay loads.

def for_codes(request):
    code_dict = ForCode.code_dict()
    json_string = dumps(code_dict)
    return HttpResponse(json_string, "application/json")

def allocation_tree(request):
    allocation_dict = AllocationRequest.restructure_allocations_tree()
    json_string = dumps(allocation_dict)
    return HttpResponse(json_string, "application/json")

def project_summary(request, allocation_request_id):
    allocation_dict = AllocationRequest.project_from_allocation_request_id(allocation_request_id)
    json_string = dumps(allocation_dict)
    return HttpResponse(json_string, "application/json")

def project_allocations(request, allocation_request_id):
    allocation_list = AllocationRequest.project_allocations_from_allocation_request_id(allocation_request_id)
    json_string = dumps(allocation_list)
    return HttpResponse(json_string, "application/json")
   
