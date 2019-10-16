#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# pygdb.console.commands - python gdb console commands
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

"""Python gdb console commands"""

import re
import gdb
from pygdb.console.core import Frame, move_in_stack, \
    PyObjectPtr, PyDictObjectPtr, PyInstanceObjectPtr, HeapTypeObjectPtr, \
    MAX_OUTPUT_LEN

from pygdb.console.extensions import attach, \
    breakpoint_continue, breakpoint_list, \
    get_pyobject_value, inject_pyframe, inspect_pyframe, \
    list_pyframe, pystep, pynext, set_pyframe_local, switch_thread

commands = None


def help():
    """Display help for all commands"""
    global commands
    if not commands:
        register()
    for cmd in commands:
        print "-------------------------------------------------------------------------------"
        cmd.help()
    print "-------------------------------------------------------------------------------"


def register():
    """Register new commands to the GDB console"""
    global commands
    commands = [
        cmd_py_info_procs('py-info-procs'),
        cmd_py_info_threads('py-info-threads'),
        cmd_py_attach('py-attach'),
        cmd_py_detach('py-detach'),
        cmd_py_thread('py-thread'),
        cmd_py_breakpoint('py-breakpoint'),
        cmd_py_step('py-step'),
        cmd_py_next('py-next'),
        cmd_py_continue('py-continue'),
        cmd_py_list('py-list'),
        cmd_py_backtrace('py-backtrace'),
        cmd_py_inspect_frame('py-inspect-frame'),
        cmd_py_builtins('py-builtins'),
        cmd_py_globals('py-globals'),
        cmd_py_locals('py-locals'),
        cmd_py_print('py-print'),
        cmd_py_set_local('py-set-local'),
        cmd_py_up('py-up'),
        cmd_py_down('py-down'),
        cmd_py_inject("py-inject")
    ]


class cmd_py_info_procs(gdb.Command):
    """Display list of attached processes"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return
        gdb.execute('info inferior')


class cmd_py_info_threads(gdb.Command):
    """Display list of attached process threads"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return
        gdb.execute('info threads')


class cmd_py_attach(gdb.Command):
    """Attach python process (PID) to gdb console"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s PID" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return
        try:
            pid = int(args)
        except:
            self.help()
            return

        # Reset GDB environment including old breakpoints

        try:
            gdb.execute('delete')
        except Exception:
            pass

        # Attach pid

        attach(pid)

        # Re-register pygdb commands

        register()


class cmd_py_detach(gdb.Command):
    """Detach python process (GDB-PROCESS-NUM) from gdb console"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s GDB-PROCESS-NUM" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return
        try:
            num = int(args)
        except:
            self.help()
            return
        gdb.execute("detach inferior %d" % num)


class cmd_py_thread(gdb.Command):
    """Switch to python thread id (TID)"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s TID" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return
        try:
            threadid = int(args, 16)
        except:
            self.help()
            return
        switch_thread(threadid)


class cmd_py_breakpoint(gdb.Command):
    """Find and display code for python breakpoint
    Switch to optional python thread id (TID) if provided"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s [TID]" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return
        threadid = None
        try:
            if args:
                threadid = int(args, 16)
        except:
            self.help()
            return
        breakpoint_list(threadid=threadid)


class cmd_py_step(gdb.Command):
    """Continue until control reaches a different python source line"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        file_prefix = None
        if args:
            file_prefix = args
        pystep(file_prefix=file_prefix)


class cmd_py_next(gdb.Command):
    """Continue until control reaches a different python source line in current frame"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        file_prefix = None
        if args:
            file_prefix = args
        pynext(file_prefix=file_prefix)


class cmd_py_continue(gdb.Command):
    """Continue until next python breakpoint and display code"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return
        breakpoint_continue()


class cmd_py_list(gdb.Command):
    """Display code for current python frame

    Use argument:
       START
    to list at a different line number within the python source.

    Use argument:
       START, END
    to list a specific range of lines within the python source.
    """

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_FILES,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s [start] [end]" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        start = None
        end = None

        m = re.match(r'\s*(\d+)\s*', args)
        if m:
            start = int(m.group(0))

        m = re.match(r'\s*(\d+)\s*,\s*(\d+)\s*', args)
        if m:
            start, end = map(int, m.groups())

        list_pyframe(start=start, end=end)


class cmd_py_backtrace(gdb.Command):
    """Display current python frame and all the frames within its call stack (if any)"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_STACK,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        frame = Frame.get_selected_python_frame()
        while frame:
            if frame.is_evalframeex():
                frame.print_summary()
            frame = frame.older()


class cmd_py_inspect_frame(gdb.Command):
    """Display information about the current python frame"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s [start] [end]" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        inspect_pyframe()


class cmd_py_builtins(gdb.Command):
    """Display builtin varialbes for current python frame"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        frame = Frame.get_selected_python_frame()
        if not frame:
            print "Unable to locate python frame"
            return

        pyop_frame = frame.get_pyop()
        if not pyop_frame:
            print "Unable to read information on python frame"
            return

        for pyop_name, pyop_value in pyop_frame.iter_builtins():
            print('%s = %s'
                  % (pyop_name.proxyval(set()),
                      pyop_value.get_truncated_repr(MAX_OUTPUT_LEN)))


class cmd_py_globals(gdb.Command):
    """Display global variables for current python frame"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        frame = Frame.get_selected_python_frame()
        if not frame:
            print "Unable to locate python frame"
            return

        pyop_frame = frame.get_pyop()
        if not pyop_frame:
            print "Unable to read information on python frame"
            return

        for pyop_name, pyop_value in pyop_frame.iter_globals():
            print('%s = %s'
                  % (pyop_name.proxyval(set()),
                      pyop_value.get_truncated_repr(MAX_OUTPUT_LEN)))


class cmd_py_locals(gdb.Command):
    """Display local variables for current python frame"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        frame = Frame.get_selected_python_frame()
        if not frame:
            print "Unable to locate python frame"
            return

        pyop_frame = frame.get_pyop()
        if not pyop_frame:
            print "Unable to read information on python frame"
            return

        for pyop_name, pyop_value in pyop_frame.iter_locals():
            print('%s = %s'
                  % (pyop_name.proxyval(set()),
                      pyop_value.get_truncated_repr(MAX_OUTPUT_LEN)))


class cmd_py_print(gdb.Command):
    """Display python frame variable (if it exists)
    Nested dictionary and object values are displayed using dots

    Use argument:
        x
    to display value for variable x

    Use argument:
        x.y
    to display value y for dictionary/object variable x
    """

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        name = str(args)
        if name == "--help":
            self.help()
            return

        (scope, value) = get_pyobject_value(name)
        if value:
            value_dict = {}
            if isinstance(value, PyDictObjectPtr):
                value_dict = value
            elif isinstance(value, PyInstanceObjectPtr):
                value_dict = value.pyop_field('in_dict')
            elif isinstance(value, HeapTypeObjectPtr):
                value_dict = value.get_attr_dict()
            if value_dict:
                print "------------------------------------------------------------------------------"
                print "(%s) %s:" % (scope, name)
                print "------------------------------------------------------------------------------"
                for key, val in value_dict.iteritems():
                    if isinstance(key, PyObjectPtr):
                        key = key.get_truncated_repr(MAX_OUTPUT_LEN)
                    print "%s = %s" % (key, val.get_truncated_repr(MAX_OUTPUT_LEN))
                print "------------------------------------------------------------------------------"
            else:
                print "(%s) %s = %s" \
                    % (scope,
                       name,
                       value.get_truncated_repr(MAX_OUTPUT_LEN))
        else:
            print "%r not found" % name


class cmd_py_set_local(gdb.Command):
    """Set local variable in current python frame"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        key, value = args.split(" ")
        set_pyframe_local(key, value)


class cmd_py_up(gdb.Command):
    """Select and display code for the python stack frame that called this one (if any)"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_STACK,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        result = move_in_stack(move_up=True, silently=True)
        if result:
            list_pyframe()
        else:
            print "Unable to find an older python frame"


class cmd_py_down(gdb.Command):
    """Select and display code for the python stack frame called by this one (if any)"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_STACK,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        result = move_in_stack(move_up=False, silently=True)
        if result:
            list_pyframe()
        else:
            print "Unable to find an newer python frame"


class cmd_py_inject(gdb.Command):
    """Inject python code into current python frame"""

    name = None

    def __init__(self, name):
        self.name = name
        gdb.Command.__init__(self,
                             self.name,
                             gdb.COMMAND_DATA,
                             gdb.COMPLETE_COMMAND)

    def help(self):
        print "USAGE: %s" % self.name
        print ""
        doc_arr = self.__doc__.split('\n')
        for ent in doc_arr:
            print ent.strip()

    def invoke(self, args, from_tty):
        if str(args) == "--help":
            self.help()
            return

        cmd = str(args)
        inject_pyframe(cmd)
