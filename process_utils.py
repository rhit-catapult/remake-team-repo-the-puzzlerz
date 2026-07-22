"""
Shared helpers for the Puzzlerz scripts:

1. launch_detached(...)   -- spawn a sibling script as a fully
   independent process (see docstring below for why this matters).
2. music_already_running() / focus_music_window() / open_or_focus_music(...)
   -- a single shared way for every screen (launcher, Sudoku,
   Crossword, Word Search, ...) to open the Music window, or bring an
   already-running one to the front instead of spawning a duplicate.
3. set_return_path(...) / get_return_path(...) -- lets Music's Close
   button always send you back to whichever screen you were actually
   on, even if Music was already running and simply got refocused
   rather than freshly launched.
"""

import os
import subprocess
import sys
import tempfile
import time

MUSIC_PID_PATH = os.path.join(tempfile.gettempdir(), "puzzlerz_music.pid")
RETURN_PATH_FILE = os.path.join(tempfile.gettempdir(), "puzzlerz_return_path.txt")


def launch_detached(args, cwd=None, env=None):
    """subprocess.Popen wrapper that survives the parent process
    exiting, even under terminals/IDEs that kill child processes on
    parent exit (a common Windows job-object behavior). Every
    Puzzlerz screen deliberately closes itself right after launching
    the next one (to avoid stacking duplicate windows), so without
    this, the new window could get silently killed before it ever
    opens.

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


def music_already_running():
    """True if Music.py's heartbeat file was touched recently, meaning
    a Music process is alive (and playing) somewhere right now."""
    try:
        mtime = os.path.getmtime(MUSIC_PID_PATH)
    except OSError:
        return False
    return (time.time() - mtime) < 3


def focus_music_window():
    """Bring the already-running Music window to the front, restoring
    it if minimized. This is platform-specific since there's no
    cross-process 'focus that window' API in pygame -- each branch
    fails silently if the needed tool isn't available."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, "Music")
            if hwnd:
                SW_RESTORE = 9
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        # Requires wmctrl (common on most desktop Linux distros).
        try:
            subprocess.Popen(["wmctrl", "-a", "Music"])
        except Exception:
            pass
    elif sys.platform == "darwin":
        # Best-effort: ask System Events to raise any window titled
        # "Music" belonging to a Python process.
        try:
            script = (
                'tell application "System Events"\n'
                '  set procs to processes whose name contains "Python"\n'
                '  repeat with p in procs\n'
                '    try\n'
                '      set frontmost of p to true\n'
                '      exit repeat\n'
                '    end try\n'
                '  end repeat\n'
                'end tell'
            )
            subprocess.Popen(["osascript", "-e", script])
        except Exception:
            pass


def set_return_path(caller_path):
    """Record which screen most recently opened (or re-focused) Music,
    so Music's Close button can always send you back to wherever you
    actually were -- even if Music was already running and this call
    only brought it to the front rather than launching a brand-new
    process. Called on every Music button click, not just the first."""
    try:
        with open(RETURN_PATH_FILE, "w") as f:
            f.write(caller_path)
    except OSError:
        pass


def get_return_path(default_path):
    """Read the most recently recorded return path, falling back to
    default_path if it's missing, unreadable, or points to a file that
    no longer exists (e.g. moved/renamed)."""
    try:
        with open(RETURN_PATH_FILE, "r") as f:
            path = f.read().strip()
    except OSError:
        return default_path
    if path and os.path.exists(path):
        return path
    return default_path


def open_or_focus_music(here, caller_path=None):
    """Launch Music.py if it isn't already running anywhere, or bring
    its window to the front if it is -- used by the Music button on
    every screen (launcher, Sudoku, Crossword, Word Search, ...).

    `here` should be the calling script's own directory (typically
    os.path.dirname(os.path.abspath(__file__))), so Music.py is found
    as a sibling file regardless of the current working directory.

    `caller_path`, if given, should be the calling script's own full
    path (typically os.path.abspath(__file__)). It's recorded via
    set_return_path on EVERY call -- whether Music is freshly launched
    or already running and just brought to the front -- so Music's
    Close button always sends you back to whichever screen you most
    recently came from.

    Returns True if an action was taken (opened or focused), False if
    launching failed -- details are printed to the console in that
    case rather than raising, so callers can decide whether to also
    show their own UI-specific error dialog."""
    if caller_path:
        set_return_path(caller_path)

    if music_already_running():
        focus_music_window()
        return True
    try:
        music_path = os.path.join(here, "Music.py")
        launch_detached([sys.executable, music_path], cwd=here)
        return True
    except Exception as e:
        print(f"Failed to open Music.py: {e}")
        return False