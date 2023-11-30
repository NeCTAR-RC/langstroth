import datetime
from django.db import models as db_models
from django import forms
from django.utils import timezone
import django_filters

from langstroth.outages import models


def _latest_update_status(queryset):
    """Annotate queryset with the status of the outage's latest update.
    """

    status = models.OutageUpdate.objects \
            .filter(outage=db_models.OuterRef('pk')) \
            .order_by('-time', '-id')[:1].values('status')
    return queryset.annotate(
        latest_update_status=db_models.Subquery(status))


def _first_update_time(queryset):
    """Annotate queryset with the time of the outage's first update.
    """

    time = models.OutageUpdate.objects \
            .filter(outage=db_models.OuterRef('pk')) \
            .order_by('time', 'id')[:1].values('time')
    return queryset.annotate(
        first_update_time=db_models.Subquery(time))


class ActivityFilterMixin():
    """Implements filtering on the notional activity of an outage.
       The filter predicates are:
           'active' => started but not ended
           'completed' => ended
           'overrunning' => started but not ended after scheduled end
           'upcoming' => scheduled in future and not started
           'overdue' => scheduled for now and not started
           'missed' => scheduled in past and never started
    """

    def filter_activity(self, queryset, name, value):
        if value == "active":
            return _latest_update_status(queryset) \
                .exclude(latest_update_status__in=
                         [models.COMPLETED, models.RESOLVED])
        elif value == "completed":
            return _latest_update_status(queryset) \
                .filter(latest_update_status__in=
                        [models.COMPLETED, models.RESOLVED])
        elif value == "overrunning":
            return _latest_update_status(queryset) \
                .exclude(latest_update_status__in=
                         [models.COMPLETED, models.RESOLVED]) \
                .exclude(scheduled_end__gt=timezone.now())

        elif value == "upcoming":
            return queryset.filter(scheduled=True, cancelled=False,
                                   scheduled_start__gt=timezone.now()) \
                           .annotate(count=db_models.Count('updates')) \
                           .filter(count=0)
        elif value == "overdue":
            return queryset.filter(scheduled=True, cancelled=False,
                                   scheduled_start__lte=timezone.now(),
                                   scheduled_end__gt=timezone.now()) \
                           .annotate(count=db_models.Count('updates')) \
                           .filter(count=0)
        elif value == "missed":
            return queryset.filter(scheduled=True, cancelled=False,
                                   scheduled_end__lte=timezone.now()) \
                           .annotate(count=db_models.Count('updates')) \
                           .filter(count=0)
        else:
            # Noop
            return queryset


class ChoiceFilter(django_filters.ChoiceFilter):
    def __init__(self, *args, **kwargs,):
        super().__init__(*args, **kwargs,
                         empty_label=None, null_label=None,
                         initial='all')
        self.extra['choices'] = kwargs.pop('choices')
        self.extra['widget'] = forms.widgets.Select(
            attrs={'class': 'form-select form-select-sm'})


class ActivityFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, method='filter_activity',
                         choices=[
                             ('all', 'All'),
                             ('active', 'Current'),
                             ('completed', 'Completed'),
                             ('overrunning', 'Overrunning'),
                             ('upcoming', 'Upcoming'),
                             ('overdue', 'Overdue'),
                             ('missed', 'Missed'),
                         ])

    def remove_staff_choices(self):
        self.extra['choices'] = filter(
            lambda c: c[0] not in {'missed', 'overdue', 'overrunning'},
            self.extra['choices'])


class TimeWindowFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, method='filter_time_window',
                         choices=[
                             ('all', 'All time'),
                             ('1m', 'Since 1 month ago'),
                             ('6m', 'Since 6 months ago'),
                             ('1y', 'Since 1 year ago')
                         ])


class OrderingFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, method='filter_start_ordering',
                         choices=[
                             ('default', 'Default'),
                             ('reverse', 'Default (reverse)'),
                             # ('start', 'Start time'),
                             # ('-start', 'Start time (descending)'),
                         ])


class CustomRadioSelect(forms.widgets.RadioSelect):
    option_template_name = 'outages/widgets/radio_option.html'
    template_name = 'outages/widgets/radio.html'


class CustomBooleanFilter(django_filters.BooleanFilter):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super().__init__(*args, **kwargs,
                         widget=CustomRadioSelect(choices=choices))


class OutageFilters(django_filters.FilterSet, ActivityFilterMixin):
    activity = ActivityFilter(label='Activity')
    time_window = TimeWindowFilter(label='Time window')
    ordering = OrderingFilter(label='Time ordering')
    scheduled = CustomBooleanFilter(label='Scheduled',
                                    choices=[(True, "Scheduled"),
                                             (False, "Unscheduled"),
                                             (None, "Both")])
    cancelled = CustomBooleanFilter(label='Cancelled',
                                    choices=[(True, "Yes"),
                                             (False, "No"),
                                             (None, "Both")])

    class Meta:
        model = models.Outage
        fields = []

    def __init__(self, *args, **kwargs):
        is_staff = kwargs.pop('is_staff', False)
        super().__init__(*args, **kwargs)
        if not is_staff:
            self.filters['activity'].remove_staff_choices()

    def _range_filter(self, queryset, days):
        date_time = timezone.now() - datetime.timedelta(days=days)
        queryset = queryset.filter(
            db_models.Q(scheduled_start__isnull=True)
            | db_models.Q(scheduled_start__gte=date_time)
            | db_models.Q(scheduled_end__isnull=True)
            | db_models.Q(scheduled_end__gte=date_time)
            | db_models.Q(updates__time__gte=date_time))
        return queryset.distinct()

    def filter_time_window(self, queryset, name, value):
        if value == '1m':
            return self._range_filter(queryset, 30)
        elif value == '6m':
            return self._range_filter(queryset, 180)
        elif value == '1y':
            return self._range_filter(queryset, 365)
        else:
            return queryset

    def filter_start_ordering(self, queryset, name, value):
        # These don't work properly.  For example, 'start' orders all
        # scheduled outages before unscheduled, irrespective of the
        # unscheduled's start dates.  It is to do with NULL's ...
        #
        # if value == 'start':
        #     return _first_update_time(queryset) \
        #         .order_by('first_update_time', 'scheduled_start')
        # elif value == '-start':
        #     return _first_update_time(queryset) \
        #        .order_by('first_update_time', 'scheduled_start') \
        #        .reverse()

        if value == 'reverse':
            return queryset.order_by('-pk')
        else:
            return queryset.order_by('pk')
