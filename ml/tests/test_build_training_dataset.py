from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from threading import Barrier

from scripts import build_training_dataset


def test_missing_ffmpeg_fails_before_dataset_work(monkeypatch):
    monkeypatch.setattr(build_training_dataset.shutil, "which", lambda _: None)

    try:
        build_training_dataset.require_ffmpeg()
    except SystemExit as exc:
        assert "sudo apt-get install -y ffmpeg" in str(exc)
    else:
        raise AssertionError("missing ffmpeg should stop the dataset builder")


def test_require_ffmpeg_returns_resolved_executable(monkeypatch):
    monkeypatch.setattr(
        build_training_dataset.shutil,
        "which",
        lambda _: "/usr/bin/ffmpeg",
    )

    assert build_training_dataset.require_ffmpeg() == "/usr/bin/ffmpeg"


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
        assert all(isinstance(arg, (str, bytes)) for arg in command)
        assert command.count("ffmpeg") <= 1
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


def test_conversion_uses_flat_preflight_ffmpeg_command(tmp_path, monkeypatch):
    monkeypatch.setattr(
        build_training_dataset.urllib.request,
        "urlopen",
        lambda *args, **kwargs: BytesIO(b"fake mp3"),
    )

    def fake_run(command, check):
        assert command[0] == "/custom/bin/ffmpeg"
        assert all(isinstance(arg, (str, bytes)) for arg in command)
        assert command[command.index("-ac") + 1] == "1"
        assert command[command.index("-ar") + 1] == "16000"
        assert command[command.index("-sample_fmt") + 1] == "s16"
        Path(command[-1]).write_bytes(b"R" * 45)

    monkeypatch.setattr(build_training_dataset.subprocess, "run", fake_run)

    result = build_training_dataset.fetch_and_convert(
        "TestReciter", 1, 1, tmp_path, "/custom/bin/ffmpeg"
    )

    assert result == tmp_path / "001001.wav"
