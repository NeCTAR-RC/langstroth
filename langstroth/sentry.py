import logging
import os
from urllib.parse import quote
from urllib.parse import urlsplit

import pbr.version
import sentry_sdk


LOG = logging.getLogger(__name__)


def _release():
    """Return "langstroth@<version>", or None if pbr can't tell.

    The production container copies the source tree without installing
    the package or its git metadata, so pbr may not be able to derive
    a version there. Returning None lets sentry-sdk fall back to the
    SENTRY_RELEASE environment variable, if set.
    """
    try:
        version = pbr.version.VersionInfo("langstroth").release_string()
    except Exception:
        return None
    return f"langstroth@{version}"


def security_endpoint(dsn=None, environment=None):
    """Return the GlitchTip/Sentry security endpoint URL, or None.

    Browsers can POST CSP violation reports to this endpoint (the CSP
    report-uri directive). It is derived from the DSN:
    scheme://key@host/project becomes
    scheme://host/api/project/security/?sentry_key=key.
    Returns None when no DSN is set (SENTRY_DSN in the settings
    override file or the SENTRY_DSN environment variable).
    """
    dsn = dsn or os.environ.get("SENTRY_DSN")
    if not dsn:
        return None
    parts = urlsplit(dsn)
    prefix, _, project = parts.path.rstrip("/").rpartition("/")
    if not (parts.scheme and parts.username and parts.hostname and project):
        LOG.warning("Can't derive a security endpoint from SENTRY_DSN")
        return None
    host = parts.hostname
    if parts.port:
        host = f"{host}:{parts.port}"
    endpoint = (
        f"{parts.scheme}://{host}{prefix}/api/{project}/security/"
        f"?sentry_key={parts.username}"
    )
    if environment:
        endpoint += f"&sentry_environment={quote(environment)}"
    return endpoint


def setup(dsn=None, environment=None):
    """Enable error reporting to GlitchTip/Sentry.

    A no-op unless a DSN is set (SENTRY_DSN in the settings override
    file or the SENTRY_DSN environment variable). Once enabled, the
    sentry-sdk default integrations report unhandled exceptions and
    ERROR level log messages.
    """
    dsn = dsn or os.environ.get("SENTRY_DSN")
    if not dsn:
        return False
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=_release(),
        # GlitchTip does not support sessions
        auto_session_tracking=False,
    )
    LOG.debug("Sentry error reporting enabled")
    return True
