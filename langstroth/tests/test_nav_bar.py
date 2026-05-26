from django.test import RequestFactory
from django.test import TestCase

from langstroth.templatetags.nav_bar import active


class NavBarActiveTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_root_is_availability(self):
        self.assertEqual('active', active(self.rf.get('/'), 'availability'))

    def test_root_not_active_for_other_section(self):
        self.assertEqual('', active(self.rf.get('/'), 'outages'))

    def test_segment_match(self):
        self.assertEqual('active', active(self.rf.get('/outages/'), 'outages'))
        self.assertEqual(
            'active',
            active(self.rf.get('/growth/infrastructure/'), 'infrastructure'),
        )

    def test_segment_match_at_root_section(self):
        # Top-level "Growth" nav lights up on any /growth/* page.
        self.assertEqual(
            'active', active(self.rf.get('/growth/users/'), 'growth')
        )

    def test_no_match_when_word_appears_only_as_substring(self):
        # Regression: the previous implementation used `url in path`,
        # which would mark the Growth nav active for any path with the
        # substring "growth" anywhere.  The segment-aware impl shouldn't.
        self.assertEqual(
            '', active(self.rf.get('/outages/growth-of-bees/'), 'growth')
        )

    def test_no_match_for_unrelated_section(self):
        self.assertEqual('', active(self.rf.get('/growth/users/'), 'outages'))
