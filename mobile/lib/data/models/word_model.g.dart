// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'word_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_WordModel _$WordModelFromJson(Map<String, dynamic> json) => _WordModel(
      wordId: (json['word_id'] as num).toInt(),
      surahNumber: (json['surah_number'] as num).toInt(),
      ayahNumber: (json['ayah_number'] as num).toInt(),
      wordNumber: (json['word_number'] as num).toInt(),
      text: json['text'] as String,
      textClean: json['text_clean'] as String?,
      transliteration: json['transliteration'] as String?,
      translationEn: json['translation_en'] as String?,
      translationUr: json['translation_ur'] as String?,
      translationHi: json['translation_hi'] as String?,
      posGroup: json['pos_group'] as String?,
      posArabic: json['pos_arabic'] as String?,
      rootArabic: json['root_arabic'] as String?,
      rootId: (json['root_id'] as num?)?.toInt(),
      morphology: json['morphology'] as String?,
      lemma: json['lemma'] as String?,
      audioUrl: json['audio_url'] as String?,
      tajweedSpans: (json['tajweed_spans'] as List<dynamic>?)
          ?.map((e) => TajweedSpan.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$WordModelToJson(_WordModel instance) =>
    <String, dynamic>{
      'word_id': instance.wordId,
      'surah_number': instance.surahNumber,
      'ayah_number': instance.ayahNumber,
      'word_number': instance.wordNumber,
      'text': instance.text,
      'text_clean': instance.textClean,
      'transliteration': instance.transliteration,
      'translation_en': instance.translationEn,
      'translation_ur': instance.translationUr,
      'translation_hi': instance.translationHi,
      'pos_group': instance.posGroup,
      'pos_arabic': instance.posArabic,
      'root_arabic': instance.rootArabic,
      'root_id': instance.rootId,
      'morphology': instance.morphology,
      'lemma': instance.lemma,
      'audio_url': instance.audioUrl,
      'tajweed_spans': instance.tajweedSpans,
    };

_TajweedSpan _$TajweedSpanFromJson(Map<String, dynamic> json) => _TajweedSpan(
      start: (json['start'] as num).toInt(),
      end: (json['end'] as num).toInt(),
      rule: json['rule'] as String,
      ruleName: json['rule_name'] as String?,
      ruleDescription: json['rule_description'] as String?,
    );

Map<String, dynamic> _$TajweedSpanToJson(_TajweedSpan instance) =>
    <String, dynamic>{
      'start': instance.start,
      'end': instance.end,
      'rule': instance.rule,
      'rule_name': instance.ruleName,
      'rule_description': instance.ruleDescription,
    };

_AyahModel _$AyahModelFromJson(Map<String, dynamic> json) => _AyahModel(
      ayahId: (json['ayah_id'] as num).toInt(),
      surahNumber: (json['surah_number'] as num).toInt(),
      ayahNumber: (json['ayah_number'] as num).toInt(),
      ayahText: json['ayah_text'] as String,
      ayahTextSimple: json['ayah_text_simple'] as String?,
      translationEn: json['translation_en'] as String?,
      translationUr: json['translation_ur'] as String?,
      translationHi: json['translation_hi'] as String?,
      transliteration: json['transliteration'] as String?,
      audioUrl: json['audio_url'] as String?,
      pageNumber: (json['page_number'] as num?)?.toInt(),
      juzNumber: (json['juz_number'] as num?)?.toInt(),
      isBismillah: json['is_bismillah'] as bool? ?? false,
      words: (json['words'] as List<dynamic>?)
              ?.map((e) => WordModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      sajda: json['sajda'] as bool? ?? false,
      contextStory: json['context_story'] as String?,
    );

Map<String, dynamic> _$AyahModelToJson(_AyahModel instance) =>
    <String, dynamic>{
      'ayah_id': instance.ayahId,
      'surah_number': instance.surahNumber,
      'ayah_number': instance.ayahNumber,
      'ayah_text': instance.ayahText,
      'ayah_text_simple': instance.ayahTextSimple,
      'translation_en': instance.translationEn,
      'translation_ur': instance.translationUr,
      'translation_hi': instance.translationHi,
      'transliteration': instance.transliteration,
      'audio_url': instance.audioUrl,
      'page_number': instance.pageNumber,
      'juz_number': instance.juzNumber,
      'is_bismillah': instance.isBismillah,
      'words': instance.words,
      'sajda': instance.sajda,
      'context_story': instance.contextStory,
    };
