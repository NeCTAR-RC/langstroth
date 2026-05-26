from datetime import timedelta
import time

from django.test import TestCase
from django.utils import timezone

from langstroth import models as auth_models
from langstroth.outages import models


class OutageUpdateCascadeTests(TestCase):
    """Covers the post-save cascade in OutageUpdate.save() that bubbles
    `modification_time` and `modified_by` onto the parent Outage so the
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
        return models.Outage.objects.create(
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
        models.OutageUpdate.objects.create(
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
        models.OutageUpdate.objects.create(
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
        update = models.OutageUpdate.objects.create(
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
        # Outage.save() recomputes the `scheduled` flag only on adding;
        # the cascade must not trigger a recompute (which would flip
        # the label for any outage whose start has since drifted into
        # the past).
        outage = self._outage()
        outage.scheduled = True
        outage.save(update_fields=['scheduled'])
        models.OutageUpdate.objects.create(
            outage=outage,
            time=timezone.now(),
            status=models.INVESTIGATING,
            content="x",
            created_by=self.updater,
        )
        outage.refresh_from_db()
        self.assertTrue(outage.scheduled)
