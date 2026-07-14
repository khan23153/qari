import 'package:freezed_annotation/freezed_annotation.dart';

part 'word_model.freezed.dart';
part 'word_model.g.dart';

/// Represents a single word in an ayah with grammar and tajweed metadata.
@freezed
abstract class WordModel with _$WordModel {
  const factory WordModel({
    @JsonKey(name: 'word_id') required int wordId,
    @JsonKey(name: 'surah_number') required int surahNumber,
    @JsonKey(name: 'ayah_number') required int ayahNumber,
    @JsonKey(name: 'word_number') required int wordNumber,
    required String text,
    @JsonKey(name: 'text_clean') String? textClean,
    @JsonKey(name: 'transliteration') String? transliteration,
    @JsonKey(name: 'translation_en') String? translationEn,
    @JsonKey(name: 'translation_ur') String? translationUr,
    @JsonKey(name: 'translation_hi') String? translationHi,
    @JsonKey(name: 'pos_group') String? posGroup,
    @JsonKey(name: 'pos_arabic') String? posArabic,
    @JsonKey(name: 'root_arabic') String? rootArabic,
    @JsonKey(name: 'root_id') int? rootId,
    @JsonKey(name: 'morphology') String? morphology,
    @JsonKey(name: 'lemma') String? lemma,
    @JsonKey(name: 'audio_url') String? audioUrl,
    @JsonKey(name: 'tajweed_spans') List<TajweedSpan>? tajweedSpans,
  }) = _WordModel;

  factory WordModel.fromJson(Map<String, dynamic> json) =>
      _$WordModelFromJson(json);
}

/// Represents a tajweed rule span within a word.
@freezed
abstract class TajweedSpan with _$TajweedSpan {
  const factory TajweedSpan({
    required int start,
    required int end,
    required String rule,
    @JsonKey(name: 'rule_name') String? ruleName,
    @JsonKey(name: 'rule_description') String? ruleDescription,
  }) = _TajweedSpan;

  factory TajweedSpan.fromJson(Map<String, dynamic> json) =>
      _$TajweedSpanFromJson(json);
}

/// Represents a complete ayah with all its words.
@freezed
abstract class AyahModel with _$AyahModel {
  const factory AyahModel({
    @JsonKey(name: 'ayah_id') required int ayahId,
    @JsonKey(name: 'surah_number') required int surahNumber,
    @JsonKey(name: 'ayah_number') required int ayahNumber,
    @JsonKey(name: 'ayah_text') required String ayahText,
    @JsonKey(name: 'ayah_text_simple') String? ayahTextSimple,
    @JsonKey(name: 'translation_en') String? translationEn,
    @JsonKey(name: 'translation_ur') String? translationUr,
    @JsonKey(name: 'translation_hi') String? translationHi,
    @JsonKey(name: 'transliteration') String? transliteration,
    @JsonKey(name: 'audio_url') String? audioUrl,
    @JsonKey(name: 'audio_url_ur') String? audioUrlUr,
    @JsonKey(name: 'page_number') int? pageNumber,
    @JsonKey(name: 'juz_number') int? juzNumber,
    @JsonKey(name: 'is_bismillah') @Default(false) bool isBismillah,
    @JsonKey(name: 'words') @Default([]) List<WordModel> words,
    @JsonKey(name: 'sajda') @Default(false) bool sajda,
    @JsonKey(name: 'context_story') String? contextStory,
  }) = _AyahModel;

  factory AyahModel.fromJson(Map<String, dynamic> json) =>
      _$AyahModelFromJson(json);
}

/// Extension with convenience getters for AyahModel.
extension AyahModelX on AyahModel {
  /// Full reference string, e.g. "2:255".
  String get reference => '$surahNumber:$ayahNumber';

  /// Translation for the user's language.
  String? translationFor(String langCode) {
    switch (langCode) {
      case 'ur':
        return translationUr;
      case 'hi':
        return translationHi;
      default:
        return translationEn;
    }
  }
}

/// Extension with convenience getters for WordModel.
extension WordModelX on WordModel {
  /// Translation for the user's language.
  String? translationFor(String langCode) {
    switch (langCode) {
      case 'ur':
        return translationUr;
      case 'hi':
        return translationHi;
      default:
        return translationEn;
    }
  }

  /// Whether this word has a known root.
  bool get hasRoot => rootArabic != null && rootArabic!.isNotEmpty;
}
