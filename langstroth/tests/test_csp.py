import os
from unittest import mock

from django.test import override_settings
from django.test import TestCase

from langstroth import defaults


DSN = "https://key@glitchtip.example.com/1"
SECURITY_ENDPOINT = (
    "https://glitchtip.example.com/api/1/security/?sentry_key=key"
)


def _directives(response):
    """Parse the Content-Security-Policy header into {directive: value}."""
    header = response.headers['Content-Security-Policy']
    return dict(part.strip().split(' ', 1) for part in header.split(';'))


class CspHeaderTests(TestCase):
    """Django's built-in ContentSecurityPolicyMiddleware renders
    SECURE_CSP (built by defaults.build_csp) onto every response."""

    def test_policy_header_on_response(self):
        # A cheap URL that touches no external service.
        response = self.client.get('/favicon.ico')
        self.assertEqual(302, response.status_code)
        directives = _directives(response)
        self.assertEqual("'self'", directives['default-src'])
        self.assertEqual("'none'", directives['frame-ancestors'])
        self.assertEqual("'none'", directives['object-src'])
        self.assertIn("'unsafe-inline'", directives['script-src'])
        # The allocations browser fetches ALLOCATION_API_URL from the
        # browser, so its origin must be allowed in connect-src.
        self.assertIn('http://allocations.test', directives['connect-src'])
        self.assertNotIn('Content-Security-Policy-Report-Only', response)

    def test_no_report_uri_without_sentry(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("SENTRY_DSN", None)
            policy = defaults.build_csp("http://allocations.test/rest_api/")
        with override_settings(SECURE_CSP=policy):
            response = self.client.get('/favicon.ico')
        self.assertNotIn('report-uri', _directives(response))

    def test_report_uri_with_sentry(self):
        policy = defaults.build_csp("http://allocations.test/rest_api/", DSN)
        with override_settings(SECURE_CSP=policy):
            response = self.client.get('/favicon.ico')
        self.assertEqual(
            SECURITY_ENDPOINT, _directives(response)['report-uri']
        )
