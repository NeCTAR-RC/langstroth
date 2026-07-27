from datetime import timedelta
import json

from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status
from rest_framework import test

from langstroth.announcements import models
from langstroth import models as auth_models


@freeze_time("2012-01-14 14:32:24")
class OutageSimpleTestCase(test.APITestCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )

        # Outage starting now (unscheduled) with no updates.
        self.one = models.Announcement.objects.create(
            title="one",
            description="Outage one",
            start=timezone.now(),
            severity=models.SIGNIFICANT,
            created_by=self.user,
        )

        # Outage with one investigating update.
        self.two = models.Announcement.objects.create(
            title="two",
            description="Outage two",
            start=timezone.now(),
            severity=models.SEVERE,
            created_by=self.user,
        )
        models.AnnouncementUpdate.objects.create(
            outage=self.two,
            status=models.INVESTIGATING,
            content="update one",
            time=timezone.now(),
            created_by=self.user,
        )

        self.expected = [
            {
                'scheduled': False,
                'scheduled_display': 'unscheduled',
                'cancelled': False,
                'title': "one",
                'description': "Outage one",
                'end': None,
                'planned_end': None,
                'id': self.one.id,
                'severity': models.SIGNIFICANT,
                'severity_display': 'Significant',
                'scheduled_start': '2012-01-14T14:32:24+0000',
                'scheduled_end': None,
                'scheduled_severity': models.SIGNIFICANT,
                'start': '2012-01-14T14:32:24+0000',
                'status_display': 'In progress',
                'updates': [],
            },
            {
                'scheduled': False,
                'scheduled_display': 'unscheduled',
                'cancelled': False,
                'title': "two",
                'description': "Outage two",
                'end': None,
                'planned_end': None,
                'id': self.two.id,
                'severity': models.SEVERE,
                'severity_display': 'Severe',
                'scheduled_start': '2012-01-14T14:32:24+0000',
                'scheduled_end': None,
                'scheduled_severity': models.SEVERE,
                'start': '2012-01-14T14:32:24+0000',
                'status_display': 'Investigating',
                'updates': [
                    {
                        'content': 'update one',
                        'status': models.INVESTIGATING,
                        'severity': models.SEVERE,
                        'time': '2012-01-14T14:32:24+0000',
                    }
                ],
            },
        ]

    def test_get_unknown(self):
        response = self.client.get("/api/v1/outages/999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_known(self):
        self.maxDiff = 1000
        response = self.client.get(f"/api/v1/outages/{self.one.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), self.expected[0])
        response = self.client.get(f"/api/v1/outages/{self.two.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), self.expected[1])

    def test_get_known_redirect(self):
        response = self.client.get(f"/api/v1/outages/{self.one.id}")
        self.assertEqual(
            response.status_code, status.HTTP_301_MOVED_PERMANENTLY
        )
        self.assertEqual(
            response.headers["Location"], f"/api/v1/outages/{self.one.id}/"
        )

    def test_get_all(self):
        self.maxDiff = 1000
        response = self.client.get("/api/v1/outages/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'], self.expected)

    def test_get_filtered_cancelled(self):
        response = self.client.get("/api/v1/outages/?cancelled=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 0)

    def test_get_filtered_severity(self):
        response = self.client.get(
            f"/api/v1/outages/?severity={models.SEVERE}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['id'], self.two.id)


class OutageFilterTestCase(test.APITestCase):
    """Activity filter behaviour after the refactor.

    Only active / completed / upcoming remain.
    """

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.user = auth_models.User.objects.create(
            username="test", email="test@test.com", is_superuser=True
        )

        now = timezone.now()

        # Active: started, no end.
        self.active = models.Announcement.objects.create(
            title="active",
            description="d",
            start=now - timedelta(hours=1),
            severity=models.SEVERE,
            created_by=self.user,
        )

        # Completed: end set.
        self.completed = models.Announcement.objects.create(
            title="completed",
            description="d",
            start=now - timedelta(days=1),
            end=now - timedelta(hours=2),
            severity=models.SEVERE,
            created_by=self.user,
        )

        # Upcoming: future start.
        self.upcoming = models.Announcement.objects.create(
            title="upcoming",
            description="d",
            start=now + timedelta(days=1),
            severity=models.SEVERE,
            created_by=self.user,
        )

    def test_filter_active(self):
        self._check_activity("active", {self.active.id})

    def test_filter_completed(self):
        self._check_activity("completed", {self.completed.id})

    def test_filter_upcoming(self):
        self._check_activity("upcoming", {self.upcoming.id})

    def test_filter_unknown_returns_all(self):
        self._check_activity(
            "all", {self.active.id, self.completed.id, self.upcoming.id}
        )

    def _check_activity(self, activity, expected_ids):
        response = self.client.get(f"/api/v1/outages/?activity={activity}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual({d['id'] for d in data['results']}, expected_ids)


class OutageFilterLookupTestCase(test.APITestCase):
    """Exercise the `start`/`end`/`planned_end`/`severity` lookup filters
    declared in OutageFilter.Meta.fields (lt/lte/gte/gt/date/in)."""

    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="filter-test",
            email="filter@test.com",
            is_superuser=True,
        )
        cls.now = timezone.now().replace(microsecond=0)
        # past: started a week ago, ended two days ago, severe.
        cls.past = models.Announcement.objects.create(
            title="past",
            description="d",
            start=cls.now - timedelta(days=7),
            end=cls.now - timedelta(days=2),
            severity=models.SEVERE,
            created_by=cls.user,
        )
        # active: started yesterday, no end, significant.
        cls.active = models.Announcement.objects.create(
            title="active",
            description="d",
            start=cls.now - timedelta(days=1),
            severity=models.SIGNIFICANT,
            created_by=cls.user,
        )
        # future: starts tomorrow, planned 2h window, minimal.
        cls.future = models.Announcement.objects.create(
            title="future",
            description="d",
            start=cls.now + timedelta(days=1),
            planned_end=cls.now + timedelta(days=1, hours=2),
            severity=models.MINIMAL,
            created_by=cls.user,
        )

    @staticmethod
    def _z(dt):
        # iso8601 with a literal 'Z' tz suffix -- avoids the '+' in
        # `+00:00` being URL-decoded to a space in query strings.
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _ids(self, query):
        response = self.client.get(f"/api/v1/outages/?{query}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        return {d['id'] for d in data['results']}

    def test_start_gte(self):
        cutoff = self._z(self.now - timedelta(hours=2))
        self.assertEqual({self.future.id}, self._ids(f"start__gte={cutoff}"))

    def test_start_lt(self):
        cutoff = self._z(self.now)
        self.assertEqual(
            {self.past.id, self.active.id}, self._ids(f"start__lt={cutoff}")
        )

    def test_start_date(self):
        # start__date filters by the calendar date component only.
        day = (self.now - timedelta(days=1)).date().isoformat()
        self.assertEqual({self.active.id}, self._ids(f"start__date={day}"))

    def test_end_lt(self):
        cutoff = self._z(self.now)
        self.assertEqual({self.past.id}, self._ids(f"end__lt={cutoff}"))

    def test_end_gte_excludes_null(self):
        # gte on end excludes rows with end IS NULL (active + future).
        cutoff = self._z(self.now - timedelta(days=30))
        self.assertEqual({self.past.id}, self._ids(f"end__gte={cutoff}"))

    def test_planned_end_gt(self):
        cutoff = self._z(self.now)
        self.assertEqual(
            {self.future.id}, self._ids(f"planned_end__gt={cutoff}")
        )

    def test_severity_exact(self):
        self.assertEqual(
            {self.past.id}, self._ids(f"severity={models.SEVERE}")
        )

    def test_severity_in(self):
        self.assertEqual(
            {self.past.id, self.future.id},
            self._ids(f"severity__in={models.SEVERE},{models.MINIMAL}"),
        )


class OutageEndpointPinningTestCase(test.APITestCase):
    """/api/v1/outages/ is a stable external contract: it must only
    ever return outage-category rows, whatever else the announcements
    table holds.
    """

    def setUp(self):
        self.user = auth_models.User.objects.create(
            username="test", email="test@test.com"
        )
        self.outage = models.Announcement.objects.create(
            title="outage",
            description="d",
            start=timezone.now(),
            severity=models.SIGNIFICANT,
            created_by=self.user,
        )
        self.news = models.Announcement.objects.create(
            title="news",
            description="d",
            category=models.Category.NEWS,
            start=timezone.now(),
            severity=None,
            created_by=self.user,
        )
        self.notice = models.Announcement.objects.create(
            title="notice",
            description="d",
            category=models.Category.NOTICE,
            start=timezone.now(),
            severity=models.SEVERE,
            created_by=self.user,
        )

    def test_list_returns_outages_only(self):
        response = self.client.get('/api/v1/outages/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        content = json.loads(response.content)
        titles = {item['title'] for item in content['results']}
        self.assertEqual({"outage"}, titles)

    def test_active_filter_excludes_news_and_notice(self):
        response = self.client.get('/api/v1/outages/?activity=active')
        content = json.loads(response.content)
        titles = {item['title'] for item in content['results']}
        self.assertEqual({"outage"}, titles)

    def test_news_and_notice_detail_404(self):
        for pk in (self.news.pk, self.notice.pk):
            response = self.client.get(f'/api/v1/outages/{pk}/')
            self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_outage_detail_still_served(self):
        response = self.client.get(f'/api/v1/outages/{self.outage.pk}/')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_no_category_field_in_response(self):
        # The legacy serializer must stay byte-compatible; category is
        # exposed on /api/v1/announcements/ only.
        response = self.client.get(f'/api/v1/outages/{self.outage.pk}/')
        self.assertNotIn('category', json.loads(response.content))


@freeze_time("2026-07-01 10:00:00")
class AnnouncementEndpointTestCase(test.APITestCase):
    """/api/v1/announcements/ serves every category with a clean
    contract: a `category` discriminator and none of the scheduled_*
    back-compat aliases carried by /api/v1/outages/.
    """

    def setUp(self):
        self.user = auth_models.User.objects.create(
            username="test", email="test@test.com"
        )
        self.outage = models.Announcement.objects.create(
            title="outage",
            description="d",
            start=timezone.now() - timedelta(hours=1),
            severity=models.SIGNIFICANT,
            created_by=self.user,
        )
        models.AnnouncementUpdate.objects.create(
            outage=self.outage,
            status=models.INVESTIGATING,
            content="looking",
            time=timezone.now(),
            created_by=self.user,
        )
        self.news = models.Announcement.objects.create(
            title="news",
            description="we shipped a thing",
            category=models.Category.NEWS,
            start=timezone.now() - timedelta(days=1),
            severity=None,
            created_by=self.user,
        )
        self.notice = models.Announcement.objects.create(
            title="notice",
            description="CVE-2026-0001",
            category=models.Category.NOTICE,
            start=timezone.now() - timedelta(hours=2),
            severity=models.SEVERE,
            created_by=self.user,
        )

    def _results(self, url):
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        return json.loads(response.content)['results']

    def test_list_serves_all_categories(self):
        results = self._results('/api/v1/announcements/')
        self.assertEqual(
            {"outage", "news", "notice"}, {r['title'] for r in results}
        )
        self.assertEqual(
            {'outage', 'news', 'notice'}, {r['category'] for r in results}
        )

    def test_news_serialisation(self):
        results = self._results('/api/v1/announcements/?category=news')
        self.assertEqual(1, len(results))
        news = results[0]
        self.assertEqual(
            {
                'id': self.news.id,
                'title': "news",
                'description': "we shipped a thing",
                'category': 'news',
                'start': '2026-06-30T10:00:00+0000',
                'planned_end': None,
                'end': None,
                'severity': None,
                'severity_display': None,
                'scheduled': False,
                'scheduled_display': 'unscheduled',
                'status_display': 'Published',
                'cancelled': False,
                'updates': [],
            },
            news,
        )

    def test_no_backcompat_aliases(self):
        results = self._results('/api/v1/announcements/')
        for result in results:
            self.assertNotIn('scheduled_start', result)
            self.assertNotIn('scheduled_end', result)
            self.assertNotIn('scheduled_severity', result)

    def test_nested_updates_have_no_severity_alias(self):
        results = self._results('/api/v1/announcements/?category=outage')
        self.assertEqual(
            [
                {
                    'content': "looking",
                    'time': '2026-07-01T10:00:00+0000',
                    'status': models.INVESTIGATING,
                }
            ],
            results[0]['updates'],
        )

    def test_category_in_filter(self):
        results = self._results(
            '/api/v1/announcements/?category__in=news,notice'
        )
        self.assertEqual({"news", "notice"}, {r['title'] for r in results})

    def test_activity_active_excludes_news(self):
        results = self._results('/api/v1/announcements/?activity=active')
        self.assertEqual({"outage", "notice"}, {r['title'] for r in results})

    def test_severity_filter(self):
        results = self._results('/api/v1/announcements/?severity=3')
        self.assertEqual({"notice"}, {r['title'] for r in results})

    def test_read_only(self):
        response = self.client.post('/api/v1/announcements/', {})
        self.assertEqual(
            status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code
        )

    def test_detail_serves_any_category(self):
        for item in (self.outage, self.news, self.notice):
            response = self.client.get(f'/api/v1/announcements/{item.pk}/')
            self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_pagination_shape(self):
        response = self.client.get('/api/v1/announcements/?page_size=2')
        content = json.loads(response.content)
        self.assertEqual(3, content['count'])
        self.assertEqual(2, len(content['results']))
        self.assertIsNotNone(content['next'])


class AnnouncementEmbargoAPITestCase(test.APITestCase):
    def setUp(self):
        self.user = auth_models.User.objects.create(
            username="embargo", email="embargo@test.com"
        )
        self.embargoed = models.Announcement.objects.create(
            title="Embargoed news",
            description="secret until launch",
            category=models.Category.NEWS,
            start=timezone.now() + timedelta(days=1),
            severity=None,
            created_by=self.user,
        )
        self.retracted = models.Announcement.objects.create(
            title="Retracted news",
            description="was wrong",
            category=models.Category.NEWS,
            start=timezone.now() - timedelta(days=1),
            severity=None,
            cancelled=True,
            created_by=self.user,
        )

    def test_embargoed_news_absent_from_list_and_detail(self):
        response = self.client.get('/api/v1/announcements/')
        titles = {r['title'] for r in json.loads(response.content)['results']}
        self.assertNotIn("Embargoed news", titles)
        detail = self.client.get(f'/api/v1/announcements/{self.embargoed.pk}/')
        self.assertEqual(status.HTTP_404_NOT_FOUND, detail.status_code)

    def test_retracted_news_reports_retracted(self):
        response = self.client.get(
            f'/api/v1/announcements/{self.retracted.pk}/'
        )
        content = json.loads(response.content)
        self.assertEqual("Retracted", content['status_display'])
        self.assertTrue(content['cancelled'])
