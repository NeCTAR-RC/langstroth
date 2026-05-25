from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.test import TestCase

from langstroth import auth
from langstroth import models as auth_models


class GenerateUsernameTests(TestCase):
    def test_basic(self):
        self.assertEqual(
            "user@example.com", auth.generate_username("user@example.com")
        )

    def test_truncates_to_150(self):
        email = "a" * 200 + "@example.com"
        self.assertEqual(150, len(auth.generate_username(email)))


class MiddlewareTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.get_response = mock.Mock(return_value="passthrough")

    def test_passes_through_non_admin(self):
        mw = auth.NoDjangoAdminForEndUserMiddleware(self.get_response)
        request = self.rf.get("/something/")
        request.user = AnonymousUser()
        result = mw(request)
        self.assertEqual("passthrough", result)

    def test_redirects_end_user_from_admin(self):
        mw = auth.NoDjangoAdminForEndUserMiddleware(self.get_response)
        request = self.rf.get("/admin/")
        request.user = auth_models.User(
            username="u", email="u@e.com", is_staff=False, is_superuser=False
        )
        result = mw(request)
        self.assertEqual(302, result.status_code)
        self.assertEqual("/", result.url)

    def test_staff_passes_through(self):
        mw = auth.NoDjangoAdminForEndUserMiddleware(self.get_response)
        request = self.rf.get("/admin/")
        request.user = auth_models.User(
            username="s", email="s@e.com", is_staff=True
        )
        self.assertEqual("passthrough", mw(request))

    def test_anonymous_passes_through(self):
        mw = auth.NoDjangoAdminForEndUserMiddleware(self.get_response)
        request = self.rf.get("/admin/")
        request.user = AnonymousUser()
        self.assertEqual("passthrough", mw(request))


class NectarAuthBackendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # The "outage_managers" group is created by migration 0002 — make sure
        # it exists so `_assign_user_roles` can add staff to it.
        Group.objects.get_or_create(name='outage_managers')

    def _claims(self, **overrides):
        c = {
            'email': 'new@test.com',
            'given_name': 'Test',
            'family_name': 'User',
            'sub': '11111111-1111-1111-1111-111111111111',
            'roles': [],
        }
        c.update(overrides)
        return c

    def test_create_user(self):
        backend = auth.NectarAuthBackend()
        user = backend.create_user(self._claims())
        self.assertEqual('new@test.com', user.email)
        self.assertEqual('11111111-1111-1111-1111-111111111111', str(user.sub))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_collision_returns_none(self):
        auth_models.User.objects.create_user(
            'existing',
            email='collide@test.com',
            sub='22222222-2222-2222-2222-222222222222',
        )
        backend = auth.NectarAuthBackend()
        result = backend.create_user(
            self._claims(
                email='collide@test.com',
                sub='33333333-3333-3333-3333-333333333333',
            )
        )
        self.assertIsNone(result)

    def test_create_user_assigns_staff_role(self):
        backend = auth.NectarAuthBackend()
        user = backend.create_user(self._claims(roles=['/staff']))
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_assigns_admin_role(self):
        backend = auth.NectarAuthBackend()
        user = backend.create_user(self._claims(roles=['/coreservices']))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_update_user(self):
        user = auth_models.User.objects.create_user(
            'old',
            email='old@test.com',
            sub='11111111-1111-1111-1111-111111111111',
        )
        backend = auth.NectarAuthBackend()
        updated = backend.update_user(
            user,
            self._claims(
                email='new@test.com',
                given_name='Newgiven',
                family_name='Newfamily',
                roles=['/staff'],
            ),
        )
        self.assertEqual('new@test.com', updated.email)
        self.assertEqual('Newgiven', updated.first_name)
        self.assertEqual('Newfamily', updated.last_name)
        self.assertTrue(updated.is_staff)

    def test_filter_users_empty_when_claims_missing(self):
        backend = auth.NectarAuthBackend()
        self.assertEqual(0, backend.filter_users_by_claims({}).count())
        self.assertEqual(
            0,
            backend.filter_users_by_claims({'sub': 'x'}).count(),
        )

    def test_filter_users_by_sub(self):
        user = auth_models.User.objects.create_user(
            'u', email='u@test.com', sub='44444444-4444-4444-4444-444444444444'
        )
        backend = auth.NectarAuthBackend()
        result = backend.filter_users_by_claims(
            {
                'sub': '44444444-4444-4444-4444-444444444444',
                'email': 'u@test.com',
            }
        )
        self.assertIn(user, result)

    def test_demotion_removes_outage_manager_membership(self):
        # Promote then demote: the group membership must follow the role.
        user = auth_models.User.objects.create_user(
            'demo',
            email='demo@test.com',
            sub='55555555-5555-5555-5555-555555555555',
        )
        backend = auth.NectarAuthBackend()
        backend.update_user(user, self._claims(roles=['/staff']))
        managers = Group.objects.get(name='outage_managers')
        self.assertIn(user, managers.user_set.all())

        backend.update_user(user, self._claims(roles=[]))
        self.assertNotIn(user, managers.user_set.all())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_filter_users_fallback_to_email(self):
        # Existing user with no `sub` — backend should find by email
        user = auth_models.User.objects.create_user('u', email='u@test.com')
        user.sub = None
        user.save()
        backend = auth.NectarAuthBackend()
        result = backend.filter_users_by_claims(
            {
                'sub': '99999999-9999-9999-9999-999999999999',
                'email': 'u@test.com',
            }
        )
        self.assertIn(user, result)
