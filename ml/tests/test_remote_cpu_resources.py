import time
from types import SimpleNamespace

import pytest
import torch

from ml.training.kaggle_phoneme_job import check_resources


@pytest.mark.parametrize('case',['ok','disk','rss','deadline'])
def test_remote_cpu_checks_disk_rss_deadline_without_cuda(tmp_path,monkeypatch,case):
    import resource
    import shutil
    monkeypatch.setattr(shutil,'disk_usage',lambda _:SimpleNamespace(free=(3 if case=='disk' else 8)*1024**3))
    monkeypatch.setattr(resource,'getrusage',lambda _:SimpleNamespace(ru_maxrss=(13 if case=='rss' else 1)*1024**2))
    monkeypatch.setattr(torch.cuda,'mem_get_info',lambda:pytest.fail('CPU resource check called CUDA'))
    deadline=time.monotonic()+(-1 if case=='deadline' else 5)
    if case=='ok':check_resources(tmp_path,'kaggle_cpu',deadline)
    else:
        with pytest.raises((RuntimeError,TimeoutError)):
            check_resources(tmp_path,'kaggle_cpu',deadline)
