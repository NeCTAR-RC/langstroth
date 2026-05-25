import datetime

from django.db import models as db_models
from django import forms
from django.utils import timezone
import django_filters

from langstroth.outages import models


class ActivityFilterMixin:
    """Filter outages by their notional activity.

    Predicates:
        'active'    => has started, not ended, not cancelled
        'completed' => `end` is set
        'upcoming'  => has not yet started, not cancelled
    """

    def filter_activity(self, queryset, name, value):
        now = timezone.now()
        if value == "active":
            return queryset.filter(
                start__lte=now, end__isnull=True, cancelled=False
            )
        if value == "completed":
            return queryset.filter(end__isnull=False)
        if value == "upcoming":
            return queryset.filter(start__gt=now, cancelled=False)
        return queryset


class ChoiceFilter(django_filters.ChoiceFilter):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args, **kwargs, empty_label=None, null_label=None, initial='all'
        )
        self.extra['choices'] = kwargs.pop('choices')
        self.extra['widget'] = forms.widgets.Select(
            attrs={'class': 'form-select form-select-sm'}
        )


class ActivityFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            method='filter_activity',
            choices=[
                ('all', 'All'),
                ('active', 'Current'),
                ('completed', 'Completed'),
                ('upcoming', 'Upcoming'),
            ],
        )


class TimeWindowFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            method='filter_time_window',
            choices=[
                ('all', 'All time'),
                ('1m', 'Since 1 month ago'),
                ('6m', 'Since 6 months ago'),
                ('1y', 'Since 1 year ago'),
            ],
        )


class OrderingFilter(ChoiceFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            method='filter_start_ordering',
            choices=[
                ('default', 'Default'),
                ('reverse', 'Default (reverse)'),
            ],
        )


class CustomRadioSelect(forms.widgets.RadioSelect):
    option_template_name = 'outages/widgets/radio_option.html'
    template_name = 'outages/widgets/radio.html'


class CustomBooleanFilter(django_filters.BooleanFilter):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super().__init__(
            *args, **kwargs, widget=CustomRadioSelect(choices=choices)
        )


class OutageFilters(django_filters.FilterSet, ActivityFilterMixin):
    activity = ActivityFilter(label='Activity')
    time_window = TimeWindowFilter(label='Time window')
    ordering = OrderingFilter(label='Time ordering')
    scheduled = CustomBooleanFilter(
        label='Type',
        choices=[(True, "Scheduled"), (False, "Unscheduled"), (None, "Both")],
    )
    cancelled = CustomBooleanFilter(
        label='Cancelled',
        choices=[(True, "Yes"), (False, "No"), (None, "Both")],
    )

    class Meta:
        model = models.Outage
        fields = []

    def __init__(self, *args, **kwargs):
        kwargs.pop('is_staff', False)
        super().__init__(*args, **kwargs)

    def _range_filter(self, queryset, days):
        date_time = timezone.now() - datetime.timedelta(days=days)
        return queryset.filter(
            db_models.Q(start__gte=date_time)
            | db_models.Q(end__gte=date_time)
            | db_models.Q(updates__time__gte=date_time)
        ).distinct()

    def filter_time_window(self, queryset, name, value):
        if value == '1m':
            return self._range_filter(queryset, 30)
        if value == '6m':
            return self._range_filter(queryset, 180)
        if value == '1y':
            return self._range_filter(queryset, 365)
        return queryset

    def filter_start_ordering(self, queryset, name, value):
        if value == 'reverse':
            return queryset.order_by('-pk')
        return queryset.order_by('pk')
