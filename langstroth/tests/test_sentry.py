import os
from unittest import mock

from django.test import SimpleTestCase

from langstroth import defaults
from langstroth import sentry


DSN = "https://key@glitchtip.example.com/1"
SECURITY_ENDPOINT = (
    "https://glitchtip.example.com/api/1/security/?sentry_key=key"
)
RELEASE = "langstroth@1.0.0"


@mock.patch("langstroth.sentry._release", return_value=RELEASE)
@mock.patch("langstroth.sentry.sentry_sdk")
class SentrySetupTests(SimpleTestCase):
    def test_setup_no_dsn(self, mock_sdk, mock_release):
        with mock.patch.dict(os.environ):
            os.environ.pop("SENTRY_DSN", None)
            self.assertFalse(sentry.setup())
        mock_sdk.init.assert_not_called()

    def test_setup_with_dsn_and_environment(self, mock_sdk, mock_release):
        self.assertTrue(sentry.setup(DSN, "testing"))
        mock_sdk.init.assert_called_once_with(
            dsn=DSN,
            environment="testing",
            release=RELEASE,
            auto_session_tracking=False,
        )

    def test_setup_dsn_only(self, mock_sdk, mock_release):
        self.assertTrue(sentry.setup(DSN))
        mock_sdk.init.assert_called_once_with(
            dsn=DSN,
            environment=None,
            release=RELEASE,
            auto_session_tracking=False,
        )

    def test_setup_dsn_from_environment(self, mock_sdk, mock_release):
        with mock.patch.dict(os.environ, {"SENTRY_DSN": DSN}):
            self.assertTrue(sentry.setup())
        mock_sdk.init.assert_called_once_with(
            dsn=DSN,
            environment=None,
            release=RELEASE,
            auto_session_tracking=False,
        )


class SecurityEndpointTests(SimpleTestCase):
    def test_no_dsn(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("SENTRY_DSN", None)
            self.assertIsNone(sentry.security_endpoint())

    def test_endpoint_from_dsn(self):
        self.assertEqual(SECURITY_ENDPOINT, sentry.security_endpoint(DSN))

    def test_endpoint_with_environment(self):
        self.assertEqual(
            SECURITY_ENDPOINT + "&sentry_environment=testing",
            sentry.security_endpoint(DSN, "testing"),
        )

    def test_endpoint_with_port_and_path(self):
        dsn = "http://key@glitchtip.example.com:8000/prefix/1"
        self.assertEqual(
            "http://glitchtip.example.com:8000/prefix/api/1/security/"
            "?sentry_key=key",
            sentry.security_endpoint(dsn),
        )

    def test_endpoint_dsn_from_environment(self):
        with mock.patch.dict(os.environ, {"SENTRY_DSN": DSN}):
            self.assertEqual(SECURITY_ENDPOINT, sentry.security_endpoint())

    def test_endpoint_invalid_dsn(self):
        with self.assertLogs("langstroth.sentry", level="WARNING"):
            self.assertIsNone(sentry.security_endpoint("not-a-dsn"))


class BuildCspTests(SimpleTestCase):
    def test_report_uri_with_dsn(self):
        csp = defaults.build_csp("http://allocations.test/rest_api/", DSN)
        self.assertEqual((SECURITY_ENDPOINT,), csp['DIRECTIVES']['report-uri'])

    def test_no_report_uri_without_dsn(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("SENTRY_DSN", None)
            csp = defaults.build_csp("http://allocations.test/rest_api/")
        self.assertNotIn('report-uri', csp['DIRECTIVES'])


class ReleaseTests(SimpleTestCase):
    def test_release(self):
        with mock.patch("langstroth.sentry.pbr") as mock_pbr:
            version_info = mock_pbr.version.VersionInfo.return_value
            version_info.release_string.return_value = "1.2.3"
            self.assertEqual("langstroth@1.2.3", sentry._release())

    def test_release_unknown(self):
        with mock.patch(
            "langstroth.sentry.pbr.version.VersionInfo",
            side_effect=Exception("no version"),
        ):
            self.assertIsNone(sentry._release())
