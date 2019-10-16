#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# pygdb.console.extension - python gdb console extension functions
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

"""GDB console python extension functions"""

import sys
import gdb
from pygdb.console.core import Frame, move_in_stack, \
    PyDictObjectPtr, PyInstanceObjectPtr, HeapTypeObjectPtr

__breakpoint_identifier = '_pygdb_breakpoint_mark'
__breakpoint_func = '_pygdb.breakpoint_mark()'


def term_color(*v):
    """
    set_term_color(text-type, text-color, background-color)
    text-type: 1: bold
               2: faded
               3: italic
               4: underlined
    text-color: 30: black
                31: red
                32: green
                33: yellow
                34: blue
                35: magneta
                36: cyan
    back-ground-color 40: black
                      41: red
                      42: green
                      43: yellow
                      44: blue
                      45: magneta
                      46: cyan
    set_term_color(0): #reset
    """

    return '\x1B['+';'.join(map(str, v))+'m'


def inject_pyframe(cmd, silently=False):
    """Inject python code *cmd* into selected frame"""

    result = gdb.execute("call PyGILState_Ensure()", to_string=True)
    gstate = result.split('=')[1].strip()
    if not silently:
        print "PyGILState_Ensure: %s" % gstate
    gdb.execute("call PyRun_SimpleString(\"%s\")" % cmd)
    gdb.execute("call PyGILState_Release(%s)" % gstate)


def get_pyframe_f_back(silently=False):
    """Get id of parent pyframe"""

    pyop_frame = get_selected_pyop()
    if not pyop_frame:
        return None

    return pyop_frame.f_back


def get_selected_pyop(silently=False):
    """Returns pyop for selected frame"""

    frame = Frame.get_selected_python_frame()
    if not frame:
        if not silently:
            print 'Unable to locate python frame'
        return None

    pyop = frame.get_pyop()
    if not pyop:
        if not silently:
            print 'Unable to read information on python frame'
        return None

    return pyop


def get_pyobject_value(name):
    """Returns pyobject value for *name*,
    supports nested pyobject values are supported"""

    name_arr = name.split('.')
    name_arr_len = len(name_arr)
    first_name = name_arr[0]

    pyop_frame = get_selected_pyop()
    if not pyop_frame:
        return (None, None)

    (pyop_var, scope) = pyop_frame.get_var_by_name(first_name)
    if not pyop_var:
        return (scope, None)

    cur_value = pyop_var
    for i in xrange(1, name_arr_len):
        next_name = name_arr[i]
        pyop_var_dict = None
        if isinstance(cur_value, PyDictObjectPtr):
            pyop_var_dict = pyop_var
        elif isinstance(cur_value, PyInstanceObjectPtr):
            pyop_var_dict = pyop_var.pyop_field('in_dict')
        elif isinstance(cur_value, HeapTypeObjectPtr):
            pyop_var_dict = cur_value.get_attr_dict()
        else:
            return (scope, None)
        cur_value = None
        if pyop_var_dict:
            # NOTE: pyop_var_dict does not support __getitem__
            for key, value in pyop_var_dict.iteritems():
                if str(key) == next_name:
                    cur_value = value
        if cur_value is None:
            break

    return (scope, cur_value)


def breakpoint_frame(silently=False):
    """Move to python frame with active breakpoint"""

    org_frame = gdb.selected_frame()
    gdb.newest_frame().select()
    pyop = get_selected_pyop()
    if not pyop:
        org_frame.select()
        return False
    line = pyop.current_line().strip()
    if line != __breakpoint_func:
        if not silently:
            print "No breakpoint found for current thread"
        org_frame.select()
        return False
    elif not silently:
        frame = Frame.get_selected_python_frame()
        frame.print_summary()

    return True


def breakpoint_caller_frame(silently=False):
    """Move to the frame that called the breakpoint frame"""
    status = breakpoint_frame(silently=silently)
    if status:
        more_frames = move_in_stack(move_up=True, silently=silently)
        if not more_frames:
            status = False

    return status


def list_pyframe(start=None, end=None):
    """List current python frame with active code line highlighted"""
    show_lines = 30
    pyop = get_selected_pyop()
    if not pyop:
        return

    filename = pyop.filename()
    lineno = pyop.current_line_num()

    if start is None:
        start = lineno - (show_lines/2)
        end = lineno + (show_lines/2)
    if end is None:
        end = start + show_lines
    if start < 1:
        start = 1

    thread = gdb.execute('thread', to_string=True)
    sys.stdout.write("%s%s:%s\n" % (thread, filename, lineno))
    with open(filename, 'r') as fh:
        all_lines = fh.readlines()
        # start and end are 1-based, all_lines is 0-based;
        for i, line in enumerate(all_lines[start-1:end]):

            display_lineno = int(i+start)
            # Highlight current line:
            # print color + sys.stdout.write(line[:-1])
            # is a hack to color the full line
            if display_lineno == lineno:
                color = term_color(0, 34, 47)
            else:
                color = term_color(0)
            print color
            sys.stdout.write("%d\t%s" % (display_lineno, line[:-1]))
    color = term_color(0)
    print color
    print ""
    fh.close()


def set_console_connected():
    """Tell 'pygdb.breakpoint' that gdb console is connected"""
    main_thread_num = gdb.selected_inferior().threads()[-1].num
    gdb.execute('thread %s' % main_thread_num)
    gdb.newest_frame().select()
    more_frames = True
    while more_frames:
        more_frames = move_in_stack(move_up=True, silently=True)
    (value_scope, value) = get_pyobject_value('pygdb')
    if value_scope and value \
            and (value.get_truncated_repr(sys.maxint)).startswith(
                '<module at remote'):
        result = True
        cmd = "pygdb.breakpoint.set_console_connected()"
        inject_pyframe(cmd)
    else:
        result = False
        print "Missing pygdb module in python script"

    return result


def attach(pid):
    """Attach process, mark gdb console as connected, delete old breakpoints,
    and continue until first breakpoint"""

    gdb.execute('attach %d' % pid)
    if set_console_connected():
        # Set breakpoint
        gdb.execute('break %s' % __breakpoint_identifier)
        gdb.execute('continue')
        breakpoint_list()


def list_threads():
    """List all threads for attached process"""
    # NOTE: threads[-1] is main thread
    threads = gdb.selected_inferior().threads()
    for thread in threads:
        print thread


def switch_thread(threadid, silently=False):
    """Change active thread to *threadid*"""
    cmd = "thread find Thread 0x%.x" % threadid
    thread_info = gdb.execute(cmd, to_string=True)
    thread_info_arr = thread_info.split(" ")
    if thread_info_arr[0] == 'No':
        if not silently:
            print "No Thread found with thread id: 0x%.x" % threadid
        return False
    else:
        cmd = "thread %s" % thread_info_arr[1]
        thread_switch = gdb.execute(cmd, to_string=True)
        if not silently:
            print thread_switch
        return True


def breakpoint_list(threadid=None, silently=False):
    """Display python code for breakpoint frame"""

    status = breakpoint_caller_frame(silently=True)
    if status:
        list_pyframe()
    elif not silently:
        if threadid:
            msg = "Unable to find breakpoint for thread: 0x%.x" % threadid
        else:
            msg = "Unable to find breakpoint for current thread"
        print msg


def breakpoint_continue():
    """Continue until next breakpoint and display it"""
    gdb.execute('continue')
    breakpoint_list()


def inspect_pyframe(show_globals=True, show_locals=True):
    """Display details about the current python frame"""

    pyframe_index = 0
    pyframe_f_back = get_pyframe_f_back()

    arguments = {'pyframe_index': pyframe_index,
                 'pyframe_f_back': pyframe_f_back,
                 'show_globals': show_globals,
                 'show_locals': show_locals}

    print "===================================================================="
    print "Output is written to gdb_logger if found otherwise to process stdout"
    print "===================================================================="

    cmd = \
        "from __future__ import print_function as __GDB_DEBUG_print_function; \
        import inspect as __GDB_DEBUG_inspect; \
        __GDB_DEBUG_logger = \
            print if not 'pygdb' in globals() \
            else pygdb.breakpoint.gdb_logger_debug; \
        __GDB_DEBUG_stack = __GDB_DEBUG_inspect.stack(); \
        __GDB_DEBUG_stack_len = len(__GDB_DEBUG_stack); \
        __GDB_DEBUG_frame = __GDB_DEBUG_stack[%(pyframe_index)d][0]; \
        __GDB_DEBUG_frameidx_func = lambda frame: \
            0 if not frame or id(frame.f_back) == %(pyframe_f_back)d \
            else 1 + __GDB_DEBUG_frameidx_func(frame.f_back); \
        __GDB_DEBUG_frameidx = __GDB_DEBUG_frameidx_func(__GDB_DEBUG_frame); \
        __GDB_DEBUG_frameidx = __GDB_DEBUG_frameidx \
            if __GDB_DEBUG_frameidx < __GDB_DEBUG_stack_len \
            else 0; \
        __GDB_DEBUG_frame, \
        __GDB_DEBUG_filename, \
        __GDB_DEBUG_line_number, \
        __GDB_DEBUG_function_name, \
        __GDB_DEBUG_lines, \
        __GDB_DEBUG_index = __GDB_DEBUG_stack[__GDB_DEBUG_frameidx]; \
        __GDB_DEBUG_logger(chr(10) \
            + '========================== py_inspect_frame ==========================' + chr(10) \
            + 'frame No.: ' + str(__GDB_DEBUG_frameidx) + chr(10) \
            + 'frame: ' + str(__GDB_DEBUG_frame) + chr(10) \
            + 'frame.f_back: ' + str(__GDB_DEBUG_frame.f_back) + chr(10) \
            + 'filename: ' + str(__GDB_DEBUG_filename) + chr(10) \
            + 'line_number: ' + str(__GDB_DEBUG_line_number) + chr(10) \
            + 'function_name: ' + str(__GDB_DEBUG_function_name) + chr(10) \
            + 'lines: ' + str(__GDB_DEBUG_lines) + chr(10) \
            + 'index: ' + str(__GDB_DEBUG_index) + chr(10) \
            + '----------------------------------------------------------------------' + chr(10) \
            + 'f_globals: ' + chr(10) \
            + '----------------------------------------------------------------------' + chr(10) \
            + chr(10).join(' = '.join((str(k),str(v))) for k,v in __GDB_DEBUG_frame.f_globals.items()\
                                if %(show_globals)s and not k.startswith('__GDB_DEBUG')) + chr(10) \
            + '----------------------------------------------------------------------' + chr(10) \
            + 'f_locals: ' + chr(10) \
            + '----------------------------------------------------------------------' + chr(10) \
            + chr(10).join(' = '.join((str(k),str(v))) for k,v in __GDB_DEBUG_frame.f_locals.items() \
                                if %(show_locals)s and not k.startswith('__GDB_DEBUG')) + chr(10) \
            + '======================== End py_inspect_frame ========================' + chr(10)); \
            [globals().pop(key) \
                for key in globals().keys() \
                    if key.startswith('__GDB_DEBUG_')]" % arguments

    inject_pyframe(cmd)


def set_pyframe_local(key, value):
    """Set local variable *key* to *value* in current python frame"""
    arguments = {'pyframe_index': 0,
                 'pyframe_f_back': get_pyframe_f_back(),
                 'key': key,
                 'value': value}
    cmd = \
        "from __future__ import print_function as __GDB_DEBUG_print_function; \
        import inspect as __GDB_DEBUG_inspect; \
        import ctypes as __GDB_DEBUG_ctypes; \
        __GDB_DEBUG_logger = \
            print if not 'pygdb' in globals() \
            else pygdb.breakpoint.gdb_logger_debug; \
        __GDB_DEBUG_stack = __GDB_DEBUG_inspect.stack(); \
        __GDB_DEBUG_stack_len = len(__GDB_DEBUG_stack); \
        __GDB_DEBUG_frame = __GDB_DEBUG_stack[%(pyframe_index)d][0]; \
        __GDB_DEBUG_frameidx_func = lambda frame: \
            0 if not frame or id(frame.f_back) == %(pyframe_f_back)d \
            else 1 + __GDB_DEBUG_frameidx_func(frame.f_back); \
        __GDB_DEBUG_frameidx = __GDB_DEBUG_frameidx_func(__GDB_DEBUG_frame); \
        __GDB_DEBUG_frameidx = __GDB_DEBUG_frameidx \
            if __GDB_DEBUG_frameidx < __GDB_DEBUG_stack_len \
            else 0; \
        __GDB_DEBUG_frame = __GDB_DEBUG_stack[__GDB_DEBUG_frameidx][0]; \
        __GDB_DEBUG_frame.f_locals['%(key)s'] = %(value)s; \
        __GDB_DEBUG_ctypes.pythonapi.PyFrame_LocalsToFast(\
                     __GDB_DEBUG_ctypes.py_object(__GDB_DEBUG_frame),\
                                              __GDB_DEBUG_ctypes.c_int(0)); \
        [globals().pop(key) \
            for key in globals().keys() \
                if key.startswith('__GDB_DEBUG_')]" % arguments

    inject_pyframe(cmd)


def pystep(skip_breakpoint_mark=True,
           file_prefix=None,
           silently=False,
           scheduler_locking=False):
    """Continue until control reaches a different python source line"""

    if scheduler_locking:
        status = gdb.execute('set scheduler-locking step', to_string=True)
    else:
        status = gdb.execute('set scheduler-locking off', to_string=True)
    if not silently:
        print status

    step_count = 0
    max_step_count = 10000
    pyop = get_selected_pyop(silently=silently)
    if not pyop:
        return
    start_filepath = filepath = pyop.filename()
    start_lineno = lineno = pyop.current_line_num()
    line = pyop.current_line().strip()
    while (start_filepath == filepath and start_lineno == lineno) \
            or (skip_breakpoint_mark and line == __breakpoint_func) \
            or (file_prefix and not filepath.startswith(file_prefix)):
        step_msg = gdb.execute('step', to_string=True)
        gdb.newest_frame().select()
        pyop = get_selected_pyop(silently=silently)
        if not pyop:
            break
        filepath = pyop.filename()
        lineno = pyop.current_line_num()
        line = pyop.current_line().strip()
        step_count += 1
        if step_count > max_step_count:
            break

    if not silently:
        print "#steps: %s" % step_count
        list_pyframe()

    if step_count > max_step_count:
        sys.stdout.write(term_color(0, 31))
        print "WARNING: Stopped after max steps: %s" % max_step_count
        sys.stdout.write(term_color(0))


def pynext(skip_breakpoint_mark=True,
           file_prefix=None,
           scheduler_locking=False,
           silently=False):
    """Continue until control reaches a different python source line in current frame"""

    if scheduler_locking:
        status = gdb.execute('set scheduler-locking on', to_string=True)
    else:
        status = gdb.execute('set scheduler-locking off', to_string=True)
    if not silently:
        print status

    next_count = 0
    max_next_count = 10000
    pyop = get_selected_pyop(silently=silently)
    if not pyop:
        return
    start_filepath = filepath = pyop.filename()
    start_lineno = lineno = pyop.current_line_num()
    line = pyop.current_line().strip()
    while (start_filepath == filepath and start_lineno == lineno) \
            or (skip_breakpoint_mark and line == __breakpoint_func) \
            or (file_prefix and not filepath.startswith(file_prefix)):
        next_msg = gdb.execute('next', to_string=True)
        gdb.newest_frame().select()
        pyop = get_selected_pyop(silently=silently)
        if not pyop:
            break
        filepath = pyop.filename()
        lineno = pyop.current_line_num()
        line = pyop.current_line().strip()
        next_count += 1

        if next_count > max_next_count:
            break

    if not silently:
        print "#next: %s" % next_count
        list_pyframe()

    if next_count > max_next_count:
        sys.stdout.write(term_color(0, 31))
        print "WARNING: Stopped after max next's: %s" % max_next_count
        sys.stdout.write(term_color(0))
