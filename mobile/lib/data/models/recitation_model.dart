import 'package:freezed_annotation/freezed_annotation.dart';

part 'recitation_model.freezed.dart';
part 'recitation_model.g.dart';

/// Represents the result of an AI recitation analysis.
@freezed
abstract class RecitationResult with _$RecitationResult {
  const factory RecitationResult({
    @JsonKey(name: 'session_id') required String sessionId,
    @JsonKey(name: 'surah_number') required int surahNumber,
    @JsonKey(name: 'ayah_number') required int ayahNumber,
    @JsonKey(name: 'overall_score') required double overallScore,
    @JsonKey(name: 'pronunciation_score') @Default(0.0) double pronunciationScore,
    @JsonKey(name: 'tajweed_score') @Default(0.0) double tajweedScore,
    @JsonKey(name: 'fluency_score') @Default(0.0) double fluencyScore,
    @JsonKey(name: 'accuracy_score') @Default(0.0) double accuracyScore,
    @JsonKey(name: 'word_verdicts') @Default([]) List<WordVerdict> wordVerdicts,
    @JsonKey(name: 'reference_audio_url') String? referenceAudioUrl,
    @JsonKey(name: 'user_audio_url') String? userAudioUrl,
    @JsonKey(name: 'feedback') String? feedback,
    @JsonKey(name: 'feedback_urdu') String? feedbackUrdu,
    @JsonKey(name: 'duration_seconds') @Default(0) int durationSeconds,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'confidence') @Default(1.0) double confidence,
  }) = _RecitationResult;

  factory RecitationResult.fromJson(Map<String, dynamic> json) =>
      _$RecitationResultFromJson(json);
}

/// Represents the verdict for a single word in a recitation.
@freezed
abstract class WordVerdict with _$WordVerdict {
  const factory WordVerdict({
    required String word,
    @JsonKey(name: 'word_index') required int wordIndex,
    @JsonKey(name: 'is_correct') required bool isCorrect,
    @JsonKey(name: 'confidence') @Default(1.0) double confidence,
    @JsonKey(name: 'expected_text') String? expectedText,
    @JsonKey(name: 'actual_text') String? actualText,
    @JsonKey(name: 'error_type') String? errorType,
    @JsonKey(name: 'error_description') String? errorDescription,
    @JsonKey(name: 'reference_audio_url') String? referenceAudioUrl,
    @JsonKey(name: 'user_audio_url') String? userAudioUrl,
    @JsonKey(name: 'phoneme_errors') @Default([]) List<PhonemeError> phonemeErrors,
  }) = _WordVerdict;

  factory WordVerdict.fromJson(Map<String, dynamic> json) =>
      _$WordVerdictFromJson(json);
}

/// Represents a phoneme-level error.
@freezed
abstract class PhonemeError with _$PhonemeError {
  const factory PhonemeError({
    required String phoneme,
    @JsonKey(name: 'expected_phoneme') required String expectedPhoneme,
    @JsonKey(name: 'actual_phoneme') required String actualPhoneme,
    @JsonKey(name: 'position') required int position,
    @JsonKey(name: 'severity') @Default('minor') String severity,
  }) = _PhonemeError;

  factory PhonemeError.fromJson(Map<String, dynamic> json) =>
      _$PhonemeErrorFromJson(json);
}

/// Extension for recitation result convenience.
extension RecitationResultX on RecitationResult {
  /// Whether the result has high confidence (no low-confidence failure).
  bool get isConfident => confidence >= 0.55;

  /// Count of correct words.
  int get correctCount => wordVerdicts.where((v) => v.isCorrect).length;

  /// Count of incorrect words.
  int get incorrectCount => wordVerdicts.where((v) => !v.isCorrect).length;

  /// Percentage of correct words.
  double get correctPercentage {
    if (wordVerdicts.isEmpty) return 0;
    return (correctCount / wordVerdicts.length) * 100;
  }

  /// Score as a percentage string.
  String get scorePercentage => '${(overallScore * 100).toStringAsFixed(0)}%';

  /// Grade label based on score.
  String get gradeLabel {
    if (overallScore >= 0.9) return 'Excellent';
    if (overallScore >= 0.75) return 'Good';
    if (overallScore >= 0.6) return 'Fair';
    return 'Needs Practice';
  }

  /// Feedback for the user's language.
  String feedbackFor(String langCode) {
    switch (langCode) {
      case 'ur':
        return feedbackUrdu ?? feedback ?? '';
      default:
        return feedback ?? '';
    }
  }

  /// List of incorrect word verdicts.
  List<WordVerdict> get incorrectVerdicts =>
      wordVerdicts.where((v) => !v.isCorrect).toList();
}
