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

import logging
import os
import stat

from django.core.exceptions import ImproperlyConfigured

from langstroth.defaults import *  # NOQA


# Fixes "No handlers could be found for logger"
logging.basicConfig()

LOG = logging.getLogger(__name__)

CUSTOM_SETTINGS_PATH = "/etc/langstroth/settings.py"
if os.path.exists(CUSTOM_SETTINGS_PATH):
    # Refuse to load if the override file is writable by group or other.
    # exec() of an attacker-writable file is arbitrary code execution.
    st = os.stat(CUSTOM_SETTINGS_PATH)
    if st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise ImproperlyConfigured(
            f"Refusing to load {CUSTOM_SETTINGS_PATH}: file is writable "
            "by group or other. Restrict to owner-only writes (chmod 600 "
            "or 644)."
        )
    with open(CUSTOM_SETTINGS_PATH, "rb") as f:
        source = f.read()
    # compile() with the real path gives tracebacks that point at the
    # override file instead of "<string>".
    exec(compile(source, CUSTOM_SETTINGS_PATH, "exec"))
else:
    LOG.warning(f"Missing custom settings file: {CUSTOM_SETTINGS_PATH}. ")
