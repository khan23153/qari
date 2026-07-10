// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'surah_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SurahModel {
  @JsonKey(name: 'surah_id')
  int get surahId;
  @JsonKey(name: 'surah_number')
  int get surahNumber;
  String get name;
  @JsonKey(name: 'name_arabic')
  String get nameArabic;
  @JsonKey(name: 'name_english')
  String get nameEnglish;
  @JsonKey(name: 'name_translation')
  String get nameTranslation;
  @JsonKey(name: 'revelation_type')
  String get revelationType;
  @JsonKey(name: 'ayah_count')
  int get ayahCount;
  @JsonKey(name: 'revelation_order')
  int get revelationOrder;
  @JsonKey(name: 'page_start')
  int? get pageStart;
  @JsonKey(name: 'page_end')
  int? get pageEnd;

  /// Create a copy of SurahModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $SurahModelCopyWith<SurahModel> get copyWith =>
      _$SurahModelCopyWithImpl<SurahModel>(this as SurahModel, _$identity);

  /// Serializes this SurahModel to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is SurahModel &&
            (identical(other.surahId, surahId) || other.surahId == surahId) &&
            (identical(other.surahNumber, surahNumber) ||
                other.surahNumber == surahNumber) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.nameArabic, nameArabic) ||
                other.nameArabic == nameArabic) &&
            (identical(other.nameEnglish, nameEnglish) ||
                other.nameEnglish == nameEnglish) &&
            (identical(other.nameTranslation, nameTranslation) ||
                other.nameTranslation == nameTranslation) &&
            (identical(other.revelationType, revelationType) ||
                other.revelationType == revelationType) &&
            (identical(other.ayahCount, ayahCount) ||
                other.ayahCount == ayahCount) &&
            (identical(other.revelationOrder, revelationOrder) ||
                other.revelationOrder == revelationOrder) &&
            (identical(other.pageStart, pageStart) ||
                other.pageStart == pageStart) &&
            (identical(other.pageEnd, pageEnd) || other.pageEnd == pageEnd));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      surahId,
      surahNumber,
      name,
      nameArabic,
      nameEnglish,
      nameTranslation,
      revelationType,
      ayahCount,
      revelationOrder,
      pageStart,
      pageEnd);

  @override
  String toString() {
    return 'SurahModel(surahId: $surahId, surahNumber: $surahNumber, name: $name, nameArabic: $nameArabic, nameEnglish: $nameEnglish, nameTranslation: $nameTranslation, revelationType: $revelationType, ayahCount: $ayahCount, revelationOrder: $revelationOrder, pageStart: $pageStart, pageEnd: $pageEnd)';
  }
}

/// @nodoc
abstract mixin class $SurahModelCopyWith<$Res> {
  factory $SurahModelCopyWith(
          SurahModel value, $Res Function(SurahModel) _then) =
      _$SurahModelCopyWithImpl;
  @useResult
  $Res call(
      {@JsonKey(name: 'surah_id') int surahId,
      @JsonKey(name: 'surah_number') int surahNumber,
      String name,
      @JsonKey(name: 'name_arabic') String nameArabic,
      @JsonKey(name: 'name_english') String nameEnglish,
      @JsonKey(name: 'name_translation') String nameTranslation,
      @JsonKey(name: 'revelation_type') String revelationType,
      @JsonKey(name: 'ayah_count') int ayahCount,
      @JsonKey(name: 'revelation_order') int revelationOrder,
      @JsonKey(name: 'page_start') int? pageStart,
      @JsonKey(name: 'page_end') int? pageEnd});
}

/// @nodoc
class _$SurahModelCopyWithImpl<$Res> implements $SurahModelCopyWith<$Res> {
  _$SurahModelCopyWithImpl(this._self, this._then);

  final SurahModel _self;
  final $Res Function(SurahModel) _then;

  /// Create a copy of SurahModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? surahId = null,
    Object? surahNumber = null,
    Object? name = null,
    Object? nameArabic = null,
    Object? nameEnglish = null,
    Object? nameTranslation = null,
    Object? revelationType = null,
    Object? ayahCount = null,
    Object? revelationOrder = null,
    Object? pageStart = freezed,
    Object? pageEnd = freezed,
  }) {
    return _then(_self.copyWith(
      surahId: null == surahId
          ? _self.surahId
          : surahId // ignore: cast_nullable_to_non_nullable
              as int,
      surahNumber: null == surahNumber
          ? _self.surahNumber
          : surahNumber // ignore: cast_nullable_to_non_nullable
              as int,
      name: null == name
          ? _self.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameArabic: null == nameArabic
          ? _self.nameArabic
          : nameArabic // ignore: cast_nullable_to_non_nullable
              as String,
      nameEnglish: null == nameEnglish
          ? _self.nameEnglish
          : nameEnglish // ignore: cast_nullable_to_non_nullable
              as String,
      nameTranslation: null == nameTranslation
          ? _self.nameTranslation
          : nameTranslation // ignore: cast_nullable_to_non_nullable
              as String,
      revelationType: null == revelationType
          ? _self.revelationType
          : revelationType // ignore: cast_nullable_to_non_nullable
              as String,
      ayahCount: null == ayahCount
          ? _self.ayahCount
          : ayahCount // ignore: cast_nullable_to_non_nullable
              as int,
      revelationOrder: null == revelationOrder
          ? _self.revelationOrder
          : revelationOrder // ignore: cast_nullable_to_non_nullable
              as int,
      pageStart: freezed == pageStart
          ? _self.pageStart
          : pageStart // ignore: cast_nullable_to_non_nullable
              as int?,
      pageEnd: freezed == pageEnd
          ? _self.pageEnd
          : pageEnd // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

/// Adds pattern-matching-related methods to [SurahModel].
extension SurahModelPatterns on SurahModel {
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
    TResult Function(_SurahModel value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _SurahModel() when $default != null:
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
    TResult Function(_SurahModel value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _SurahModel():
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
    TResult? Function(_SurahModel value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _SurahModel() when $default != null:
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
            @JsonKey(name: 'surah_id') int surahId,
            @JsonKey(name: 'surah_number') int surahNumber,
            String name,
            @JsonKey(name: 'name_arabic') String nameArabic,
            @JsonKey(name: 'name_english') String nameEnglish,
            @JsonKey(name: 'name_translation') String nameTranslation,
            @JsonKey(name: 'revelation_type') String revelationType,
            @JsonKey(name: 'ayah_count') int ayahCount,
            @JsonKey(name: 'revelation_order') int revelationOrder,
            @JsonKey(name: 'page_start') int? pageStart,
            @JsonKey(name: 'page_end') int? pageEnd)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _SurahModel() when $default != null:
        return $default(
            _that.surahId,
            _that.surahNumber,
            _that.name,
            _that.nameArabic,
            _that.nameEnglish,
            _that.nameTranslation,
            _that.revelationType,
            _that.ayahCount,
            _that.revelationOrder,
            _that.pageStart,
            _that.pageEnd);
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
            @JsonKey(name: 'surah_id') int surahId,
            @JsonKey(name: 'surah_number') int surahNumber,
            String name,
            @JsonKey(name: 'name_arabic') String nameArabic,
            @JsonKey(name: 'name_english') String nameEnglish,
            @JsonKey(name: 'name_translation') String nameTranslation,
            @JsonKey(name: 'revelation_type') String revelationType,
            @JsonKey(name: 'ayah_count') int ayahCount,
            @JsonKey(name: 'revelation_order') int revelationOrder,
            @JsonKey(name: 'page_start') int? pageStart,
            @JsonKey(name: 'page_end') int? pageEnd)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _SurahModel():
        return $default(
            _that.surahId,
            _that.surahNumber,
            _that.name,
            _that.nameArabic,
            _that.nameEnglish,
            _that.nameTranslation,
            _that.revelationType,
            _that.ayahCount,
            _that.revelationOrder,
            _that.pageStart,
            _that.pageEnd);
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
            @JsonKey(name: 'surah_id') int surahId,
            @JsonKey(name: 'surah_number') int surahNumber,
            String name,
            @JsonKey(name: 'name_arabic') String nameArabic,
            @JsonKey(name: 'name_english') String nameEnglish,
            @JsonKey(name: 'name_translation') String nameTranslation,
            @JsonKey(name: 'revelation_type') String revelationType,
            @JsonKey(name: 'ayah_count') int ayahCount,
            @JsonKey(name: 'revelation_order') int revelationOrder,
            @JsonKey(name: 'page_start') int? pageStart,
            @JsonKey(name: 'page_end') int? pageEnd)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _SurahModel() when $default != null:
        return $default(
            _that.surahId,
            _that.surahNumber,
            _that.name,
            _that.nameArabic,
            _that.nameEnglish,
            _that.nameTranslation,
            _that.revelationType,
            _that.ayahCount,
            _that.revelationOrder,
            _that.pageStart,
            _that.pageEnd);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _SurahModel implements SurahModel {
  const _SurahModel(
      {@JsonKey(name: 'surah_id') required this.surahId,
      @JsonKey(name: 'surah_number') required this.surahNumber,
      required this.name,
      @JsonKey(name: 'name_arabic') required this.nameArabic,
      @JsonKey(name: 'name_english') required this.nameEnglish,
      @JsonKey(name: 'name_translation') required this.nameTranslation,
      @JsonKey(name: 'revelation_type') required this.revelationType,
      @JsonKey(name: 'ayah_count') required this.ayahCount,
      @JsonKey(name: 'revelation_order') required this.revelationOrder,
      @JsonKey(name: 'page_start') this.pageStart,
      @JsonKey(name: 'page_end') this.pageEnd});
  factory _SurahModel.fromJson(Map<String, dynamic> json) =>
      _$SurahModelFromJson(json);

  @override
  @JsonKey(name: 'surah_id')
  final int surahId;
  @override
  @JsonKey(name: 'surah_number')
  final int surahNumber;
  @override
  final String name;
  @override
  @JsonKey(name: 'name_arabic')
  final String nameArabic;
  @override
  @JsonKey(name: 'name_english')
  final String nameEnglish;
  @override
  @JsonKey(name: 'name_translation')
  final String nameTranslation;
  @override
  @JsonKey(name: 'revelation_type')
  final String revelationType;
  @override
  @JsonKey(name: 'ayah_count')
  final int ayahCount;
  @override
  @JsonKey(name: 'revelation_order')
  final int revelationOrder;
  @override
  @JsonKey(name: 'page_start')
  final int? pageStart;
  @override
  @JsonKey(name: 'page_end')
  final int? pageEnd;

  /// Create a copy of SurahModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$SurahModelCopyWith<_SurahModel> get copyWith =>
      __$SurahModelCopyWithImpl<_SurahModel>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$SurahModelToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _SurahModel &&
            (identical(other.surahId, surahId) || other.surahId == surahId) &&
            (identical(other.surahNumber, surahNumber) ||
                other.surahNumber == surahNumber) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.nameArabic, nameArabic) ||
                other.nameArabic == nameArabic) &&
            (identical(other.nameEnglish, nameEnglish) ||
                other.nameEnglish == nameEnglish) &&
            (identical(other.nameTranslation, nameTranslation) ||
                other.nameTranslation == nameTranslation) &&
            (identical(other.revelationType, revelationType) ||
                other.revelationType == revelationType) &&
            (identical(other.ayahCount, ayahCount) ||
                other.ayahCount == ayahCount) &&
            (identical(other.revelationOrder, revelationOrder) ||
                other.revelationOrder == revelationOrder) &&
            (identical(other.pageStart, pageStart) ||
                other.pageStart == pageStart) &&
            (identical(other.pageEnd, pageEnd) || other.pageEnd == pageEnd));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      surahId,
      surahNumber,
      name,
      nameArabic,
      nameEnglish,
      nameTranslation,
      revelationType,
      ayahCount,
      revelationOrder,
      pageStart,
      pageEnd);

  @override
  String toString() {
    return 'SurahModel(surahId: $surahId, surahNumber: $surahNumber, name: $name, nameArabic: $nameArabic, nameEnglish: $nameEnglish, nameTranslation: $nameTranslation, revelationType: $revelationType, ayahCount: $ayahCount, revelationOrder: $revelationOrder, pageStart: $pageStart, pageEnd: $pageEnd)';
  }
}

/// @nodoc
abstract mixin class _$SurahModelCopyWith<$Res>
    implements $SurahModelCopyWith<$Res> {
  factory _$SurahModelCopyWith(
          _SurahModel value, $Res Function(_SurahModel) _then) =
      __$SurahModelCopyWithImpl;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'surah_id') int surahId,
      @JsonKey(name: 'surah_number') int surahNumber,
      String name,
      @JsonKey(name: 'name_arabic') String nameArabic,
      @JsonKey(name: 'name_english') String nameEnglish,
      @JsonKey(name: 'name_translation') String nameTranslation,
      @JsonKey(name: 'revelation_type') String revelationType,
      @JsonKey(name: 'ayah_count') int ayahCount,
      @JsonKey(name: 'revelation_order') int revelationOrder,
      @JsonKey(name: 'page_start') int? pageStart,
      @JsonKey(name: 'page_end') int? pageEnd});
}

/// @nodoc
class __$SurahModelCopyWithImpl<$Res> implements _$SurahModelCopyWith<$Res> {
  __$SurahModelCopyWithImpl(this._self, this._then);

  final _SurahModel _self;
  final $Res Function(_SurahModel) _then;

  /// Create a copy of SurahModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? surahId = null,
    Object? surahNumber = null,
    Object? name = null,
    Object? nameArabic = null,
    Object? nameEnglish = null,
    Object? nameTranslation = null,
    Object? revelationType = null,
    Object? ayahCount = null,
    Object? revelationOrder = null,
    Object? pageStart = freezed,
    Object? pageEnd = freezed,
  }) {
    return _then(_SurahModel(
      surahId: null == surahId
          ? _self.surahId
          : surahId // ignore: cast_nullable_to_non_nullable
              as int,
      surahNumber: null == surahNumber
          ? _self.surahNumber
          : surahNumber // ignore: cast_nullable_to_non_nullable
              as int,
      name: null == name
          ? _self.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      nameArabic: null == nameArabic
          ? _self.nameArabic
          : nameArabic // ignore: cast_nullable_to_non_nullable
              as String,
      nameEnglish: null == nameEnglish
          ? _self.nameEnglish
          : nameEnglish // ignore: cast_nullable_to_non_nullable
              as String,
      nameTranslation: null == nameTranslation
          ? _self.nameTranslation
          : nameTranslation // ignore: cast_nullable_to_non_nullable
              as String,
      revelationType: null == revelationType
          ? _self.revelationType
          : revelationType // ignore: cast_nullable_to_non_nullable
              as String,
      ayahCount: null == ayahCount
          ? _self.ayahCount
          : ayahCount // ignore: cast_nullable_to_non_nullable
              as int,
      revelationOrder: null == revelationOrder
          ? _self.revelationOrder
          : revelationOrder // ignore: cast_nullable_to_non_nullable
              as int,
      pageStart: freezed == pageStart
          ? _self.pageStart
          : pageStart // ignore: cast_nullable_to_non_nullable
              as int?,
      pageEnd: freezed == pageEnd
          ? _self.pageEnd
          : pageEnd // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

// dart format on
