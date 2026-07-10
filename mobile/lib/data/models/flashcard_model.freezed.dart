// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'flashcard_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$FlashcardModel {
  @JsonKey(name: 'card_id')
  int get cardId;
  @JsonKey(name: 'user_id')
  String? get userId;
  @JsonKey(name: 'word_id')
  int get wordId;
  @JsonKey(name: 'surah_number')
  int get surahNumber;
  @JsonKey(name: 'ayah_number')
  int get ayahNumber;
  @JsonKey(name: 'word_text')
  String get wordText;
  @JsonKey(name: 'transliteration')
  String? get transliteration;
  @JsonKey(name: 'meaning_en')
  String? get meaningEn;
  @JsonKey(name: 'meaning_ur')
  String? get meaningUr;
  @JsonKey(name: 'meaning_hi')
  String? get meaningHi;
  @JsonKey(name: 'root_arabic')
  String? get rootArabic;
  @JsonKey(name: 'pos_group')
  String? get posGroup;
  @JsonKey(name: 'audio_url')
  String? get audioUrl;
  @JsonKey(name: 'ayah_text')
  String? get ayahText;
  @JsonKey(name: 'ayah_translation')
  String? get ayahTranslation; // SM-2 fields
  @JsonKey(name: 'sm2_ease')
  double get ease;
  @JsonKey(name: 'sm2_interval')
  int get interval;
  @JsonKey(name: 'sm2_repetitions')
  int get repetitions;
  @JsonKey(name: 'next_review')
  DateTime get nextReview;
  @JsonKey(name: 'last_reviewed')
  DateTime? get lastReviewed;
  @JsonKey(name: 'is_due')
  bool get isDue;
  @JsonKey(name: 'created_at')
  DateTime get createdAt;

  /// Create a copy of FlashcardModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $FlashcardModelCopyWith<FlashcardModel> get copyWith =>
      _$FlashcardModelCopyWithImpl<FlashcardModel>(
          this as FlashcardModel, _$identity);

  /// Serializes this FlashcardModel to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is FlashcardModel &&
            (identical(other.cardId, cardId) || other.cardId == cardId) &&
            (identical(other.userId, userId) || other.userId == userId) &&
            (identical(other.wordId, wordId) || other.wordId == wordId) &&
            (identical(other.surahNumber, surahNumber) ||
                other.surahNumber == surahNumber) &&
            (identical(other.ayahNumber, ayahNumber) ||
                other.ayahNumber == ayahNumber) &&
            (identical(other.wordText, wordText) ||
                other.wordText == wordText) &&
            (identical(other.transliteration, transliteration) ||
                other.transliteration == transliteration) &&
            (identical(other.meaningEn, meaningEn) ||
                other.meaningEn == meaningEn) &&
            (identical(other.meaningUr, meaningUr) ||
                other.meaningUr == meaningUr) &&
            (identical(other.meaningHi, meaningHi) ||
                other.meaningHi == meaningHi) &&
            (identical(other.rootArabic, rootArabic) ||
                other.rootArabic == rootArabic) &&
            (identical(other.posGroup, posGroup) ||
                other.posGroup == posGroup) &&
            (identical(other.audioUrl, audioUrl) ||
                other.audioUrl == audioUrl) &&
            (identical(other.ayahText, ayahText) ||
                other.ayahText == ayahText) &&
            (identical(other.ayahTranslation, ayahTranslation) ||
                other.ayahTranslation == ayahTranslation) &&
            (identical(other.ease, ease) || other.ease == ease) &&
            (identical(other.interval, interval) ||
                other.interval == interval) &&
            (identical(other.repetitions, repetitions) ||
                other.repetitions == repetitions) &&
            (identical(other.nextReview, nextReview) ||
                other.nextReview == nextReview) &&
            (identical(other.lastReviewed, lastReviewed) ||
                other.lastReviewed == lastReviewed) &&
            (identical(other.isDue, isDue) || other.isDue == isDue) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hashAll([
        runtimeType,
        cardId,
        userId,
        wordId,
        surahNumber,
        ayahNumber,
        wordText,
        transliteration,
        meaningEn,
        meaningUr,
        meaningHi,
        rootArabic,
        posGroup,
        audioUrl,
        ayahText,
        ayahTranslation,
        ease,
        interval,
        repetitions,
        nextReview,
        lastReviewed,
        isDue,
        createdAt
      ]);

  @override
  String toString() {
    return 'FlashcardModel(cardId: $cardId, userId: $userId, wordId: $wordId, surahNumber: $surahNumber, ayahNumber: $ayahNumber, wordText: $wordText, transliteration: $transliteration, meaningEn: $meaningEn, meaningUr: $meaningUr, meaningHi: $meaningHi, rootArabic: $rootArabic, posGroup: $posGroup, audioUrl: $audioUrl, ayahText: $ayahText, ayahTranslation: $ayahTranslation, ease: $ease, interval: $interval, repetitions: $repetitions, nextReview: $nextReview, lastReviewed: $lastReviewed, isDue: $isDue, createdAt: $createdAt)';
  }
}

/// @nodoc
abstract mixin class $FlashcardModelCopyWith<$Res> {
  factory $FlashcardModelCopyWith(
          FlashcardModel value, $Res Function(FlashcardModel) _then) =
      _$FlashcardModelCopyWithImpl;
  @useResult
  $Res call(
      {@JsonKey(name: 'card_id') int cardId,
      @JsonKey(name: 'user_id') String? userId,
      @JsonKey(name: 'word_id') int wordId,
      @JsonKey(name: 'surah_number') int surahNumber,
      @JsonKey(name: 'ayah_number') int ayahNumber,
      @JsonKey(name: 'word_text') String wordText,
      @JsonKey(name: 'transliteration') String? transliteration,
      @JsonKey(name: 'meaning_en') String? meaningEn,
      @JsonKey(name: 'meaning_ur') String? meaningUr,
      @JsonKey(name: 'meaning_hi') String? meaningHi,
      @JsonKey(name: 'root_arabic') String? rootArabic,
      @JsonKey(name: 'pos_group') String? posGroup,
      @JsonKey(name: 'audio_url') String? audioUrl,
      @JsonKey(name: 'ayah_text') String? ayahText,
      @JsonKey(name: 'ayah_translation') String? ayahTranslation,
      @JsonKey(name: 'sm2_ease') double ease,
      @JsonKey(name: 'sm2_interval') int interval,
      @JsonKey(name: 'sm2_repetitions') int repetitions,
      @JsonKey(name: 'next_review') DateTime nextReview,
      @JsonKey(name: 'last_reviewed') DateTime? lastReviewed,
      @JsonKey(name: 'is_due') bool isDue,
      @JsonKey(name: 'created_at') DateTime createdAt});
}

/// @nodoc
class _$FlashcardModelCopyWithImpl<$Res>
    implements $FlashcardModelCopyWith<$Res> {
  _$FlashcardModelCopyWithImpl(this._self, this._then);

  final FlashcardModel _self;
  final $Res Function(FlashcardModel) _then;

  /// Create a copy of FlashcardModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? cardId = null,
    Object? userId = freezed,
    Object? wordId = null,
    Object? surahNumber = null,
    Object? ayahNumber = null,
    Object? wordText = null,
    Object? transliteration = freezed,
    Object? meaningEn = freezed,
    Object? meaningUr = freezed,
    Object? meaningHi = freezed,
    Object? rootArabic = freezed,
    Object? posGroup = freezed,
    Object? audioUrl = freezed,
    Object? ayahText = freezed,
    Object? ayahTranslation = freezed,
    Object? ease = null,
    Object? interval = null,
    Object? repetitions = null,
    Object? nextReview = null,
    Object? lastReviewed = freezed,
    Object? isDue = null,
    Object? createdAt = null,
  }) {
    return _then(_self.copyWith(
      cardId: null == cardId
          ? _self.cardId
          : cardId // ignore: cast_nullable_to_non_nullable
              as int,
      userId: freezed == userId
          ? _self.userId
          : userId // ignore: cast_nullable_to_non_nullable
              as String?,
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
      wordText: null == wordText
          ? _self.wordText
          : wordText // ignore: cast_nullable_to_non_nullable
              as String,
      transliteration: freezed == transliteration
          ? _self.transliteration
          : transliteration // ignore: cast_nullable_to_non_nullable
              as String?,
      meaningEn: freezed == meaningEn
          ? _self.meaningEn
          : meaningEn // ignore: cast_nullable_to_non_nullable
              as String?,
      meaningUr: freezed == meaningUr
          ? _self.meaningUr
          : meaningUr // ignore: cast_nullable_to_non_nullable
              as String?,
      meaningHi: freezed == meaningHi
          ? _self.meaningHi
          : meaningHi // ignore: cast_nullable_to_non_nullable
              as String?,
      rootArabic: freezed == rootArabic
          ? _self.rootArabic
          : rootArabic // ignore: cast_nullable_to_non_nullable
              as String?,
      posGroup: freezed == posGroup
          ? _self.posGroup
          : posGroup // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrl: freezed == audioUrl
          ? _self.audioUrl
          : audioUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      ayahText: freezed == ayahText
          ? _self.ayahText
          : ayahText // ignore: cast_nullable_to_non_nullable
              as String?,
      ayahTranslation: freezed == ayahTranslation
          ? _self.ayahTranslation
          : ayahTranslation // ignore: cast_nullable_to_non_nullable
              as String?,
      ease: null == ease
          ? _self.ease
          : ease // ignore: cast_nullable_to_non_nullable
              as double,
      interval: null == interval
          ? _self.interval
          : interval // ignore: cast_nullable_to_non_nullable
              as int,
      repetitions: null == repetitions
          ? _self.repetitions
          : repetitions // ignore: cast_nullable_to_non_nullable
              as int,
      nextReview: null == nextReview
          ? _self.nextReview
          : nextReview // ignore: cast_nullable_to_non_nullable
              as DateTime,
      lastReviewed: freezed == lastReviewed
          ? _self.lastReviewed
          : lastReviewed // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      isDue: null == isDue
          ? _self.isDue
          : isDue // ignore: cast_nullable_to_non_nullable
              as bool,
      createdAt: null == createdAt
          ? _self.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// Adds pattern-matching-related methods to [FlashcardModel].
extension FlashcardModelPatterns on FlashcardModel {
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
    TResult Function(_FlashcardModel value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _FlashcardModel() when $default != null:
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
    TResult Function(_FlashcardModel value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _FlashcardModel():
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
    TResult? Function(_FlashcardModel value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _FlashcardModel() when $default != null:
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
            @JsonKey(name: 'card_id') int cardId,
            @JsonKey(name: 'user_id') String? userId,
            @JsonKey(name: 'word_id') int wordId,
            @JsonKey(name: 'surah_number') int surahNumber,
            @JsonKey(name: 'ayah_number') int ayahNumber,
            @JsonKey(name: 'word_text') String wordText,
            @JsonKey(name: 'transliteration') String? transliteration,
            @JsonKey(name: 'meaning_en') String? meaningEn,
            @JsonKey(name: 'meaning_ur') String? meaningUr,
            @JsonKey(name: 'meaning_hi') String? meaningHi,
            @JsonKey(name: 'root_arabic') String? rootArabic,
            @JsonKey(name: 'pos_group') String? posGroup,
            @JsonKey(name: 'audio_url') String? audioUrl,
            @JsonKey(name: 'ayah_text') String? ayahText,
            @JsonKey(name: 'ayah_translation') String? ayahTranslation,
            @JsonKey(name: 'sm2_ease') double ease,
            @JsonKey(name: 'sm2_interval') int interval,
            @JsonKey(name: 'sm2_repetitions') int repetitions,
            @JsonKey(name: 'next_review') DateTime nextReview,
            @JsonKey(name: 'last_reviewed') DateTime? lastReviewed,
            @JsonKey(name: 'is_due') bool isDue,
            @JsonKey(name: 'created_at') DateTime createdAt)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _FlashcardModel() when $default != null:
        return $default(
            _that.cardId,
            _that.userId,
            _that.wordId,
            _that.surahNumber,
            _that.ayahNumber,
            _that.wordText,
            _that.transliteration,
            _that.meaningEn,
            _that.meaningUr,
            _that.meaningHi,
            _that.rootArabic,
            _that.posGroup,
            _that.audioUrl,
            _that.ayahText,
            _that.ayahTranslation,
            _that.ease,
            _that.interval,
            _that.repetitions,
            _that.nextReview,
            _that.lastReviewed,
            _that.isDue,
            _that.createdAt);
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
            @JsonKey(name: 'card_id') int cardId,
            @JsonKey(name: 'user_id') String? userId,
            @JsonKey(name: 'word_id') int wordId,
            @JsonKey(name: 'surah_number') int surahNumber,
            @JsonKey(name: 'ayah_number') int ayahNumber,
            @JsonKey(name: 'word_text') String wordText,
            @JsonKey(name: 'transliteration') String? transliteration,
            @JsonKey(name: 'meaning_en') String? meaningEn,
            @JsonKey(name: 'meaning_ur') String? meaningUr,
            @JsonKey(name: 'meaning_hi') String? meaningHi,
            @JsonKey(name: 'root_arabic') String? rootArabic,
            @JsonKey(name: 'pos_group') String? posGroup,
            @JsonKey(name: 'audio_url') String? audioUrl,
            @JsonKey(name: 'ayah_text') String? ayahText,
            @JsonKey(name: 'ayah_translation') String? ayahTranslation,
            @JsonKey(name: 'sm2_ease') double ease,
            @JsonKey(name: 'sm2_interval') int interval,
            @JsonKey(name: 'sm2_repetitions') int repetitions,
            @JsonKey(name: 'next_review') DateTime nextReview,
            @JsonKey(name: 'last_reviewed') DateTime? lastReviewed,
            @JsonKey(name: 'is_due') bool isDue,
            @JsonKey(name: 'created_at') DateTime createdAt)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _FlashcardModel():
        return $default(
            _that.cardId,
            _that.userId,
            _that.wordId,
            _that.surahNumber,
            _that.ayahNumber,
            _that.wordText,
            _that.transliteration,
            _that.meaningEn,
            _that.meaningUr,
            _that.meaningHi,
            _that.rootArabic,
            _that.posGroup,
            _that.audioUrl,
            _that.ayahText,
            _that.ayahTranslation,
            _that.ease,
            _that.interval,
            _that.repetitions,
            _that.nextReview,
            _that.lastReviewed,
            _that.isDue,
            _that.createdAt);
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
            @JsonKey(name: 'card_id') int cardId,
            @JsonKey(name: 'user_id') String? userId,
            @JsonKey(name: 'word_id') int wordId,
            @JsonKey(name: 'surah_number') int surahNumber,
            @JsonKey(name: 'ayah_number') int ayahNumber,
            @JsonKey(name: 'word_text') String wordText,
            @JsonKey(name: 'transliteration') String? transliteration,
            @JsonKey(name: 'meaning_en') String? meaningEn,
            @JsonKey(name: 'meaning_ur') String? meaningUr,
            @JsonKey(name: 'meaning_hi') String? meaningHi,
            @JsonKey(name: 'root_arabic') String? rootArabic,
            @JsonKey(name: 'pos_group') String? posGroup,
            @JsonKey(name: 'audio_url') String? audioUrl,
            @JsonKey(name: 'ayah_text') String? ayahText,
            @JsonKey(name: 'ayah_translation') String? ayahTranslation,
            @JsonKey(name: 'sm2_ease') double ease,
            @JsonKey(name: 'sm2_interval') int interval,
            @JsonKey(name: 'sm2_repetitions') int repetitions,
            @JsonKey(name: 'next_review') DateTime nextReview,
            @JsonKey(name: 'last_reviewed') DateTime? lastReviewed,
            @JsonKey(name: 'is_due') bool isDue,
            @JsonKey(name: 'created_at') DateTime createdAt)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _FlashcardModel() when $default != null:
        return $default(
            _that.cardId,
            _that.userId,
            _that.wordId,
            _that.surahNumber,
            _that.ayahNumber,
            _that.wordText,
            _that.transliteration,
            _that.meaningEn,
            _that.meaningUr,
            _that.meaningHi,
            _that.rootArabic,
            _that.posGroup,
            _that.audioUrl,
            _that.ayahText,
            _that.ayahTranslation,
            _that.ease,
            _that.interval,
            _that.repetitions,
            _that.nextReview,
            _that.lastReviewed,
            _that.isDue,
            _that.createdAt);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _FlashcardModel implements FlashcardModel {
  const _FlashcardModel(
      {@JsonKey(name: 'card_id') required this.cardId,
      @JsonKey(name: 'user_id') this.userId,
      @JsonKey(name: 'word_id') required this.wordId,
      @JsonKey(name: 'surah_number') required this.surahNumber,
      @JsonKey(name: 'ayah_number') required this.ayahNumber,
      @JsonKey(name: 'word_text') required this.wordText,
      @JsonKey(name: 'transliteration') this.transliteration,
      @JsonKey(name: 'meaning_en') this.meaningEn,
      @JsonKey(name: 'meaning_ur') this.meaningUr,
      @JsonKey(name: 'meaning_hi') this.meaningHi,
      @JsonKey(name: 'root_arabic') this.rootArabic,
      @JsonKey(name: 'pos_group') this.posGroup,
      @JsonKey(name: 'audio_url') this.audioUrl,
      @JsonKey(name: 'ayah_text') this.ayahText,
      @JsonKey(name: 'ayah_translation') this.ayahTranslation,
      @JsonKey(name: 'sm2_ease') this.ease = 2.5,
      @JsonKey(name: 'sm2_interval') this.interval = 0,
      @JsonKey(name: 'sm2_repetitions') this.repetitions = 0,
      @JsonKey(name: 'next_review') required this.nextReview,
      @JsonKey(name: 'last_reviewed') this.lastReviewed,
      @JsonKey(name: 'is_due') this.isDue = false,
      @JsonKey(name: 'created_at') required this.createdAt});
  factory _FlashcardModel.fromJson(Map<String, dynamic> json) =>
      _$FlashcardModelFromJson(json);

  @override
  @JsonKey(name: 'card_id')
  final int cardId;
  @override
  @JsonKey(name: 'user_id')
  final String? userId;
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
  @JsonKey(name: 'word_text')
  final String wordText;
  @override
  @JsonKey(name: 'transliteration')
  final String? transliteration;
  @override
  @JsonKey(name: 'meaning_en')
  final String? meaningEn;
  @override
  @JsonKey(name: 'meaning_ur')
  final String? meaningUr;
  @override
  @JsonKey(name: 'meaning_hi')
  final String? meaningHi;
  @override
  @JsonKey(name: 'root_arabic')
  final String? rootArabic;
  @override
  @JsonKey(name: 'pos_group')
  final String? posGroup;
  @override
  @JsonKey(name: 'audio_url')
  final String? audioUrl;
  @override
  @JsonKey(name: 'ayah_text')
  final String? ayahText;
  @override
  @JsonKey(name: 'ayah_translation')
  final String? ayahTranslation;
// SM-2 fields
  @override
  @JsonKey(name: 'sm2_ease')
  final double ease;
  @override
  @JsonKey(name: 'sm2_interval')
  final int interval;
  @override
  @JsonKey(name: 'sm2_repetitions')
  final int repetitions;
  @override
  @JsonKey(name: 'next_review')
  final DateTime nextReview;
  @override
  @JsonKey(name: 'last_reviewed')
  final DateTime? lastReviewed;
  @override
  @JsonKey(name: 'is_due')
  final bool isDue;
  @override
  @JsonKey(name: 'created_at')
  final DateTime createdAt;

  /// Create a copy of FlashcardModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$FlashcardModelCopyWith<_FlashcardModel> get copyWith =>
      __$FlashcardModelCopyWithImpl<_FlashcardModel>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$FlashcardModelToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _FlashcardModel &&
            (identical(other.cardId, cardId) || other.cardId == cardId) &&
            (identical(other.userId, userId) || other.userId == userId) &&
            (identical(other.wordId, wordId) || other.wordId == wordId) &&
            (identical(other.surahNumber, surahNumber) ||
                other.surahNumber == surahNumber) &&
            (identical(other.ayahNumber, ayahNumber) ||
                other.ayahNumber == ayahNumber) &&
            (identical(other.wordText, wordText) ||
                other.wordText == wordText) &&
            (identical(other.transliteration, transliteration) ||
                other.transliteration == transliteration) &&
            (identical(other.meaningEn, meaningEn) ||
                other.meaningEn == meaningEn) &&
            (identical(other.meaningUr, meaningUr) ||
                other.meaningUr == meaningUr) &&
            (identical(other.meaningHi, meaningHi) ||
                other.meaningHi == meaningHi) &&
            (identical(other.rootArabic, rootArabic) ||
                other.rootArabic == rootArabic) &&
            (identical(other.posGroup, posGroup) ||
                other.posGroup == posGroup) &&
            (identical(other.audioUrl, audioUrl) ||
                other.audioUrl == audioUrl) &&
            (identical(other.ayahText, ayahText) ||
                other.ayahText == ayahText) &&
            (identical(other.ayahTranslation, ayahTranslation) ||
                other.ayahTranslation == ayahTranslation) &&
            (identical(other.ease, ease) || other.ease == ease) &&
            (identical(other.interval, interval) ||
                other.interval == interval) &&
            (identical(other.repetitions, repetitions) ||
                other.repetitions == repetitions) &&
            (identical(other.nextReview, nextReview) ||
                other.nextReview == nextReview) &&
            (identical(other.lastReviewed, lastReviewed) ||
                other.lastReviewed == lastReviewed) &&
            (identical(other.isDue, isDue) || other.isDue == isDue) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hashAll([
        runtimeType,
        cardId,
        userId,
        wordId,
        surahNumber,
        ayahNumber,
        wordText,
        transliteration,
        meaningEn,
        meaningUr,
        meaningHi,
        rootArabic,
        posGroup,
        audioUrl,
        ayahText,
        ayahTranslation,
        ease,
        interval,
        repetitions,
        nextReview,
        lastReviewed,
        isDue,
        createdAt
      ]);

  @override
  String toString() {
    return 'FlashcardModel(cardId: $cardId, userId: $userId, wordId: $wordId, surahNumber: $surahNumber, ayahNumber: $ayahNumber, wordText: $wordText, transliteration: $transliteration, meaningEn: $meaningEn, meaningUr: $meaningUr, meaningHi: $meaningHi, rootArabic: $rootArabic, posGroup: $posGroup, audioUrl: $audioUrl, ayahText: $ayahText, ayahTranslation: $ayahTranslation, ease: $ease, interval: $interval, repetitions: $repetitions, nextReview: $nextReview, lastReviewed: $lastReviewed, isDue: $isDue, createdAt: $createdAt)';
  }
}

/// @nodoc
abstract mixin class _$FlashcardModelCopyWith<$Res>
    implements $FlashcardModelCopyWith<$Res> {
  factory _$FlashcardModelCopyWith(
          _FlashcardModel value, $Res Function(_FlashcardModel) _then) =
      __$FlashcardModelCopyWithImpl;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'card_id') int cardId,
      @JsonKey(name: 'user_id') String? userId,
      @JsonKey(name: 'word_id') int wordId,
      @JsonKey(name: 'surah_number') int surahNumber,
      @JsonKey(name: 'ayah_number') int ayahNumber,
      @JsonKey(name: 'word_text') String wordText,
      @JsonKey(name: 'transliteration') String? transliteration,
      @JsonKey(name: 'meaning_en') String? meaningEn,
      @JsonKey(name: 'meaning_ur') String? meaningUr,
      @JsonKey(name: 'meaning_hi') String? meaningHi,
      @JsonKey(name: 'root_arabic') String? rootArabic,
      @JsonKey(name: 'pos_group') String? posGroup,
      @JsonKey(name: 'audio_url') String? audioUrl,
      @JsonKey(name: 'ayah_text') String? ayahText,
      @JsonKey(name: 'ayah_translation') String? ayahTranslation,
      @JsonKey(name: 'sm2_ease') double ease,
      @JsonKey(name: 'sm2_interval') int interval,
      @JsonKey(name: 'sm2_repetitions') int repetitions,
      @JsonKey(name: 'next_review') DateTime nextReview,
      @JsonKey(name: 'last_reviewed') DateTime? lastReviewed,
      @JsonKey(name: 'is_due') bool isDue,
      @JsonKey(name: 'created_at') DateTime createdAt});
}

/// @nodoc
class __$FlashcardModelCopyWithImpl<$Res>
    implements _$FlashcardModelCopyWith<$Res> {
  __$FlashcardModelCopyWithImpl(this._self, this._then);

  final _FlashcardModel _self;
  final $Res Function(_FlashcardModel) _then;

  /// Create a copy of FlashcardModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? cardId = null,
    Object? userId = freezed,
    Object? wordId = null,
    Object? surahNumber = null,
    Object? ayahNumber = null,
    Object? wordText = null,
    Object? transliteration = freezed,
    Object? meaningEn = freezed,
    Object? meaningUr = freezed,
    Object? meaningHi = freezed,
    Object? rootArabic = freezed,
    Object? posGroup = freezed,
    Object? audioUrl = freezed,
    Object? ayahText = freezed,
    Object? ayahTranslation = freezed,
    Object? ease = null,
    Object? interval = null,
    Object? repetitions = null,
    Object? nextReview = null,
    Object? lastReviewed = freezed,
    Object? isDue = null,
    Object? createdAt = null,
  }) {
    return _then(_FlashcardModel(
      cardId: null == cardId
          ? _self.cardId
          : cardId // ignore: cast_nullable_to_non_nullable
              as int,
      userId: freezed == userId
          ? _self.userId
          : userId // ignore: cast_nullable_to_non_nullable
              as String?,
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
      wordText: null == wordText
          ? _self.wordText
          : wordText // ignore: cast_nullable_to_non_nullable
              as String,
      transliteration: freezed == transliteration
          ? _self.transliteration
          : transliteration // ignore: cast_nullable_to_non_nullable
              as String?,
      meaningEn: freezed == meaningEn
          ? _self.meaningEn
          : meaningEn // ignore: cast_nullable_to_non_nullable
              as String?,
      meaningUr: freezed == meaningUr
          ? _self.meaningUr
          : meaningUr // ignore: cast_nullable_to_non_nullable
              as String?,
      meaningHi: freezed == meaningHi
          ? _self.meaningHi
          : meaningHi // ignore: cast_nullable_to_non_nullable
              as String?,
      rootArabic: freezed == rootArabic
          ? _self.rootArabic
          : rootArabic // ignore: cast_nullable_to_non_nullable
              as String?,
      posGroup: freezed == posGroup
          ? _self.posGroup
          : posGroup // ignore: cast_nullable_to_non_nullable
              as String?,
      audioUrl: freezed == audioUrl
          ? _self.audioUrl
          : audioUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      ayahText: freezed == ayahText
          ? _self.ayahText
          : ayahText // ignore: cast_nullable_to_non_nullable
              as String?,
      ayahTranslation: freezed == ayahTranslation
          ? _self.ayahTranslation
          : ayahTranslation // ignore: cast_nullable_to_non_nullable
              as String?,
      ease: null == ease
          ? _self.ease
          : ease // ignore: cast_nullable_to_non_nullable
              as double,
      interval: null == interval
          ? _self.interval
          : interval // ignore: cast_nullable_to_non_nullable
              as int,
      repetitions: null == repetitions
          ? _self.repetitions
          : repetitions // ignore: cast_nullable_to_non_nullable
              as int,
      nextReview: null == nextReview
          ? _self.nextReview
          : nextReview // ignore: cast_nullable_to_non_nullable
              as DateTime,
      lastReviewed: freezed == lastReviewed
          ? _self.lastReviewed
          : lastReviewed // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      isDue: null == isDue
          ? _self.isDue
          : isDue // ignore: cast_nullable_to_non_nullable
              as bool,
      createdAt: null == createdAt
          ? _self.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// @nodoc
mixin _$FlashcardSessionResult {
  @JsonKey(name: 'cards_reviewed')
  int get cardsReviewed;
  @JsonKey(name: 'cards_again')
  int get cardsAgain;
  @JsonKey(name: 'cards_hard')
  int get cardsHard;
  @JsonKey(name: 'cards_easy')
  int get cardsEasy;
  @JsonKey(name: 'next_due_date')
  DateTime? get nextDueDate;
  @JsonKey(name: 'xp_earned')
  int get xpEarned;

  /// Create a copy of FlashcardSessionResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $FlashcardSessionResultCopyWith<FlashcardSessionResult> get copyWith =>
      _$FlashcardSessionResultCopyWithImpl<FlashcardSessionResult>(
          this as FlashcardSessionResult, _$identity);

  /// Serializes this FlashcardSessionResult to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is FlashcardSessionResult &&
            (identical(other.cardsReviewed, cardsReviewed) ||
                other.cardsReviewed == cardsReviewed) &&
            (identical(other.cardsAgain, cardsAgain) ||
                other.cardsAgain == cardsAgain) &&
            (identical(other.cardsHard, cardsHard) ||
                other.cardsHard == cardsHard) &&
            (identical(other.cardsEasy, cardsEasy) ||
                other.cardsEasy == cardsEasy) &&
            (identical(other.nextDueDate, nextDueDate) ||
                other.nextDueDate == nextDueDate) &&
            (identical(other.xpEarned, xpEarned) ||
                other.xpEarned == xpEarned));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, cardsReviewed, cardsAgain,
      cardsHard, cardsEasy, nextDueDate, xpEarned);

  @override
  String toString() {
    return 'FlashcardSessionResult(cardsReviewed: $cardsReviewed, cardsAgain: $cardsAgain, cardsHard: $cardsHard, cardsEasy: $cardsEasy, nextDueDate: $nextDueDate, xpEarned: $xpEarned)';
  }
}

/// @nodoc
abstract mixin class $FlashcardSessionResultCopyWith<$Res> {
  factory $FlashcardSessionResultCopyWith(FlashcardSessionResult value,
          $Res Function(FlashcardSessionResult) _then) =
      _$FlashcardSessionResultCopyWithImpl;
  @useResult
  $Res call(
      {@JsonKey(name: 'cards_reviewed') int cardsReviewed,
      @JsonKey(name: 'cards_again') int cardsAgain,
      @JsonKey(name: 'cards_hard') int cardsHard,
      @JsonKey(name: 'cards_easy') int cardsEasy,
      @JsonKey(name: 'next_due_date') DateTime? nextDueDate,
      @JsonKey(name: 'xp_earned') int xpEarned});
}

/// @nodoc
class _$FlashcardSessionResultCopyWithImpl<$Res>
    implements $FlashcardSessionResultCopyWith<$Res> {
  _$FlashcardSessionResultCopyWithImpl(this._self, this._then);

  final FlashcardSessionResult _self;
  final $Res Function(FlashcardSessionResult) _then;

  /// Create a copy of FlashcardSessionResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? cardsReviewed = null,
    Object? cardsAgain = null,
    Object? cardsHard = null,
    Object? cardsEasy = null,
    Object? nextDueDate = freezed,
    Object? xpEarned = null,
  }) {
    return _then(_self.copyWith(
      cardsReviewed: null == cardsReviewed
          ? _self.cardsReviewed
          : cardsReviewed // ignore: cast_nullable_to_non_nullable
              as int,
      cardsAgain: null == cardsAgain
          ? _self.cardsAgain
          : cardsAgain // ignore: cast_nullable_to_non_nullable
              as int,
      cardsHard: null == cardsHard
          ? _self.cardsHard
          : cardsHard // ignore: cast_nullable_to_non_nullable
              as int,
      cardsEasy: null == cardsEasy
          ? _self.cardsEasy
          : cardsEasy // ignore: cast_nullable_to_non_nullable
              as int,
      nextDueDate: freezed == nextDueDate
          ? _self.nextDueDate
          : nextDueDate // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      xpEarned: null == xpEarned
          ? _self.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// Adds pattern-matching-related methods to [FlashcardSessionResult].
extension FlashcardSessionResultPatterns on FlashcardSessionResult {
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
    TResult Function(_FlashcardSessionResult value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _FlashcardSessionResult() when $default != null:
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
    TResult Function(_FlashcardSessionResult value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _FlashcardSessionResult():
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
    TResult? Function(_FlashcardSessionResult value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _FlashcardSessionResult() when $default != null:
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
            @JsonKey(name: 'cards_reviewed') int cardsReviewed,
            @JsonKey(name: 'cards_again') int cardsAgain,
            @JsonKey(name: 'cards_hard') int cardsHard,
            @JsonKey(name: 'cards_easy') int cardsEasy,
            @JsonKey(name: 'next_due_date') DateTime? nextDueDate,
            @JsonKey(name: 'xp_earned') int xpEarned)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _FlashcardSessionResult() when $default != null:
        return $default(_that.cardsReviewed, _that.cardsAgain, _that.cardsHard,
            _that.cardsEasy, _that.nextDueDate, _that.xpEarned);
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
            @JsonKey(name: 'cards_reviewed') int cardsReviewed,
            @JsonKey(name: 'cards_again') int cardsAgain,
            @JsonKey(name: 'cards_hard') int cardsHard,
            @JsonKey(name: 'cards_easy') int cardsEasy,
            @JsonKey(name: 'next_due_date') DateTime? nextDueDate,
            @JsonKey(name: 'xp_earned') int xpEarned)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _FlashcardSessionResult():
        return $default(_that.cardsReviewed, _that.cardsAgain, _that.cardsHard,
            _that.cardsEasy, _that.nextDueDate, _that.xpEarned);
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
            @JsonKey(name: 'cards_reviewed') int cardsReviewed,
            @JsonKey(name: 'cards_again') int cardsAgain,
            @JsonKey(name: 'cards_hard') int cardsHard,
            @JsonKey(name: 'cards_easy') int cardsEasy,
            @JsonKey(name: 'next_due_date') DateTime? nextDueDate,
            @JsonKey(name: 'xp_earned') int xpEarned)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _FlashcardSessionResult() when $default != null:
        return $default(_that.cardsReviewed, _that.cardsAgain, _that.cardsHard,
            _that.cardsEasy, _that.nextDueDate, _that.xpEarned);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _FlashcardSessionResult implements FlashcardSessionResult {
  const _FlashcardSessionResult(
      {@JsonKey(name: 'cards_reviewed') this.cardsReviewed = 0,
      @JsonKey(name: 'cards_again') this.cardsAgain = 0,
      @JsonKey(name: 'cards_hard') this.cardsHard = 0,
      @JsonKey(name: 'cards_easy') this.cardsEasy = 0,
      @JsonKey(name: 'next_due_date') this.nextDueDate,
      @JsonKey(name: 'xp_earned') this.xpEarned = 0});
  factory _FlashcardSessionResult.fromJson(Map<String, dynamic> json) =>
      _$FlashcardSessionResultFromJson(json);

  @override
  @JsonKey(name: 'cards_reviewed')
  final int cardsReviewed;
  @override
  @JsonKey(name: 'cards_again')
  final int cardsAgain;
  @override
  @JsonKey(name: 'cards_hard')
  final int cardsHard;
  @override
  @JsonKey(name: 'cards_easy')
  final int cardsEasy;
  @override
  @JsonKey(name: 'next_due_date')
  final DateTime? nextDueDate;
  @override
  @JsonKey(name: 'xp_earned')
  final int xpEarned;

  /// Create a copy of FlashcardSessionResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$FlashcardSessionResultCopyWith<_FlashcardSessionResult> get copyWith =>
      __$FlashcardSessionResultCopyWithImpl<_FlashcardSessionResult>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$FlashcardSessionResultToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _FlashcardSessionResult &&
            (identical(other.cardsReviewed, cardsReviewed) ||
                other.cardsReviewed == cardsReviewed) &&
            (identical(other.cardsAgain, cardsAgain) ||
                other.cardsAgain == cardsAgain) &&
            (identical(other.cardsHard, cardsHard) ||
                other.cardsHard == cardsHard) &&
            (identical(other.cardsEasy, cardsEasy) ||
                other.cardsEasy == cardsEasy) &&
            (identical(other.nextDueDate, nextDueDate) ||
                other.nextDueDate == nextDueDate) &&
            (identical(other.xpEarned, xpEarned) ||
                other.xpEarned == xpEarned));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, cardsReviewed, cardsAgain,
      cardsHard, cardsEasy, nextDueDate, xpEarned);

  @override
  String toString() {
    return 'FlashcardSessionResult(cardsReviewed: $cardsReviewed, cardsAgain: $cardsAgain, cardsHard: $cardsHard, cardsEasy: $cardsEasy, nextDueDate: $nextDueDate, xpEarned: $xpEarned)';
  }
}

/// @nodoc
abstract mixin class _$FlashcardSessionResultCopyWith<$Res>
    implements $FlashcardSessionResultCopyWith<$Res> {
  factory _$FlashcardSessionResultCopyWith(_FlashcardSessionResult value,
          $Res Function(_FlashcardSessionResult) _then) =
      __$FlashcardSessionResultCopyWithImpl;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'cards_reviewed') int cardsReviewed,
      @JsonKey(name: 'cards_again') int cardsAgain,
      @JsonKey(name: 'cards_hard') int cardsHard,
      @JsonKey(name: 'cards_easy') int cardsEasy,
      @JsonKey(name: 'next_due_date') DateTime? nextDueDate,
      @JsonKey(name: 'xp_earned') int xpEarned});
}

/// @nodoc
class __$FlashcardSessionResultCopyWithImpl<$Res>
    implements _$FlashcardSessionResultCopyWith<$Res> {
  __$FlashcardSessionResultCopyWithImpl(this._self, this._then);

  final _FlashcardSessionResult _self;
  final $Res Function(_FlashcardSessionResult) _then;

  /// Create a copy of FlashcardSessionResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? cardsReviewed = null,
    Object? cardsAgain = null,
    Object? cardsHard = null,
    Object? cardsEasy = null,
    Object? nextDueDate = freezed,
    Object? xpEarned = null,
  }) {
    return _then(_FlashcardSessionResult(
      cardsReviewed: null == cardsReviewed
          ? _self.cardsReviewed
          : cardsReviewed // ignore: cast_nullable_to_non_nullable
              as int,
      cardsAgain: null == cardsAgain
          ? _self.cardsAgain
          : cardsAgain // ignore: cast_nullable_to_non_nullable
              as int,
      cardsHard: null == cardsHard
          ? _self.cardsHard
          : cardsHard // ignore: cast_nullable_to_non_nullable
              as int,
      cardsEasy: null == cardsEasy
          ? _self.cardsEasy
          : cardsEasy // ignore: cast_nullable_to_non_nullable
              as int,
      nextDueDate: freezed == nextDueDate
          ? _self.nextDueDate
          : nextDueDate // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      xpEarned: null == xpEarned
          ? _self.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

// dart format on
