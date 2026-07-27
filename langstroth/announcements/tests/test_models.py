from datetime import timedelta
import time

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from langstroth.announcements import models
from langstroth import models as auth_models


class OutageUpdateCascadeTests(TestCase):
    """Covers the post-save cascade in AnnouncementUpdate.save() that
    bubbles `modification_time` and `modified_by` onto the parent
    Announcement so the
    list view (ordered by `-modification_time`) surfaces recent activity
    and correctly attributes the last action.
    """

    @classmethod
    def setUpTestData(cls):
        cls.author = auth_models.User.objects.create(
            username="author", email="author@test"
        )
        cls.updater = auth_models.User.objects.create(
            username="updater", email="updater@test"
        )

    def _outage(self):
        return models.Announcement.objects.create(
            title="o",
            description="d",
            start=timezone.now() - timedelta(hours=1),
            severity=models.SIGNIFICANT,
            created_by=self.author,
            modified_by=self.author,
        )

    def test_creating_update_bumps_modification_time(self):
        outage = self._outage()
        before = outage.modification_time
        # Sleep briefly so the new auto_now timestamp is strictly later.
        time.sleep(0.01)
        models.AnnouncementUpdate.objects.create(
            outage=outage,
            time=timezone.now(),
            status=models.INVESTIGATING,
            content="x",
            created_by=self.updater,
        )
        outage.refresh_from_db()
        self.assertGreater(outage.modification_time, before)

    def test_creating_update_sets_modified_by_to_actor(self):
        # Before fix #29 the cascade left modified_by unchanged. The
        # parent's "last modified by" must reflect the operator who
        # added the latest update.
        outage = self._outage()
        self.assertEqual(self.author, outage.modified_by)
        models.AnnouncementUpdate.objects.create(
            outage=outage,
            time=timezone.now(),
            status=models.INVESTIGATING,
            content="x",
            created_by=self.updater,
        )
        outage.refresh_from_db()
        self.assertEqual(self.updater, outage.modified_by)

    def test_update_modified_by_takes_precedence_over_created_by(self):
        # If the update is itself edited, the cascade prefers
        # modified_by over created_by as the actor.
        outage = self._outage()
        update = models.AnnouncementUpdate.objects.create(
            outage=outage,
            time=timezone.now(),
            status=models.INVESTIGATING,
            content="x",
            created_by=self.author,
        )
        # Now a different user edits the update.
        update.modified_by = self.updater
        update.content = "y"
        update.save()
        outage.refresh_from_db()
        self.assertEqual(self.updater, outage.modified_by)

    def test_cascade_does_not_recompute_scheduled(self):
        # Announcement.save() recomputes the `scheduled` flag only on adding;
        # the cascade must not trigger a recompute (which would flip
        # the label for any outage whose start has since drifted into
        # the past).
        outage = self._outage()
        outage.scheduled = True
        outage.save(update_fields=['scheduled'])
        models.AnnouncementUpdate.objects.create(
            outage=outage,
            time=timezone.now(),
            status=models.INVESTIGATING,
            content="x",
            created_by=self.updater,
        )
        outage.refresh_from_db()
        self.assertTrue(outage.scheduled)


class CategoryTests(TestCase):
    """Cover the category discriminator added for news/notice support."""

    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="author", email="author@test"
        )

    def _make(self, **overrides):
        defaults = {
            "title": "t",
            "description": "d",
            "start": timezone.now() - timedelta(hours=1),
            "severity": models.SIGNIFICANT,
            "created_by": self.user,
        }
        defaults.update(overrides)
        return models.Announcement.objects.create(**defaults)

    def test_category_defaults_to_outage(self):
        self.assertEqual(models.Category.OUTAGE, self._make().category)

    def test_news_status_display_is_published(self):
        news = self._make(category=models.Category.NEWS, severity=None)
        self.assertEqual("Published", news.status_display)
        # Even a cancelled (retracted) news item stays "Published" --
        # retraction is admin-only and the item is filtered out of
        # public views instead.
        news.cancelled = True
        self.assertEqual("Published", news.status_display)

    def test_severity_display_none_for_null_severity(self):
        news = self._make(category=models.Category.NEWS, severity=None)
        self.assertIsNone(news.severity_display)

    def test_severity_display_unknown_for_unrecognised_code(self):
        outage = self._make(severity=99)
        self.assertEqual("Unknown", outage.severity_display)

    def test_current_includes_notices_and_outages_but_not_news(self):
        outage = self._make(title="outage")
        notice = self._make(title="notice", category=models.Category.NOTICE)
        self._make(title="news", category=models.Category.NEWS, severity=None)
        current = list(models.Announcement.objects.current())
        self.assertIn(outage, current)
        self.assertIn(notice, current)
        self.assertEqual(2, len(current))

    def test_clean_requires_severity_for_outage_and_notice(self):
        for category in (models.Category.OUTAGE, models.Category.NOTICE):
            announcement = models.Announcement(
                title="t",
                description="d",
                category=category,
                start=timezone.now(),
                severity=None,
                created_by=self.user,
            )
            with self.assertRaises(ValidationError):
                announcement.clean()

    def test_clean_rejects_severity_on_news(self):
        news = models.Announcement(
            title="t",
            description="d",
            category=models.Category.NEWS,
            start=timezone.now(),
            severity=models.SIGNIFICANT,
            created_by=self.user,
        )
        with self.assertRaises(ValidationError):
            news.clean()

    def test_clean_accepts_valid_rows(self):
        self._make().clean()
        self._make(category=models.Category.NOTICE).clean()
        self._make(category=models.Category.NEWS, severity=None).clean()


@freeze_time("2026-07-01 10:00:00")
class ManagerQuerysetTests(TestCase):
    """Cover upcoming() and recently_ended(), which drive the home
    page's Upcoming and Recently Resolved sections.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = auth_models.User.objects.create(
            username="mgr", email="mgr@test"
        )

    def _make(self, **overrides):
        defaults = {
            "title": "t",
            "description": "d",
            "start": timezone.now() - timedelta(hours=1),
            "severity": models.SIGNIFICANT,
            "created_by": self.user,
        }
        defaults.update(overrides)
        return models.Announcement.objects.create(**defaults)

    def test_upcoming_membership(self):
        started = self._make(title="started")
        soon = self._make(
            title="soon", start=timezone.now() + timedelta(hours=2)
        )
        later = self._make(
            title="later", start=timezone.now() + timedelta(days=2)
        )
        cancelled = self._make(
            title="cancelled", start=timezone.now() + timedelta(hours=3)
        )
        cancelled.cancelled = True
        cancelled.save()
        future_news = self._make(
            title="future news",
            category=models.Category.NEWS,
            severity=None,
            start=timezone.now() + timedelta(hours=4),
        )
        future_notice = self._make(
            title="future notice",
            category=models.Category.NOTICE,
            start=timezone.now() + timedelta(hours=5),
        )

        upcoming = list(models.Announcement.objects.upcoming())
        self.assertNotIn(started, upcoming)
        self.assertNotIn(cancelled, upcoming)
        self.assertNotIn(future_news, upcoming)
        # Ordered soonest first.
        self.assertEqual([soon, future_notice, later], upcoming)

    def test_recently_ended_window_boundaries(self):
        now = timezone.now()
        recent = self._make(
            title="recent",
            start=now - timedelta(days=10),
            end=now - timedelta(days=5),
        )
        edge = self._make(
            title="edge",
            start=now - timedelta(days=30),
            end=now - timedelta(days=29),
        )
        old = self._make(
            title="old",
            start=now - timedelta(days=40),
            end=now - timedelta(days=31),
        )
        ongoing = self._make(title="ongoing")

        ended = list(models.Announcement.objects.recently_ended())
        self.assertNotIn(old, ended)
        self.assertNotIn(ongoing, ended)
        # Most recently ended first.
        self.assertEqual([recent, edge], ended)

    def test_recently_ended_days_argument(self):
        now = timezone.now()
        self._make(
            title="last week",
            start=now - timedelta(days=8),
            end=now - timedelta(days=6),
        )
        self.assertEqual(
            0, models.Announcement.objects.recently_ended(days=5).count()
        )
        self.assertEqual(
            1, models.Announcement.objects.recently_ended(days=7).count()
        )

    def test_recently_ended_includes_notices(self):
        now = timezone.now()
        notice = self._make(
            title="stood down",
            category=models.Category.NOTICE,
            start=now - timedelta(days=2),
            end=now - timedelta(days=1),
        )
        self.assertIn(notice, models.Announcement.objects.recently_ended())
