/// A persisted record of a completed live (AI) recitation session.
///
/// Stored locally (SharedPreferences) so the user can review past sessions,
/// track their streak, and replay mistakes — Tarteel-style "Mistake Review" +
/// "History". Kept as a plain (hand-rolled JSON) model so it does not require
/// `build_runner`, unlike the freezed [RecitationResult].
class RecitationSessionRecord {
  RecitationSessionRecord({
    required this.id,
    required this.scope,
    required this.surahNumber,
    required this.ayahFrom,
    required this.ayahTo,
    required this.recordedAt,
    required this.overallScore,
    required this.correctCount,
    required this.totalCount,
    required this.durationSeconds,
    this.mistakes = const [],
  });

  /// Stable UUID for this session record.
  final String id;

  /// 'page' | 'surah' | 'range' — what block the user recited.
  final String scope;

  /// Target reference.
  final int surahNumber;
  final int ayahFrom;
  final int ayahTo;

  final DateTime recordedAt;

  /// 0..1 overall accuracy.
  final double overallScore;
  final int correctCount;
  final int totalCount;
  final int durationSeconds;

  /// Words the engine flagged (mispronounced / skipped) for mistake review.
  final List<RecitationMistake> mistakes;

  String get referenceLabel {
    if (scope == 'page') return 'Page $surahNumber';
    if (ayahFrom == ayahTo) return '$surahNumber:$ayahFrom';
    return '$surahNumber:$ayahFrom-$ayahTo';
  }

  factory RecitationSessionRecord.fromJson(Map<String, dynamic> json) {
    return RecitationSessionRecord(
      id: json['id'] as String,
      scope: json['scope'] as String? ?? 'surah',
      surahNumber: json['surah_number'] as int,
      ayahFrom: json['ayah_from'] as int,
      ayahTo: json['ayah_to'] as int,
      recordedAt: DateTime.parse(json['recorded_at'] as String),
      overallScore: (json['overall_score'] as num).toDouble(),
      correctCount: json['correct_count'] as int,
      totalCount: json['total_count'] as int,
      durationSeconds: json['duration_seconds'] as int,
      mistakes: (json['mistakes'] as List<dynamic>? ?? [])
          .map((m) => RecitationMistake.fromJson(m as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'scope': scope,
        'surah_number': surahNumber,
        'ayah_from': ayahFrom,
        'ayah_to': ayahTo,
        'recorded_at': recordedAt.toIso8601String(),
        'overall_score': overallScore,
        'correct_count': correctCount,
        'total_count': totalCount,
        'duration_seconds': durationSeconds,
        'mistakes': mistakes.map((m) => m.toJson()).toList(),
      };
}

/// A single mispronounced / skipped word captured during a session.
class RecitationMistake {
  RecitationMistake({
    required this.word,
    required this.expectedText,
    required this.errorType,
    this.surahNumber,
    this.ayahNumber,
  });

  final String word;
  final String expectedText;
  final String errorType;
  final int? surahNumber;
  final int? ayahNumber;

  factory RecitationMistake.fromJson(Map<String, dynamic> json) {
    return RecitationMistake(
      word: json['word'] as String? ?? '',
      expectedText: json['expected_text'] as String? ?? '',
      errorType: json['error_type'] as String? ?? 'error',
      surahNumber: json['surah_number'] as int?,
      ayahNumber: json['ayah_number'] as int?,
    );
  }

  Map<String, dynamic> toJson() => {
        'word': word,
        'expected_text': expectedText,
        'error_type': errorType,
        if (surahNumber != null) 'surah_number': surahNumber,
        if (ayahNumber != null) 'ayah_number': ayahNumber,
      };
}
