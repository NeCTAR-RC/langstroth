from json import dumps
from django.http import HttpResponse
from django.shortcuts import render
from nectar_allocations.models.forcode import ForCode
from nectar_allocations.models.allocation import AllocationRequest


def index(request):
    return allocation_visualisation(request)

def allocation_visualisation(request):
    context = {
        "title": "Allocations",
        "tagline": ""}
    return render(request, "allocation_visualisation.html", context)

def for_codes(request):
    code_dict = ForCode.code_dict()
    json_string = dumps(code_dict)
    return HttpResponse(json_string, "application/json")

def allocation_tree(request):
    allocation_dict = AllocationRequest.restructure_allocations_tree()
    json_string = dumps(allocation_dict)
    return HttpResponse(json_string, "application/json")
   
