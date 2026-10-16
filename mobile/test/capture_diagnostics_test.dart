import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/services/capture_diagnostics.dart';

void main() {
  test('capture-start reports rate source gain and conversion without raw text',
      () {
    expect(
        parseCaptureDiagnostics(
            'capture started: rate=44100 resample=true source=MIC gain=3x'),
        {
          'capture_rate': 44100,
          'audio_source': 'MIC',
          'software_gain': 3,
          'resampling': true,
        });
  });
  test('reading reports dropped frames and preserves a fallback source', () {
    expect(
        parseCaptureDiagnostics(
            'reading: rate=16000 source=VOICE_RECOGNITION zeroTicks=0 dataTicks=40 dropped=2'),
        {
          'capture_rate': 16000,
          'audio_source': 'VOICE_RECOGNITION',
          'dropped_frames': 2,
        });
  });
  test('errors unknown sources and impossible rates are not telemetry', () {
    for (final status in [
      'capture error: secret-value',
      'capture started: rate=0 source=MIC',
      'capture started: rate=44100 source=Bearer-secret',
      'unrelated rate=44100 source=MIC'
    ]) {
      expect(parseCaptureDiagnostics(status), isNull, reason: status);
    }
  });
  test('a short old capture cannot label a failed new capture', () {
    const old =
        'capture started: capture_id=100 rate=44100 resample=true source=VOICE_RECOGNITION gain=3x';
    expect(parseCaptureDiagnostics(old, captureId: '101'), isNull);
    expect(
        parseCaptureDiagnostics('capture error: unavailable', captureId: '101'),
        isNull);
    expect(
        parseCaptureDiagnostics(
            'capture started: capture_id=101 rate=44100 resample=true source=MIC gain=3x',
            captureId: '101')?['audio_source'],
        'MIC');
  });
}
