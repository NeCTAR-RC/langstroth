import datetime
from unittest import mock
import zoneinfo

from django.forms.utils import from_current_timezone
from django.forms.utils import to_current_timezone
from django.test import RequestFactory
from django.test import TestCase
from django.utils import timezone

from langstroth import middleware


class TimezoneMiddlewareTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.get_response = mock.Mock(return_value="passthrough")
        self.mw = middleware.TimezoneMiddleware(self.get_response)
        self.addCleanup(timezone.deactivate)

    def _request(self, detected_tz=None):
        request = self.rf.get("/")
        request.session = (
            {} if detected_tz is None else {"detected_tz": detected_tz}
        )
        return request

    def test_passes_response_through(self):
        self.assertEqual("passthrough", self.mw(self._request()))

    def test_no_detected_tz_deactivates(self):
        timezone.activate(zoneinfo.ZoneInfo("Australia/Melbourne"))
        self.mw(self._request())
        # get_current_timezone falls back to settings.TIME_ZONE (UTC).
        self.assertEqual("UTC", timezone.get_current_timezone_name())

    def test_iana_name_activates_zoneinfo(self):
        request = self._request("Australia/Melbourne")
        self.mw(request)
        self.assertEqual(
            zoneinfo.ZoneInfo("Australia/Melbourne"),
            timezone.get_current_timezone(),
        )
        self.assertTrue(request.timezone_active)

    def test_integer_offset_activates_a_zone(self):
        # JS-style minutes offset fallback. -600 == UTC+10.
        request = self._request(-600)
        self.mw(request)
        tz = timezone.get_current_timezone()
        self.assertIsInstance(tz, zoneinfo.ZoneInfo)
        ref = datetime.datetime(2026, 6, 18, tzinfo=datetime.timezone.utc)
        self.assertEqual(datetime.timedelta(hours=10), tz.utcoffset(ref))

    def test_unknown_name_deactivates_without_error(self):
        timezone.activate(zoneinfo.ZoneInfo("Australia/Melbourne"))
        request = self._request("Mars/Olympus_Mons")
        self.mw(request)
        self.assertEqual("UTC", timezone.get_current_timezone_name())
        self.assertFalse(hasattr(request, "timezone_active"))

    def test_round_trip_preserves_wall_clock_time(self):
        # Regression: a datetime rendered then re-parsed through a form
        # under the active timezone must not drift. Under the old pytz
        # middleware Australia/Melbourne drifted ~20 minutes per save.
        self.mw(self._request("Australia/Melbourne"))
        stored = datetime.datetime(
            2026, 6, 18, 0, 0, tzinfo=datetime.timezone.utc
        )
        shown = to_current_timezone(stored)  # what the widget renders
        # Operator re-submits the same wall-clock value unchanged.
        reparsed = from_current_timezone(shown.replace(tzinfo=None))
        self.assertEqual(stored, reparsed)
        self.assertEqual(datetime.timedelta(0), reparsed - stored)
