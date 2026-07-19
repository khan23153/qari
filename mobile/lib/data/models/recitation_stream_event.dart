import 'dart:convert';
import 'package:flutter/foundation.dart';
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

  /// Parses a Tarteel frame into a LIST of events (a single STATES_UPDATE may
  /// resolve several words). Returns an empty list for non-word frames.
  ///
  /// Captured protocol (via Reqable): the app sends Base64 audio chunks as
  /// `{"type":3,"data":"<base64>"}` and Tarteel replies with TEXT frames
  /// wrapped as `{"type":2,"text":"{...}"}` where the inner JSON has an
  /// `event` field:
  ///   • `PARTIAL_TRANSCRIPT` → `data.queryText` (live ASR transcript string)
  ///   • `STATES_UPDATE`      → `data.stateIndexOffset` (0-based start index) +
  ///                            `data.newStates` (per-word state codes) +
  ///                            `data.mistakeUpdates` (map of word idx → mistake)
  ///                            + `data.audioProcessedMs`
  /// Tarteel word-state codes (observed): 0 = scheduled/not-yet, 1 = recited
  /// (correct), 2 = mistake. Tarteel's word indices are its OWN reference
  /// sequence and do NOT align with our local `_words` array, so we prefer the
  /// `PARTIAL_TRANSCRIPT` text to drive the reveal (matched against local words
  /// in the page) and use STATES_UPDATE only as a mistake signal.
  static List<RecitationStreamEvent> fromTarteelJson(Map<String, dynamic> json) {
    // Unwrap the `{"type":2,"text":"..."}` envelope if present.
    String? innerText = json['text'] as String?;
    Map<String, dynamic> inner = json;
    if (innerText != null) {
      try {
        inner = jsonDecode(innerText) as Map<String, dynamic>;
      } catch (_) {
        return const [];
      }
    }

    final event = inner['event'] as String?;
    final data = inner['data'] as Map<String, dynamic>? ?? {};

    switch (event) {
      case 'STATES_UPDATE':
        // Emit one `word` event per state that has actually been resolved
        // (state != 0 / not merely scheduled). `stateIndexOffset` is the
        // 0-based index of `newStates[0]`. We expose the index + whether it is
        // a mistake; the page decides how to reveal (it uses the live
        // transcript text to pick the actual Arabic word, since Tarteel's index
        // space diverges from ours).
        final offset = (data['stateIndexOffset'] as num?)?.toInt() ?? 0;
        final newStates = data['newStates'] as List<dynamic>? ?? [];
        final mistakeUpdates =
            data['mistakeUpdates'] as Map<String, dynamic>? ?? {};
        final events = <RecitationStreamEvent>[];
        for (var i = 0; i < newStates.length; i++) {
          // Each item is either a raw code (int/string) or an object
          // {"type":"FAILURE"/"SUCCESS", ...} (Tarteel's real shape).
          final item = newStates[i];
          final code = item is Map
              ? (item['type'] ?? item['state'] ?? item['status'])
              : item;
          final status = _tarteelStateCode(code);
          if (status == LiveWordStatus.pending) continue; // not yet resolved
          final idx = offset + i;
          final isMistake = mistakeUpdates.containsKey(idx.toString()) ||
              mistakeUpdates.containsKey(i.toString());
          final finalStatus = isMistake ? LiveWordStatus.error : status;
          events.add(RecitationStreamEvent(
            type: RecitationStreamEventType.word,
            wordIndex: idx,
            status: finalStatus,
          ));
        }
        return events;

      case 'PARTIAL_TRANSCRIPT':
        // Live ASR transcript. The page fuzzy-matches the last spoken token
        // against our local target words to reveal the correct Arabic word,
        // which is robust to Tarteel's index space. We pass the full transcript
        // text in [spoken] and let the page find the matching local word.
        final query = (data['queryText'] as String? ?? '').trim();
        if (query.isEmpty) return const [];
        return [
          RecitationStreamEvent(
            type: RecitationStreamEventType.word,
            wordIndex: null,
            status: LiveWordStatus.matched,
            spoken: query,
          )
        ];

      case 'FINAL_TRANSCRIPT':
      case 'COMPLETE':
      case 'SESSION_END':
      case 'RESULT':
        return const [
          RecitationStreamEvent(
            type: RecitationStreamEventType.finalResult,
            result: null,
          )
        ];

      default:
        debugPrint('[Tarteel] unknown event: $event — inner=$inner');
        return const [];
    }
  }

  /// Maps Tarteel's numeric/string word-state code onto [LiveWordStatus].
  /// Observed codes: 0 = scheduled (not yet recited) → pending;
  /// 1 = recited correctly → matched; 2 = mistake → error.
  static LiveWordStatus _tarteelStateCode(dynamic code) {
    if (code == null) return LiveWordStatus.pending;
    if (code is num) {
      switch (code.toInt()) {
        case 1:
          return LiveWordStatus.matched;
        case 2:
          return LiveWordStatus.error;
        default:
          return LiveWordStatus.pending;
      }
    }
    final s = code.toString().toLowerCase();
    if (s == '1' ||
        s == 'recited' ||
        s == 'correct' ||
        s == 'match' ||
        s == 'matched' ||
        s == 'success' ||
        s == 'successful' ||
        s == 'completed' ||
        s == 'ok') {
      return LiveWordStatus.matched;
    }
    if (s == '2' ||
        s == 'mistake' ||
        s == 'error' ||
        s == 'skipped' ||
        s == 'failure' ||
        s == 'fail' ||
        s == 'incorrect') {
      return LiveWordStatus.error;
    }
    return LiveWordStatus.pending;
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
