from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from threading import Barrier

from scripts import build_training_dataset


def test_concurrent_conversion_uses_independent_temporary_files(tmp_path, monkeypatch):
    mp3_inputs: list[Path] = []
    downloads_started = Barrier(2)

    def fake_urlopen(*args, **kwargs):
        downloads_started.wait(timeout=2)
        return BytesIO(b"fake mp3")

    monkeypatch.setattr(
        build_training_dataset.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    def fake_run(command, check):
        source = Path(command[command.index("-i") + 1])
        destination = Path(command[-1])
        assert source.exists()
        mp3_inputs.append(source)
        destination.write_bytes(b"R" * 45)

    monkeypatch.setattr(build_training_dataset.subprocess, "run", fake_run)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _: build_training_dataset.fetch_and_convert(
                    "TestReciter", 1, 1, tmp_path
                ),
                range(2),
            )
        )

    expected = tmp_path / "001001.wav"
    assert results == [expected, expected]
    assert expected.stat().st_size == 45
    assert len(set(mp3_inputs)) == 2
    assert not list(tmp_path.glob("*.mp3"))
    assert not list(tmp_path.glob(".*.wav"))
