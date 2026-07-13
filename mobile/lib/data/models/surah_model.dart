import 'package:freezed_annotation/freezed_annotation.dart';

part 'surah_model.freezed.dart';
part 'surah_model.g.dart';

/// Represents a Surah (chapter) of the Quran.
@freezed
abstract class SurahModel with _$SurahModel {
  const factory SurahModel({
    @JsonKey(name: 'surah_id') required int surahId,
    @JsonKey(name: 'surah_number') required int surahNumber,
    // The backend's SurahBrief exposes a computed `name` (the transliteration,
    // often absent). Kept as nullable and not used by the UI (we use
    // nameArabic), so a missing key never breaks fromJson.
    String? name,
    @JsonKey(name: 'name_arabic') required String nameArabic,
    @JsonKey(name: 'name_english') required String nameEnglish,
    @JsonKey(name: 'name_translation') required String nameTranslation,
    @JsonKey(name: 'revelation_type') required String revelationType,
    @JsonKey(name: 'ayah_count') required int ayahCount,
    @JsonKey(name: 'revelation_order') required int revelationOrder,
    @JsonKey(name: 'page_start') int? pageStart,
    @JsonKey(name: 'page_end') int? pageEnd,
  }) = _SurahModel;

  factory SurahModel.fromJson(Map<String, dynamic> json) =>
      _$SurahModelFromJson(json);
}

/// Extension with convenience getters.
extension SurahModelX on SurahModel {
  /// Whether this surah was revealed in Mecca.
  bool get isMeccan => revelationType.toLowerCase() == 'meccan';

  /// Whether this surah was revealed in Medina.
  bool get isMedinan => revelationType.toLowerCase() == 'medinan';

  /// Display name in the user's language.
  String displayName(String langCode) {
    switch (langCode) {
      case 'ur':
        return nameArabic;
      case 'hi':
        return nameEnglish;
      default:
        return nameEnglish;
    }
  }
}
