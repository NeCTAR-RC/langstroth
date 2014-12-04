# -*- coding: utf-8 -*-
#
# Copyright 20014-2014 NeCTAR
#
# This file is part of Langstroth.
#
# Langstroth is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Langstroth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Langstroth  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
from .defaults import *  # NOQA


# Fixes "No handlers could be found for logger"
logging.basicConfig()

LOG = logging.getLogger(__name__)

CUSTOM_SETTINGS_PATH = "/etc/langstroth/settings.py"
if os.path.exists(CUSTOM_SETTINGS_PATH):
    exec(open(CUSTOM_SETTINGS_PATH, "rb").read())
else:
    LOG.warn("Missing custom settings file: %s. " % CUSTOM_SETTINGS_PATH)

if SITE_DOMAIN == "":
    LOG.warn("Define SITE_DOMAIN in the settings file. "
             "Currently SITE_DOMAIN = %s. "
             "This is needed for the sitemap consistency check. "
             % SITE_DOMAIN)

# Need to import Site AFTER the database settings are loaded.
from django.contrib.sites.models import Site

try:
    current_site = Site.objects.get_current()
    if SITE_DOMAIN != current_site.domain:
        LOG.warn("Missing sites domain definition. "
                 "This is needed to generate a valid sitemap. ")
except Site.DoesNotExist:
    LOG.warn("Site is not defined in the database table django_site. ")
