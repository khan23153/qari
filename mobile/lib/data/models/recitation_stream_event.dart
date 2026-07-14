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

  static LiveWordStatus fromString(String? s) {
    switch (s) {
      case 'matched':
        return LiveWordStatus.matched;
      case 'error':
        return LiveWordStatus.error;
      case 'skipped':
        return LiveWordStatus.skipped;
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
        return RecitationStreamEvent(
          type: RecitationStreamEventType.word,
          sessionId: json['session_id'] as String?,
          wordIndex: (json['word_index'] as num?)?.toInt(),
          status: LiveWordStatus.fromString(json['status'] as String?),
          expected: json['expected'] as String?,
          spoken: json['spoken'] as String?,
          confidence: (json['confidence'] as num?)?.toDouble() ?? 1.0,
          timestampMs: (json['timestamp_ms'] as num?)?.toInt(),
        );
      case 'final':
        final resultJson = json['result'] as Map<String, dynamic>?;
        return RecitationStreamEvent(
          type: RecitationStreamEventType.finalResult,
          sessionId: json['session_id'] as String?,
          result: resultJson != null ? RecitationResult.fromJson(resultJson) : null,
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

/// A reference word sent in the `ready` payload (index + display Arabic text).
class StreamWord {
  final int index;
  final String text;

  const StreamWord({required this.index, required this.text});

  factory StreamWord.fromJson(Map<String, dynamic> json) => StreamWord(
        index: (json['index'] as num).toInt(),
        text: json['text'] as String? ?? '',
      );
}
