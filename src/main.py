#!/usr/bin/env python3
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# This is set to True when the startup was successful.
successStartup = False

import better_exchook
better_exchook.install()

import sys

try:
	import faulthandler
	# Only enable if we don't execute from within the MusicPlayer binary.
	# The MusicPlayer binary will setup its own crash handlers.
	# Import the `faulthandler` module though, we might use it.
	if not getattr(sys, "MusicPlayerBin", None):
		faulthandler.enable(all_threads=True)
except ImportError:
	print("note: faulthandler module not available")
	faulthandler = None

# Do this early to do some option parsing and maybe special handling.
import appinfo

# Early check for "--profile".
# Enable profiling.
if __name__ == '__main__' and appinfo.args.profile:
	# No try/except. If requested and it fails -> exit.
	import cProfile
	profiler = cProfile.Profile()
	# Note that this should be done outside of main() because
	# otherwise it would not really profile the main() itself.
	profiler.enable()
else:
	profiler = None

# Early check for "--addsyspythonpaths".
# Add System Python paths.
if __name__ == '__main__' and appinfo.args.addsyspythonpaths:
	import debug
	debug.addSysPythonPath()


def handleApplicationInit():
	import ModuleSystem

	if not appinfo.args.nomodstartup:
		for m in ModuleSystem.modules: m.start()
	else:
		# In some cases, we at least need some modules. Start only those.
		if appinfo.args.shell:
			ModuleSystem.getModule("stdinconsole").start()

	global successStartup
	successStartup = True


def main():
	import sys, os
	from pprint import pprint

	# Early check for forked process.
	if appinfo.args.forkExecProc:
		# Only import utils now for this case.
		# Otherwise, I want "--pyshell" to be without utils loaded.
		import TaskSystem
		TaskSystem.ExecingProcess.checkExec()

	# Early check for "--pyshell".
	# This is a simple debug shell where we don't load anything.
	if appinfo.args.pyshell:
		better_exchook.simple_debug_shell({}, {})
		raise SystemExit

	# Early check for "--pyexec".
	# This is a simple Python execution where we don't load anything.
	if appinfo.args.pyexec:
		sourcecode = appinfo.args.pyexec[0]
		exec(compile(sourcecode, "<pyexec>", "exec"))
		raise SystemExit

	import utils
	import time

	print("MusicPlayer", appinfo.version, "from", appinfo.buildTime, "git-ref", appinfo.gitRef[:10], "on", appinfo.platform, "(%s)" % sys.platform)
	print("startup on", utils.formatDate(time.time()))

	utils.setCurThreadName("Python main")

	try:
		# Hack: Make the `__main__` module also accessible as `main`.
		mainmod = sys.modules["__main__"]
		sys.modules.setdefault("main", mainmod)
		del mainmod
	except Exception:
		sys.excepthook(*sys.exc_info())
		# doesn't matter, continue

	# Import PyObjC here. This is because the first import of PyObjC *must* be
	# in the main thread. Otherwise, the NSAutoreleasePool created automatically
	# by PyObjC on the first import would be released at exit by the main thread
	# which would crash (because it was created in a different thread).
	# http://pyobjc.sourceforge.net/documentation/pyobjc-core/intro.html
	objc, AppKit = None, None
	try:
		import objc
	except Exception:
		if sys.platform == "darwin":
			print("Error while importing objc")
			sys.excepthook(*sys.exc_info())
		# Otherwise it doesn't matter.
	try:
		# Seems that the `objc` module is not enough. Without `AppKit`,
		# I still get a lot of
		#   __NSAutoreleaseNoPool(): ... autoreleased with no pool in place - just leaking
		# errors.
		if objc:
			import AppKit
	except Exception:
		# Print error in any case, also ImportError, because we would expect that this works.
		print("Error while importing AppKit")
		sys.excepthook(*sys.exc_info())

	# Import core module here. This is mostly as an early error check.
	try:
		import musicplayer
	except Exception:
		print("Error while importing core module! This is fatal.")
		sys.excepthook(*sys.exc_info())
		print("Environment:")
		pprint(os.environ)
		sys.exit(1)

	# Import gui module here. Again, mostly as an early error check.
	# If there is no gui, the module should still load and provide
	# dummy functions where appropriate.
	import gui

	# Default quit handling.
	# Note that this is executed after `threading._shutdown`, i.e. after
	# all non-daemon threads have finished.
	import atexit
	atexit.register(gui.handleApplicationQuit)

	# Import some core modules. They propagate themselves to other
	# subsystems, like GUI.
	# XXX: Maybe move all this to `State` module?
	import State
	import Preferences
	import Search
	import SongEdit

	# This will overtake the main loop and raise SystemExit at its end,
	# or never return.
	# It also just might do nothing.
	gui.main()
	# If we continue here, we can setup our own main loop.

	# We have no GUI. Continue with some simple console control handling.
	import stdinconsole

	handleApplicationInit()

	# Note on quit behavior: Simply iterating state.updates
	# and waiting for its end does not work because we would
	# not interrupt on signals, e.g. KeyboardInterrupt.
	# It is also not possible (in general) to catch
	# signals from other threads, thus we have to do it here.
	# time.sleep() is a good way to wait for signals.
	# However, we use stdinconsole.readNextInput() because
	# there is simply no way to have os.read() in another thread
	# and to be able to interrupt that from here (the main thread).
	# In other threads: thread.interrupt_main() does not work
	# for time.sleep() (or at least it will not interrupt the sleep).
	# os.kill(0, signal.SIGINT) works, though.
	# To interrupt/stop all threads:
	# signal.set_wakeup_fd(sys.stdin.fileno()) also does not really
	# work to interrupt the stdin thread, probably because stdin is
	# not non-blocking.
	# Every thread must only wait on a OnRequestQueue which registers
	# itself in its thread. We cancelAll() here already the main queue
	# (state.updates) and in Module.stop(), we also cancel any custom
	# queue.

	while True:
		try:
			stdinconsole.readNextInput()  # wait for KeyboardInterrupt
		except BaseException as e:
			State.state.updates.put((e, (), {}))
			State.state.updates.cancelAll()
			break


if __name__ == '__main__':
	main()

