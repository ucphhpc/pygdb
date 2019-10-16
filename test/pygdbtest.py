#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# pygdbtest.py - Test program for python GDB debugger
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

"""Test program for python GDB debugger"""

import sys
import threading
import time
import traceback
import logging
import pygdb.breakpoint

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: pygdb: %(message)s')
pygdb.breakpoint.enable(logger=logging.getLogger())


def test(threadid, counter):
    """Test function"""
    print "0x%0.X: Called test with counter: %d" % (threadid, counter)
    print "0x%0.X: test breakpoint" % threadid
    pygdb.breakpoint.set()
    print "0x%0.X: Counter value is %d" % (threadid, counter)
    print "0x%0.X: All done!" % threadid


class TestThread(threading.Thread):
    """Python Test Thread"""

    def __init__(self):
        """Init thread"""
        threading.Thread.__init__(self)
        self.shutdown = threading.Event()
        self.counter = 0

    def run(self):
        """Start thread"""
        print "Starting TestThread: 0x%0.X" % self.ident
        sleeptime = 1

        while not self.shutdown.is_set():
            time.sleep(sleeptime)
            print "0x%0.X: Thread woke up" % self.ident
            test(self.ident, self.counter)
            self.counter += 1
            # print "shutdown"
            # self.shutdown.set()
            # print "shutdown: %s" % self.shutdown.is_set()

    def stop(self):
        """Stop thread"""
        print "Stopping TestThread: 0x%0.X" % self.ident
        self.shutdown.set()
        print "0x%0.X: stop: Shutdown set" % self.ident
        self.join()
        print "0x%0.X: stop: joined" % self.ident


def gdbtest(threadcount):
    """Start gdbtest"""
    print "Initializing using #threads: %d" % threadcount
    main_threadid = threading.current_thread().ident

    if threadcount == 0:
        counter = 0
        while True:
            test(main_threadid, counter)
            counter += 1
    else:
        threadlist = []
        for _ in xrange(threadcount):
            threadlist.append(TestThread())
        try:
            active_count = 0
            for thread in threadlist:
                thread.start()
                active_count += 1
            while active_count > 0:
                time.sleep(1)
                for thread in threadlist:
                    if thread.shutdown.is_set():
                        print "run: shutdown.is_set for thread 0x%0.X" \
                            % thread.ident
                        thread.join()
                        print "run: joined thread 0x%0.X" % thread.ident
                        active_count -= 1
                        print "run: Active threads: %d" % active_count
        except KeyboardInterrupt:
            for thread in threadlist:
                thread.stop()
            # forward KeyboardInterrupt to main thread
            raise
        except Exception:
            for thread in threadlist:
                thread.stop()
            raise


if __name__ == "__main__":
    argc = len(sys.argv)-1
    if argc != 1:
        print "USAGE: %s #threads" % sys.argv[0]
        sys.exit(1)
    threadcount = int(sys.argv[1])
    try:
        gdbtest(threadcount)
    except KeyboardInterrupt:
        info_msg = "Received user interrupt"
        print info_msg
    except Exception, exc:
        print "exiting on unexpected exception: %s" % exc
        print traceback.format_exc()
