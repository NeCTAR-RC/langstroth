import logging
import zoneinfo

from django.utils import timezone

from tz_detect.utils import offset_to_timezone


logger = logging.getLogger(__name__)


class TimezoneMiddleware:
    """Activate the request timezone detected by django-tz-detect.

    This replaces ``tz_detect.middleware.TimezoneMiddleware``, which
    activates a *pytz* timezone object. Django 5.0 dropped pytz support,
    so ``timezone.make_aware`` no longer special-cases pytz and instead
    does ``value.replace(tzinfo=tz)``. Attaching a pytz zone that way
    yields its Local Mean Time offset (e.g. Australia/Melbourne is
    +09:39:52, ~20 minutes off AEST) rather than the standard offset.
    Form rendering still converts via ``astimezone``, which pytz handles
    correctly, so every datetime round-tripped through a form (notably
    the Django admin's Outage start/planned_end/end fields) was saved
    ~20 minutes later than entered.

    Activating a ``zoneinfo`` zone instead computes the offset for the
    actual instant, so render and save agree.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz = request.session.get("detected_tz")
        if tz:
            zone = self._resolve(tz)
            if zone is not None:
                # ``request.timezone_active`` tells the {% tz_detect %}
                # template tag the timezone is already set, so it skips
                # re-emitting the detector script.
                request.timezone_active = True
                timezone.activate(zone)
            else:
                timezone.deactivate()
        else:
            timezone.deactivate()
        return self.get_response(request)

    def _resolve(self, tz):
        """Resolve a stored ``detected_tz`` value to a zoneinfo zone.

        The session stores either an IANA name (modern browsers report
        ``Intl.DateTimeFormat().resolvedOptions().timeZone``) or, as a
        fallback, an integer minutes offset. Legacy sessions may hold a
        pytz object; ``str()`` of either a pytz or zoneinfo zone is the
        IANA name.
        """
        if isinstance(tz, int):
            # offset_to_timezone returns a pytz zone; take its name.
            tz = str(offset_to_timezone(tz))
        elif not isinstance(tz, str):
            tz = str(tz)
        try:
            return zoneinfo.ZoneInfo(tz)
        except (zoneinfo.ZoneInfoNotFoundError, ValueError):
            logger.warning("Ignoring unknown detected timezone: %r", tz)
            return None
