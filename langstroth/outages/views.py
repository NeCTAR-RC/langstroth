from django.contrib.auth import mixins
from django.core.exceptions import BadRequest
from django import shortcuts
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, FormView

from langstroth.outages import filters
from langstroth.outages import forms
from langstroth.outages import models


def index_page(request):
    f = filters.OutageFilters(
        request.GET,
        is_staff=request.user.is_staff,
        queryset=models.Outage.objects.all(),
    )
    context = {"title": "Service Announcements", "tagline": "", "filter": f}
    return shortcuts.render(request, "outages/list.html", context)


class BaseDetailView(DetailView):
    title = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context


class BaseCreateView(
    mixins.UserPassesTestMixin, mixins.AccessMixin, CreateView
):
    title = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def test_func(self):
        return self.request.user.is_staff


class OutageDetailView(BaseDetailView):
    queryset = models.Outage.objects.all()
    template_name = "outages/detail.html"
    title = "Announcement Details"


class OutageCreateView(BaseCreateView):
    """Create an outage announcement.

    Whether the outage is "scheduled" or "unscheduled" is decided from
    the submitted start time -- there is no separate workflow.
    """

    model = models.Outage
    form_class = forms.OutageForm
    template_name = "outages/create.html"
    title = "Create Outage Announcement"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('outages:detail', args=[self.object.id])


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
        return models.Outage.objects.get(pk=self.pk)

    def form_valid(self, form):
        form.instance.outage = self.get_outage()
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def check_state(self):
        pass


class UpdateOutageView(BaseUpdateCreateView):
    """Add an update to an outage that is in progress."""

    template_name = "outages/add_update.html"

    def get_success_url(self):
        return reverse('outages:detail', args=[self.pk])

    def get_initial(self):
        outage = self.get_outage()
        latest = outage.latest_update
        if latest is None:
            next_status = models.INVESTIGATING
        else:
            # Stay on the current status if there's no defined
            # progression (e.g. FIXED -- the operator should end the
            # outage rather than pick another update status).
            next_status = models.STATUS_TRANSITIONS.get(
                latest.status, latest.status
            )
        return {
            "outage": outage,
            "time": timezone.now(),
            "status": next_status,
        }

    def form_valid(self, form):
        outage = self.get_outage()
        # If the operator is reopening a resolved outage, clear `end`.
        if (
            form.cleaned_data.get('status') == models.PROGRESSING
            and outage.end
        ):
            outage.end = None
            outage.save()
        return super().form_valid(form)

    def check_state(self):
        outage = self.get_outage()
        if outage.cancelled or outage.start > timezone.now():
            raise BadRequest(f"Outage {self.pk} in wrong state for update.")


class EndOutageView(mixins.UserPassesTestMixin, mixins.AccessMixin, FormView):
    """End an in-progress outage by stamping `outage.end`."""

    template_name = "outages/end.html"
    form_class = forms.OutageEndForm
    title = "End Outage Announcement"

    def setup(self, request, *args, **kwargs):
        self.pk = kwargs.pop('pk')
        return super().setup(request, *args, **kwargs)

    def get(self, request, **kwargs):
        self.check_state()
        return super().get(request, **kwargs)

    def post(self, request, **kwargs):
        self.check_state()
        return super().post(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['outage'] = self.get_outage()
        return context

    def get_success_url(self):
        return reverse('outages:detail', args=[self.pk])

    def get_outage(self):
        return models.Outage.objects.get(pk=self.pk)

    def form_valid(self, form):
        outage = self.get_outage()
        now = timezone.now()
        outage.end = now
        outage.modified_by = self.request.user
        outage.save()
        content = form.cleaned_data.get('content')
        if content:
            models.OutageUpdate.objects.create(
                outage=outage,
                time=now,
                status=models.RESOLVED,
                content=content,
                created_by=self.request.user,
            )
        return super().form_valid(form)

    def check_state(self):
        outage = self.get_outage()
        if (
            outage.cancelled
            or outage.end is not None
            or outage.start > timezone.now()
        ):
            raise BadRequest(f"Outage {self.pk} in wrong state to end.")

    def test_func(self):
        return self.request.user.is_staff


class CancelOutageView(
    mixins.UserPassesTestMixin, mixins.AccessMixin, BaseDetailView
):
    """Cancel an outage that has not yet started."""

    queryset = models.Outage.objects.all()
    template_name = "outages/cancel.html"
    title = "Confirm Cancellation"

    def get(self, request, **kwargs):
        self._check_state()
        return super().get(request, **kwargs)

    def post(self, request, **kwargs):
        outage = self._check_state()
        outage.cancelled = True
        outage.modified_by = self.request.user
        outage.save()
        return shortcuts.redirect(reverse('outages:list'))

    def _check_state(self):
        outage = self.get_object()
        if outage.cancelled or outage.start <= timezone.now():
            raise BadRequest("Outage is in wrong state to cancel.")
        return outage

    def test_func(self):
        return self.request.user.is_staff
