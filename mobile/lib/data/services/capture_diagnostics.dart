/// Converts native capture status into technical metadata without raw text.
Map<String, Object>? parseCaptureDiagnostics(String status,
    {String? captureId}) {
  if (!status.startsWith('capture started: ') &&
      !status.startsWith('reading: ')) {
    return null;
  }
  String? field(String key) =>
      RegExp('(?:^| )$key=([^ ]+)').firstMatch(status)?.group(1);
  if (captureId != null && field('capture_id') != captureId) return null;
  final rate = int.tryParse(field('rate') ?? '');
  final source = field('source');
  if (rate == null ||
      rate < 8000 ||
      rate > 192000 ||
      !const ['MIC', 'VOICE_RECOGNITION', 'UNPROCESSED'].contains(source)) {
    return null;
  }
  final result = <String, Object>{
    'capture_rate': rate,
    'audio_source': source!
  };
  final gain =
      int.tryParse((field('gain') ?? '').replaceFirst(RegExp(r'x$'), ''));
  if (gain != null && gain >= 1 && gain <= 10) result['software_gain'] = gain;
  final resample = field('resample');
  if (resample == 'true' || resample == 'false') {
    result['resampling'] = resample == 'true';
  }
  final dropped = int.tryParse(field('dropped') ?? '');
  if (dropped != null && dropped >= 0 && dropped <= 10000000) {
    result['dropped_frames'] = dropped;
  }
  return result;
}
