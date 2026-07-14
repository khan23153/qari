// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'word_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$WordModel {
  @JsonKey(name: 'word_id')
  int get wordId;
  @JsonKey(name: 'surah_number')
  int get surahNumber;
  @JsonKey(name: 'ayah_number')
  int get ayahNumber;
  @JsonKey(name: 'word_number')
  int get wordNumber;
  String get text;
  @JsonKey(name: 'text_clean')
  String? get textClean;
  @JsonKey(name: 'transliteration')
  String? get transliteration;
  @JsonKey(name: 'translation_en')
  String? get translationEn;
  @JsonKey(name: 'translation_ur')
  String? get translationUr;
  @JsonKey(name: 'translation_hi')
  String? get translationHi;
  @JsonKey(name: 'pos_group')
  String? get posGroup;
  @JsonKey(name: 'pos_arabic')
  String? get posArabic;
  @JsonKey(name: 'root_arabic')
  String? get rootArabic;
  @JsonKey(name: 'root_id')
  int? get rootId;
  @JsonKey(name: 'morphology')
  String? get morphology;
  @JsonKey(name: 'lemma')
  String? get lemma;
  @JsonKey(name: 'audio_url')
  String? get audioUrl;
  @JsonKey(name: 'tajweed_spans')
  List<TajweedSpan>? get tajweedSpans;

  /// Create a copy of WordModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $WordModelCopyWith<WordModel> get copyWith =>
      _$WordModelCopyWithImpl<WordModel>(this as WordModel, _$identity);

  /// Serializes this WordModel to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is WordModel &&
            (identical(other.wordId, wordId) || other.wordId == wordId) &&
            (identical(other.surahNumber, surahNumber) ||
                other.surahNumber == surahNumber) &&
            (identical(other.ayahNumber, ayahNumber) ||
                other.ayahNumber == ayahNumber) &&
            (identical(other.wordNumber, wordNumber) ||
                other.wordNumber == wordNumber) &&
            (identical(other.text, text) || other.text == text) &&
            (identical(other.textClean, textClean) ||
                other.textClean == textClean) &&
            (identical(other.transliteration, transliteration) ||
                other.transliteration == transliteration) &&
            (identical(other.translationEn, translationEn) ||
                other.translationEn == translationEn) &&
            (identical(other.translationUr, translationUr) ||
                other.translationUr == translationUr) &&
            (identical(other.translationHi, translationHi) ||
                other.translationHi == translationHi) &&
            (identical(other.posGroup, posGroup) ||
                other.posGroup == posGroup) &&
            (identical(other.posArabic, posArabic) ||
                other.posArabic == posArabic) &&
            (identical(other.rootArabic, rootArabic) ||
                other.rootArabic == rootArabic) &&
            (identical(other.rootId, rootId) || other.rootId == rootId) &&
            (identical(other.morphology, morphology) ||
                other.morphology == morphology) &&
            (identical(other.lemma, lemma) || other.lemma == lemma) &&
            (identical(other.audioUrl, audioUrl) ||
                other.audioUrl == audioUrl) &&
            const DeepCollectionEquality()
                .equals(other.tajweedSpans, tajweedSpans));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      wordId,
      surahNumber,
      ayahNumber,
      wordNumber,
      text,
      textClean,
      transliteration,
      translationEn,
      translationUr,
      translationHi,
      posGroup,
      posArabic,
      rootArabic,
      rootId,
      morphology,
      lemma,
      audioUrl,
      const DeepCollectionEquality().hash(tajweedSpans));

  @override
  String toString() {
    return 'WordModel(wordId: $wordId, surahNumber: $surahNumber, ayahNumber: $ayahNumber, wordNumber: $wordNumber, text: $text, textClean: $textClean, transliteration: $transliteration, translationEn: $translationEn, translationUr: $translationUr, translationHi: $translationHi, posGroup: $posGroup, posArabic: $posArabic, rootArabic: $rootArabic, rootId: $rootId, morphology: $morphology, lemma: $lemma, audioUrl: $audioUrl, tajweedSpans: $tajweedSpans)';
  }
}

/// @nodoc
abstract mixin class $WordModelCopyWith<$Res> {
  factory $WordModelCopyWith(WordModel value, $Res Function(WordModel) _then) =
      _$WordModelCopyWithImpl;
  @useResult
  $Res call(
      {@JsonKey(name: 'word_id') int wordId,
      @JsonKey(name: 'surah_number') int surahNumber,
      @JsonKey(name: 'ayah_number') int ayahNumber,
      @JsonKey(name: 'word_number') int wordNumber,
      String text,
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
      @JsonKey(name: 'tajweed_spans') List<TajweedSpan>? tajweedSpans});
}

/// @nodoc
class _$WordModelCopyWithImpl<$Res> implements $WordModelCopyWith<$Res> {
  _$WordModelCopyWithImpl(this._self, this._then);

  final WordModel _self;
  final $Res Function(WordModel) _then;

  /// Create a copy of WordModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? wordId = null,
    Object? surahNumber = null,
    Object? ayahNumber = null,
    Object? wordNumber = null,
    Object? text = null,
    Object? textClean = freezed,
    Object? transliteration = freezed,
    Object? translationEn = freezed,
    Object? translationUr = freezed,
    Object? translationHi = freezed,
    Object? posGroup = freezed,
    Object? posArabic = freezed,
    Object? rootArabic = freezed,
    Object? rootId = freezed,
    Object? morphology = freezed,
    Object? lemma = freezed,
    Object? audioUrl = freezed,
    Object? tajweedSpans = freezed,
  }) {
    return _then(_self.copyWith(
      wordId: null == wordId
          ? _self.wordId
          : wordId // ignore: cast_nullable_to_non_nullable
              as int,
      surahNumber: null == surahNumber
          ? _self.surahNumber
          : surahNumber // ignore: cast_nullable_to_non_nullable
              as int,
      ayahNumber: null == ayahNumber
          ? _self.ayahNumber
          : ayahNumber // ignore: cast_nullable_to_non_nullable
              as int,
      wordNumber: null == wordNumber
          ? _self.wordNumber
          : wordNumber // ignore: cast_nullable_to_non_nullable
              as int,
      text: null == text
          ? _self.text
          : text // ignore: cast_nullable_to_non_nullable
              as String,
      textClean: freezed == textClean
          ? _self.textClean
          : textClean // ignore: cast_nullable_to_non_nullable
              as String?,
      transliteration: freezed == transliteration
          ? _self.transliteration
          : transliteration // ignore: cast_nullable_to_non_nullable
              as String?,
      translationEn: freezed == translationEn
          ? _self.translationEn
          : translationEn // ignore: cast_nullable_to_non_nullable
              as String?,
      translationUr: freezed == translationUr
          ? _self.translationUr
          : translationUr // ignore: cast_nullable_to_non_nullable
              as String?,
      translationHi: freezed == translationHi
          ? _self.translationHi
          : translationHi // ignore: cast_nullable_to_non_nullable
              as String?,
      posGroup: freezed == posGroup
          ? _self.posGroup
          : posGroup // ignore: cast_nullable_to_non_nullable
              as String?,
      posArabic: freezed == posArabic
          ? _self.posArabic
          : posArabic // ignore: cast_nullable_to_non_nullable
              as String?,
      rootArabic: freezed == rootArabic
          ? _self.rootArabic
          : rootArabic // ignore: cast_nullable_to_non_nullable
              as String?,
      rootId: freezed == rootId
          ? _self.rootId
          : rootId // ignore: cast_nullable_to_non_nullable
              as int?,
      morphology: freezed == morphology
          ? _self.morphology
          : morphology // ignore: cast_nullable_to_non_nullable
              as String?,
      lemma: freezed == lemma
          ? _self.lemma
          : lemma // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrl: freezed == audioUrl
          ? _self.audioUrl
          : audioUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      tajweedSpans: freezed == tajweedSpans
          ? _self.tajweedSpans
          : tajweedSpans // ignore: cast_nullable_to_non_nullable
              as List<TajweedSpan>?,
    ));
  }
}

/// Adds pattern-matching-related methods to [WordModel].
extension WordModelPatterns on WordModel {
  /// A variant of `map` that fallback to returning `orElse`.
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case final Subclass value:
  ///     return ...;
  ///   case _:
  ///     return orElse();
  /// }
  /// ```

  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>(
    TResult Function(_WordModel value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _WordModel() when $default != null:
        return $default(_that);
      case _:
        return orElse();
    }
  }

  /// A `switch`-like method, using callbacks.
  ///
  /// Callbacks receives the raw object, upcasted.
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case final Subclass value:
  ///     return ...;
  ///   case final Subclass2 value:
  ///     return ...;
  /// }
  /// ```

  @optionalTypeArgs
  TResult map<TResult extends Object?>(
    TResult Function(_WordModel value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _WordModel():
        return $default(_that);
      case _:
        throw StateError('Unexpected subclass');
    }
  }

  /// A variant of `map` that fallback to returning `null`.
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case final Subclass value:
  ///     return ...;
  ///   case _:
  ///     return null;
  /// }
  /// ```

  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>(
    TResult? Function(_WordModel value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _WordModel() when $default != null:
        return $default(_that);
      case _:
        return null;
    }
  }

  /// A variant of `when` that fallback to an `orElse` callback.
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case Subclass(:final field):
  ///     return ...;
  ///   case _:
  ///     return orElse();
  /// }
  /// ```

  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>(
    TResult Function(
            @JsonKey(name: 'word_id') int wordId,
            @JsonKey(name: 'surah_number') int surahNumber,
            @JsonKey(name: 'ayah_number') int ayahNumber,
            @JsonKey(name: 'word_number') int wordNumber,
            String text,
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
            @JsonKey(name: 'tajweed_spans') List<TajweedSpan>? tajweedSpans)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _WordModel() when $default != null:
        return $default(
            _that.wordId,
            _that.surahNumber,
            _that.ayahNumber,
            _that.wordNumber,
            _that.text,
            _that.textClean,
            _that.transliteration,
            _that.translationEn,
            _that.translationUr,
            _that.translationHi,
            _that.posGroup,
            _that.posArabic,
            _that.rootArabic,
            _that.rootId,
            _that.morphology,
            _that.lemma,
            _that.audioUrl,
            _that.tajweedSpans);
      case _:
        return orElse();
    }
  }

  /// A `switch`-like method, using callbacks.
  ///
  /// As opposed to `map`, this offers destructuring.
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case Subclass(:final field):
  ///     return ...;
  ///   case Subclass2(:final field2):
  ///     return ...;
  /// }
  /// ```

  @optionalTypeArgs
  TResult when<TResult extends Object?>(
    TResult Function(
            @JsonKey(name: 'word_id') int wordId,
            @JsonKey(name: 'surah_number') int surahNumber,
            @JsonKey(name: 'ayah_number') int ayahNumber,
            @JsonKey(name: 'word_number') int wordNumber,
            String text,
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
            @JsonKey(name: 'tajweed_spans') List<TajweedSpan>? tajweedSpans)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _WordModel():
        return $default(
            _that.wordId,
            _that.surahNumber,
            _that.ayahNumber,
            _that.wordNumber,
            _that.text,
            _that.textClean,
            _that.transliteration,
            _that.translationEn,
            _that.translationUr,
            _that.translationHi,
            _that.posGroup,
            _that.posArabic,
            _that.rootArabic,
            _that.rootId,
            _that.morphology,
            _that.lemma,
            _that.audioUrl,
            _that.tajweedSpans);
      case _:
        throw StateError('Unexpected subclass');
    }
  }

  /// A variant of `when` that fallback to returning `null`
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case Subclass(:final field):
  ///     return ...;
  ///   case _:
  ///     return null;
  /// }
  /// ```

  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>(
    TResult? Function(
            @JsonKey(name: 'word_id') int wordId,
            @JsonKey(name: 'surah_number') int surahNumber,
            @JsonKey(name: 'ayah_number') int ayahNumber,
            @JsonKey(name: 'word_number') int wordNumber,
            String text,
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
            @JsonKey(name: 'tajweed_spans') List<TajweedSpan>? tajweedSpans)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _WordModel() when $default != null:
        return $default(
            _that.wordId,
            _that.surahNumber,
            _that.ayahNumber,
            _that.wordNumber,
            _that.text,
            _that.textClean,
            _that.transliteration,
            _that.translationEn,
            _that.translationUr,
            _that.translationHi,
            _that.posGroup,
            _that.posArabic,
            _that.rootArabic,
            _that.rootId,
            _that.morphology,
            _that.lemma,
            _that.audioUrl,
            _that.tajweedSpans);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _WordModel implements WordModel {
  const _WordModel(
      {@JsonKey(name: 'word_id') required this.wordId,
      @JsonKey(name: 'surah_number') required this.surahNumber,
      @JsonKey(name: 'ayah_number') required this.ayahNumber,
      @JsonKey(name: 'word_number') required this.wordNumber,
      required this.text,
      @JsonKey(name: 'text_clean') this.textClean,
      @JsonKey(name: 'transliteration') this.transliteration,
      @JsonKey(name: 'translation_en') this.translationEn,
      @JsonKey(name: 'translation_ur') this.translationUr,
      @JsonKey(name: 'translation_hi') this.translationHi,
      @JsonKey(name: 'pos_group') this.posGroup,
      @JsonKey(name: 'pos_arabic') this.posArabic,
      @JsonKey(name: 'root_arabic') this.rootArabic,
      @JsonKey(name: 'root_id') this.rootId,
      @JsonKey(name: 'morphology') this.morphology,
      @JsonKey(name: 'lemma') this.lemma,
      @JsonKey(name: 'audio_url') this.audioUrl,
      @JsonKey(name: 'tajweed_spans') final List<TajweedSpan>? tajweedSpans})
      : _tajweedSpans = tajweedSpans;
  factory _WordModel.fromJson(Map<String, dynamic> json) =>
      _$WordModelFromJson(json);

  @override
  @JsonKey(name: 'word_id')
  final int wordId;
  @override
  @JsonKey(name: 'surah_number')
  final int surahNumber;
  @override
  @JsonKey(name: 'ayah_number')
  final int ayahNumber;
  @override
  @JsonKey(name: 'word_number')
  final int wordNumber;
  @override
  final String text;
  @override
  @JsonKey(name: 'text_clean')
  final String? textClean;
  @override
  @JsonKey(name: 'transliteration')
  final String? transliteration;
  @override
  @JsonKey(name: 'translation_en')
  final String? translationEn;
  @override
  @JsonKey(name: 'translation_ur')
  final String? translationUr;
  @override
  @JsonKey(name: 'translation_hi')
  final String? translationHi;
  @override
  @JsonKey(name: 'pos_group')
  final String? posGroup;
  @override
  @JsonKey(name: 'pos_arabic')
  final String? posArabic;
  @override
  @JsonKey(name: 'root_arabic')
  final String? rootArabic;
  @override
  @JsonKey(name: 'root_id')
  final int? rootId;
  @override
  @JsonKey(name: 'morphology')
  final String? morphology;
  @override
  @JsonKey(name: 'lemma')
  final String? lemma;
  @override
  @JsonKey(name: 'audio_url')
  final String? audioUrl;
  final List<TajweedSpan>? _tajweedSpans;
  @override
  @JsonKey(name: 'tajweed_spans')
  List<TajweedSpan>? get tajweedSpans {
    final value = _tajweedSpans;
    if (value == null) return null;
    if (_tajweedSpans is EqualUnmodifiableListView) return _tajweedSpans;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  /// Create a copy of WordModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$WordModelCopyWith<_WordModel> get copyWith =>
      __$WordModelCopyWithImpl<_WordModel>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$WordModelToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _WordModel &&
            (identical(other.wordId, wordId) || other.wordId == wordId) &&
            (identical(other.surahNumber, surahNumber) ||
                other.surahNumber == surahNumber) &&
            (identical(other.ayahNumber, ayahNumber) ||
                other.ayahNumber == ayahNumber) &&
            (identical(other.wordNumber, wordNumber) ||
                other.wordNumber == wordNumber) &&
            (identical(other.text, text) || other.text == text) &&
            (identical(other.textClean, textClean) ||
                other.textClean == textClean) &&
            (identical(other.transliteration, transliteration) ||
                other.transliteration == transliteration) &&
            (identical(other.translationEn, translationEn) ||
                other.translationEn == translationEn) &&
            (identical(other.translationUr, translationUr) ||
                other.translationUr == translationUr) &&
            (identical(other.translationHi, translationHi) ||
                other.translationHi == translationHi) &&
            (identical(other.posGroup, posGroup) ||
                other.posGroup == posGroup) &&
            (identical(other.posArabic, posArabic) ||
                other.posArabic == posArabic) &&
            (identical(other.rootArabic, rootArabic) ||
                other.rootArabic == rootArabic) &&
            (identical(other.rootId, rootId) || other.rootId == rootId) &&
            (identical(other.morphology, morphology) ||
                other.morphology == morphology) &&
            (identical(other.lemma, lemma) || other.lemma == lemma) &&
            (identical(other.audioUrl, audioUrl) ||
                other.audioUrl == audioUrl) &&
            const DeepCollectionEquality()
                .equals(other._tajweedSpans, _tajweedSpans));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      wordId,
      surahNumber,
      ayahNumber,
      wordNumber,
      text,
      textClean,
      transliteration,
      translationEn,
      translationUr,
      translationHi,
      posGroup,
      posArabic,
      rootArabic,
      rootId,
      morphology,
      lemma,
      audioUrl,
      const DeepCollectionEquality().hash(_tajweedSpans));

  @override
  String toString() {
    return 'WordModel(wordId: $wordId, surahNumber: $surahNumber, ayahNumber: $ayahNumber, wordNumber: $wordNumber, text: $text, textClean: $textClean, transliteration: $transliteration, translationEn: $translationEn, translationUr: $translationUr, translationHi: $translationHi, posGroup: $posGroup, posArabic: $posArabic, rootArabic: $rootArabic, rootId: $rootId, morphology: $morphology, lemma: $lemma, audioUrl: $audioUrl, tajweedSpans: $tajweedSpans)';
  }
}

/// @nodoc
abstract mixin class _$WordModelCopyWith<$Res>
    implements $WordModelCopyWith<$Res> {
  factory _$WordModelCopyWith(
          _WordModel value, $Res Function(_WordModel) _then) =
      __$WordModelCopyWithImpl;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'word_id') int wordId,
      @JsonKey(name: 'surah_number') int surahNumber,
      @JsonKey(name: 'ayah_number') int ayahNumber,
      @JsonKey(name: 'word_number') int wordNumber,
      String text,
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
      @JsonKey(name: 'tajweed_spans') List<TajweedSpan>? tajweedSpans});
}

/// @nodoc
class __$WordModelCopyWithImpl<$Res> implements _$WordModelCopyWith<$Res> {
  __$WordModelCopyWithImpl(this._self, this._then);

  final _WordModel _self;
  final $Res Function(_WordModel) _then;

  /// Create a copy of WordModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? wordId = null,
    Object? surahNumber = null,
    Object? ayahNumber = null,
    Object? wordNumber = null,
    Object? text = null,
    Object? textClean = freezed,
    Object? transliteration = freezed,
    Object? translationEn = freezed,
    Object? translationUr = freezed,
    Object? translationHi = freezed,
    Object? posGroup = freezed,
    Object? posArabic = freezed,
    Object? rootArabic = freezed,
    Object? rootId = freezed,
    Object? morphology = freezed,
    Object? lemma = freezed,
    Object? audioUrl = freezed,
    Object? tajweedSpans = freezed,
  }) {
    return _then(_WordModel(
      wordId: null == wordId
          ? _self.wordId
          : wordId // ignore: cast_nullable_to_non_nullable
              as int,
      surahNumber: null == surahNumber
          ? _self.surahNumber
          : surahNumber // ignore: cast_nullable_to_non_nullable
              as int,
      ayahNumber: null == ayahNumber
          ? _self.ayahNumber
          : ayahNumber // ignore: cast_nullable_to_non_nullable
              as int,
      wordNumber: null == wordNumber
          ? _self.wordNumber
          : wordNumber // ignore: cast_nullable_to_non_nullable
              as int,
      text: null == text
          ? _self.text
          : text // ignore: cast_nullable_to_non_nullable
              as String,
      textClean: freezed == textClean
          ? _self.textClean
          : textClean // ignore: cast_nullable_to_non_nullable
              as String?,
      transliteration: freezed == transliteration
          ? _self.transliteration
          : transliteration // ignore: cast_nullable_to_non_nullable
              as String?,
      translationEn: freezed == translationEn
          ? _self.translationEn
          : translationEn // ignore: cast_nullable_to_non_nullable
              as String?,
      translationUr: freezed == translationUr
          ? _self.translationUr
          : translationUr // ignore: cast_nullable_to_non_nullable
              as String?,
      translationHi: freezed == translationHi
          ? _self.translationHi
          : translationHi // ignore: cast_nullable_to_non_nullable
              as String?,
      posGroup: freezed == posGroup
          ? _self.posGroup
          : posGroup // ignore: cast_nullable_to_non_nullable
              as String?,
      posArabic: freezed == posArabic
          ? _self.posArabic
          : posArabic // ignore: cast_nullable_to_non_nullable
              as String?,
      rootArabic: freezed == rootArabic
          ? _self.rootArabic
          : rootArabic // ignore: cast_nullable_to_non_nullable
              as String?,
      rootId: freezed == rootId
          ? _self.rootId
          : rootId // ignore: cast_nullable_to_non_nullable
              as int?,
      morphology: freezed == morphology
          ? _self.morphology
          : morphology // ignore: cast_nullable_to_non_nullable
              as String?,
      lemma: freezed == lemma
          ? _self.lemma
          : lemma // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrl: freezed == audioUrl
          ? _self.audioUrl
          : audioUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      tajweedSpans: freezed == tajweedSpans
          ? _self._tajweedSpans
          : tajweedSpans // ignore: cast_nullable_to_non_nullable
              as List<TajweedSpan>?,
    ));
  }
}

/// @nodoc
mixin _$TajweedSpan {
  int get start;
  int get end;
  String get rule;
  @JsonKey(name: 'rule_name')
  String? get ruleName;
  @JsonKey(name: 'rule_description')
  String? get ruleDescription;

  /// Create a copy of TajweedSpan
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $TajweedSpanCopyWith<TajweedSpan> get copyWith =>
      _$TajweedSpanCopyWithImpl<TajweedSpan>(this as TajweedSpan, _$identity);

  /// Serializes this TajweedSpan to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is TajweedSpan &&
            (identical(other.start, start) || other.start == start) &&
            (identical(other.end, end) || other.end == end) &&
            (identical(other.rule, rule) || other.rule == rule) &&
            (identical(other.ruleName, ruleName) ||
                other.ruleName == ruleName) &&
            (identical(other.ruleDescription, ruleDescription) ||
                other.ruleDescription == ruleDescription));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, start, end, rule, ruleName, ruleDescription);

  @override
  String toString() {
    return 'TajweedSpan(start: $start, end: $end, rule: $rule, ruleName: $ruleName, ruleDescription: $ruleDescription)';
  }
}

/// @nodoc
abstract mixin class $TajweedSpanCopyWith<$Res> {
  factory $TajweedSpanCopyWith(
          TajweedSpan value, $Res Function(TajweedSpan) _then) =
      _$TajweedSpanCopyWithImpl;
  @useResult
  $Res call(
      {int start,
      int end,
      String rule,
      @JsonKey(name: 'rule_name') String? ruleName,
      @JsonKey(name: 'rule_description') String? ruleDescription});
}

/// @nodoc
class _$TajweedSpanCopyWithImpl<$Res> implements $TajweedSpanCopyWith<$Res> {
  _$TajweedSpanCopyWithImpl(this._self, this._then);

  final TajweedSpan _self;
  final $Res Function(TajweedSpan) _then;

  /// Create a copy of TajweedSpan
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? start = null,
    Object? end = null,
    Object? rule = null,
    Object? ruleName = freezed,
    Object? ruleDescription = freezed,
  }) {
    return _then(_self.copyWith(
      start: null == start
          ? _self.start
          : start // ignore: cast_nullable_to_non_nullable
              as int,
      end: null == end
          ? _self.end
          : end // ignore: cast_nullable_to_non_nullable
              as int,
      rule: null == rule
          ? _self.rule
          : rule // ignore: cast_nullable_to_non_nullable
              as String,
      ruleName: freezed == ruleName
          ? _self.ruleName
          : ruleName // ignore: cast_nullable_to_non_nullable
              as String?,
      ruleDescription: freezed == ruleDescription
          ? _self.ruleDescription
          : ruleDescription // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// Adds pattern-matching-related methods to [TajweedSpan].
extension TajweedSpanPatterns on TajweedSpan {
  /// A variant of `map` that fallback to returning `orElse`.
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case final Subclass value:
  ///     return ...;
  ///   case _:
  ///     return orElse();
  /// }
  /// ```

  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>(
    TResult Function(_TajweedSpan value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _TajweedSpan() when $default != null:
        return $default(_that);
      case _:
        return orElse();
    }
  }

  /// A `switch`-like method, using callbacks.
  ///
  /// Callbacks receives the raw object, upcasted.
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case final Subclass value:
  ///     return ...;
  ///   case final Subclass2 value:
  ///     return ...;
  /// }
  /// ```

  @optionalTypeArgs
  TResult map<TResult extends Object?>(
    TResult Function(_TajweedSpan value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _TajweedSpan():
        return $default(_that);
      case _:
        throw StateError('Unexpected subclass');
    }
  }

  /// A variant of `map` that fallback to returning `null`.
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case final Subclass value:
  ///     return ...;
  ///   case _:
  ///     return null;
  /// }
  /// ```

  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>(
    TResult? Function(_TajweedSpan value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _TajweedSpan() when $default != null:
        return $default(_that);
      case _:
        return null;
    }
  }

  /// A variant of `when` that fallback to an `orElse` callback.
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case Subclass(:final field):
  ///     return ...;
  ///   case _:
  ///     return orElse();
  /// }
  /// ```

  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>(
    TResult Function(
            int start,
            int end,
            String rule,
            @JsonKey(name: 'rule_name') String? ruleName,
            @JsonKey(name: 'rule_description') String? ruleDescription)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _TajweedSpan() when $default != null:
        return $default(_that.start, _that.end, _that.rule, _that.ruleName,
            _that.ruleDescription);
      case _:
        return orElse();
    }
  }

  /// A `switch`-like method, using callbacks.
  ///
  /// As opposed to `map`, this offers destructuring.
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case Subclass(:final field):
  ///     return ...;
  ///   case Subclass2(:final field2):
  ///     return ...;
  /// }
  /// ```

  @optionalTypeArgs
  TResult when<TResult extends Object?>(
    TResult Function(
            int start,
            int end,
            String rule,
            @JsonKey(name: 'rule_name') String? ruleName,
            @JsonKey(name: 'rule_description') String? ruleDescription)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _TajweedSpan():
        return $default(_that.start, _that.end, _that.rule, _that.ruleName,
            _that.ruleDescription);
      case _:
        throw StateError('Unexpected subclass');
    }
  }

  /// A variant of `when` that fallback to returning `null`
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case Subclass(:final field):
  ///     return ...;
  ///   case _:
  ///     return null;
  /// }
  /// ```

  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>(
    TResult? Function(
            int start,
            int end,
            String rule,
            @JsonKey(name: 'rule_name') String? ruleName,
            @JsonKey(name: 'rule_description') String? ruleDescription)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _TajweedSpan() when $default != null:
        return $default(_that.start, _that.end, _that.rule, _that.ruleName,
            _that.ruleDescription);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _TajweedSpan implements TajweedSpan {
  const _TajweedSpan(
      {required this.start,
      required this.end,
      required this.rule,
      @JsonKey(name: 'rule_name') this.ruleName,
      @JsonKey(name: 'rule_description') this.ruleDescription});
  factory _TajweedSpan.fromJson(Map<String, dynamic> json) =>
      _$TajweedSpanFromJson(json);

  @override
  final int start;
  @override
  final int end;
  @override
  final String rule;
  @override
  @JsonKey(name: 'rule_name')
  final String? ruleName;
  @override
  @JsonKey(name: 'rule_description')
  final String? ruleDescription;

  /// Create a copy of TajweedSpan
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$TajweedSpanCopyWith<_TajweedSpan> get copyWith =>
      __$TajweedSpanCopyWithImpl<_TajweedSpan>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$TajweedSpanToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _TajweedSpan &&
            (identical(other.start, start) || other.start == start) &&
            (identical(other.end, end) || other.end == end) &&
            (identical(other.rule, rule) || other.rule == rule) &&
            (identical(other.ruleName, ruleName) ||
                other.ruleName == ruleName) &&
            (identical(other.ruleDescription, ruleDescription) ||
                other.ruleDescription == ruleDescription));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, start, end, rule, ruleName, ruleDescription);

  @override
  String toString() {
    return 'TajweedSpan(start: $start, end: $end, rule: $rule, ruleName: $ruleName, ruleDescription: $ruleDescription)';
  }
}

/// @nodoc
abstract mixin class _$TajweedSpanCopyWith<$Res>
    implements $TajweedSpanCopyWith<$Res> {
  factory _$TajweedSpanCopyWith(
          _TajweedSpan value, $Res Function(_TajweedSpan) _then) =
      __$TajweedSpanCopyWithImpl;
  @override
  @useResult
  $Res call(
      {int start,
      int end,
      String rule,
      @JsonKey(name: 'rule_name') String? ruleName,
      @JsonKey(name: 'rule_description') String? ruleDescription});
}

/// @nodoc
class __$TajweedSpanCopyWithImpl<$Res> implements _$TajweedSpanCopyWith<$Res> {
  __$TajweedSpanCopyWithImpl(this._self, this._then);

  final _TajweedSpan _self;
  final $Res Function(_TajweedSpan) _then;

  /// Create a copy of TajweedSpan
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? start = null,
    Object? end = null,
    Object? rule = null,
    Object? ruleName = freezed,
    Object? ruleDescription = freezed,
  }) {
    return _then(_TajweedSpan(
      start: null == start
          ? _self.start
          : start // ignore: cast_nullable_to_non_nullable
              as int,
      end: null == end
          ? _self.end
          : end // ignore: cast_nullable_to_non_nullable
              as int,
      rule: null == rule
          ? _self.rule
          : rule // ignore: cast_nullable_to_non_nullable
              as String,
      ruleName: freezed == ruleName
          ? _self.ruleName
          : ruleName // ignore: cast_nullable_to_non_nullable
              as String?,
      ruleDescription: freezed == ruleDescription
          ? _self.ruleDescription
          : ruleDescription // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
mixin _$AyahModel {
  @JsonKey(name: 'ayah_id')
  int get ayahId;
  @JsonKey(name: 'surah_number')
  int get surahNumber;
  @JsonKey(name: 'ayah_number')
  int get ayahNumber;
  @JsonKey(name: 'ayah_text')
  String get ayahText;
  @JsonKey(name: 'ayah_text_simple')
  String? get ayahTextSimple;
  @JsonKey(name: 'translation_en')
  String? get translationEn;
  @JsonKey(name: 'translation_ur')
  String? get translationUr;
  @JsonKey(name: 'translation_hi')
  String? get translationHi;
  @JsonKey(name: 'transliteration')
  String? get transliteration;
  @JsonKey(name: 'audio_url')
  String? get audioUrl;
  @JsonKey(name: 'audio_url_ur')
  String? get audioUrlUr;
  @JsonKey(name: 'page_number')
  int? get pageNumber;
  @JsonKey(name: 'juz_number')
  int? get juzNumber;
  @JsonKey(name: 'is_bismillah')
  bool get isBismillah;
  @JsonKey(name: 'words')
  List<WordModel> get words;
  @JsonKey(name: 'sajda')
  bool get sajda;
  @JsonKey(name: 'context_story')
  String? get contextStory;

  /// Create a copy of AyahModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $AyahModelCopyWith<AyahModel> get copyWith =>
      _$AyahModelCopyWithImpl<AyahModel>(this as AyahModel, _$identity);

  /// Serializes this AyahModel to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is AyahModel &&
            (identical(other.ayahId, ayahId) || other.ayahId == ayahId) &&
            (identical(other.surahNumber, surahNumber) ||
                other.surahNumber == surahNumber) &&
            (identical(other.ayahNumber, ayahNumber) ||
                other.ayahNumber == ayahNumber) &&
            (identical(other.ayahText, ayahText) ||
                other.ayahText == ayahText) &&
            (identical(other.ayahTextSimple, ayahTextSimple) ||
                other.ayahTextSimple == ayahTextSimple) &&
            (identical(other.translationEn, translationEn) ||
                other.translationEn == translationEn) &&
            (identical(other.translationUr, translationUr) ||
                other.translationUr == translationUr) &&
            (identical(other.translationHi, translationHi) ||
                other.translationHi == translationHi) &&
            (identical(other.transliteration, transliteration) ||
                other.transliteration == transliteration) &&
            (identical(other.audioUrl, audioUrl) ||
                other.audioUrl == audioUrl) &&
            (identical(other.audioUrlUr, audioUrlUr) ||
                other.audioUrlUr == audioUrlUr) &&
            (identical(other.pageNumber, pageNumber) ||
                other.pageNumber == pageNumber) &&
            (identical(other.juzNumber, juzNumber) ||
                other.juzNumber == juzNumber) &&
            (identical(other.isBismillah, isBismillah) ||
                other.isBismillah == isBismillah) &&
            const DeepCollectionEquality().equals(other.words, words) &&
            (identical(other.sajda, sajda) || other.sajda == sajda) &&
            (identical(other.contextStory, contextStory) ||
                other.contextStory == contextStory));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      ayahId,
      surahNumber,
      ayahNumber,
      ayahText,
      ayahTextSimple,
      translationEn,
      translationUr,
      translationHi,
      transliteration,
      audioUrl,
      audioUrlUr,
      pageNumber,
      juzNumber,
      isBismillah,
      const DeepCollectionEquality().hash(words),
      sajda,
      contextStory);

  @override
  String toString() {
    return 'AyahModel(ayahId: $ayahId, surahNumber: $surahNumber, ayahNumber: $ayahNumber, ayahText: $ayahText, ayahTextSimple: $ayahTextSimple, translationEn: $translationEn, translationUr: $translationUr, translationHi: $translationHi, transliteration: $transliteration, audioUrl: $audioUrl, audioUrlUr: $audioUrlUr, pageNumber: $pageNumber, juzNumber: $juzNumber, isBismillah: $isBismillah, words: $words, sajda: $sajda, contextStory: $contextStory)';
  }
}

/// @nodoc
abstract mixin class $AyahModelCopyWith<$Res> {
  factory $AyahModelCopyWith(AyahModel value, $Res Function(AyahModel) _then) =
      _$AyahModelCopyWithImpl;
  @useResult
  $Res call(
      {@JsonKey(name: 'ayah_id') int ayahId,
      @JsonKey(name: 'surah_number') int surahNumber,
      @JsonKey(name: 'ayah_number') int ayahNumber,
      @JsonKey(name: 'ayah_text') String ayahText,
      @JsonKey(name: 'ayah_text_simple') String? ayahTextSimple,
      @JsonKey(name: 'translation_en') String? translationEn,
      @JsonKey(name: 'translation_ur') String? translationUr,
      @JsonKey(name: 'translation_hi') String? translationHi,
      @JsonKey(name: 'transliteration') String? transliteration,
      @JsonKey(name: 'audio_url') String? audioUrl,
      @JsonKey(name: 'audio_url_ur') String? audioUrlUr,
      @JsonKey(name: 'page_number') int? pageNumber,
      @JsonKey(name: 'juz_number') int? juzNumber,
      @JsonKey(name: 'is_bismillah') bool isBismillah,
      @JsonKey(name: 'words') List<WordModel> words,
      @JsonKey(name: 'sajda') bool sajda,
      @JsonKey(name: 'context_story') String? contextStory});
}

/// @nodoc
class _$AyahModelCopyWithImpl<$Res> implements $AyahModelCopyWith<$Res> {
  _$AyahModelCopyWithImpl(this._self, this._then);

  final AyahModel _self;
  final $Res Function(AyahModel) _then;

  /// Create a copy of AyahModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? ayahId = null,
    Object? surahNumber = null,
    Object? ayahNumber = null,
    Object? ayahText = null,
    Object? ayahTextSimple = freezed,
    Object? translationEn = freezed,
    Object? translationUr = freezed,
    Object? translationHi = freezed,
    Object? transliteration = freezed,
    Object? audioUrl = freezed,
    Object? audioUrlUr = freezed,
    Object? pageNumber = freezed,
    Object? juzNumber = freezed,
    Object? isBismillah = null,
    Object? words = null,
    Object? sajda = null,
    Object? contextStory = freezed,
  }) {
    return _then(_self.copyWith(
      ayahId: null == ayahId
          ? _self.ayahId
          : ayahId // ignore: cast_nullable_to_non_nullable
              as int,
      surahNumber: null == surahNumber
          ? _self.surahNumber
          : surahNumber // ignore: cast_nullable_to_non_nullable
              as int,
      ayahNumber: null == ayahNumber
          ? _self.ayahNumber
          : ayahNumber // ignore: cast_nullable_to_non_nullable
              as int,
      ayahText: null == ayahText
          ? _self.ayahText
          : ayahText // ignore: cast_nullable_to_non_nullable
              as String,
      ayahTextSimple: freezed == ayahTextSimple
          ? _self.ayahTextSimple
          : ayahTextSimple // ignore: cast_nullable_to_non_nullable
              as String?,
      translationEn: freezed == translationEn
          ? _self.translationEn
          : translationEn // ignore: cast_nullable_to_non_nullable
              as String?,
      translationUr: freezed == translationUr
          ? _self.translationUr
          : translationUr // ignore: cast_nullable_to_non_nullable
              as String?,
      translationHi: freezed == translationHi
          ? _self.translationHi
          : translationHi // ignore: cast_nullable_to_non_nullable
              as String?,
      transliteration: freezed == transliteration
          ? _self.transliteration
          : transliteration // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrl: freezed == audioUrl
          ? _self.audioUrl
          : audioUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrlUr: freezed == audioUrlUr
          ? _self.audioUrlUr
          : audioUrlUr // ignore: cast_nullable_to_non_nullable
              as String?,
      pageNumber: freezed == pageNumber
          ? _self.pageNumber
          : pageNumber // ignore: cast_nullable_to_non_nullable
              as int?,
      juzNumber: freezed == juzNumber
          ? _self.juzNumber
          : juzNumber // ignore: cast_nullable_to_non_nullable
              as int?,
      isBismillah: null == isBismillah
          ? _self.isBismillah
          : isBismillah // ignore: cast_nullable_to_non_nullable
              as bool,
      words: null == words
          ? _self.words
          : words // ignore: cast_nullable_to_non_nullable
              as List<WordModel>,
      sajda: null == sajda
          ? _self.sajda
          : sajda // ignore: cast_nullable_to_non_nullable
              as bool,
      contextStory: freezed == contextStory
          ? _self.contextStory
          : contextStory // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// Adds pattern-matching-related methods to [AyahModel].
extension AyahModelPatterns on AyahModel {
  /// A variant of `map` that fallback to returning `orElse`.
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case final Subclass value:
  ///     return ...;
  ///   case _:
  ///     return orElse();
  /// }
  /// ```

  @optionalTypeArgs
  TResult maybeMap<TResult extends Object?>(
    TResult Function(_AyahModel value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _AyahModel() when $default != null:
        return $default(_that);
      case _:
        return orElse();
    }
  }

  /// A `switch`-like method, using callbacks.
  ///
  /// Callbacks receives the raw object, upcasted.
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case final Subclass value:
  ///     return ...;
  ///   case final Subclass2 value:
  ///     return ...;
  /// }
  /// ```

  @optionalTypeArgs
  TResult map<TResult extends Object?>(
    TResult Function(_AyahModel value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _AyahModel():
        return $default(_that);
      case _:
        throw StateError('Unexpected subclass');
    }
  }

  /// A variant of `map` that fallback to returning `null`.
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case final Subclass value:
  ///     return ...;
  ///   case _:
  ///     return null;
  /// }
  /// ```

  @optionalTypeArgs
  TResult? mapOrNull<TResult extends Object?>(
    TResult? Function(_AyahModel value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _AyahModel() when $default != null:
        return $default(_that);
      case _:
        return null;
    }
  }

  /// A variant of `when` that fallback to an `orElse` callback.
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case Subclass(:final field):
  ///     return ...;
  ///   case _:
  ///     return orElse();
  /// }
  /// ```

  @optionalTypeArgs
  TResult maybeWhen<TResult extends Object?>(
    TResult Function(
            @JsonKey(name: 'ayah_id') int ayahId,
            @JsonKey(name: 'surah_number') int surahNumber,
            @JsonKey(name: 'ayah_number') int ayahNumber,
            @JsonKey(name: 'ayah_text') String ayahText,
            @JsonKey(name: 'ayah_text_simple') String? ayahTextSimple,
            @JsonKey(name: 'translation_en') String? translationEn,
            @JsonKey(name: 'translation_ur') String? translationUr,
            @JsonKey(name: 'translation_hi') String? translationHi,
            @JsonKey(name: 'transliteration') String? transliteration,
            @JsonKey(name: 'audio_url') String? audioUrl,
            @JsonKey(name: 'audio_url_ur') String? audioUrlUr,
            @JsonKey(name: 'page_number') int? pageNumber,
            @JsonKey(name: 'juz_number') int? juzNumber,
            @JsonKey(name: 'is_bismillah') bool isBismillah,
            @JsonKey(name: 'words') List<WordModel> words,
            @JsonKey(name: 'sajda') bool sajda,
            @JsonKey(name: 'context_story') String? contextStory)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _AyahModel() when $default != null:
        return $default(
            _that.ayahId,
            _that.surahNumber,
            _that.ayahNumber,
            _that.ayahText,
            _that.ayahTextSimple,
            _that.translationEn,
            _that.translationUr,
            _that.translationHi,
            _that.transliteration,
            _that.audioUrl,
            _that.audioUrlUr,
            _that.pageNumber,
            _that.juzNumber,
            _that.isBismillah,
            _that.words,
            _that.sajda,
            _that.contextStory);
      case _:
        return orElse();
    }
  }

  /// A `switch`-like method, using callbacks.
  ///
  /// As opposed to `map`, this offers destructuring.
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case Subclass(:final field):
  ///     return ...;
  ///   case Subclass2(:final field2):
  ///     return ...;
  /// }
  /// ```

  @optionalTypeArgs
  TResult when<TResult extends Object?>(
    TResult Function(
            @JsonKey(name: 'ayah_id') int ayahId,
            @JsonKey(name: 'surah_number') int surahNumber,
            @JsonKey(name: 'ayah_number') int ayahNumber,
            @JsonKey(name: 'ayah_text') String ayahText,
            @JsonKey(name: 'ayah_text_simple') String? ayahTextSimple,
            @JsonKey(name: 'translation_en') String? translationEn,
            @JsonKey(name: 'translation_ur') String? translationUr,
            @JsonKey(name: 'translation_hi') String? translationHi,
            @JsonKey(name: 'transliteration') String? transliteration,
            @JsonKey(name: 'audio_url') String? audioUrl,
            @JsonKey(name: 'audio_url_ur') String? audioUrlUr,
            @JsonKey(name: 'page_number') int? pageNumber,
            @JsonKey(name: 'juz_number') int? juzNumber,
            @JsonKey(name: 'is_bismillah') bool isBismillah,
            @JsonKey(name: 'words') List<WordModel> words,
            @JsonKey(name: 'sajda') bool sajda,
            @JsonKey(name: 'context_story') String? contextStory)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _AyahModel():
        return $default(
            _that.ayahId,
            _that.surahNumber,
            _that.ayahNumber,
            _that.ayahText,
            _that.ayahTextSimple,
            _that.translationEn,
            _that.translationUr,
            _that.translationHi,
            _that.transliteration,
            _that.audioUrl,
            _that.audioUrlUr,
            _that.pageNumber,
            _that.juzNumber,
            _that.isBismillah,
            _that.words,
            _that.sajda,
            _that.contextStory);
      case _:
        throw StateError('Unexpected subclass');
    }
  }

  /// A variant of `when` that fallback to returning `null`
  ///
  /// It is equivalent to doing:
  /// ```dart
  /// switch (sealedClass) {
  ///   case Subclass(:final field):
  ///     return ...;
  ///   case _:
  ///     return null;
  /// }
  /// ```

  @optionalTypeArgs
  TResult? whenOrNull<TResult extends Object?>(
    TResult? Function(
            @JsonKey(name: 'ayah_id') int ayahId,
            @JsonKey(name: 'surah_number') int surahNumber,
            @JsonKey(name: 'ayah_number') int ayahNumber,
            @JsonKey(name: 'ayah_text') String ayahText,
            @JsonKey(name: 'ayah_text_simple') String? ayahTextSimple,
            @JsonKey(name: 'translation_en') String? translationEn,
            @JsonKey(name: 'translation_ur') String? translationUr,
            @JsonKey(name: 'translation_hi') String? translationHi,
            @JsonKey(name: 'transliteration') String? transliteration,
            @JsonKey(name: 'audio_url') String? audioUrl,
            @JsonKey(name: 'audio_url_ur') String? audioUrlUr,
            @JsonKey(name: 'page_number') int? pageNumber,
            @JsonKey(name: 'juz_number') int? juzNumber,
            @JsonKey(name: 'is_bismillah') bool isBismillah,
            @JsonKey(name: 'words') List<WordModel> words,
            @JsonKey(name: 'sajda') bool sajda,
            @JsonKey(name: 'context_story') String? contextStory)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _AyahModel() when $default != null:
        return $default(
            _that.ayahId,
            _that.surahNumber,
            _that.ayahNumber,
            _that.ayahText,
            _that.ayahTextSimple,
            _that.translationEn,
            _that.translationUr,
            _that.translationHi,
            _that.transliteration,
            _that.audioUrl,
            _that.audioUrlUr,
            _that.pageNumber,
            _that.juzNumber,
            _that.isBismillah,
            _that.words,
            _that.sajda,
            _that.contextStory);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _AyahModel implements AyahModel {
  const _AyahModel(
      {@JsonKey(name: 'ayah_id') required this.ayahId,
      @JsonKey(name: 'surah_number') required this.surahNumber,
      @JsonKey(name: 'ayah_number') required this.ayahNumber,
      @JsonKey(name: 'ayah_text') required this.ayahText,
      @JsonKey(name: 'ayah_text_simple') this.ayahTextSimple,
      @JsonKey(name: 'translation_en') this.translationEn,
      @JsonKey(name: 'translation_ur') this.translationUr,
      @JsonKey(name: 'translation_hi') this.translationHi,
      @JsonKey(name: 'transliteration') this.transliteration,
      @JsonKey(name: 'audio_url') this.audioUrl,
      @JsonKey(name: 'audio_url_ur') this.audioUrlUr,
      @JsonKey(name: 'page_number') this.pageNumber,
      @JsonKey(name: 'juz_number') this.juzNumber,
      @JsonKey(name: 'is_bismillah') this.isBismillah = false,
      @JsonKey(name: 'words') final List<WordModel> words = const [],
      @JsonKey(name: 'sajda') this.sajda = false,
      @JsonKey(name: 'context_story') this.contextStory})
      : _words = words;
  factory _AyahModel.fromJson(Map<String, dynamic> json) =>
      _$AyahModelFromJson(json);

  @override
  @JsonKey(name: 'ayah_id')
  final int ayahId;
  @override
  @JsonKey(name: 'surah_number')
  final int surahNumber;
  @override
  @JsonKey(name: 'ayah_number')
  final int ayahNumber;
  @override
  @JsonKey(name: 'ayah_text')
  final String ayahText;
  @override
  @JsonKey(name: 'ayah_text_simple')
  final String? ayahTextSimple;
  @override
  @JsonKey(name: 'translation_en')
  final String? translationEn;
  @override
  @JsonKey(name: 'translation_ur')
  final String? translationUr;
  @override
  @JsonKey(name: 'translation_hi')
  final String? translationHi;
  @override
  @JsonKey(name: 'transliteration')
  final String? transliteration;
  @override
  @JsonKey(name: 'audio_url')
  final String? audioUrl;
  @override
  @JsonKey(name: 'audio_url_ur')
  final String? audioUrlUr;
  @override
  @JsonKey(name: 'page_number')
  final int? pageNumber;
  @override
  @JsonKey(name: 'juz_number')
  final int? juzNumber;
  @override
  @JsonKey(name: 'is_bismillah')
  final bool isBismillah;
  final List<WordModel> _words;
  @override
  @JsonKey(name: 'words')
  List<WordModel> get words {
    if (_words is EqualUnmodifiableListView) return _words;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_words);
  }

  @override
  @JsonKey(name: 'sajda')
  final bool sajda;
  @override
  @JsonKey(name: 'context_story')
  final String? contextStory;

  /// Create a copy of AyahModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$AyahModelCopyWith<_AyahModel> get copyWith =>
      __$AyahModelCopyWithImpl<_AyahModel>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$AyahModelToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _AyahModel &&
            (identical(other.ayahId, ayahId) || other.ayahId == ayahId) &&
            (identical(other.surahNumber, surahNumber) ||
                other.surahNumber == surahNumber) &&
            (identical(other.ayahNumber, ayahNumber) ||
                other.ayahNumber == ayahNumber) &&
            (identical(other.ayahText, ayahText) ||
                other.ayahText == ayahText) &&
            (identical(other.ayahTextSimple, ayahTextSimple) ||
                other.ayahTextSimple == ayahTextSimple) &&
            (identical(other.translationEn, translationEn) ||
                other.translationEn == translationEn) &&
            (identical(other.translationUr, translationUr) ||
                other.translationUr == translationUr) &&
            (identical(other.translationHi, translationHi) ||
                other.translationHi == translationHi) &&
            (identical(other.transliteration, transliteration) ||
                other.transliteration == transliteration) &&
            (identical(other.audioUrl, audioUrl) ||
                other.audioUrl == audioUrl) &&
            (identical(other.audioUrlUr, audioUrlUr) ||
                other.audioUrlUr == audioUrlUr) &&
            (identical(other.pageNumber, pageNumber) ||
                other.pageNumber == pageNumber) &&
            (identical(other.juzNumber, juzNumber) ||
                other.juzNumber == juzNumber) &&
            (identical(other.isBismillah, isBismillah) ||
                other.isBismillah == isBismillah) &&
            const DeepCollectionEquality().equals(other._words, _words) &&
            (identical(other.sajda, sajda) || other.sajda == sajda) &&
            (identical(other.contextStory, contextStory) ||
                other.contextStory == contextStory));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      ayahId,
      surahNumber,
      ayahNumber,
      ayahText,
      ayahTextSimple,
      translationEn,
      translationUr,
      translationHi,
      transliteration,
      audioUrl,
      audioUrlUr,
      pageNumber,
      juzNumber,
      isBismillah,
      const DeepCollectionEquality().hash(_words),
      sajda,
      contextStory);

  @override
  String toString() {
    return 'AyahModel(ayahId: $ayahId, surahNumber: $surahNumber, ayahNumber: $ayahNumber, ayahText: $ayahText, ayahTextSimple: $ayahTextSimple, translationEn: $translationEn, translationUr: $translationUr, translationHi: $translationHi, transliteration: $transliteration, audioUrl: $audioUrl, audioUrlUr: $audioUrlUr, pageNumber: $pageNumber, juzNumber: $juzNumber, isBismillah: $isBismillah, words: $words, sajda: $sajda, contextStory: $contextStory)';
  }
}

/// @nodoc
abstract mixin class _$AyahModelCopyWith<$Res>
    implements $AyahModelCopyWith<$Res> {
  factory _$AyahModelCopyWith(
          _AyahModel value, $Res Function(_AyahModel) _then) =
      __$AyahModelCopyWithImpl;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'ayah_id') int ayahId,
      @JsonKey(name: 'surah_number') int surahNumber,
      @JsonKey(name: 'ayah_number') int ayahNumber,
      @JsonKey(name: 'ayah_text') String ayahText,
      @JsonKey(name: 'ayah_text_simple') String? ayahTextSimple,
      @JsonKey(name: 'translation_en') String? translationEn,
      @JsonKey(name: 'translation_ur') String? translationUr,
      @JsonKey(name: 'translation_hi') String? translationHi,
      @JsonKey(name: 'transliteration') String? transliteration,
      @JsonKey(name: 'audio_url') String? audioUrl,
      @JsonKey(name: 'audio_url_ur') String? audioUrlUr,
      @JsonKey(name: 'page_number') int? pageNumber,
      @JsonKey(name: 'juz_number') int? juzNumber,
      @JsonKey(name: 'is_bismillah') bool isBismillah,
      @JsonKey(name: 'words') List<WordModel> words,
      @JsonKey(name: 'sajda') bool sajda,
      @JsonKey(name: 'context_story') String? contextStory});
}

/// @nodoc
class __$AyahModelCopyWithImpl<$Res> implements _$AyahModelCopyWith<$Res> {
  __$AyahModelCopyWithImpl(this._self, this._then);

  final _AyahModel _self;
  final $Res Function(_AyahModel) _then;

  /// Create a copy of AyahModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? ayahId = null,
    Object? surahNumber = null,
    Object? ayahNumber = null,
    Object? ayahText = null,
    Object? ayahTextSimple = freezed,
    Object? translationEn = freezed,
    Object? translationUr = freezed,
    Object? translationHi = freezed,
    Object? transliteration = freezed,
    Object? audioUrl = freezed,
    Object? audioUrlUr = freezed,
    Object? pageNumber = freezed,
    Object? juzNumber = freezed,
    Object? isBismillah = null,
    Object? words = null,
    Object? sajda = null,
    Object? contextStory = freezed,
  }) {
    return _then(_AyahModel(
      ayahId: null == ayahId
          ? _self.ayahId
          : ayahId // ignore: cast_nullable_to_non_nullable
              as int,
      surahNumber: null == surahNumber
          ? _self.surahNumber
          : surahNumber // ignore: cast_nullable_to_non_nullable
              as int,
      ayahNumber: null == ayahNumber
          ? _self.ayahNumber
          : ayahNumber // ignore: cast_nullable_to_non_nullable
              as int,
      ayahText: null == ayahText
          ? _self.ayahText
          : ayahText // ignore: cast_nullable_to_non_nullable
              as String,
      ayahTextSimple: freezed == ayahTextSimple
          ? _self.ayahTextSimple
          : ayahTextSimple // ignore: cast_nullable_to_non_nullable
              as String?,
      translationEn: freezed == translationEn
          ? _self.translationEn
          : translationEn // ignore: cast_nullable_to_non_nullable
              as String?,
      translationUr: freezed == translationUr
          ? _self.translationUr
          : translationUr // ignore: cast_nullable_to_non_nullable
              as String?,
      translationHi: freezed == translationHi
          ? _self.translationHi
          : translationHi // ignore: cast_nullable_to_non_nullable
              as String?,
      transliteration: freezed == transliteration
          ? _self.transliteration
          : transliteration // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrl: freezed == audioUrl
          ? _self.audioUrl
          : audioUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrlUr: freezed == audioUrlUr
          ? _self.audioUrlUr
          : audioUrlUr // ignore: cast_nullable_to_non_nullable
              as String?,
      pageNumber: freezed == pageNumber
          ? _self.pageNumber
          : pageNumber // ignore: cast_nullable_to_non_nullable
              as int?,
      juzNumber: freezed == juzNumber
          ? _self.juzNumber
          : juzNumber // ignore: cast_nullable_to_non_nullable
              as int?,
      isBismillah: null == isBismillah
          ? _self.isBismillah
          : isBismillah // ignore: cast_nullable_to_non_nullable
              as bool,
      words: null == words
          ? _self._words
          : words // ignore: cast_nullable_to_non_nullable
              as List<WordModel>,
      sajda: null == sajda
          ? _self.sajda
          : sajda // ignore: cast_nullable_to_non_nullable
              as bool,
      contextStory: freezed == contextStory
          ? _self.contextStory
          : contextStory // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

// dart format on
