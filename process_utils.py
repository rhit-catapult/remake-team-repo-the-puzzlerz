"""
Shared helper for launching sibling Puzzlerz scripts as fully
independent processes.

On Windows, terminals/IDEs often place a running script inside a job
object that kills all of its child processes the instant the parent
exits. Since every Puzzlerz screen deliberately closes itself right
after launching the next one (to avoid stacking duplicate windows),
that default behavior would silently kill the new window before it
ever gets to open -- with no error, no traceback, nothing. Passing
DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP breaks the new process out
of that job so it keeps running on its own.
"""

import subprocess
import sys


def launch_detached(args, cwd=None, env=None):
    """subprocess.Popen wrapper that survives the parent process
    exiting, even under terminals/IDEs that kill child processes on
    parent exit (a common Windows job-object behavior).

    `env`, if given, is passed straight through to Popen -- use this
    to hand off things like PUZZLER_GAME_TYPE or
    PUZZLER_ELAPSED_SECONDS to the next screen (e.g. CongratsScreen)."""
    kwargs = {}
    if cwd:
        kwargs["cwd"] = cwd
    if env is not None:
        kwargs["env"] = env

    if sys.platform.startswith("win"):
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        # POSIX equivalent: start a new session so it's not tied to
        # the parent's process group/terminal.
        kwargs["start_new_session"] = True

    return subprocess.Popen(args, **kwargs)