from datetime import timedelta

from django import test
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from icalendar import Calendar

from langstroth.announcements import models
from langstroth import models as auth_models


def _make_outage(user, **overrides):
    defaults = {
        "title": "t",
        "description": "d",
        "start": timezone.now() + timedelta(hours=2),
        "severity": models.SIGNIFICANT,
        "created_by": user,
    }
    defaults.update(overrides)
    return models.Announcement.objects.create(**defaults)


class ListAndDetailTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )
        cls.outage1 = _make_outage(cls.user, title="one")
        cls.outage2 = _make_outage(
            cls.user, title="two", start=timezone.now() - timedelta(hours=1)
        )

    def test_list(self):
        response = self.client.get(reverse('announcements:list'))
        self.assertEqual(response.status_code, 200)

    def test_list_staff(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('announcements:list'))
        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        response = self.client.get(self.outage1.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_list_query_count_bounded(self):
        # Prefetch on the list view means status_display / latest_update
        # do not issue per-row queries. Add another outage with several
        # updates, then assert the query count is independent of how
        # many updates exist -- an N+1 regression would scale with
        # outage_count * update_count.
        outage = _make_outage(
            self.user,
            title="busy",
            start=timezone.now() - timedelta(hours=2),
        )
        for i in range(5):
            models.AnnouncementUpdate.objects.create(
                outage=outage,
                time=timezone.now() - timedelta(minutes=10 - i),
                status=models.INVESTIGATING,
                content=f"update {i}",
                created_by=self.user,
            )
        # 1 COUNT(*) (Paginator.count, cached) + 1 page-slice SELECT +
        # 1 prefetched updates = 3. If this number drifts upward
        # without an explanation, an N+1 has probably been
        # reintroduced.
        with self.assertNumQueries(3):
            response = self.client.get(reverse('announcements:list'))
        self.assertEqual(response.status_code, 200)


class CreateOutageTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )
        cls.enduser = auth_models.User.objects.create(
            username="end", email="end@test.com"
        )

    def test_get_requires_staff(self):
        self.client.force_login(self.enduser)
        response = self.client.get(reverse('announcements:create'))
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('announcements:create'))
        self.assertEqual(response.status_code, 200)

    def test_post_future_start(self):
        self.client.force_login(self.staff)
        future = timezone.now() + timedelta(days=1)
        planned_end = future + timedelta(hours=2)
        response = self.client.post(
            reverse('announcements:create'),
            data={
                "title": "Maintenance",
                "description": "Routine",
                "start": future.strftime("%Y-%m-%dT%H:%M:%S"),
                "severity": models.SIGNIFICANT,
                "planned_end": planned_end.strftime("%Y-%m-%dT%H:%M:%S"),
                "status": "",
                "content": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        outage = models.Announcement.objects.get(title="Maintenance")
        self.assertTrue(outage.scheduled)
        self.assertEqual(0, outage.updates.count())

    def test_post_now_start_with_update(self):
        self.client.force_login(self.staff)
        now = timezone.now()
        response = self.client.post(
            reverse('announcements:create'),
            data={
                "title": "Broken",
                "description": "Down",
                "start": now.strftime("%Y-%m-%dT%H:%M:%S"),
                "severity": models.SEVERE,
                "planned_end": "",
                "status": models.INVESTIGATING,
                "content": "Outage detected",
            },
        )
        self.assertEqual(response.status_code, 302)
        outage = models.Announcement.objects.get(title="Broken")
        self.assertFalse(outage.scheduled)
        self.assertEqual(1, outage.updates.count())


class UpdateAndEndFlowTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )

    def setUp(self):
        self.client.force_login(self.staff)
        # An in-progress outage (start in the past, no end).
        self.outage = _make_outage(
            self.staff, start=timezone.now() - timedelta(hours=1)
        )

    def _add_update(self, status=models.INVESTIGATING):
        return models.AnnouncementUpdate.objects.create(
            outage=self.outage,
            time=timezone.now(),
            status=status,
            content="x",
            created_by=self.staff,
        )

    def _assert_bad_request(self, response):
        self.assertTemplateUsed(response, "error.html")

    def test_add_update_get(self):
        response = self.client.get(
            reverse('announcements:add_update', args=[self.outage.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_add_update_blocked_when_not_started(self):
        future = _make_outage(
            self.staff, start=timezone.now() + timedelta(hours=2)
        )
        response = self.client.get(
            reverse('announcements:add_update', args=[future.id])
        )
        self._assert_bad_request(response)

    def test_add_update_blocked_when_cancelled(self):
        future = _make_outage(
            self.staff, start=timezone.now() + timedelta(hours=2)
        )
        future.cancelled = True
        future.save()
        response = self.client.get(
            reverse('announcements:add_update', args=[future.id])
        )
        self._assert_bad_request(response)

    def test_add_update_post(self):
        response = self.client.post(
            reverse('announcements:add_update', args=[self.outage.id]),
            data={
                "time": timezone.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "status": models.INVESTIGATING,
                "content": "looking into it",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(1, self.outage.updates.count())

    def test_reopen_clears_end(self):
        # Mark the outage as ended.
        self.outage.end = timezone.now()
        self.outage.save()
        self._add_update(status=models.RESOLVED)

        response = self.client.post(
            reverse('announcements:add_update', args=[self.outage.id]),
            data={
                "time": timezone.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "status": models.PROGRESSING,
                "content": "back open",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.outage.refresh_from_db()
        self.assertIsNone(self.outage.end)

    def test_end_get(self):
        response = self.client.get(
            reverse('announcements:end', args=[self.outage.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_end_blocked_when_already_ended(self):
        self.outage.end = timezone.now()
        self.outage.save()
        response = self.client.get(
            reverse('announcements:end', args=[self.outage.id])
        )
        self._assert_bad_request(response)

    def test_end_blocked_when_not_started(self):
        future = _make_outage(
            self.staff, start=timezone.now() + timedelta(hours=2)
        )
        response = self.client.get(
            reverse('announcements:end', args=[future.id])
        )
        self._assert_bad_request(response)

    def test_end_blocked_when_cancelled(self):
        self.outage.cancelled = True
        self.outage.save()
        response = self.client.get(
            reverse('announcements:end', args=[self.outage.id])
        )
        self._assert_bad_request(response)

    def test_end_post_sets_end_field(self):
        response = self.client.post(
            reverse('announcements:end', args=[self.outage.id]),
            data={"content": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.outage.refresh_from_db()
        self.assertIsNotNone(self.outage.end)
        self.assertEqual(0, self.outage.updates.count())

    def test_end_post_with_final_note_creates_resolved_update(self):
        response = self.client.post(
            reverse('announcements:end', args=[self.outage.id]),
            data={"content": "all clear"},
        )
        self.assertEqual(response.status_code, 302)
        self.outage.refresh_from_db()
        self.assertIsNotNone(self.outage.end)
        self.assertEqual(1, self.outage.updates.count())
        update = self.outage.updates.first()
        self.assertEqual(models.RESOLVED, update.status)
        self.assertEqual("all clear", update.content)


class CancelOutageTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )

    def setUp(self):
        self.client.force_login(self.staff)
        self.future = _make_outage(
            self.staff, start=timezone.now() + timedelta(hours=2)
        )

    def test_cancel_get(self):
        response = self.client.get(
            reverse('announcements:cancel', args=[self.future.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_cancel_post(self):
        response = self.client.post(
            reverse('announcements:cancel', args=[self.future.id])
        )
        self.assertEqual(response.status_code, 302)
        self.future.refresh_from_db()
        self.assertTrue(self.future.cancelled)

    def test_cancel_blocked_once_started(self):
        started = _make_outage(
            self.staff, start=timezone.now() - timedelta(minutes=1)
        )
        response = self.client.get(
            reverse('announcements:cancel', args=[started.id])
        )
        self.assertTemplateUsed(response, "error.html")

    def test_cancel_blocked_when_already_cancelled(self):
        self.future.cancelled = True
        self.future.save()
        response = self.client.get(
            reverse('announcements:cancel', args=[self.future.id])
        )
        self.assertTemplateUsed(response, "error.html")


@freeze_time("2024-01-15 12:00:00")
class FilterTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )
        # Three outages to exercise activity choices.
        cls.upcoming = _make_outage(
            cls.staff,
            title="future",
            start=timezone.now() + timedelta(days=1),
        )
        cls.active = _make_outage(
            cls.staff,
            title="now",
            start=timezone.now() - timedelta(hours=1),
        )
        cls.completed = _make_outage(
            cls.staff,
            title="done",
            start=timezone.now() - timedelta(days=1),
            end=timezone.now() - timedelta(hours=2),
        )

    def test_filter_time_window_1m(self):
        response = self.client.get(
            reverse('announcements:list'), {'time_window': '1m'}
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_time_window_6m(self):
        response = self.client.get(
            reverse('announcements:list'), {'time_window': '6m'}
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_time_window_1y(self):
        response = self.client.get(
            reverse('announcements:list'), {'time_window': '1y'}
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_ordering_reverse(self):
        response = self.client.get(
            reverse('announcements:list'), {'ordering': 'reverse'}
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_activity_upcoming(self):
        response = self.client.get(
            reverse('announcements:list'), {'activity': 'upcoming'}
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_activity_active(self):
        response = self.client.get(
            reverse('announcements:list'), {'activity': 'active'}
        )
        self.assertEqual(response.status_code, 200)

    def test_filter_activity_completed(self):
        response = self.client.get(
            reverse('announcements:list'), {'activity': 'completed'}
        )
        self.assertEqual(response.status_code, 200)


class CalendarTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="cal", email="cal@test.com", is_superuser=True
        )
        cls.scheduled = _make_outage(
            cls.user,
            title="Scheduled maintenance",
            description="Planned work",
            start=timezone.now() + timedelta(days=1),
            planned_end=timezone.now() + timedelta(days=1, hours=2),
        )
        cls.completed = _make_outage(
            cls.user,
            title="Resolved outage",
            description="It broke",
            start=timezone.now() - timedelta(days=1),
            end=timezone.now() - timedelta(hours=20),
        )
        models.AnnouncementUpdate.objects.create(
            outage=cls.completed,
            time=timezone.now() - timedelta(hours=22),
            status=models.INVESTIGATING,
            content="Looking into it",
            created_by=cls.user,
        )

    def _get_calendar(self):
        response = self.client.get(reverse('announcements:calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'], 'text/calendar; charset=utf-8'
        )
        return Calendar.from_ical(response.content)

    def test_calendar_is_public(self):
        # No authentication required.
        response = self.client.get(reverse('announcements:calendar'))
        self.assertEqual(response.status_code, 200)

    def test_calendar_lists_all_outages(self):
        cal = self._get_calendar()
        events = [c for c in cal.walk('VEVENT')]
        self.assertEqual(len(events), 2)
        summaries = {str(e['summary']) for e in events}
        self.assertEqual(
            summaries, {"Scheduled maintenance", "Resolved outage"}
        )

    def test_event_uids_are_stable(self):
        cal = self._get_calendar()
        uids = {str(e['uid']) for e in cal.walk('VEVENT')}
        self.assertIn(f'outage-{self.scheduled.pk}@rc.nectar.org.au', uids)
        self.assertIn(f'outage-{self.completed.pk}@rc.nectar.org.au', uids)

    def _event_by_title(self, cal, title):
        for event in cal.walk('VEVENT'):
            if str(event['summary']) == title:
                return event
        self.fail(f"no event titled {title!r}")

    def test_scheduled_uses_planned_end_for_dtend(self):
        cal = self._get_calendar()
        event = self._event_by_title(cal, "Scheduled maintenance")
        # iCalendar DATE-TIME has second resolution, so compare without
        # the microseconds carried on the model's DateTimeField.
        self.assertEqual(
            event.decoded('dtend'),
            self.scheduled.planned_end.replace(microsecond=0),
        )
        self.assertEqual(str(event['status']), 'CONFIRMED')

    def test_completed_uses_end_for_dtend(self):
        cal = self._get_calendar()
        event = self._event_by_title(cal, "Resolved outage")
        self.assertEqual(
            event.decoded('dtend'),
            self.completed.end.replace(microsecond=0),
        )

    def test_description_includes_updates(self):
        cal = self._get_calendar()
        event = self._event_by_title(cal, "Resolved outage")
        description = str(event['description'])
        self.assertIn("It broke", description)
        self.assertIn("Looking into it", description)

    def test_cancelled_outage_marked_cancelled(self):
        self.scheduled.cancelled = True
        self.scheduled.save()
        cal = self._get_calendar()
        event = self._event_by_title(cal, "Scheduled maintenance")
        self.assertEqual(str(event['status']), 'CANCELLED')

    def test_event_url_is_absolute(self):
        cal = self._get_calendar()
        event = self._event_by_title(cal, "Scheduled maintenance")
        self.assertIn(self.scheduled.get_absolute_url(), str(event['url']))

    def test_outages_older_than_12_months_excluded(self):
        # Started just over a year ago: outside the feed window.
        _make_outage(
            self.user,
            title="Ancient history",
            start=timezone.now() - timedelta(days=366),
            end=timezone.now() - timedelta(days=366) + timedelta(hours=1),
        )
        cal = self._get_calendar()
        summaries = {str(e['summary']) for e in cal.walk('VEVENT')}
        self.assertNotIn("Ancient history", summaries)
        # The recent outages are still present.
        self.assertIn("Scheduled maintenance", summaries)
        self.assertIn("Resolved outage", summaries)


class OldUrlRedirectTests(test.TestCase):
    """The web pages moved /outages/... -> /announcements/...

    Deployed dashboards link to /outages/<pk>/ (OUTAGE_BASE_URL) and
    calendar clients subscribe to /outages/calendar.ics, so the old
    paths must permanently redirect.
    """

    def test_list_redirects(self):
        response = self.client.get('/outages/')
        self.assertEqual(301, response.status_code)
        self.assertEqual('/announcements/', response['Location'])

    def test_detail_redirects(self):
        response = self.client.get('/outages/42/')
        self.assertEqual(301, response.status_code)
        self.assertEqual('/announcements/42/', response['Location'])

    def test_calendar_redirects(self):
        response = self.client.get('/outages/calendar.ics')
        self.assertEqual(301, response.status_code)
        self.assertEqual('/announcements/calendar.ics', response['Location'])

    def test_query_string_preserved(self):
        response = self.client.get('/outages/?activity=active')
        self.assertEqual(301, response.status_code)
        self.assertEqual(
            '/announcements/?activity=active', response['Location']
        )


class CalendarCategoryTests(test.TestCase):
    """News is not a calendar event; notices are."""

    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="cal-cat", email="cal-cat@test"
        )

    def test_calendar_excludes_news_includes_notices(self):
        _make_outage(self.user, title="An outage", start=timezone.now())
        _make_outage(
            self.user,
            title="A notice",
            category=models.Category.NOTICE,
            start=timezone.now(),
        )
        _make_outage(
            self.user,
            title="Some news",
            category=models.Category.NEWS,
            severity=None,
            start=timezone.now(),
        )
        response = self.client.get(reverse('announcements:calendar'))
        cal = Calendar.from_ical(response.content)
        summaries = {str(e['summary']) for e in cal.walk('VEVENT')}
        self.assertIn("An outage", summaries)
        self.assertIn("A notice", summaries)
        self.assertNotIn("Some news", summaries)


class CreateNoticeAndNewsTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )
        cls.enduser = auth_models.User.objects.create(
            username="end", email="end@test.com"
        )

    def test_get_requires_staff(self):
        self.client.force_login(self.enduser)
        for name in ('create_notice', 'create_news'):
            response = self.client.get(reverse(f'announcements:{name}'))
            self.assertEqual(response.status_code, 403)

    def test_get(self):
        self.client.force_login(self.staff)
        for name in ('create_notice', 'create_news'):
            response = self.client.get(reverse(f'announcements:{name}'))
            self.assertEqual(response.status_code, 200)

    def test_post_notice_starting_now_without_initial_update(self):
        # Unlike an outage, a notice may start immediately with just
        # its description, and needs no planned end.
        self.client.force_login(self.staff)
        now = timezone.now()
        response = self.client.post(
            reverse('announcements:create_notice'),
            data={
                "title": "CVE-2026-0001",
                "description": "Patch your instances",
                "start": now.strftime("%Y-%m-%dT%H:%M:%S"),
                "severity": models.SEVERE,
                "planned_end": "",
                "status": "",
                "content": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        notice = models.Announcement.objects.get(title="CVE-2026-0001")
        self.assertEqual(models.Category.NOTICE, notice.category)
        self.assertEqual(models.SEVERE, notice.severity)
        self.assertEqual(self.staff, notice.created_by)
        self.assertEqual(0, notice.updates.count())

    def test_post_future_notice_without_planned_end(self):
        self.client.force_login(self.staff)
        future = timezone.now() + timedelta(days=1)
        response = self.client.post(
            reverse('announcements:create_notice'),
            data={
                "title": "Heatwave",
                "description": "DC cooling at risk",
                "start": future.strftime("%Y-%m-%dT%H:%M:%S"),
                "severity": models.SIGNIFICANT,
                "planned_end": "",
                "status": "",
                "content": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        notice = models.Announcement.objects.get(title="Heatwave")
        self.assertEqual(models.Category.NOTICE, notice.category)

    def test_post_news(self):
        self.client.force_login(self.staff)
        now = timezone.now()
        response = self.client.post(
            reverse('announcements:create_news'),
            data={
                "title": "New flavors available",
                "description": "Bigger and better",
                "start": now.strftime("%Y-%m-%dT%H:%M:%S"),
            },
        )
        self.assertEqual(response.status_code, 302)
        news = models.Announcement.objects.get(title="New flavors available")
        self.assertEqual(models.Category.NEWS, news.category)
        self.assertIsNone(news.severity)
        self.assertIsNone(news.planned_end)
        self.assertEqual(self.staff, news.created_by)
        self.assertEqual("Published", news.status_display)


class NewsLifecycleGuardTests(test.TestCase):
    """News is lifecycle-free: update/end/cancel must all refuse it."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )

    def setUp(self):
        self.client.force_login(self.staff)
        self.news = _make_outage(
            self.staff,
            title="Some news",
            category=models.Category.NEWS,
            severity=None,
            start=timezone.now() - timedelta(hours=1),
        )

    def _assert_bad_request(self, response):
        self.assertTemplateUsed(response, "error.html")

    def test_add_update_refused(self):
        response = self.client.get(
            reverse('announcements:add_update', args=[self.news.id])
        )
        self._assert_bad_request(response)

    def test_add_update_post_refused(self):
        response = self.client.post(
            reverse('announcements:add_update', args=[self.news.id]),
            data={
                "time": timezone.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "status": models.INVESTIGATING,
                "content": "nope",
            },
        )
        self._assert_bad_request(response)
        self.assertEqual(0, self.news.updates.count())

    def test_end_refused(self):
        response = self.client.get(
            reverse('announcements:end', args=[self.news.id])
        )
        self._assert_bad_request(response)
        response = self.client.post(
            reverse('announcements:end', args=[self.news.id]), data={}
        )
        self._assert_bad_request(response)
        self.news.refresh_from_db()
        self.assertIsNone(self.news.end)

    def test_cancel_refused_even_for_future_news(self):
        future_news = _make_outage(
            self.staff,
            title="Scheduled post",
            category=models.Category.NEWS,
            severity=None,
            start=timezone.now() + timedelta(hours=2),
        )
        response = self.client.get(
            reverse('announcements:cancel', args=[future_news.id])
        )
        self._assert_bad_request(response)

    def test_news_detail_renders_without_lifecycle_ui(self):
        response = self.client.get(self.news.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published:")
        self.assertNotContains(response, 'id="update"')
        self.assertNotContains(response, 'id="end"')
        self.assertNotContains(response, 'id="cancel"')
        self.assertNotContains(response, "<h2>Updates</h2>", html=False)
        # Admin edit stays available to staff.
        self.assertContains(response, 'id="edit"')


class NoticeLifecycleTests(test.TestCase):
    """A notice reuses the outage lifecycle: updates and End work."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )

    def setUp(self):
        self.client.force_login(self.staff)
        self.notice = _make_outage(
            self.staff,
            title="A hazard",
            category=models.Category.NOTICE,
            start=timezone.now() - timedelta(hours=1),
        )

    def test_add_update(self):
        response = self.client.post(
            reverse('announcements:add_update', args=[self.notice.id]),
            data={
                "time": timezone.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "status": models.INVESTIGATING,
                "content": "assessing",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(1, self.notice.updates.count())

    def test_end_page_uses_notice_wording(self):
        response = self.client.get(
            reverse('announcements:end', args=[self.notice.id])
        )
        self.assertContains(response, "End this notice")
        self.assertContains(response, "End Notice")
        self.assertNotContains(response, "End this outage")

    def test_end_stands_down_the_notice(self):
        response = self.client.post(
            reverse('announcements:end', args=[self.notice.id]), data={}
        )
        self.assertEqual(response.status_code, 302)
        self.notice.refresh_from_db()
        self.assertIsNotNone(self.notice.end)


class ListCategoryFilterTests(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="filt", email="filt@test.com"
        )
        _make_outage(cls.user, title="an outage")
        _make_outage(
            cls.user, title="a notice", category=models.Category.NOTICE
        )
        _make_outage(
            cls.user,
            title="some news",
            category=models.Category.NEWS,
            severity=None,
            # Published: _make_outage's default start is in the
            # future, which would be an embargoed scheduled post.
            start=timezone.now() - timedelta(hours=1),
        )

    def _titles(self, params=None):
        response = self.client.get(reverse('announcements:list'), params or {})
        return {o.title for o in response.context['filter'].qs}

    def test_all_categories_by_default(self):
        self.assertEqual(
            {"an outage", "a notice", "some news"}, self._titles()
        )

    def test_category_filter(self):
        self.assertEqual({"an outage"}, self._titles({'category': 'outage'}))
        self.assertEqual({"a notice"}, self._titles({'category': 'notice'}))
        self.assertEqual({"some news"}, self._titles({'category': 'news'}))


class ListPaginationTests(test.TestCase):
    PAGE_SIZE = 20

    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="pager", email="pager@test.com"
        )
        for i in range(cls.PAGE_SIZE + 1):
            _make_outage(cls.user, title=f"outage {i:02d}")

    def _get(self, params=None):
        return self.client.get(reverse('announcements:list'), params or {})

    def test_first_page_holds_page_size_items(self):
        response = self._get()
        page = response.context['page_obj']
        self.assertEqual(self.PAGE_SIZE, len(page.object_list))
        self.assertTrue(page.has_next())
        self.assertContains(
            response,
            f"Showing 1&ndash;{self.PAGE_SIZE} of "
            f"{self.PAGE_SIZE + 1} announcements.",
        )

    def test_second_page_holds_remainder(self):
        response = self._get({'page': '2'})
        page = response.context['page_obj']
        self.assertEqual(1, len(page.object_list))
        self.assertFalse(page.has_next())

    def test_numeric_page_buttons(self):
        # The ARDC theme styles page links as fixed 35px squares, so
        # the controls are numeric buttons plus chevrons -- never
        # longer labels like "Previous".
        response = self._get()
        self.assertContains(
            response,
            '<li class="page-item active" aria-current="page">'
            '<span class="page-link">1</span></li>',
            html=True,
        )
        self.assertContains(response, 'href="?page=2"')
        self.assertContains(response, "&laquo;")
        self.assertContains(response, "&raquo;")
        self.assertNotContains(response, ">Previous<")

    def test_out_of_range_page_falls_back_to_last(self):
        response = self._get({'page': '999'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, response.context['page_obj'].number)

    def test_invalid_page_falls_back_to_first(self):
        response = self._get({'page': 'bogus'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.context['page_obj'].number)

    def test_pagination_links_preserve_filters(self):
        response = self._get({'activity': 'upcoming'})
        self.assertContains(response, "activity=upcoming&amp;page=2")

    def test_empty_state(self):
        response = self._get({'time_window': '1m', 'activity': 'completed'})
        self.assertContains(response, "No announcements match these filters.")


class NewsEmbargoAndRetractionTests(test.TestCase):
    """Scheduled (future-start) news is embargoed on every public
    surface until its publish time; retracted (cancelled) news is
    visibly labelled.
    """

    @classmethod
    def setUpTestData(cls):
        cls.staff = auth_models.User.objects.create(
            username="staff", email="staff@test.com", is_staff=True
        )
        cls.embargoed = _make_outage(
            cls.staff,
            title="Embargoed feature news",
            category=models.Category.NEWS,
            severity=None,
            start=timezone.now() + timedelta(days=2),
        )
        cls.retracted = _make_outage(
            cls.staff,
            title="Retracted news",
            category=models.Category.NEWS,
            severity=None,
            start=timezone.now() - timedelta(days=1),
            cancelled=True,
        )

    def test_archive_hides_embargoed_news(self):
        response = self.client.get(reverse('announcements:list'))
        self.assertNotContains(response, "Embargoed feature news")

    def test_detail_404s_embargoed_news_for_public(self):
        response = self.client.get(self.embargoed.get_absolute_url())
        self.assertEqual(404, response.status_code)

    def test_detail_serves_embargoed_news_to_staff(self):
        # The create flow redirects to the detail page, so staff must
        # be able to preview scheduled news.
        self.client.force_login(self.staff)
        response = self.client.get(self.embargoed.get_absolute_url())
        self.assertEqual(200, response.status_code)

    def test_upcoming_outages_and_notices_unaffected_by_embargo(self):
        upcoming = _make_outage(
            self.staff,
            title="Upcoming maintenance",
            start=timezone.now() + timedelta(days=1),
        )
        response = self.client.get(reverse('announcements:list'))
        self.assertContains(response, upcoming.title)

    def test_retracted_news_is_labelled(self):
        response = self.client.get(self.retracted.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "(Retracted)")
        list_response = self.client.get(reverse('announcements:list'))
        self.assertContains(list_response, "(Retracted)")
