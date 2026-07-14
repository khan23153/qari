import 'package:freezed_annotation/freezed_annotation.dart';

part 'flashcard_model.freezed.dart';
part 'flashcard_model.g.dart';

/// Represents a flashcard with SM-2 spaced repetition metadata.
@freezed
abstract class FlashcardModel with _$FlashcardModel {
  const factory FlashcardModel({
    @JsonKey(name: 'card_id') required int cardId,
    @JsonKey(name: 'user_id') String? userId,
    @JsonKey(name: 'word_id') required int wordId,
    @JsonKey(name: 'surah_number') required int surahNumber,
    @JsonKey(name: 'ayah_number') required int ayahNumber,
    @JsonKey(name: 'word_text') required String wordText,
    @JsonKey(name: 'transliteration') String? transliteration,
    @JsonKey(name: 'meaning_en') String? meaningEn,
    @JsonKey(name: 'meaning_ur') String? meaningUr,
    @JsonKey(name: 'root_arabic') String? rootArabic,
    @JsonKey(name: 'pos_group') String? posGroup,
    @JsonKey(name: 'audio_url') String? audioUrl,
    @JsonKey(name: 'ayah_text') String? ayahText,
    @JsonKey(name: 'ayah_translation') String? ayahTranslation,
    // SM-2 fields
    @JsonKey(name: 'sm2_ease') @Default(2.5) double ease,
    @JsonKey(name: 'sm2_interval') @Default(0) int interval,
    @JsonKey(name: 'sm2_repetitions') @Default(0) int repetitions,
    @JsonKey(name: 'next_review') required DateTime nextReview,
    @JsonKey(name: 'last_reviewed') DateTime? lastReviewed,
    @JsonKey(name: 'is_due') @Default(false) bool isDue,
    @JsonKey(name: 'created_at') required DateTime createdAt,
  }) = _FlashcardModel;

  factory FlashcardModel.fromJson(Map<String, dynamic> json) =>
      _$FlashcardModelFromJson(json);
}

/// Extension with convenience getters.
extension FlashcardModelX on FlashcardModel {
  /// Meaning for the user's language.
  String? meaningFor(String langCode) {
    switch (langCode) {
      case 'ur':
        return meaningUr;
      default:
        return meaningEn;
    }
  }

  /// Whether this card is new (never reviewed).
  bool get isNew => repetitions == 0;

  /// Days until next review.
  int get daysUntilReview {
    final now = DateTime.now();
    return nextReview.difference(now).inDays;
  }
}

/// Represents a flashcard review session result.
@freezed
abstract class FlashcardSessionResult with _$FlashcardSessionResult {
  const factory FlashcardSessionResult({
    @JsonKey(name: 'cards_reviewed') @Default(0) int cardsReviewed,
    @JsonKey(name: 'cards_again') @Default(0) int cardsAgain,
    @JsonKey(name: 'cards_hard') @Default(0) int cardsHard,
    @JsonKey(name: 'cards_easy') @Default(0) int cardsEasy,
    @JsonKey(name: 'next_due_date') DateTime? nextDueDate,
    @JsonKey(name: 'xp_earned') @Default(0) int xpEarned,
  }) = _FlashcardSessionResult;

  factory FlashcardSessionResult.fromJson(Map<String, dynamic> json) =>
      _$FlashcardSessionResultFromJson(json);
}

/// SM-2 grade values.
enum Sm2Grade {
  again(1),
  hard(3),
  easy(5);

  final int value;
  const Sm2Grade(this.value);
}
