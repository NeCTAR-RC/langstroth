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

from .defaults import *  # NOQA

exec(open("/etc/langstroth/settings.py", "rb").read())
