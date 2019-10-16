/* --- BEGIN_HEADER ---

_breakpoint - Shared library functions for Python GDB breakpoint
Copyright (C) 2019  The pygdb Project lead by Brian Vinter

This file is part of pygdb.

pygdb is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

pygdb is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

-- END_HEADER --- */

#include <Python.h>

// NOTE: We need a non-static function for the GDB breakpoint
PyObject* _pygdb_breakpoint_mark() {
	return Py_BuildValue("");
}

static PyObject* breakpoint_mark(PyObject* self) {
	return _pygdb_breakpoint_mark();
}

static char breakpoint_mark_docs[] = \
    "Used for python GDB breakpoints.\n";

static PyMethodDef breakpoint_mark_funcs[] = {
    {"breakpoint_mark",
    (PyCFunction)breakpoint_mark,
    METH_NOARGS,
    breakpoint_mark_docs},
    {NULL}
};

void init_pygdb(void) {	
    Py_InitModule3("_pygdb", breakpoint_mark_funcs, breakpoint_mark_docs);
}
