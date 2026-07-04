import 'package:freezed_annotation/freezed_annotation.dart';

part 'word_model.freezed.dart';
part 'word_model.g.dart';

@freezed
class WordModel with _$WordModel {
  const factory WordModel({
    required int wordPosition,
    required String textUthmani,
    required String transliteration,
    required Map<String, dynamic> translation,
    required String posTag,
    required String posGroup,
    String? audioUrl,
    @Default([]) List<TajweedSpan> tajweedSpans,
  }) = _WordModel;

  factory WordModel.fromJson(Map<String, dynamic> json) =>
      _$WordModelFromJson(json);
}

@freezed
class TajweedSpan with _$TajweedSpan {
  const factory TajweedSpan({
    required int charStart,
    required int charEnd,
    required String rule,
  }) = _TajweedSpan;

  factory TajweedSpan.fromJson(Map<String, dynamic> json) =>
      _$TajweedSpanFromJson(json);
}

@freezed
class AyahModel with _$AyahModel {
  const factory AyahModel({
    required int surahNumber,
    required int ayahNumber,
    required String textUthmani,
    required String textImlaei,
    int? pageNumber,
    int? juzNumber,
    @Default([]) List<WordModel> words,
  }) = _AyahModel;

  factory AyahModel.fromJson(Map<String, dynamic> json) =>
      _$AyahModelFromJson(json);
}
