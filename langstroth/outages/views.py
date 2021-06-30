from django.shortcuts import render
from django.views.generic import DetailView

from langstroth.outages import models


def index_page(request):
    context = {
        "title": "Service Announcements",
        "tagline": "",
        "outages": list(models.Outage.objects.filter(deleted=False))
    }
    return render(request, "outage_list.html", context)


class OutageDetailView(DetailView):
    queryset = models.Outage.objects.filter(deleted=False)
    template_name = "outage_detail.html"
