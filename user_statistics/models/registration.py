import datetime
from datetime import timedelta
from operator import itemgetter

from django.db import models
from django.conf import settings


class UserRegistration(models.Model):

    user_name = models.CharField(
        max_length=80, db_column="user_name", null=False)
    creation_time = models.DateTimeField(
        db_column="term", null=False)

    def __unicode__(self):
        return self.user_name + '(' + self.id + ')'

    class Meta:
        ordering = ["creation_time"]
        app_label = 'user_statistics'
        db_table = 'user_statistics_registration'
        managed = False if not settings.TEST_MODE else True

    @classmethod
    def history(cls):
        # Null dates will not be counted.
        history = UserRegistration.objects.exclude(creation_time__isnull=True)
        # Invalid dates (e.g. 0000-00-00 00:00:00) will not be counted.
        history = [history_item for history_item in history
                   if history_item.creation_time]
        history_items = []
        for record in history:
            item = {}
            item['user_name'] = record.user_name
            item['creation_time'] = record.creation_time.strftime(
                '%Y-%m-%d %H:%M:%S')
            history_items.append(item)
        return history_items

    @classmethod
    def frequency(cls):
        # Null dates will not be counted.
        history = UserRegistration.objects.exclude(creation_time__isnull=True)
        # Invalid dates (e.g. 0000-00-00 00:00:00) will not be counted.
        history = [history_item for history_item in history
                   if history_item.creation_time]

        # Build a sequence of dates covering the date range in question.
        # history is ordered by creation time so first
        # and last date should give range.
        first = history[0]
        last = history[len(history) - 1]
        first_date = first.creation_time.date()
        last_date = last.creation_time.date()
        known_dates = dict()
        date = first_date
        while date <= last_date:
            known_dates[date] = 0
            date += datetime.timedelta(days=1)

        # Bin the registration date-times by day.
        for record in history:
            creation_time = record.creation_time
            date = creation_time.date()
            if date not in known_dates:
                # Should not get here.
                known_dates[date] = 0
            known_dates[date] += 1

        # Restructure the data so it can be sent in JSON formated string.
        frequency_items = []
        for date in known_dates:
            item = {'date': date, 'count': known_dates[date]}
            frequency_items.append(item)
        # Data were stored in dictionary so not necessarily
        # sorted by date, so resort by date.
        frequency_items = sorted(
            frequency_items, key=itemgetter('date'))
        return frequency_items

    @classmethod
    def monthly_frequency(cls):
        daily_registrations = cls.frequency()
        first = daily_registrations[0]
        last = daily_registrations[len(daily_registrations) - 1]
        first_date = first['date']
        last_date = last['date']
        first_month = datetime.date(first_date.year, first_date.month, 1)
        last_month = datetime.date(last_date.year, last_date.month, 1)
        end_of_last_month = UserRegistration.last_date_of_month(last_month)
        if last_date != end_of_last_month:
            last_month = (last_month - timedelta(days=1)).replace(day=1)
        known_months = dict()
        date = first_month
        # Build bins as a map.
        while date <= last_month:
            known_months[date] = 0
            date = (date + timedelta(days=31)).replace(day=1)
        # Populate bins
        for registration in daily_registrations:
            day_date = registration['date']
            day_count = registration['count']
            month = datetime.date(day_date.year, day_date.month, 1)
            if month in known_months:
                known_months[month] += day_count
        monthly_registrations = []
        # Reorganise bins into a date sorted array.
        for month in known_months:
            item = {'date': month, 'count': known_months[month]}
            monthly_registrations.append(item)

        monthly_registrations = sorted(
            monthly_registrations, key=itemgetter('date'))
        return monthly_registrations

    @classmethod
    def mid_month(cls, date):
        begin_month_date = datetime.date(date.year, date.month, 1)
        end_month_date = (date + timedelta(days=31)).replace(day=1)
        end_month_date += datetime.timedelta(days=-1)
        middle_day = (end_month_date.day + begin_month_date.day) / 2
        return datetime.date(date.year, date.month, middle_day)

    @classmethod
    def last_date_of_month(cls, date):
        return (date + timedelta(days=31)).replace(day=1) - timedelta(days=1)

    @classmethod
    def user_dict(cls):
        # Null dates will not be counted.
        pairs = UserRegistration.objects.exclude(creation_time__isnull=True)
        # Invalid dates (e.g. 0000-00-00 00:00:00) will not be counted.
        pairs = [pair for pair in pairs if pair.creation_time]
        code_map = {}
        for pair in pairs:
            key = pair.user_name
            value = pair.creation_time.strftime('%Y-%m-%d %H:%M:%S')
            code_map[key] = value
        return code_map
