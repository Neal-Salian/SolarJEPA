"""Pilot-only catchable cancellation and conservative orphan identification.

SIGKILL, host loss and workers/descendants that leave the original process group
are outside this local supervisor's guarantees. Recovery never authorizes fitting
or continuation.
Tokens identify trusted same-user workers, not hostile-process authentication.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading

from .v2_resource_controls import SupervisionIntegrityError

OWNER_ENV = 'SOLARJEPA_PILOT_OWNER_TOKEN'
_current = None


class PilotInterrupted(BaseException):
    """Catchable supervisor cancellation; never an infrastructure retry."""
    def __init__(self, signal_number):
        self.signal_number = signal_number
        super().__init__(f'Pilot cancelled by {signal.Signals(signal_number).name}')


class _Signals:
    def __init__(self):
        self.depth = 0
        self.error = None
        self.delivered = False

    @property
    def stopping(self):
        return self.error is not None or self.delivered

    def cancel(self, error):
        if self.error is None:
            self.error = error
        self.checkpoint()

    def checkpoint(self):
        if self.depth == 0 and self.error is not None and not self.delivered:
            self.delivered = True
            raise self.error

    def begin_cleanup(self):
        # Ordinary failure also disarms asynchronous exceptions during teardown.
        self.delivered = True

    @contextmanager
    def defer(self, *, flush=True):
        self.depth += 1
        try:
            yield
        finally:
            self.depth -= 1
            if flush:
                self.checkpoint()


def current_signals():
    return _current


@contextmanager
def pilot_signals():
    """Own INT/TERM/HUP in the main thread; nested users share cancellation."""
    global _current
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError('Pilot supervision requires the main thread for signal ownership')
    if _current is not None:
        yield _current
        return
    state = _Signals()
    previous = {}
    _current = state
    def interrupted(signum, frame):
        state.cancel(PilotInterrupted(signum))
    try:
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, interrupted)
        yield state
        state.checkpoint()
    finally:
        state.begin_cleanup()
        for signum, handler in previous.items():
            signal.signal(signum, handler)
        _current = None


def _metadata(pid):
    try:
        result = subprocess.run(['ps', '-p', str(pid), '-o', 'pid=,pgid=,uid=,stat=,lstart='],
                                capture_output=True, text=True, timeout=.5, check=False)
        if result.returncode == 1 and not result.stdout.strip():
            return None
        values = result.stdout.split()
        if result.returncode != 0 or len(values) != 9:
            raise ValueError('Unsupported or ambiguous process identity')
        actual, group, uid = map(int, values[:3])
        if actual != pid:
            raise ValueError('Process identity changed')
        if values[3].startswith('Z'):
            return None
        return dict(pid=actual, pgid=group, uid=uid, session=os.getsid(pid),
                    birth=' '.join(values[4:]))
    except ProcessLookupError:
        return None
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise SupervisionIntegrityError('Cannot establish exact pilot process identity') from error


def read_process_identity(pid, token=None):
    """Read identity privately; never return/log unrelated environment bytes.

    A random token inherited at spawn disambiguates same-second PID reuse. Two
    metadata reads bracket token inspection. Confirmed disappearance/zombie
    transitions yield no identity; live mismatches and missing tokens fail closed.
    """
    if type(pid) is not int or pid <= 1:
        raise SupervisionIntegrityError('Unsafe pilot PID')
    if not isinstance(token, str) or len(token) != 64 or any(c not in '0123456789abcdef' for c in token):
        raise SupervisionIntegrityError('Missing or malformed pilot ownership token')
    before = _metadata(pid)
    if before is None:
        return None
    try:
        expected = f'{OWNER_ENV}={token}'
        if sys.platform == 'linux':
            owned = expected.encode() in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0')
        elif sys.platform == 'darwin':
            result = subprocess.run(['ps', 'eww', '-p', str(pid), '-o', 'command='],
                                    capture_output=True, text=True, timeout=.5, check=True)
            owned = expected in result.stdout.split()
        else:
            raise OSError('Unsupported ownership inspection')
    except (OSError, subprocess.SubprocessError) as error:
        if _metadata(pid) is None:
            return None
        raise SupervisionIntegrityError('Cannot inspect pilot ownership token') from error
    if not owned:
        if _metadata(pid) is None:
            return None
        raise SupervisionIntegrityError('Pilot ownership token differs or is unavailable')
    before['token'] = token
    after = _metadata(pid)
    if after is None:
        return None
    comparison = {key: value for key, value in before.items() if key != 'token'}
    if after != comparison:
        raise SupervisionIntegrityError('Pilot identity changed during inspection')
    return before
