import 'package:freezed_annotation/freezed_annotation.dart';

part 'surah_model.freezed.dart';
part 'surah_model.g.dart';

@freezed
class SurahModel with _$SurahModel {
  const factory SurahModel({
    required int surahNumber,
    required String nameArabic,
    required String nameTranslit,
    required Map<String, dynamic> nameTranslated,
    required String revelationPlace,
    required int ayahCount,
    @Default(false) bool hasContextStory,
    Map<String, dynamic>? contextStory,
  }) = _SurahModel;

  factory SurahModel.fromJson(Map<String, dynamic> json) =>
      _$SurahModelFromJson(json);
}
