from json import dumps
from django.views.decorators.cache import cache_page
from django.http import HttpResponse, Http404
from django.shortcuts import render
from nectar_allocations.models.forcode import ForCode
from nectar_allocations.models.allocation import AllocationRequest
from services import project_details


# Web pages


def index_page(request):
    return allocation_visualisation_page(request)


def allocation_visualisation_page(request):
    context = {
        "title": "Allocations",
        "tagline": ""}
    return render(request, "allocation_visualisation.html", context)


def project_details_page(request, allocation_request_id):
    allocation_dict = AllocationRequest \
        .project_from_request_id(allocation_request_id)

    context = {
        "title": allocation_dict['project_description'].replace('_', ' '),
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

@cache_page(60 * 60 * 24)
def allocation_tree(request):
    allocation_dict = AllocationRequest.restructure_allocations_tree()
    json_string = dumps(allocation_dict)
    return HttpResponse(json_string, "application/json")


def project_summary(request, allocation_request_id):
    try:
        allocation_dict = AllocationRequest \
            .project_from_request_id(allocation_request_id)
    except AllocationRequest.DoesNotExist:
        raise Http404("Allocation does not Exist")
    tenancy_id = allocation_dict['project_id']
    usages = project_details.find_current_project_resource_usage(tenancy_id)
    for usage in usages:
        if usage['target'] == 'instance_count':
            allocation_dict['used_instances'] = usage['datapoints'][0][0]
        elif usage['target'] == 'core_count':
            allocation_dict['used_cores'] = usage['datapoints'][0][0]

    json_string = dumps(allocation_dict)
    return HttpResponse(json_string, "application/json")


def project_allocations(request, allocation_request_id):
    allocation_list = AllocationRequest \
        .get_all_for_project(allocation_request_id)
    json_string = dumps(allocation_list)
    return HttpResponse(json_string, "application/json")
