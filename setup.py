#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# setup.py - Setup for Python GDB debugger
# Copyright (C) 2019  The pygdb Project lead by Brian Vinter
#
# This file is part of pygdb.
#
# pygdb is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# pygdb is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# -- END_HEADER ---
#
from setuptools import setup, Extension

from pygdb import version_string, short_name, project_team, \
    project_email, short_desc, long_desc, project_url, download_url, \
    license_name, project_class, project_keywords, versioned_requires, \
    project_requires, project_extras, project_platforms, maintainer_team, \
    maintainer_email

setup(
    name=short_name,
    version=version_string,
    description=short_desc,
    long_description=long_desc,
    author=project_team,
    author_email=project_email,
    maintainer=maintainer_team,
    maintainer_email=maintainer_email,
    url=project_url,
    download_url=download_url,
    license=license_name,
    classifiers=project_class,
    keywords=project_keywords,
    platforms=project_platforms,
    install_requires=versioned_requires,
    requires=project_requires,
    extras_require=project_extras,
    packages=['pygdb', 'pygdb.console'],
    package_dir={'pygdb': 'pygdb',
                 'pygdb.console': 'pygdb/console'},
    ext_modules = [
        Extension('_pygdb', ['pygdb/_breakpoint.c'],
          define_macros=[('NDEBUG', '0')],),
        ]
    )