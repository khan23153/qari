"""Standard-library-only deadline shared by dependency setup and GPU processing."""
from contextlib import contextmanager
import json
from pathlib import Path
import signal
import subprocess
import time


@contextmanager
def job_budget(output, *, seconds=7100):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic()+seconds
    previous = signal.getsignal(signal.SIGALRM)

    def expired(signum, frame):
        raise TimeoutError('Whole-job budget exhausted, including dependency bootstrap')

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield deadline
    except Exception as error:
        signal.setitimer(signal.ITIMER_REAL, 0)
        temporary = output/'failure.json.tmp'
        temporary.write_text(json.dumps({'status': 'failed', 'qualified': False,
                                         'production_changed': False,
                                         'error_type': type(error).__name__,
                                         'message': str(error)}, indent=2)+'\n')
        temporary.replace(output/'failure.json')
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def run_bootstrap(command, deadline):
    remaining = deadline-time.monotonic()
    if remaining <= 0:
        raise TimeoutError('Whole-job budget exhausted before bootstrap')
    return subprocess.run(command, check=True, timeout=min(600, remaining))
