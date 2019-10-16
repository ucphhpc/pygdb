# pygdb
Python extension for the [GNU project debugger (GDB)](https://www.gnu.org/software/gdb/)

## Introduction

This package provides a set of tools for debugging python code with GDB, including python code breakpoints.
GDB breakpoints operate on native shared libraries (C/assembler code). Since python is an interpreted language it's not possible to set python code breakpoints directly from the GDB console.
In this package python code breakpoints are supported by utilizing a python-c-extension breakpoint-mark function which is accessible from the GDB console. This method requires
that python code breakpoints are set explictly in the python code.

## Dependencies
GDB python: https://wiki.python.org/moin/DebuggingWithGdb

## Install
From source:
`pip install .`

Latest release:
`pip install pygdb`

Copy [.gdbinit](https://github.com/ucphhpc/pygdb/blob/master/.gdbinit) to `~/.gdbinit`

## Literature
https://devguide.python.org/gdb/

https://sourceware.org/gdb/onlinedocs/gdb/Python-API.html

## Usage
### Python code breakpoints
Breakpoints are set explicitly in the python code:
```
import pygdb.breakpoint
pygdb.breakpoint.enable()

def Test():
  print "Before breakpoint"
  pygdb.breakpoint.set()
  print "After breakpoint"
```

__NOTE__: pygdb.breakpoint.set() busy-waits until the python process is attached to the GDB console using the `py-attach` command (see below)

Pygdb breakpoint messages are written to stderr unless a [Python logger](https://docs.python.org/2/library/logging.html) is provided:
```
import logging
import pygdb.breakpoint

logging.basicConfig(level=logging.INFO)
pygdb.breakpoint.enable(logger=logging.getLogger())
```

### GDB console

Launch GDB in python-mode from the shell

`$> gdb python`

Add source-path if not current shell directory

`gdb> dir PATH`

Init the pygdb framework

`gdb> py-init`

Attach GDB console to the python process with PID, notify pygdb.breakpoint that the console is connected
and continue until the native GDB breakpoint

`gdb> py-attach PID`

#### command list

__NOTE__: The GDB console supports tab-completion.

All GDB console commands added by this packages are prefixed with `py-`

For each command use --help for detailed help.
```
py-init:            Initializes pygdb commands and extensions
py-info-procs:      Display list of attached processes
py-info-threads:    Display list of attached process threads
py-attach:          Attach python process to gdb console
py-detach:          Detach python process from gdb console
py-thread:          Change python thread in attached process
py-breakpoint:      Find and display code for python breakpoint
py-step:            Continue until control reaches a different python source line
py-next:            Continue until control reaches a different python source line in current frame
py-continue:        Continue until next python breakpoint and display code
py-list:            Display code for current python frame
py-backtrace:       Display current python frame and all the frames within its call stack (if any)
py-inspect-frame:   Display information about the current python frame
py-builtins:        Display builtin varialbes for current python frame
py-globals:         Display global variables for current python frame
py-locals:          Display local variables for current python frame
py-print:           Display python frame variable (if it exists)
py-set-local:       Set local variable in current python frame
py-up:              Select and display code for the python stack frame that called this one (if any)
py-down:            Select and display code for the python stack frame called by this one (if any)
py-inject:          Inject python code into current python frame
```
