
from django.conf import settings

from keystoneauth1.identity import v3
from keystoneauth1 import session


def get_auth_session():
    username = settings.KEYSTONE_USERNAME
    password = settings.KEYSTONE_PASSWORD
    project_name = settings.KEYSTONE_PROJECT_NAME
    auth_url = settings.KEYSTONE_AUTH_URL

    auth = v3.Password(username=username,
                       password=password,
                       project_name=project_name,
                       auth_url=auth_url,
                       user_domain_id='default',
                       project_domain_id='default')
    return session.Session(auth=auth)
