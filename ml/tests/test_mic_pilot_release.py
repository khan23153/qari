"""Exercise release publication with an external compiler stand-in."""
import json
import os
import subprocess
from pathlib import Path


def test_mic_pilot_does_not_replace_normal_apk_metadata_or_version(tmp_path):
    root = tmp_path/'qari'
    for name in ['scripts', 'mobile', 'releases', 'bin']:
        (root/name).mkdir(parents=True)
    source = Path(__file__).resolve().parents[2]/'scripts/release_app.sh'
    (root/'scripts/release_app.sh').write_bytes(source.read_bytes())
    version = 'name: qari\nversion: 1.0.49+75\n'
    (root/'mobile/pubspec.yaml').write_text(version)
    normal = '{"version":"1.0.49","version_code":75,"apk_url":"https://aiquranic.com/v1/app/download"}\n'
    (root/'releases/app_release.json').write_text(normal)
    (root/'releases/app-release.apk').write_bytes(b'normal-release')
    compiler = root/'bin/flutter'
    compiler.write_text('#!/bin/sh\nif [ "$1" = build ]; then mkdir -p build/app/outputs/flutter-apk; printf "compiled-pilot" > build/app/outputs/flutter-apk/app-release.apk; fi\n')
    compiler.chmod(0o755)
    env = {**os.environ, 'PATH': str(root/'bin')+os.pathsep+os.environ['PATH']}
    subprocess.run(['bash',str(root/'scripts/release_app.sh'),'--bump','--mic-pilot'],env=env,check=True,capture_output=True,text=True)
    assert (root/'releases/app-release.apk').read_bytes() == b'normal-release'
    assert (root/'releases/app_release.json').read_text() == normal
    assert (root/'mobile/pubspec.yaml').read_text() == version
    assert (root/'releases/app-mic-pilot.apk').read_bytes() == b'compiled-pilot'
    pilot = json.loads((root/'releases/app_mic_pilot.json').read_text())
    assert pilot['version_code'] == 76
    assert pilot['package_id'] == 'com.qari.app.micpilot'
    assert pilot['apk_url'] == 'https://aiquranic.com/v1/app/download?file=app-mic-pilot.apk'
