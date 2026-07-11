// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'lesson_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$LessonModel {
  @JsonKey(name: 'lesson_id')
  int get lessonId;
  @JsonKey(name: 'module_number')
  int get moduleNumber;
  @JsonKey(name: 'lesson_number')
  int get lessonNumber;
  String get title;
  @JsonKey(name: 'title_urdu')
  String? get titleUrdu;
  @JsonKey(name: 'title_hinglish')
  String? get titleHinglish;
  String get description;
  @JsonKey(name: 'description_urdu')
  String? get descriptionUrdu;
  @JsonKey(name: 'description_hinglish')
  String? get descriptionHinglish;
  @JsonKey(name: 'xp_reward')
  int get xpReward;
  @JsonKey(name: 'estimated_minutes')
  int get estimatedMinutes;
  @JsonKey(name: 'is_completed')
  bool get isCompleted;
  @JsonKey(name: 'is_locked')
  bool get isLocked;
  @JsonKey(name: 'icon_name')
  String get iconName;
  @JsonKey(name: 'concepts')
  List<LessonConcept> get concepts;
  @JsonKey(name: 'quiz_questions')
  List<QuizQuestionModel> get quizQuestions;

  /// Create a copy of LessonModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $LessonModelCopyWith<LessonModel> get copyWith =>
      _$LessonModelCopyWithImpl<LessonModel>(this as LessonModel, _$identity);

  /// Serializes this LessonModel to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is LessonModel &&
            (identical(other.lessonId, lessonId) ||
                other.lessonId == lessonId) &&
            (identical(other.moduleNumber, moduleNumber) ||
                other.moduleNumber == moduleNumber) &&
            (identical(other.lessonNumber, lessonNumber) ||
                other.lessonNumber == lessonNumber) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.titleUrdu, titleUrdu) ||
                other.titleUrdu == titleUrdu) &&
            (identical(other.titleHinglish, titleHinglish) ||
                other.titleHinglish == titleHinglish) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.descriptionUrdu, descriptionUrdu) ||
                other.descriptionUrdu == descriptionUrdu) &&
            (identical(other.descriptionHinglish, descriptionHinglish) ||
                other.descriptionHinglish == descriptionHinglish) &&
            (identical(other.xpReward, xpReward) ||
                other.xpReward == xpReward) &&
            (identical(other.estimatedMinutes, estimatedMinutes) ||
                other.estimatedMinutes == estimatedMinutes) &&
            (identical(other.isCompleted, isCompleted) ||
                other.isCompleted == isCompleted) &&
            (identical(other.isLocked, isLocked) ||
                other.isLocked == isLocked) &&
            (identical(other.iconName, iconName) ||
                other.iconName == iconName) &&
            const DeepCollectionEquality().equals(other.concepts, concepts) &&
            const DeepCollectionEquality()
                .equals(other.quizQuestions, quizQuestions));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      lessonId,
      moduleNumber,
      lessonNumber,
      title,
      titleUrdu,
      titleHinglish,
      description,
      descriptionUrdu,
      descriptionHinglish,
      xpReward,
      estimatedMinutes,
      isCompleted,
      isLocked,
      iconName,
      const DeepCollectionEquality().hash(concepts),
      const DeepCollectionEquality().hash(quizQuestions));

  @override
  String toString() {
    return 'LessonModel(lessonId: $lessonId, moduleNumber: $moduleNumber, lessonNumber: $lessonNumber, title: $title, titleUrdu: $titleUrdu, titleHinglish: $titleHinglish, description: $description, descriptionUrdu: $descriptionUrdu, descriptionHinglish: $descriptionHinglish, xpReward: $xpReward, estimatedMinutes: $estimatedMinutes, isCompleted: $isCompleted, isLocked: $isLocked, iconName: $iconName, concepts: $concepts, quizQuestions: $quizQuestions)';
  }
}

/// @nodoc
abstract mixin class $LessonModelCopyWith<$Res> {
  factory $LessonModelCopyWith(
          LessonModel value, $Res Function(LessonModel) _then) =
      _$LessonModelCopyWithImpl;
  @useResult
  $Res call(
      {@JsonKey(name: 'lesson_id') int lessonId,
      @JsonKey(name: 'module_number') int moduleNumber,
      @JsonKey(name: 'lesson_number') int lessonNumber,
      String title,
      @JsonKey(name: 'title_urdu') String? titleUrdu,
      @JsonKey(name: 'title_hinglish') String? titleHinglish,
      String description,
      @JsonKey(name: 'description_urdu') String? descriptionUrdu,
      @JsonKey(name: 'description_hinglish') String? descriptionHinglish,
      @JsonKey(name: 'xp_reward') int xpReward,
      @JsonKey(name: 'estimated_minutes') int estimatedMinutes,
      @JsonKey(name: 'is_completed') bool isCompleted,
      @JsonKey(name: 'is_locked') bool isLocked,
      @JsonKey(name: 'icon_name') String iconName,
      @JsonKey(name: 'concepts') List<LessonConcept> concepts,
      @JsonKey(name: 'quiz_questions') List<QuizQuestionModel> quizQuestions});
}

/// @nodoc
class _$LessonModelCopyWithImpl<$Res> implements $LessonModelCopyWith<$Res> {
  _$LessonModelCopyWithImpl(this._self, this._then);

  final LessonModel _self;
  final $Res Function(LessonModel) _then;

  /// Create a copy of LessonModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? lessonId = null,
    Object? moduleNumber = null,
    Object? lessonNumber = null,
    Object? title = null,
    Object? titleUrdu = freezed,
    Object? titleHinglish = freezed,
    Object? description = null,
    Object? descriptionUrdu = freezed,
    Object? descriptionHinglish = freezed,
    Object? xpReward = null,
    Object? estimatedMinutes = null,
    Object? isCompleted = null,
    Object? isLocked = null,
    Object? iconName = null,
    Object? concepts = null,
    Object? quizQuestions = null,
  }) {
    return _then(_self.copyWith(
      lessonId: null == lessonId
          ? _self.lessonId
          : lessonId // ignore: cast_nullable_to_non_nullable
              as int,
      moduleNumber: null == moduleNumber
          ? _self.moduleNumber
          : moduleNumber // ignore: cast_nullable_to_non_nullable
              as int,
      lessonNumber: null == lessonNumber
          ? _self.lessonNumber
          : lessonNumber // ignore: cast_nullable_to_non_nullable
              as int,
      title: null == title
          ? _self.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      titleUrdu: freezed == titleUrdu
          ? _self.titleUrdu
          : titleUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      titleHinglish: freezed == titleHinglish
          ? _self.titleHinglish
          : titleHinglish // ignore: cast_nullable_to_non_nullable
              as String?,
      description: null == description
          ? _self.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      descriptionUrdu: freezed == descriptionUrdu
          ? _self.descriptionUrdu
          : descriptionUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      descriptionHinglish: freezed == descriptionHinglish
          ? _self.descriptionHinglish
          : descriptionHinglish // ignore: cast_nullable_to_non_nullable
              as String?,
      xpReward: null == xpReward
          ? _self.xpReward
          : xpReward // ignore: cast_nullable_to_non_nullable
              as int,
      estimatedMinutes: null == estimatedMinutes
          ? _self.estimatedMinutes
          : estimatedMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      isCompleted: null == isCompleted
          ? _self.isCompleted
          : isCompleted // ignore: cast_nullable_to_non_nullable
              as bool,
      isLocked: null == isLocked
          ? _self.isLocked
          : isLocked // ignore: cast_nullable_to_non_nullable
              as bool,
      iconName: null == iconName
          ? _self.iconName
          : iconName // ignore: cast_nullable_to_non_nullable
              as String,
      concepts: null == concepts
          ? _self.concepts
          : concepts // ignore: cast_nullable_to_non_nullable
              as List<LessonConcept>,
      quizQuestions: null == quizQuestions
          ? _self.quizQuestions
          : quizQuestions // ignore: cast_nullable_to_non_nullable
              as List<QuizQuestionModel>,
    ));
  }
}

/// Adds pattern-matching-related methods to [LessonModel].
extension LessonModelPatterns on LessonModel {
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
    TResult Function(_LessonModel value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _LessonModel() when $default != null:
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
    TResult Function(_LessonModel value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonModel():
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
    TResult? Function(_LessonModel value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonModel() when $default != null:
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
            @JsonKey(name: 'lesson_id') int lessonId,
            @JsonKey(name: 'module_number') int moduleNumber,
            @JsonKey(name: 'lesson_number') int lessonNumber,
            String title,
            @JsonKey(name: 'title_urdu') String? titleUrdu,
            @JsonKey(name: 'title_hinglish') String? titleHinglish,
            String description,
            @JsonKey(name: 'description_urdu') String? descriptionUrdu,
            @JsonKey(name: 'description_hinglish') String? descriptionHinglish,
            @JsonKey(name: 'xp_reward') int xpReward,
            @JsonKey(name: 'estimated_minutes') int estimatedMinutes,
            @JsonKey(name: 'is_completed') bool isCompleted,
            @JsonKey(name: 'is_locked') bool isLocked,
            @JsonKey(name: 'icon_name') String iconName,
            @JsonKey(name: 'concepts') List<LessonConcept> concepts,
            @JsonKey(name: 'quiz_questions')
            List<QuizQuestionModel> quizQuestions)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _LessonModel() when $default != null:
        return $default(
            _that.lessonId,
            _that.moduleNumber,
            _that.lessonNumber,
            _that.title,
            _that.titleUrdu,
            _that.titleHinglish,
            _that.description,
            _that.descriptionUrdu,
            _that.descriptionHinglish,
            _that.xpReward,
            _that.estimatedMinutes,
            _that.isCompleted,
            _that.isLocked,
            _that.iconName,
            _that.concepts,
            _that.quizQuestions);
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
            @JsonKey(name: 'lesson_id') int lessonId,
            @JsonKey(name: 'module_number') int moduleNumber,
            @JsonKey(name: 'lesson_number') int lessonNumber,
            String title,
            @JsonKey(name: 'title_urdu') String? titleUrdu,
            @JsonKey(name: 'title_hinglish') String? titleHinglish,
            String description,
            @JsonKey(name: 'description_urdu') String? descriptionUrdu,
            @JsonKey(name: 'description_hinglish') String? descriptionHinglish,
            @JsonKey(name: 'xp_reward') int xpReward,
            @JsonKey(name: 'estimated_minutes') int estimatedMinutes,
            @JsonKey(name: 'is_completed') bool isCompleted,
            @JsonKey(name: 'is_locked') bool isLocked,
            @JsonKey(name: 'icon_name') String iconName,
            @JsonKey(name: 'concepts') List<LessonConcept> concepts,
            @JsonKey(name: 'quiz_questions')
            List<QuizQuestionModel> quizQuestions)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonModel():
        return $default(
            _that.lessonId,
            _that.moduleNumber,
            _that.lessonNumber,
            _that.title,
            _that.titleUrdu,
            _that.titleHinglish,
            _that.description,
            _that.descriptionUrdu,
            _that.descriptionHinglish,
            _that.xpReward,
            _that.estimatedMinutes,
            _that.isCompleted,
            _that.isLocked,
            _that.iconName,
            _that.concepts,
            _that.quizQuestions);
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
            @JsonKey(name: 'lesson_id') int lessonId,
            @JsonKey(name: 'module_number') int moduleNumber,
            @JsonKey(name: 'lesson_number') int lessonNumber,
            String title,
            @JsonKey(name: 'title_urdu') String? titleUrdu,
            @JsonKey(name: 'title_hinglish') String? titleHinglish,
            String description,
            @JsonKey(name: 'description_urdu') String? descriptionUrdu,
            @JsonKey(name: 'description_hinglish') String? descriptionHinglish,
            @JsonKey(name: 'xp_reward') int xpReward,
            @JsonKey(name: 'estimated_minutes') int estimatedMinutes,
            @JsonKey(name: 'is_completed') bool isCompleted,
            @JsonKey(name: 'is_locked') bool isLocked,
            @JsonKey(name: 'icon_name') String iconName,
            @JsonKey(name: 'concepts') List<LessonConcept> concepts,
            @JsonKey(name: 'quiz_questions')
            List<QuizQuestionModel> quizQuestions)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonModel() when $default != null:
        return $default(
            _that.lessonId,
            _that.moduleNumber,
            _that.lessonNumber,
            _that.title,
            _that.titleUrdu,
            _that.titleHinglish,
            _that.description,
            _that.descriptionUrdu,
            _that.descriptionHinglish,
            _that.xpReward,
            _that.estimatedMinutes,
            _that.isCompleted,
            _that.isLocked,
            _that.iconName,
            _that.concepts,
            _that.quizQuestions);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _LessonModel implements LessonModel {
  const _LessonModel(
      {@JsonKey(name: 'lesson_id') required this.lessonId,
      @JsonKey(name: 'module_number') required this.moduleNumber,
      @JsonKey(name: 'lesson_number') required this.lessonNumber,
      required this.title,
      @JsonKey(name: 'title_urdu') this.titleUrdu,
      @JsonKey(name: 'title_hinglish') this.titleHinglish,
      required this.description,
      @JsonKey(name: 'description_urdu') this.descriptionUrdu,
      @JsonKey(name: 'description_hinglish') this.descriptionHinglish,
      @JsonKey(name: 'xp_reward') this.xpReward = 10,
      @JsonKey(name: 'estimated_minutes') this.estimatedMinutes = 5,
      @JsonKey(name: 'is_completed') this.isCompleted = false,
      @JsonKey(name: 'is_locked') this.isLocked = false,
      @JsonKey(name: 'icon_name') this.iconName = 'book',
      @JsonKey(name: 'concepts') final List<LessonConcept> concepts = const [],
      @JsonKey(name: 'quiz_questions')
      final List<QuizQuestionModel> quizQuestions = const []})
      : _concepts = concepts,
        _quizQuestions = quizQuestions;
  factory _LessonModel.fromJson(Map<String, dynamic> json) =>
      _$LessonModelFromJson(json);

  @override
  @JsonKey(name: 'lesson_id')
  final int lessonId;
  @override
  @JsonKey(name: 'module_number')
  final int moduleNumber;
  @override
  @JsonKey(name: 'lesson_number')
  final int lessonNumber;
  @override
  final String title;
  @override
  @JsonKey(name: 'title_urdu')
  final String? titleUrdu;
  @override
  @JsonKey(name: 'title_hinglish')
  final String? titleHinglish;
  @override
  final String description;
  @override
  @JsonKey(name: 'description_urdu')
  final String? descriptionUrdu;
  @override
  @JsonKey(name: 'description_hinglish')
  final String? descriptionHinglish;
  @override
  @JsonKey(name: 'xp_reward')
  final int xpReward;
  @override
  @JsonKey(name: 'estimated_minutes')
  final int estimatedMinutes;
  @override
  @JsonKey(name: 'is_completed')
  final bool isCompleted;
  @override
  @JsonKey(name: 'is_locked')
  final bool isLocked;
  @override
  @JsonKey(name: 'icon_name')
  final String iconName;
  final List<LessonConcept> _concepts;
  @override
  @JsonKey(name: 'concepts')
  List<LessonConcept> get concepts {
    if (_concepts is EqualUnmodifiableListView) return _concepts;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_concepts);
  }

  final List<QuizQuestionModel> _quizQuestions;
  @override
  @JsonKey(name: 'quiz_questions')
  List<QuizQuestionModel> get quizQuestions {
    if (_quizQuestions is EqualUnmodifiableListView) return _quizQuestions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_quizQuestions);
  }

  /// Create a copy of LessonModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$LessonModelCopyWith<_LessonModel> get copyWith =>
      __$LessonModelCopyWithImpl<_LessonModel>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$LessonModelToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _LessonModel &&
            (identical(other.lessonId, lessonId) ||
                other.lessonId == lessonId) &&
            (identical(other.moduleNumber, moduleNumber) ||
                other.moduleNumber == moduleNumber) &&
            (identical(other.lessonNumber, lessonNumber) ||
                other.lessonNumber == lessonNumber) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.titleUrdu, titleUrdu) ||
                other.titleUrdu == titleUrdu) &&
            (identical(other.titleHinglish, titleHinglish) ||
                other.titleHinglish == titleHinglish) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.descriptionUrdu, descriptionUrdu) ||
                other.descriptionUrdu == descriptionUrdu) &&
            (identical(other.descriptionHinglish, descriptionHinglish) ||
                other.descriptionHinglish == descriptionHinglish) &&
            (identical(other.xpReward, xpReward) ||
                other.xpReward == xpReward) &&
            (identical(other.estimatedMinutes, estimatedMinutes) ||
                other.estimatedMinutes == estimatedMinutes) &&
            (identical(other.isCompleted, isCompleted) ||
                other.isCompleted == isCompleted) &&
            (identical(other.isLocked, isLocked) ||
                other.isLocked == isLocked) &&
            (identical(other.iconName, iconName) ||
                other.iconName == iconName) &&
            const DeepCollectionEquality().equals(other._concepts, _concepts) &&
            const DeepCollectionEquality()
                .equals(other._quizQuestions, _quizQuestions));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      lessonId,
      moduleNumber,
      lessonNumber,
      title,
      titleUrdu,
      titleHinglish,
      description,
      descriptionUrdu,
      descriptionHinglish,
      xpReward,
      estimatedMinutes,
      isCompleted,
      isLocked,
      iconName,
      const DeepCollectionEquality().hash(_concepts),
      const DeepCollectionEquality().hash(_quizQuestions));

  @override
  String toString() {
    return 'LessonModel(lessonId: $lessonId, moduleNumber: $moduleNumber, lessonNumber: $lessonNumber, title: $title, titleUrdu: $titleUrdu, titleHinglish: $titleHinglish, description: $description, descriptionUrdu: $descriptionUrdu, descriptionHinglish: $descriptionHinglish, xpReward: $xpReward, estimatedMinutes: $estimatedMinutes, isCompleted: $isCompleted, isLocked: $isLocked, iconName: $iconName, concepts: $concepts, quizQuestions: $quizQuestions)';
  }
}

/// @nodoc
abstract mixin class _$LessonModelCopyWith<$Res>
    implements $LessonModelCopyWith<$Res> {
  factory _$LessonModelCopyWith(
          _LessonModel value, $Res Function(_LessonModel) _then) =
      __$LessonModelCopyWithImpl;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'lesson_id') int lessonId,
      @JsonKey(name: 'module_number') int moduleNumber,
      @JsonKey(name: 'lesson_number') int lessonNumber,
      String title,
      @JsonKey(name: 'title_urdu') String? titleUrdu,
      @JsonKey(name: 'title_hinglish') String? titleHinglish,
      String description,
      @JsonKey(name: 'description_urdu') String? descriptionUrdu,
      @JsonKey(name: 'description_hinglish') String? descriptionHinglish,
      @JsonKey(name: 'xp_reward') int xpReward,
      @JsonKey(name: 'estimated_minutes') int estimatedMinutes,
      @JsonKey(name: 'is_completed') bool isCompleted,
      @JsonKey(name: 'is_locked') bool isLocked,
      @JsonKey(name: 'icon_name') String iconName,
      @JsonKey(name: 'concepts') List<LessonConcept> concepts,
      @JsonKey(name: 'quiz_questions') List<QuizQuestionModel> quizQuestions});
}

/// @nodoc
class __$LessonModelCopyWithImpl<$Res> implements _$LessonModelCopyWith<$Res> {
  __$LessonModelCopyWithImpl(this._self, this._then);

  final _LessonModel _self;
  final $Res Function(_LessonModel) _then;

  /// Create a copy of LessonModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? lessonId = null,
    Object? moduleNumber = null,
    Object? lessonNumber = null,
    Object? title = null,
    Object? titleUrdu = freezed,
    Object? titleHinglish = freezed,
    Object? description = null,
    Object? descriptionUrdu = freezed,
    Object? descriptionHinglish = freezed,
    Object? xpReward = null,
    Object? estimatedMinutes = null,
    Object? isCompleted = null,
    Object? isLocked = null,
    Object? iconName = null,
    Object? concepts = null,
    Object? quizQuestions = null,
  }) {
    return _then(_LessonModel(
      lessonId: null == lessonId
          ? _self.lessonId
          : lessonId // ignore: cast_nullable_to_non_nullable
              as int,
      moduleNumber: null == moduleNumber
          ? _self.moduleNumber
          : moduleNumber // ignore: cast_nullable_to_non_nullable
              as int,
      lessonNumber: null == lessonNumber
          ? _self.lessonNumber
          : lessonNumber // ignore: cast_nullable_to_non_nullable
              as int,
      title: null == title
          ? _self.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      titleUrdu: freezed == titleUrdu
          ? _self.titleUrdu
          : titleUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      titleHinglish: freezed == titleHinglish
          ? _self.titleHinglish
          : titleHinglish // ignore: cast_nullable_to_non_nullable
              as String?,
      description: null == description
          ? _self.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      descriptionUrdu: freezed == descriptionUrdu
          ? _self.descriptionUrdu
          : descriptionUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      descriptionHinglish: freezed == descriptionHinglish
          ? _self.descriptionHinglish
          : descriptionHinglish // ignore: cast_nullable_to_non_nullable
              as String?,
      xpReward: null == xpReward
          ? _self.xpReward
          : xpReward // ignore: cast_nullable_to_non_nullable
              as int,
      estimatedMinutes: null == estimatedMinutes
          ? _self.estimatedMinutes
          : estimatedMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      isCompleted: null == isCompleted
          ? _self.isCompleted
          : isCompleted // ignore: cast_nullable_to_non_nullable
              as bool,
      isLocked: null == isLocked
          ? _self.isLocked
          : isLocked // ignore: cast_nullable_to_non_nullable
              as bool,
      iconName: null == iconName
          ? _self.iconName
          : iconName // ignore: cast_nullable_to_non_nullable
              as String,
      concepts: null == concepts
          ? _self._concepts
          : concepts // ignore: cast_nullable_to_non_nullable
              as List<LessonConcept>,
      quizQuestions: null == quizQuestions
          ? _self._quizQuestions
          : quizQuestions // ignore: cast_nullable_to_non_nullable
              as List<QuizQuestionModel>,
    ));
  }
}

/// @nodoc
mixin _$LessonConcept {
  String get id;
  String get title;
  String get explanation;
  @JsonKey(name: 'explanation_urdu')
  String? get explanationUrdu;
  @JsonKey(name: 'arabic_example')
  String? get arabicExample;
  @JsonKey(name: 'transliteration')
  String? get transliteration;
  @JsonKey(name: 'translation')
  String? get translation;
  @JsonKey(name: 'pos_group')
  String? get posGroup;
  @JsonKey(name: 'grammar_note')
  String? get grammarNote;
  @JsonKey(name: 'image_url')
  String? get imageUrl;

  /// Create a copy of LessonConcept
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $LessonConceptCopyWith<LessonConcept> get copyWith =>
      _$LessonConceptCopyWithImpl<LessonConcept>(
          this as LessonConcept, _$identity);

  /// Serializes this LessonConcept to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is LessonConcept &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.explanation, explanation) ||
                other.explanation == explanation) &&
            (identical(other.explanationUrdu, explanationUrdu) ||
                other.explanationUrdu == explanationUrdu) &&
            (identical(other.arabicExample, arabicExample) ||
                other.arabicExample == arabicExample) &&
            (identical(other.transliteration, transliteration) ||
                other.transliteration == transliteration) &&
            (identical(other.translation, translation) ||
                other.translation == translation) &&
            (identical(other.posGroup, posGroup) ||
                other.posGroup == posGroup) &&
            (identical(other.grammarNote, grammarNote) ||
                other.grammarNote == grammarNote) &&
            (identical(other.imageUrl, imageUrl) ||
                other.imageUrl == imageUrl));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      title,
      explanation,
      explanationUrdu,
      arabicExample,
      transliteration,
      translation,
      posGroup,
      grammarNote,
      imageUrl);

  @override
  String toString() {
    return 'LessonConcept(id: $id, title: $title, explanation: $explanation, explanationUrdu: $explanationUrdu, arabicExample: $arabicExample, transliteration: $transliteration, translation: $translation, posGroup: $posGroup, grammarNote: $grammarNote, imageUrl: $imageUrl)';
  }
}

/// @nodoc
abstract mixin class $LessonConceptCopyWith<$Res> {
  factory $LessonConceptCopyWith(
          LessonConcept value, $Res Function(LessonConcept) _then) =
      _$LessonConceptCopyWithImpl;
  @useResult
  $Res call(
      {String id,
      String title,
      String explanation,
      @JsonKey(name: 'explanation_urdu') String? explanationUrdu,
      @JsonKey(name: 'arabic_example') String? arabicExample,
      @JsonKey(name: 'transliteration') String? transliteration,
      @JsonKey(name: 'translation') String? translation,
      @JsonKey(name: 'pos_group') String? posGroup,
      @JsonKey(name: 'grammar_note') String? grammarNote,
      @JsonKey(name: 'image_url') String? imageUrl});
}

/// @nodoc
class _$LessonConceptCopyWithImpl<$Res>
    implements $LessonConceptCopyWith<$Res> {
  _$LessonConceptCopyWithImpl(this._self, this._then);

  final LessonConcept _self;
  final $Res Function(LessonConcept) _then;

  /// Create a copy of LessonConcept
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? title = null,
    Object? explanation = null,
    Object? explanationUrdu = freezed,
    Object? arabicExample = freezed,
    Object? transliteration = freezed,
    Object? translation = freezed,
    Object? posGroup = freezed,
    Object? grammarNote = freezed,
    Object? imageUrl = freezed,
  }) {
    return _then(_self.copyWith(
      id: null == id
          ? _self.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _self.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      explanation: null == explanation
          ? _self.explanation
          : explanation // ignore: cast_nullable_to_non_nullable
              as String,
      explanationUrdu: freezed == explanationUrdu
          ? _self.explanationUrdu
          : explanationUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      arabicExample: freezed == arabicExample
          ? _self.arabicExample
          : arabicExample // ignore: cast_nullable_to_non_nullable
              as String?,
      transliteration: freezed == transliteration
          ? _self.transliteration
          : transliteration // ignore: cast_nullable_to_non_nullable
              as String?,
      translation: freezed == translation
          ? _self.translation
          : translation // ignore: cast_nullable_to_non_nullable
              as String?,
      posGroup: freezed == posGroup
          ? _self.posGroup
          : posGroup // ignore: cast_nullable_to_non_nullable
              as String?,
      grammarNote: freezed == grammarNote
          ? _self.grammarNote
          : grammarNote // ignore: cast_nullable_to_non_nullable
              as String?,
      imageUrl: freezed == imageUrl
          ? _self.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// Adds pattern-matching-related methods to [LessonConcept].
extension LessonConceptPatterns on LessonConcept {
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
    TResult Function(_LessonConcept value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _LessonConcept() when $default != null:
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
    TResult Function(_LessonConcept value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonConcept():
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
    TResult? Function(_LessonConcept value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonConcept() when $default != null:
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
            String id,
            String title,
            String explanation,
            @JsonKey(name: 'explanation_urdu') String? explanationUrdu,
            @JsonKey(name: 'arabic_example') String? arabicExample,
            @JsonKey(name: 'transliteration') String? transliteration,
            @JsonKey(name: 'translation') String? translation,
            @JsonKey(name: 'pos_group') String? posGroup,
            @JsonKey(name: 'grammar_note') String? grammarNote,
            @JsonKey(name: 'image_url') String? imageUrl)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _LessonConcept() when $default != null:
        return $default(
            _that.id,
            _that.title,
            _that.explanation,
            _that.explanationUrdu,
            _that.arabicExample,
            _that.transliteration,
            _that.translation,
            _that.posGroup,
            _that.grammarNote,
            _that.imageUrl);
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
            String id,
            String title,
            String explanation,
            @JsonKey(name: 'explanation_urdu') String? explanationUrdu,
            @JsonKey(name: 'arabic_example') String? arabicExample,
            @JsonKey(name: 'transliteration') String? transliteration,
            @JsonKey(name: 'translation') String? translation,
            @JsonKey(name: 'pos_group') String? posGroup,
            @JsonKey(name: 'grammar_note') String? grammarNote,
            @JsonKey(name: 'image_url') String? imageUrl)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonConcept():
        return $default(
            _that.id,
            _that.title,
            _that.explanation,
            _that.explanationUrdu,
            _that.arabicExample,
            _that.transliteration,
            _that.translation,
            _that.posGroup,
            _that.grammarNote,
            _that.imageUrl);
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
            String id,
            String title,
            String explanation,
            @JsonKey(name: 'explanation_urdu') String? explanationUrdu,
            @JsonKey(name: 'arabic_example') String? arabicExample,
            @JsonKey(name: 'transliteration') String? transliteration,
            @JsonKey(name: 'translation') String? translation,
            @JsonKey(name: 'pos_group') String? posGroup,
            @JsonKey(name: 'grammar_note') String? grammarNote,
            @JsonKey(name: 'image_url') String? imageUrl)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonConcept() when $default != null:
        return $default(
            _that.id,
            _that.title,
            _that.explanation,
            _that.explanationUrdu,
            _that.arabicExample,
            _that.transliteration,
            _that.translation,
            _that.posGroup,
            _that.grammarNote,
            _that.imageUrl);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _LessonConcept implements LessonConcept {
  const _LessonConcept(
      {required this.id,
      required this.title,
      required this.explanation,
      @JsonKey(name: 'explanation_urdu') this.explanationUrdu,
      @JsonKey(name: 'arabic_example') this.arabicExample,
      @JsonKey(name: 'transliteration') this.transliteration,
      @JsonKey(name: 'translation') this.translation,
      @JsonKey(name: 'pos_group') this.posGroup,
      @JsonKey(name: 'grammar_note') this.grammarNote,
      @JsonKey(name: 'image_url') this.imageUrl});
  factory _LessonConcept.fromJson(Map<String, dynamic> json) =>
      _$LessonConceptFromJson(json);

  @override
  final String id;
  @override
  final String title;
  @override
  final String explanation;
  @override
  @JsonKey(name: 'explanation_urdu')
  final String? explanationUrdu;
  @override
  @JsonKey(name: 'arabic_example')
  final String? arabicExample;
  @override
  @JsonKey(name: 'transliteration')
  final String? transliteration;
  @override
  @JsonKey(name: 'translation')
  final String? translation;
  @override
  @JsonKey(name: 'pos_group')
  final String? posGroup;
  @override
  @JsonKey(name: 'grammar_note')
  final String? grammarNote;
  @override
  @JsonKey(name: 'image_url')
  final String? imageUrl;

  /// Create a copy of LessonConcept
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$LessonConceptCopyWith<_LessonConcept> get copyWith =>
      __$LessonConceptCopyWithImpl<_LessonConcept>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$LessonConceptToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _LessonConcept &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.explanation, explanation) ||
                other.explanation == explanation) &&
            (identical(other.explanationUrdu, explanationUrdu) ||
                other.explanationUrdu == explanationUrdu) &&
            (identical(other.arabicExample, arabicExample) ||
                other.arabicExample == arabicExample) &&
            (identical(other.transliteration, transliteration) ||
                other.transliteration == transliteration) &&
            (identical(other.translation, translation) ||
                other.translation == translation) &&
            (identical(other.posGroup, posGroup) ||
                other.posGroup == posGroup) &&
            (identical(other.grammarNote, grammarNote) ||
                other.grammarNote == grammarNote) &&
            (identical(other.imageUrl, imageUrl) ||
                other.imageUrl == imageUrl));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      title,
      explanation,
      explanationUrdu,
      arabicExample,
      transliteration,
      translation,
      posGroup,
      grammarNote,
      imageUrl);

  @override
  String toString() {
    return 'LessonConcept(id: $id, title: $title, explanation: $explanation, explanationUrdu: $explanationUrdu, arabicExample: $arabicExample, transliteration: $transliteration, translation: $translation, posGroup: $posGroup, grammarNote: $grammarNote, imageUrl: $imageUrl)';
  }
}

/// @nodoc
abstract mixin class _$LessonConceptCopyWith<$Res>
    implements $LessonConceptCopyWith<$Res> {
  factory _$LessonConceptCopyWith(
          _LessonConcept value, $Res Function(_LessonConcept) _then) =
      __$LessonConceptCopyWithImpl;
  @override
  @useResult
  $Res call(
      {String id,
      String title,
      String explanation,
      @JsonKey(name: 'explanation_urdu') String? explanationUrdu,
      @JsonKey(name: 'arabic_example') String? arabicExample,
      @JsonKey(name: 'transliteration') String? transliteration,
      @JsonKey(name: 'translation') String? translation,
      @JsonKey(name: 'pos_group') String? posGroup,
      @JsonKey(name: 'grammar_note') String? grammarNote,
      @JsonKey(name: 'image_url') String? imageUrl});
}

/// @nodoc
class __$LessonConceptCopyWithImpl<$Res>
    implements _$LessonConceptCopyWith<$Res> {
  __$LessonConceptCopyWithImpl(this._self, this._then);

  final _LessonConcept _self;
  final $Res Function(_LessonConcept) _then;

  /// Create a copy of LessonConcept
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? id = null,
    Object? title = null,
    Object? explanation = null,
    Object? explanationUrdu = freezed,
    Object? arabicExample = freezed,
    Object? transliteration = freezed,
    Object? translation = freezed,
    Object? posGroup = freezed,
    Object? grammarNote = freezed,
    Object? imageUrl = freezed,
  }) {
    return _then(_LessonConcept(
      id: null == id
          ? _self.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _self.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      explanation: null == explanation
          ? _self.explanation
          : explanation // ignore: cast_nullable_to_non_nullable
              as String,
      explanationUrdu: freezed == explanationUrdu
          ? _self.explanationUrdu
          : explanationUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      arabicExample: freezed == arabicExample
          ? _self.arabicExample
          : arabicExample // ignore: cast_nullable_to_non_nullable
              as String?,
      transliteration: freezed == transliteration
          ? _self.transliteration
          : transliteration // ignore: cast_nullable_to_non_nullable
              as String?,
      translation: freezed == translation
          ? _self.translation
          : translation // ignore: cast_nullable_to_non_nullable
              as String?,
      posGroup: freezed == posGroup
          ? _self.posGroup
          : posGroup // ignore: cast_nullable_to_non_nullable
              as String?,
      grammarNote: freezed == grammarNote
          ? _self.grammarNote
          : grammarNote // ignore: cast_nullable_to_non_nullable
              as String?,
      imageUrl: freezed == imageUrl
          ? _self.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
mixin _$QuizQuestionModel {
  String get id;
  QuizType get type;
  String get question;
  @JsonKey(name: 'question_arabic')
  String? get questionArabic;
  @JsonKey(name: 'options')
  List<String> get options;
  @JsonKey(name: 'correct_answer')
  String? get correctAnswer;
  @JsonKey(name: 'match_pairs')
  List<MatchPair>? get matchPairs;
  @JsonKey(name: 'blank_answer')
  String? get blankAnswer;
  @JsonKey(name: 'explanation')
  String? get explanation;
  @JsonKey(name: 'hint')
  String? get hint;

  /// Create a copy of QuizQuestionModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $QuizQuestionModelCopyWith<QuizQuestionModel> get copyWith =>
      _$QuizQuestionModelCopyWithImpl<QuizQuestionModel>(
          this as QuizQuestionModel, _$identity);

  /// Serializes this QuizQuestionModel to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is QuizQuestionModel &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.question, question) ||
                other.question == question) &&
            (identical(other.questionArabic, questionArabic) ||
                other.questionArabic == questionArabic) &&
            const DeepCollectionEquality().equals(other.options, options) &&
            (identical(other.correctAnswer, correctAnswer) ||
                other.correctAnswer == correctAnswer) &&
            const DeepCollectionEquality()
                .equals(other.matchPairs, matchPairs) &&
            (identical(other.blankAnswer, blankAnswer) ||
                other.blankAnswer == blankAnswer) &&
            (identical(other.explanation, explanation) ||
                other.explanation == explanation) &&
            (identical(other.hint, hint) || other.hint == hint));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      type,
      question,
      questionArabic,
      const DeepCollectionEquality().hash(options),
      correctAnswer,
      const DeepCollectionEquality().hash(matchPairs),
      blankAnswer,
      explanation,
      hint);

  @override
  String toString() {
    return 'QuizQuestionModel(id: $id, type: $type, question: $question, questionArabic: $questionArabic, options: $options, correctAnswer: $correctAnswer, matchPairs: $matchPairs, blankAnswer: $blankAnswer, explanation: $explanation, hint: $hint)';
  }
}

/// @nodoc
abstract mixin class $QuizQuestionModelCopyWith<$Res> {
  factory $QuizQuestionModelCopyWith(
          QuizQuestionModel value, $Res Function(QuizQuestionModel) _then) =
      _$QuizQuestionModelCopyWithImpl;
  @useResult
  $Res call(
      {String id,
      QuizType type,
      String question,
      @JsonKey(name: 'question_arabic') String? questionArabic,
      @JsonKey(name: 'options') List<String> options,
      @JsonKey(name: 'correct_answer') String? correctAnswer,
      @JsonKey(name: 'match_pairs') List<MatchPair>? matchPairs,
      @JsonKey(name: 'blank_answer') String? blankAnswer,
      @JsonKey(name: 'explanation') String? explanation,
      @JsonKey(name: 'hint') String? hint});
}

/// @nodoc
class _$QuizQuestionModelCopyWithImpl<$Res>
    implements $QuizQuestionModelCopyWith<$Res> {
  _$QuizQuestionModelCopyWithImpl(this._self, this._then);

  final QuizQuestionModel _self;
  final $Res Function(QuizQuestionModel) _then;

  /// Create a copy of QuizQuestionModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? type = null,
    Object? question = null,
    Object? questionArabic = freezed,
    Object? options = null,
    Object? correctAnswer = freezed,
    Object? matchPairs = freezed,
    Object? blankAnswer = freezed,
    Object? explanation = freezed,
    Object? hint = freezed,
  }) {
    return _then(_self.copyWith(
      id: null == id
          ? _self.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _self.type
          : type // ignore: cast_nullable_to_non_nullable
              as QuizType,
      question: null == question
          ? _self.question
          : question // ignore: cast_nullable_to_non_nullable
              as String,
      questionArabic: freezed == questionArabic
          ? _self.questionArabic
          : questionArabic // ignore: cast_nullable_to_non_nullable
              as String?,
      options: null == options
          ? _self.options
          : options // ignore: cast_nullable_to_non_nullable
              as List<String>,
      correctAnswer: freezed == correctAnswer
          ? _self.correctAnswer
          : correctAnswer // ignore: cast_nullable_to_non_nullable
              as String?,
      matchPairs: freezed == matchPairs
          ? _self.matchPairs
          : matchPairs // ignore: cast_nullable_to_non_nullable
              as List<MatchPair>?,
      blankAnswer: freezed == blankAnswer
          ? _self.blankAnswer
          : blankAnswer // ignore: cast_nullable_to_non_nullable
              as String?,
      explanation: freezed == explanation
          ? _self.explanation
          : explanation // ignore: cast_nullable_to_non_nullable
              as String?,
      hint: freezed == hint
          ? _self.hint
          : hint // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// Adds pattern-matching-related methods to [QuizQuestionModel].
extension QuizQuestionModelPatterns on QuizQuestionModel {
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
    TResult Function(_QuizQuestionModel value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _QuizQuestionModel() when $default != null:
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
    TResult Function(_QuizQuestionModel value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _QuizQuestionModel():
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
    TResult? Function(_QuizQuestionModel value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _QuizQuestionModel() when $default != null:
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
            String id,
            QuizType type,
            String question,
            @JsonKey(name: 'question_arabic') String? questionArabic,
            @JsonKey(name: 'options') List<String> options,
            @JsonKey(name: 'correct_answer') String? correctAnswer,
            @JsonKey(name: 'match_pairs') List<MatchPair>? matchPairs,
            @JsonKey(name: 'blank_answer') String? blankAnswer,
            @JsonKey(name: 'explanation') String? explanation,
            @JsonKey(name: 'hint') String? hint)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _QuizQuestionModel() when $default != null:
        return $default(
            _that.id,
            _that.type,
            _that.question,
            _that.questionArabic,
            _that.options,
            _that.correctAnswer,
            _that.matchPairs,
            _that.blankAnswer,
            _that.explanation,
            _that.hint);
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
            String id,
            QuizType type,
            String question,
            @JsonKey(name: 'question_arabic') String? questionArabic,
            @JsonKey(name: 'options') List<String> options,
            @JsonKey(name: 'correct_answer') String? correctAnswer,
            @JsonKey(name: 'match_pairs') List<MatchPair>? matchPairs,
            @JsonKey(name: 'blank_answer') String? blankAnswer,
            @JsonKey(name: 'explanation') String? explanation,
            @JsonKey(name: 'hint') String? hint)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _QuizQuestionModel():
        return $default(
            _that.id,
            _that.type,
            _that.question,
            _that.questionArabic,
            _that.options,
            _that.correctAnswer,
            _that.matchPairs,
            _that.blankAnswer,
            _that.explanation,
            _that.hint);
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
            String id,
            QuizType type,
            String question,
            @JsonKey(name: 'question_arabic') String? questionArabic,
            @JsonKey(name: 'options') List<String> options,
            @JsonKey(name: 'correct_answer') String? correctAnswer,
            @JsonKey(name: 'match_pairs') List<MatchPair>? matchPairs,
            @JsonKey(name: 'blank_answer') String? blankAnswer,
            @JsonKey(name: 'explanation') String? explanation,
            @JsonKey(name: 'hint') String? hint)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _QuizQuestionModel() when $default != null:
        return $default(
            _that.id,
            _that.type,
            _that.question,
            _that.questionArabic,
            _that.options,
            _that.correctAnswer,
            _that.matchPairs,
            _that.blankAnswer,
            _that.explanation,
            _that.hint);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _QuizQuestionModel implements QuizQuestionModel {
  const _QuizQuestionModel(
      {required this.id,
      required this.type,
      required this.question,
      @JsonKey(name: 'question_arabic') this.questionArabic,
      @JsonKey(name: 'options') final List<String> options = const [],
      @JsonKey(name: 'correct_answer') this.correctAnswer,
      @JsonKey(name: 'match_pairs') final List<MatchPair>? matchPairs,
      @JsonKey(name: 'blank_answer') this.blankAnswer,
      @JsonKey(name: 'explanation') this.explanation,
      @JsonKey(name: 'hint') this.hint})
      : _options = options,
        _matchPairs = matchPairs;
  factory _QuizQuestionModel.fromJson(Map<String, dynamic> json) =>
      _$QuizQuestionModelFromJson(json);

  @override
  final String id;
  @override
  final QuizType type;
  @override
  final String question;
  @override
  @JsonKey(name: 'question_arabic')
  final String? questionArabic;
  final List<String> _options;
  @override
  @JsonKey(name: 'options')
  List<String> get options {
    if (_options is EqualUnmodifiableListView) return _options;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_options);
  }

  @override
  @JsonKey(name: 'correct_answer')
  final String? correctAnswer;
  final List<MatchPair>? _matchPairs;
  @override
  @JsonKey(name: 'match_pairs')
  List<MatchPair>? get matchPairs {
    final value = _matchPairs;
    if (value == null) return null;
    if (_matchPairs is EqualUnmodifiableListView) return _matchPairs;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  @JsonKey(name: 'blank_answer')
  final String? blankAnswer;
  @override
  @JsonKey(name: 'explanation')
  final String? explanation;
  @override
  @JsonKey(name: 'hint')
  final String? hint;

  /// Create a copy of QuizQuestionModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$QuizQuestionModelCopyWith<_QuizQuestionModel> get copyWith =>
      __$QuizQuestionModelCopyWithImpl<_QuizQuestionModel>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$QuizQuestionModelToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _QuizQuestionModel &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.question, question) ||
                other.question == question) &&
            (identical(other.questionArabic, questionArabic) ||
                other.questionArabic == questionArabic) &&
            const DeepCollectionEquality().equals(other._options, _options) &&
            (identical(other.correctAnswer, correctAnswer) ||
                other.correctAnswer == correctAnswer) &&
            const DeepCollectionEquality()
                .equals(other._matchPairs, _matchPairs) &&
            (identical(other.blankAnswer, blankAnswer) ||
                other.blankAnswer == blankAnswer) &&
            (identical(other.explanation, explanation) ||
                other.explanation == explanation) &&
            (identical(other.hint, hint) || other.hint == hint));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      type,
      question,
      questionArabic,
      const DeepCollectionEquality().hash(_options),
      correctAnswer,
      const DeepCollectionEquality().hash(_matchPairs),
      blankAnswer,
      explanation,
      hint);

  @override
  String toString() {
    return 'QuizQuestionModel(id: $id, type: $type, question: $question, questionArabic: $questionArabic, options: $options, correctAnswer: $correctAnswer, matchPairs: $matchPairs, blankAnswer: $blankAnswer, explanation: $explanation, hint: $hint)';
  }
}

/// @nodoc
abstract mixin class _$QuizQuestionModelCopyWith<$Res>
    implements $QuizQuestionModelCopyWith<$Res> {
  factory _$QuizQuestionModelCopyWith(
          _QuizQuestionModel value, $Res Function(_QuizQuestionModel) _then) =
      __$QuizQuestionModelCopyWithImpl;
  @override
  @useResult
  $Res call(
      {String id,
      QuizType type,
      String question,
      @JsonKey(name: 'question_arabic') String? questionArabic,
      @JsonKey(name: 'options') List<String> options,
      @JsonKey(name: 'correct_answer') String? correctAnswer,
      @JsonKey(name: 'match_pairs') List<MatchPair>? matchPairs,
      @JsonKey(name: 'blank_answer') String? blankAnswer,
      @JsonKey(name: 'explanation') String? explanation,
      @JsonKey(name: 'hint') String? hint});
}

/// @nodoc
class __$QuizQuestionModelCopyWithImpl<$Res>
    implements _$QuizQuestionModelCopyWith<$Res> {
  __$QuizQuestionModelCopyWithImpl(this._self, this._then);

  final _QuizQuestionModel _self;
  final $Res Function(_QuizQuestionModel) _then;

  /// Create a copy of QuizQuestionModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? id = null,
    Object? type = null,
    Object? question = null,
    Object? questionArabic = freezed,
    Object? options = null,
    Object? correctAnswer = freezed,
    Object? matchPairs = freezed,
    Object? blankAnswer = freezed,
    Object? explanation = freezed,
    Object? hint = freezed,
  }) {
    return _then(_QuizQuestionModel(
      id: null == id
          ? _self.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _self.type
          : type // ignore: cast_nullable_to_non_nullable
              as QuizType,
      question: null == question
          ? _self.question
          : question // ignore: cast_nullable_to_non_nullable
              as String,
      questionArabic: freezed == questionArabic
          ? _self.questionArabic
          : questionArabic // ignore: cast_nullable_to_non_nullable
              as String?,
      options: null == options
          ? _self._options
          : options // ignore: cast_nullable_to_non_nullable
              as List<String>,
      correctAnswer: freezed == correctAnswer
          ? _self.correctAnswer
          : correctAnswer // ignore: cast_nullable_to_non_nullable
              as String?,
      matchPairs: freezed == matchPairs
          ? _self._matchPairs
          : matchPairs // ignore: cast_nullable_to_non_nullable
              as List<MatchPair>?,
      blankAnswer: freezed == blankAnswer
          ? _self.blankAnswer
          : blankAnswer // ignore: cast_nullable_to_non_nullable
              as String?,
      explanation: freezed == explanation
          ? _self.explanation
          : explanation // ignore: cast_nullable_to_non_nullable
              as String?,
      hint: freezed == hint
          ? _self.hint
          : hint // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
mixin _$MatchPair {
  String get left;
  String get right;

  /// Create a copy of MatchPair
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $MatchPairCopyWith<MatchPair> get copyWith =>
      _$MatchPairCopyWithImpl<MatchPair>(this as MatchPair, _$identity);

  /// Serializes this MatchPair to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is MatchPair &&
            (identical(other.left, left) || other.left == left) &&
            (identical(other.right, right) || other.right == right));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, left, right);

  @override
  String toString() {
    return 'MatchPair(left: $left, right: $right)';
  }
}

/// @nodoc
abstract mixin class $MatchPairCopyWith<$Res> {
  factory $MatchPairCopyWith(MatchPair value, $Res Function(MatchPair) _then) =
      _$MatchPairCopyWithImpl;
  @useResult
  $Res call({String left, String right});
}

/// @nodoc
class _$MatchPairCopyWithImpl<$Res> implements $MatchPairCopyWith<$Res> {
  _$MatchPairCopyWithImpl(this._self, this._then);

  final MatchPair _self;
  final $Res Function(MatchPair) _then;

  /// Create a copy of MatchPair
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? left = null,
    Object? right = null,
  }) {
    return _then(_self.copyWith(
      left: null == left
          ? _self.left
          : left // ignore: cast_nullable_to_non_nullable
              as String,
      right: null == right
          ? _self.right
          : right // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// Adds pattern-matching-related methods to [MatchPair].
extension MatchPairPatterns on MatchPair {
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
    TResult Function(_MatchPair value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _MatchPair() when $default != null:
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
    TResult Function(_MatchPair value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _MatchPair():
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
    TResult? Function(_MatchPair value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _MatchPair() when $default != null:
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
    TResult Function(String left, String right)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _MatchPair() when $default != null:
        return $default(_that.left, _that.right);
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
    TResult Function(String left, String right) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _MatchPair():
        return $default(_that.left, _that.right);
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
    TResult? Function(String left, String right)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _MatchPair() when $default != null:
        return $default(_that.left, _that.right);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _MatchPair implements MatchPair {
  const _MatchPair({required this.left, required this.right});
  factory _MatchPair.fromJson(Map<String, dynamic> json) =>
      _$MatchPairFromJson(json);

  @override
  final String left;
  @override
  final String right;

  /// Create a copy of MatchPair
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$MatchPairCopyWith<_MatchPair> get copyWith =>
      __$MatchPairCopyWithImpl<_MatchPair>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$MatchPairToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _MatchPair &&
            (identical(other.left, left) || other.left == left) &&
            (identical(other.right, right) || other.right == right));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, left, right);

  @override
  String toString() {
    return 'MatchPair(left: $left, right: $right)';
  }
}

/// @nodoc
abstract mixin class _$MatchPairCopyWith<$Res>
    implements $MatchPairCopyWith<$Res> {
  factory _$MatchPairCopyWith(
          _MatchPair value, $Res Function(_MatchPair) _then) =
      __$MatchPairCopyWithImpl;
  @override
  @useResult
  $Res call({String left, String right});
}

/// @nodoc
class __$MatchPairCopyWithImpl<$Res> implements _$MatchPairCopyWith<$Res> {
  __$MatchPairCopyWithImpl(this._self, this._then);

  final _MatchPair _self;
  final $Res Function(_MatchPair) _then;

  /// Create a copy of MatchPair
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? left = null,
    Object? right = null,
  }) {
    return _then(_MatchPair(
      left: null == left
          ? _self.left
          : left // ignore: cast_nullable_to_non_nullable
              as String,
      right: null == right
          ? _self.right
          : right // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

// dart format on
