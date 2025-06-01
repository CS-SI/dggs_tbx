# Copyright (C) 2024-2025 CS GROUP, https://cs-soprasteria.com
#
# This file is part of DGGS Toolbox:
#
#     https://github.com/CS-SI/dggs_tbx
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
# DGGS Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# DGGS Toolbox is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with DGGS Toolbox. If not, see
# https://www.gnu.org/licenses/.

"""
    Setup file for dggs_tbx.
    Use setup.cfg to configure your project.

    This file was generated with PyScaffold 4.3.
    PyScaffold helps you to put up the scaffold of your new Python project.
    Learn more under: https://pyscaffold.org/
"""
from setuptools import setup

if __name__ == "__main__":
    try:
        setup(use_scm_version={"version_scheme": "no-guess-dev"})
    except:  # noqa
        print(
            "\n\nAn error occurred while building the project, "
            "please ensure you have the most updated version of setuptools, "
            "setuptools_scm and wheel with:\n"
            "   pip install -U setuptools setuptools_scm wheel\n\n"
        )
        raise
