from django.contrib.auth import mixins
from django.core.exceptions import BadRequest
from django import shortcuts
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.edit import CreateView

from langstroth.outages import filters
from langstroth.outages import forms
from langstroth.outages import models


# Expected state transitions for each Outage status code
STATUS_TRANSITIONS = {
    True: {   # Scheduled outage transitions
        models.STARTED: models.PROGRESSING,
        models.PROGRESSING: models.PROGRESSING,
        models.COMPLETED: models.PROGRESSING   # reopen
    },
    False: {   # Unscheduled outage transitions
        models.INVESTIGATING: models.IDENTIFIED,
        models.IDENTIFIED: models.PROGRESSING,
        models.PROGRESSING: models.FIXED,
        models.FIXED: models.RESOLVED,
        models.RESOLVED: models.PROGRESSING    # reopen
    }
}


def index_page(request):
    f = filters.OutageFilters(
        request.GET,
        is_staff=request.user.is_staff,
        queryset=models.Outage.objects.filter(deleted=False))
    context = {
        "title": "Service Announcements",
        "tagline": "",
        "filter": f
    }
    return shortcuts.render(request, "outages/list.html", context)


class BaseDetailView(DetailView):
    title = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class BaseCreateView(mixins.UserPassesTestMixin,
                     mixins.AccessMixin,
                     CreateView):
    title = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def test_func(self):
        return self.request.user.is_staff


class OutageDetailView(BaseDetailView):
    queryset = models.Outage.objects.filter(deleted=False)
    template_name = "outages/detail.html"
    title = "Announcement Details"


class BaseOutageCreateView(BaseCreateView):
    model = models.Outage

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('outages:detail', args=[self.object.id])


class CreateScheduledView(BaseOutageCreateView):
    """Create a scheduled outage.
    """

    form_class = forms.ScheduledOutageForm
    template_name = "outages/scheduled.html"
    title = "Create Scheduled Announcement"
    initial = {'scheduled': True}


class CreateUnscheduledView(BaseOutageCreateView):
    """Create an unscheduled outage.
    """

    form_class = forms.UnscheduledOutageForm
    template_name = "outages/unscheduled.html"
    title = "Create Unscheduled Announcement"
    initial = {'scheduled': False}


class BaseUpdateCreateView(BaseCreateView):
    model = models.OutageUpdate
    form_class = forms.OutageUpdateForm
    title = "Outage Announcement Update"

    def setup(self, request, *args, **kwargs):
        self.pk = kwargs.pop('pk')
        return super().setup(request, *args, **kwargs)

    def get(self, request, **kwargs):
        self.check_state()
        return super().get(request, **kwargs)

    def post(self, request, **kwargs):
        self.check_state()
        return super().post(request, **kwargs)

    def get_outage(self):
        return models.Outage.objects.exclude(deleted=True).get(pk=self.pk)

    def form_valid(self, form):
        form.instance.outage = self.get_outage()
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def check_state(self):
        pass


class UpdateOutageView(BaseUpdateCreateView):
    """Create an outage update.
    """

    template_name = "outages/add_update.html"

    def get_success_url(self):
        return reverse('outages:detail', args=[self.pk])

    def get_initial(self):
        outage = self.get_outage()
        latest = outage.latest_update
        transitions = STATUS_TRANSITIONS[outage.scheduled]
        return {
            "outage": outage,
            "time": timezone.now(),
            "status": transitions[latest.status],
            "severity": latest.severity
        }

    def check_state(self):
        outage = self.get_outage()
        if not outage.start:
            raise BadRequest(f"Outage {self.pk} in wrong state for update.")


class StartOutageView(BaseUpdateCreateView):
    """Start a scheduled or unsheduled outage.
    """

    template_name = "outages/start.html"

    def get_success_url(self):
        return reverse('outages:detail', args=[self.pk])

    def get_form_class(self):
        outage = self.get_outage()
        if not outage.start:
            # This allows the operator to adjust the start time
            # when starting an outage (for the first time)
            return forms.OutageStartForm
        else:
            return forms.OutageUpdateForm

    def get_initial(self):
        outage = self.get_outage()
        return {
            "outage": outage,
            # For the (first) start of a scheduled outage, we will
            # use the scheduled start time
            "time": (outage.scheduled_start
                     if (outage.scheduled and not outage.start)
                     else timezone.now()),
            "content": ("Scheduled outage started."
                        if outage.scheduled else ""),
            "status": (models.STARTED if outage.scheduled
                       else models.INVESTIGATING),
            "severity": outage.scheduled_severity
        }

    def check_state(self):
        outage = self.get_outage()
        if outage.cancelled or outage.start:
            raise BadRequest(f"Outage {self.pk} in wrong state to start.")


class EndOutageView(BaseUpdateCreateView):
    """End an outage that is in progress.
    """

    template_name = "outages/end.html"
    title = "Outage Announcement Update"

    def get_success_url(self):
        return reverse('outages:detail', args=[self.pk])

    def get_initial(self):
        outage = self.get_outage()
        return {
            "outage": outage,
            "time": timezone.now(),
            "content": ("Scheduled outage completed."
                        if outage.scheduled
                        else "Unscheduled outage resolved."),
            "status": (models.COMPLETED if outage.scheduled
                       else models.RESOLVED),
            "severity": outage.latest_update.severity
        }

    def check_state(self):
        outage = self.get_outage()
        last = outage.latest_update
        if not last or last.status in {models.RESOLVED, models.COMPLETED}:
            raise BadRequest(f"Outage {self.pk} in wrong state to end.")


class CancelOutageView(mixins.UserPassesTestMixin,
                       mixins.AccessMixin,
                       BaseDetailView):
    """Cancel a previously scheduled outage.
    """

    queryset = models.Outage.objects.filter(deleted=False)
    template_name = "outages/cancel.html"
    title = "Confirm Cancellation"

    def get(self, request, **kwargs):
        self._check_state()
        return super().get(request, **kwargs)

    def post(self, request, **kwargs):
        outage = self._check_state()
        outage.cancelled = True
        outage.save()
        return shortcuts.redirect(reverse('outages:list'))

    def _check_state(self):
        outage = self.get_object()
        if outage.cancelled or outage.start or not outage.scheduled:
            raise BadRequest("Outage is in wrong state to cancel.")
        return outage

    def test_func(self):
        return self.request.user.is_staff
