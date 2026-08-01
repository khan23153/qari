import 'recitation_model.dart';

/// Live status of a single word during real-time recitation tracking.
/// Mirrors the backend `ml.alignment.streaming_matcher.WordStatus`.
enum LiveWordStatus {
  /// Not yet resolved — stays hidden / masked in Memorization Mode.
  pending,

  /// Correctly recited — reveal + tint green.
  matched,

  /// Mispronounced — reveal + flag red.
  error,

  /// Jumped over — reveal + flag (a later word matched instead).
  skipped;

  /// Parses a backend ``status`` string. Understands both the blueprint wire
  /// contract (``match`` / ``error_skipped``) and the legacy internal values
  /// (``matched`` / ``error`` / ``skipped``) for backwards compatibility.
  static LiveWordStatus fromString(String? s) {
    switch (s) {
      case 'match':
      case 'matched':
        return LiveWordStatus.matched;
      case 'error':
        // ``error_skipped`` folds skip + mispronunciation into one bucket on
        // the wire (blueprint spec) — mapped to [error] for the UI.
      case 'error_skipped':
      case 'skipped':
        return LiveWordStatus.error;
      default:
        return LiveWordStatus.pending;
    }
  }

  bool get isResolved => this != LiveWordStatus.pending;
  bool get isMistake => this == LiveWordStatus.error || this == LiveWordStatus.skipped;
}

/// Type of message received over the streaming recitation WebSocket.
enum RecitationStreamEventType { ready, word, finalResult, error, pong, unknown }

/// A single decoded message from the `/ws/recitation/stream` socket.
class RecitationStreamEvent {
  final RecitationStreamEventType type;

  // ready
  final String? sessionId;
  final List<StreamWord> words;

  // word
  final int? wordIndex;
  final LiveWordStatus status;
  final String? expected;
  final String? spoken;
  final double confidence;
  final int? timestampMs;

  // final
  final RecitationResult? result;

  // error
  final String? detail;

  const RecitationStreamEvent({
    required this.type,
    this.sessionId,
    this.words = const [],
    this.wordIndex,
    this.status = LiveWordStatus.pending,
    this.expected,
    this.spoken,
    this.confidence = 1.0,
    this.timestampMs,
    this.result,
    this.detail,
  });

  factory RecitationStreamEvent.fromJson(Map<String, dynamic> json) {
    final rawType = json['type'] as String?;
    switch (rawType) {
      case 'ready':
        return RecitationStreamEvent(
          type: RecitationStreamEventType.ready,
          sessionId: json['session_id'] as String?,
          words: (json['words'] as List<dynamic>? ?? [])
              .map((w) => StreamWord.fromJson(w as Map<String, dynamic>))
              .toList(),
        );
      case 'word':
        // Blueprint wire contract uses a 1-based ``word_id``; the legacy
        // protocol used a 0-based ``word_index``. Accept either.
        final rawIndex = json['word_index'] as num?;
        final rawId = json['word_id'] as num?;
        final wordIndex = rawIndex != null
            ? rawIndex.toInt()
            : (rawId != null ? rawId.toInt() - 1 : null);
        return RecitationStreamEvent(
          type: RecitationStreamEventType.word,
          sessionId: json['session_id'] as String?,
          wordIndex: wordIndex,
          status: LiveWordStatus.fromString(json['status'] as String?),
          expected: json['expected'] as String?,
          spoken: json['spoken'] as String?,
          confidence: (json['confidence'] as num?)?.toDouble() ?? 1.0,
          timestampMs: (json['timestamp_ms'] as num?)?.toInt(),
        );
      case 'final':
        final resultJson = json['result'] as Map<String, dynamic>?;
        RecitationResult? result;
        if (resultJson != null) {
          final normalized = Map<String, dynamic>.from(resultJson);
          final verdicts = normalized['word_verdicts'];
          final noSpeech = normalized['no_speech_detected'] == true;

          // The current live page treats an empty verdict list as a missing
          // backend result and replaces it with a local generic result. Preserve
          // an explicit no-speech response by carrying a private sentinel
          // verdict through the existing RecitationResult model. The results UI
          // recognizes and hides this sentinel; it is never shown as a Quran
          // word or counted as practice history.
          if (noSpeech && (verdicts is! List || verdicts.isEmpty)) {
            normalized['word_verdicts'] = [
              {
                'word': '',
                'word_index': -1,
                'is_correct': false,
                'confidence': 0.0,
                'expected_text': null,
                'actual_text': null,
                'error_type': 'no_speech',
                'error_description': normalized['feedback'],
                'reference_audio_url': normalized['reference_audio_url'],
                'user_audio_url': normalized['user_audio_url'],
                'phoneme_errors': <dynamic>[],
              }
            ];
          }
          result = RecitationResult.fromJson(normalized);
        }
        return RecitationStreamEvent(
          type: RecitationStreamEventType.finalResult,
          sessionId: json['session_id'] as String?,
          result: result,
        );
      case 'error':
        return RecitationStreamEvent(
          type: RecitationStreamEventType.error,
          detail: json['detail'] as String?,
        );
      case 'pong':
        return const RecitationStreamEvent(type: RecitationStreamEventType.pong);
      default:
        return const RecitationStreamEvent(type: RecitationStreamEventType.unknown);
    }
  }
}

/// A reference word sent in the `ready` payload. Mirrors the blueprint
/// word-level model: ``word_id`` (1-based) / ``sequence_index``, the
/// diacritic ``text_with_tashkeel`` (UI) and ``clean_text`` (ASR key), plus an
/// initial ``state``. Tolerant of the legacy ``index`` / ``text`` keys.
class StreamWord {
  final int index;
  final String text;

  const StreamWord({required this.index, required this.text});

  factory StreamWord.fromJson(Map<String, dynamic> json) {
    final rawId = json['word_id'] as num?;
    final rawIndex = json['index'] as num?;
    final index = rawId != null
        ? rawId.toInt() - 1
        : (rawIndex != null ? rawIndex.toInt() : 0);
    final text =
        (json['text_with_tashkeel'] as String?) ?? (json['text'] as String? ?? '');
    return StreamWord(index: index, text: text);
  }
}