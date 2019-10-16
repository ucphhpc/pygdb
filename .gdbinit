# --- BEGIN_HEADER ---
#
# .gdbinit - GDB console init file for Python GDB debugger
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

# TODO: Look at color filters: https://github.com/daskol/gdb-colour-filter

# Disable prompt for console output pages
set pagination off 

# Load pygdb commands
# https://sourceware.org/gdb/onlinedocs/gdb/Python-API.html

define py-init    
    python import sys
    python if 'pygdb.console.commands' in sys.modules: del sys.modules['pygdb.console.commands']
    python if 'pygdb.console.core' in sys.modules: del sys.modules['pygdb.console.core']
    python if 'pygdb.console.extensions' in sys.modules: del sys.modules['pygdb.console.extensions']
    python if 'pygdb.console' in sys.modules: del sys.modules['pygdb.console']
    python if 'pygdb' in sys.modules: del sys.modules['pygdb']
    python if 'pyext' in globals(): del globals()['pyext']
    python import pygdb.console.commands
    python import pygdb.console.extensions as pyext
    python pygdb.console.commands.register()
end