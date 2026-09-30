import os
from pathlib import Path
import re
from unittest import mock

from django.test import override_settings
from django.test import TestCase

import langstroth
from langstroth.announcements import forms as announcement_forms
from langstroth import defaults


DSN = "https://key@glitchtip.example.com/1"
SECURITY_ENDPOINT = (
    "https://glitchtip.example.com/api/1/security/?sentry_key=key"
)

NONCE_TOKEN_RE = re.compile(r"'nonce-([A-Za-z0-9_-]+)'")
# Opening <script ...> tags, with their attribute string captured.
SCRIPT_TAG_RE = re.compile(r'<script\b([^>]*)>', re.IGNORECASE)
# Inline event handler attributes such as onclick="..." -- CSP never
# allows these without 'unsafe-inline', nonces included.
EVENT_HANDLER_RE = re.compile(r'\son[a-z]+\s*=', re.IGNORECASE)


def _directives(response):
    """Parse the Content-Security-Policy header into {directive: value}."""
    header = response.headers['Content-Security-Policy']
    return dict(part.strip().split(' ', 1) for part in header.split(';'))


def _inline_script_tags(html):
    """Return the attribute strings of <script> tags without a src."""
    return [
        attrs
        for attrs in SCRIPT_TAG_RE.findall(html)
        if not re.search(r'\bsrc\s*=', attrs)
    ]


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
        # The allocations browser fetches ALLOCATION_API_URL from the
        # browser, so its origin must be allowed in connect-src.
        self.assertIn('http://allocations.test', directives['connect-src'])
        self.assertNotIn('Content-Security-Policy-Report-Only', response)

    def test_script_src_is_nonce_based(self):
        response = self.client.get('/favicon.ico')
        directives = _directives(response)
        self.assertNotIn("'unsafe-inline'", directives['script-src'])
        # Nothing rendered a template, so no nonce was generated and
        # the middleware drops the placeholder rather than emitting an
        # unused token.
        self.assertIsNone(NONCE_TOKEN_RE.search(directives['script-src']))
        # Inline style="" attributes and third-party widgets still need
        # this; see the SECURE_CSP comment in defaults.py.
        self.assertIn("'unsafe-inline'", directives['style-src'])

    def test_rendered_page_nonce_matches_header(self):
        # growth.html extends base.html, whose {% tz_detect %} emits an
        # inline script, and fetches no external data server-side.
        response = self.client.get('/growth/infrastructure/')
        self.assertEqual(200, response.status_code)
        match = NONCE_TOKEN_RE.search(_directives(response)['script-src'])
        self.assertIsNotNone(match, "header carries no nonce")
        nonce = match.group(1)
        body = response.content.decode()
        inline = _inline_script_tags(body)
        self.assertTrue(inline, "expected at least one inline script")
        for attrs in inline:
            self.assertIn(f'nonce="{nonce}"', attrs)

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


class ThirdPartyWidgetTests(TestCase):
    def test_datepicker_renders_no_inline_script(self):
        # bootstrap_datepicker_plus emits an inline "form.media was not
        # loaded" checker when its debug flag is on. The flag follows
        # DEBUG (which settings_test enables) unless
        # BOOTSTRAP_DATEPICKER_PLUS turns it off; the checker can't
        # carry our nonce, so it must not be rendered.
        html = str(announcement_forms.OutageForm()['start'])
        self.assertNotIn('<script', html)
        self.assertNotIn('data-dbdp-debug', html)


class TemplateAuditTests(TestCase):
    """Static checks that our templates stay compatible with the
    nonce-based script-src: every inline <script> must carry
    {% csp_nonce_attr %} (or be a non-executable JSON data block), and
    there must be no inline event handlers or javascript: URLs."""

    @staticmethod
    def _templates():
        root = Path(langstroth.__file__).parent
        return sorted(root.glob('**/templates/**/*.html'))

    def test_templates_found(self):
        self.assertGreater(len(self._templates()), 10)

    def test_inline_scripts_carry_nonce(self):
        offenders = []
        for path in self._templates():
            source = path.read_text()
            for attrs in _inline_script_tags(source):
                if 'csp_nonce_attr' in attrs:
                    continue
                if 'type="application/json"' in attrs:
                    continue
                offenders.append(f"{path}: <script{attrs}>")
        self.assertEqual([], offenders)

    def test_no_inline_event_handlers(self):
        offenders = []
        for path in self._templates():
            source = path.read_text()
            # Strip Django tag/variable syntax first so that e.g. a
            # {% url %} argument can't trip the attribute pattern.
            html_only = re.sub(r'\{[%{#].*?[%}#]\}', '', source, flags=re.S)
            if EVENT_HANDLER_RE.search(html_only):
                offenders.append(f"{path}: inline event handler")
            if re.search(r'javascript:', html_only, re.IGNORECASE):
                offenders.append(f"{path}: javascript: URL")
        self.assertEqual([], offenders)

    def test_template_comments_are_single_line(self):
        # Django's {# ... #} comments only work on one line; a
        # multi-line one is rendered as page text (and would defeat
        # the inline-script audit above by hiding a literal <script>).
        offenders = []
        for path in self._templates():
            for match in re.finditer(r'\{#.*?#\}', path.read_text(), re.S):
                if '\n' in match.group(0):
                    offenders.append(str(path))
        self.assertEqual([], offenders)
