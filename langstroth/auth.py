import logging
import unicodedata

from django.shortcuts import redirect
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from .outages import admin as outage_admin

logger = logging.getLogger(__name__)

# Roles to determine user level
ROLE_CLAIM = 'roles'
ADMIN_ROLES = ['/coreservices']
STAFF_ROLES = ADMIN_ROLES + ['/staff']


class NoDjangoAdminForEndUserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path.startswith("/admin/"):
            if request.user.is_authenticated \
               and not request.user.is_staff \
               and not request.user.is_superuser:
                return redirect("/")  # Get outa here!

        response = self.get_response(request)

        return response


class NectarAuthBackend(OIDCAuthenticationBackend):

    def create_user(self, claims):
        email = claims.get('email')
        username = self.get_username(claims)
        sub = claims.get('sub')  # OIDC persistent ID
        first_name = claims.get('given_name')
        last_name = claims.get('family_name')

        existing = self.UserModel.objects.filter(email__iexact=email).first()
        if existing:
            # username/sub mismatch
            logger.error(
                f"Login failed for {username}: "
                f"Sub value {sub} did not match existing value {existing.sub}")
            return

        user = self.UserModel.objects.create_user(
            username, email=email, sub=sub,
            first_name=first_name, last_name=last_name)

        self._assign_user_roles(user, claims)
        return user

    def update_user(self, user, claims):
        # Update user values
        user.first_name = claims.get('given_name')
        user.last_name = claims.get('family_name')
        user.email = claims.get('email')
        user.sub = claims.get('sub')
        user.username = generate_username(user.email)

        self._assign_user_roles(user, claims)
        return user

    def _assign_user_roles(self, user, claims):
        # Assign staff/superuser status based on Keycloak claims.  Users
        # without staff or superuser will be redirected back to the
        # Langstroth home page by the middleware ^^^.
        roles = claims.get(ROLE_CLAIM, [])
        user.is_staff = any(i in STAFF_ROLES for i in roles)
        user.is_superuser = any(i in ADMIN_ROLES for i in roles)
        if user.is_staff or user.is_superuser:
            outage_managers = outage_admin.get_outage_manager_group()
            outage_managers.user_set.add(user)
            # The permissions for the outage managers group will determine
            # what staff can do to objects via the admin interface.
            # Superusers can do anything ...

        user.save()

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified sub."""
        email = claims.get('email')
        sub = claims.get('sub')
        if not sub or not email:
            return self.UserModel.objects.none()

        users = self.UserModel.objects.filter(sub__iexact=sub)
        if not users:
            users = self.UserModel.objects.filter(
                email__iexact=email).filter(sub__isnull=True)
        return users


def generate_username(email):
    # Enabled with settings.OIDC_USERNAME_ALGO in settings.py
    # Using Python 3 and Django 1.11+, usernames can contain alphanumeric
    # (ascii and unicode), _, @, +, . and - characters. So we normalize
    # it and slice at 150 characters.
    # https://mozilla-django-oidc.readthedocs.io/en/stable/installation.html#generating-usernames
    return unicodedata.normalize('NFKC', email)[:150]
