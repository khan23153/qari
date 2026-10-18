"""Exercise real bootstrap and processing deadlines without network/GPU access."""
import json
import signal
import subprocess
import sys
import time

import pytest

from ml.training.kaggle_job_budget import job_budget, run_bootstrap


def test_slow_bootstrap_is_bounded_and_reports_failure(tmp_path):
    before = signal.getsignal(signal.SIGALRM)
    start = time.monotonic()
    with pytest.raises((TimeoutError, subprocess.TimeoutExpired)):
        with job_budget(tmp_path, seconds=.1) as deadline:
            run_bootstrap([sys.executable, '-c', 'import time; time.sleep(5)'], deadline)
    assert time.monotonic()-start < 2
    report = json.loads((tmp_path/'failure.json').read_text())
    assert report['status'] == 'failed' and report['qualified'] is False
    assert report['production_changed'] is False
    assert signal.getsignal(signal.SIGALRM) == before


def test_processing_uses_remaining_whole_job_budget(tmp_path):
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        with job_budget(tmp_path, seconds=.2) as deadline:
            run_bootstrap([sys.executable, '-c', 'import time; time.sleep(.08)'], deadline)
            assert deadline == pytest.approx(start+.2, abs=.02)
            time.sleep(5)
    assert time.monotonic()-start < 2
    assert json.loads((tmp_path/'failure.json').read_text())['error_type'] == 'TimeoutError'


def test_success_leaves_no_failure_metadata(tmp_path):
    with job_budget(tmp_path, seconds=2) as deadline:
        run_bootstrap([sys.executable, '-c', 'print("bootstrap complete")'], deadline)
    assert not (tmp_path/'failure.json').exists()
