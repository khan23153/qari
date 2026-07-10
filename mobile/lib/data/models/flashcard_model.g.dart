// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'flashcard_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_FlashcardModel _$FlashcardModelFromJson(Map<String, dynamic> json) =>
    _FlashcardModel(
      cardId: (json['card_id'] as num).toInt(),
      userId: json['user_id'] as String?,
      wordId: (json['word_id'] as num).toInt(),
      surahNumber: (json['surah_number'] as num).toInt(),
      ayahNumber: (json['ayah_number'] as num).toInt(),
      wordText: json['word_text'] as String,
      transliteration: json['transliteration'] as String?,
      meaningEn: json['meaning_en'] as String?,
      meaningUr: json['meaning_ur'] as String?,
      meaningHi: json['meaning_hi'] as String?,
      rootArabic: json['root_arabic'] as String?,
      posGroup: json['pos_group'] as String?,
      audioUrl: json['audio_url'] as String?,
      ayahText: json['ayah_text'] as String?,
      ayahTranslation: json['ayah_translation'] as String?,
      ease: (json['sm2_ease'] as num?)?.toDouble() ?? 2.5,
      interval: (json['sm2_interval'] as num?)?.toInt() ?? 0,
      repetitions: (json['sm2_repetitions'] as num?)?.toInt() ?? 0,
      nextReview: DateTime.parse(json['next_review'] as String),
      lastReviewed: json['last_reviewed'] == null
          ? null
          : DateTime.parse(json['last_reviewed'] as String),
      isDue: json['is_due'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
    );

Map<String, dynamic> _$FlashcardModelToJson(_FlashcardModel instance) =>
    <String, dynamic>{
      'card_id': instance.cardId,
      'user_id': instance.userId,
      'word_id': instance.wordId,
      'surah_number': instance.surahNumber,
      'ayah_number': instance.ayahNumber,
      'word_text': instance.wordText,
      'transliteration': instance.transliteration,
      'meaning_en': instance.meaningEn,
      'meaning_ur': instance.meaningUr,
      'meaning_hi': instance.meaningHi,
      'root_arabic': instance.rootArabic,
      'pos_group': instance.posGroup,
      'audio_url': instance.audioUrl,
      'ayah_text': instance.ayahText,
      'ayah_translation': instance.ayahTranslation,
      'sm2_ease': instance.ease,
      'sm2_interval': instance.interval,
      'sm2_repetitions': instance.repetitions,
      'next_review': instance.nextReview.toIso8601String(),
      'last_reviewed': instance.lastReviewed?.toIso8601String(),
      'is_due': instance.isDue,
      'created_at': instance.createdAt.toIso8601String(),
    };

_FlashcardSessionResult _$FlashcardSessionResultFromJson(
        Map<String, dynamic> json) =>
    _FlashcardSessionResult(
      cardsReviewed: (json['cards_reviewed'] as num?)?.toInt() ?? 0,
      cardsAgain: (json['cards_again'] as num?)?.toInt() ?? 0,
      cardsHard: (json['cards_hard'] as num?)?.toInt() ?? 0,
      cardsEasy: (json['cards_easy'] as num?)?.toInt() ?? 0,
      nextDueDate: json['next_due_date'] == null
          ? null
          : DateTime.parse(json['next_due_date'] as String),
      xpEarned: (json['xp_earned'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$FlashcardSessionResultToJson(
        _FlashcardSessionResult instance) =>
    <String, dynamic>{
      'cards_reviewed': instance.cardsReviewed,
      'cards_again': instance.cardsAgain,
      'cards_hard': instance.cardsHard,
      'cards_easy': instance.cardsEasy,
      'next_due_date': instance.nextDueDate?.toIso8601String(),
      'xp_earned': instance.xpEarned,
    };
