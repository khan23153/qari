// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'user_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$UserModel {
  @JsonKey(name: 'user_id')
  String get userId;
  @JsonKey(name: 'email')
  String? get email;
  @JsonKey(name: 'display_name')
  String? get displayName;
  @JsonKey(name: 'avatar_url')
  String? get avatarUrl;
  @JsonKey(name: 'selected_language')
  String get selectedLanguage;
  @JsonKey(name: 'learning_path')
  String get learningPath;
  @JsonKey(name: 'total_xp')
  int get totalXp;
  @JsonKey(name: 'current_streak')
  int get currentStreak;
  @JsonKey(name: 'longest_streak')
  int get longestStreak;
  @JsonKey(name: 'daily_goal')
  int get dailyGoal;
  @JsonKey(name: 'lessons_completed')
  int get lessonsCompleted;
  @JsonKey(name: 'ayahs_read')
  int get ayahsRead;
  @JsonKey(name: 'flashcards_reviewed')
  int get flashcardsReviewed;
  @JsonKey(name: 'recitation_sessions')
  int get recitationSessions;
  @JsonKey(name: 'created_at')
  DateTime get createdAt;

  /// Create a copy of UserModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $UserModelCopyWith<UserModel> get copyWith =>
      _$UserModelCopyWithImpl<UserModel>(this as UserModel, _$identity);

  /// Serializes this UserModel to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is UserModel &&
            (identical(other.userId, userId) || other.userId == userId) &&
            (identical(other.email, email) || other.email == email) &&
            (identical(other.displayName, displayName) ||
                other.displayName == displayName) &&
            (identical(other.avatarUrl, avatarUrl) ||
                other.avatarUrl == avatarUrl) &&
            (identical(other.selectedLanguage, selectedLanguage) ||
                other.selectedLanguage == selectedLanguage) &&
            (identical(other.learningPath, learningPath) ||
                other.learningPath == learningPath) &&
            (identical(other.totalXp, totalXp) || other.totalXp == totalXp) &&
            (identical(other.currentStreak, currentStreak) ||
                other.currentStreak == currentStreak) &&
            (identical(other.longestStreak, longestStreak) ||
                other.longestStreak == longestStreak) &&
            (identical(other.dailyGoal, dailyGoal) ||
                other.dailyGoal == dailyGoal) &&
            (identical(other.lessonsCompleted, lessonsCompleted) ||
                other.lessonsCompleted == lessonsCompleted) &&
            (identical(other.ayahsRead, ayahsRead) ||
                other.ayahsRead == ayahsRead) &&
            (identical(other.flashcardsReviewed, flashcardsReviewed) ||
                other.flashcardsReviewed == flashcardsReviewed) &&
            (identical(other.recitationSessions, recitationSessions) ||
                other.recitationSessions == recitationSessions) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      userId,
      email,
      displayName,
      avatarUrl,
      selectedLanguage,
      learningPath,
      totalXp,
      currentStreak,
      longestStreak,
      dailyGoal,
      lessonsCompleted,
      ayahsRead,
      flashcardsReviewed,
      recitationSessions,
      createdAt);

  @override
  String toString() {
    return 'UserModel(userId: $userId, email: $email, displayName: $displayName, avatarUrl: $avatarUrl, selectedLanguage: $selectedLanguage, learningPath: $learningPath, totalXp: $totalXp, currentStreak: $currentStreak, longestStreak: $longestStreak, dailyGoal: $dailyGoal, lessonsCompleted: $lessonsCompleted, ayahsRead: $ayahsRead, flashcardsReviewed: $flashcardsReviewed, recitationSessions: $recitationSessions, createdAt: $createdAt)';
  }
}

/// @nodoc
abstract mixin class $UserModelCopyWith<$Res> {
  factory $UserModelCopyWith(UserModel value, $Res Function(UserModel) _then) =
      _$UserModelCopyWithImpl;
  @useResult
  $Res call(
      {@JsonKey(name: 'user_id') String userId,
      @JsonKey(name: 'email') String? email,
      @JsonKey(name: 'display_name') String? displayName,
      @JsonKey(name: 'avatar_url') String? avatarUrl,
      @JsonKey(name: 'selected_language') String selectedLanguage,
      @JsonKey(name: 'learning_path') String learningPath,
      @JsonKey(name: 'total_xp') int totalXp,
      @JsonKey(name: 'current_streak') int currentStreak,
      @JsonKey(name: 'longest_streak') int longestStreak,
      @JsonKey(name: 'daily_goal') int dailyGoal,
      @JsonKey(name: 'lessons_completed') int lessonsCompleted,
      @JsonKey(name: 'ayahs_read') int ayahsRead,
      @JsonKey(name: 'flashcards_reviewed') int flashcardsReviewed,
      @JsonKey(name: 'recitation_sessions') int recitationSessions,
      @JsonKey(name: 'created_at') DateTime createdAt});
}

/// @nodoc
class _$UserModelCopyWithImpl<$Res> implements $UserModelCopyWith<$Res> {
  _$UserModelCopyWithImpl(this._self, this._then);

  final UserModel _self;
  final $Res Function(UserModel) _then;

  /// Create a copy of UserModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? userId = null,
    Object? email = freezed,
    Object? displayName = freezed,
    Object? avatarUrl = freezed,
    Object? selectedLanguage = null,
    Object? learningPath = null,
    Object? totalXp = null,
    Object? currentStreak = null,
    Object? longestStreak = null,
    Object? dailyGoal = null,
    Object? lessonsCompleted = null,
    Object? ayahsRead = null,
    Object? flashcardsReviewed = null,
    Object? recitationSessions = null,
    Object? createdAt = null,
  }) {
    return _then(_self.copyWith(
      userId: null == userId
          ? _self.userId
          : userId // ignore: cast_nullable_to_non_nullable
              as String,
      email: freezed == email
          ? _self.email
          : email // ignore: cast_nullable_to_non_nullable
              as String?,
      displayName: freezed == displayName
          ? _self.displayName
          : displayName // ignore: cast_nullable_to_non_nullable
              as String?,
      avatarUrl: freezed == avatarUrl
          ? _self.avatarUrl
          : avatarUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      selectedLanguage: null == selectedLanguage
          ? _self.selectedLanguage
          : selectedLanguage // ignore: cast_nullable_to_non_nullable
              as String,
      learningPath: null == learningPath
          ? _self.learningPath
          : learningPath // ignore: cast_nullable_to_non_nullable
              as String,
      totalXp: null == totalXp
          ? _self.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      currentStreak: null == currentStreak
          ? _self.currentStreak
          : currentStreak // ignore: cast_nullable_to_non_nullable
              as int,
      longestStreak: null == longestStreak
          ? _self.longestStreak
          : longestStreak // ignore: cast_nullable_to_non_nullable
              as int,
      dailyGoal: null == dailyGoal
          ? _self.dailyGoal
          : dailyGoal // ignore: cast_nullable_to_non_nullable
              as int,
      lessonsCompleted: null == lessonsCompleted
          ? _self.lessonsCompleted
          : lessonsCompleted // ignore: cast_nullable_to_non_nullable
              as int,
      ayahsRead: null == ayahsRead
          ? _self.ayahsRead
          : ayahsRead // ignore: cast_nullable_to_non_nullable
              as int,
      flashcardsReviewed: null == flashcardsReviewed
          ? _self.flashcardsReviewed
          : flashcardsReviewed // ignore: cast_nullable_to_non_nullable
              as int,
      recitationSessions: null == recitationSessions
          ? _self.recitationSessions
          : recitationSessions // ignore: cast_nullable_to_non_nullable
              as int,
      createdAt: null == createdAt
          ? _self.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// Adds pattern-matching-related methods to [UserModel].
extension UserModelPatterns on UserModel {
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
    TResult Function(_UserModel value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _UserModel() when $default != null:
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
    TResult Function(_UserModel value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _UserModel():
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
    TResult? Function(_UserModel value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _UserModel() when $default != null:
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
            @JsonKey(name: 'user_id') String userId,
            @JsonKey(name: 'email') String? email,
            @JsonKey(name: 'display_name') String? displayName,
            @JsonKey(name: 'avatar_url') String? avatarUrl,
            @JsonKey(name: 'selected_language') String selectedLanguage,
            @JsonKey(name: 'learning_path') String learningPath,
            @JsonKey(name: 'total_xp') int totalXp,
            @JsonKey(name: 'current_streak') int currentStreak,
            @JsonKey(name: 'longest_streak') int longestStreak,
            @JsonKey(name: 'daily_goal') int dailyGoal,
            @JsonKey(name: 'lessons_completed') int lessonsCompleted,
            @JsonKey(name: 'ayahs_read') int ayahsRead,
            @JsonKey(name: 'flashcards_reviewed') int flashcardsReviewed,
            @JsonKey(name: 'recitation_sessions') int recitationSessions,
            @JsonKey(name: 'created_at') DateTime createdAt)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _UserModel() when $default != null:
        return $default(
            _that.userId,
            _that.email,
            _that.displayName,
            _that.avatarUrl,
            _that.selectedLanguage,
            _that.learningPath,
            _that.totalXp,
            _that.currentStreak,
            _that.longestStreak,
            _that.dailyGoal,
            _that.lessonsCompleted,
            _that.ayahsRead,
            _that.flashcardsReviewed,
            _that.recitationSessions,
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
            @JsonKey(name: 'user_id') String userId,
            @JsonKey(name: 'email') String? email,
            @JsonKey(name: 'display_name') String? displayName,
            @JsonKey(name: 'avatar_url') String? avatarUrl,
            @JsonKey(name: 'selected_language') String selectedLanguage,
            @JsonKey(name: 'learning_path') String learningPath,
            @JsonKey(name: 'total_xp') int totalXp,
            @JsonKey(name: 'current_streak') int currentStreak,
            @JsonKey(name: 'longest_streak') int longestStreak,
            @JsonKey(name: 'daily_goal') int dailyGoal,
            @JsonKey(name: 'lessons_completed') int lessonsCompleted,
            @JsonKey(name: 'ayahs_read') int ayahsRead,
            @JsonKey(name: 'flashcards_reviewed') int flashcardsReviewed,
            @JsonKey(name: 'recitation_sessions') int recitationSessions,
            @JsonKey(name: 'created_at') DateTime createdAt)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _UserModel():
        return $default(
            _that.userId,
            _that.email,
            _that.displayName,
            _that.avatarUrl,
            _that.selectedLanguage,
            _that.learningPath,
            _that.totalXp,
            _that.currentStreak,
            _that.longestStreak,
            _that.dailyGoal,
            _that.lessonsCompleted,
            _that.ayahsRead,
            _that.flashcardsReviewed,
            _that.recitationSessions,
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
            @JsonKey(name: 'user_id') String userId,
            @JsonKey(name: 'email') String? email,
            @JsonKey(name: 'display_name') String? displayName,
            @JsonKey(name: 'avatar_url') String? avatarUrl,
            @JsonKey(name: 'selected_language') String selectedLanguage,
            @JsonKey(name: 'learning_path') String learningPath,
            @JsonKey(name: 'total_xp') int totalXp,
            @JsonKey(name: 'current_streak') int currentStreak,
            @JsonKey(name: 'longest_streak') int longestStreak,
            @JsonKey(name: 'daily_goal') int dailyGoal,
            @JsonKey(name: 'lessons_completed') int lessonsCompleted,
            @JsonKey(name: 'ayahs_read') int ayahsRead,
            @JsonKey(name: 'flashcards_reviewed') int flashcardsReviewed,
            @JsonKey(name: 'recitation_sessions') int recitationSessions,
            @JsonKey(name: 'created_at') DateTime createdAt)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _UserModel() when $default != null:
        return $default(
            _that.userId,
            _that.email,
            _that.displayName,
            _that.avatarUrl,
            _that.selectedLanguage,
            _that.learningPath,
            _that.totalXp,
            _that.currentStreak,
            _that.longestStreak,
            _that.dailyGoal,
            _that.lessonsCompleted,
            _that.ayahsRead,
            _that.flashcardsReviewed,
            _that.recitationSessions,
            _that.createdAt);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _UserModel implements UserModel {
  const _UserModel(
      {@JsonKey(name: 'user_id') required this.userId,
      @JsonKey(name: 'email') this.email,
      @JsonKey(name: 'display_name') this.displayName,
      @JsonKey(name: 'avatar_url') this.avatarUrl,
      @JsonKey(name: 'selected_language') this.selectedLanguage = 'en',
      @JsonKey(name: 'learning_path') this.learningPath = 'foundation',
      @JsonKey(name: 'total_xp') this.totalXp = 0,
      @JsonKey(name: 'current_streak') this.currentStreak = 0,
      @JsonKey(name: 'longest_streak') this.longestStreak = 0,
      @JsonKey(name: 'daily_goal') this.dailyGoal = 5,
      @JsonKey(name: 'lessons_completed') this.lessonsCompleted = 0,
      @JsonKey(name: 'ayahs_read') this.ayahsRead = 0,
      @JsonKey(name: 'flashcards_reviewed') this.flashcardsReviewed = 0,
      @JsonKey(name: 'recitation_sessions') this.recitationSessions = 0,
      @JsonKey(name: 'created_at') required this.createdAt});
  factory _UserModel.fromJson(Map<String, dynamic> json) =>
      _$UserModelFromJson(json);

  @override
  @JsonKey(name: 'user_id')
  final String userId;
  @override
  @JsonKey(name: 'email')
  final String? email;
  @override
  @JsonKey(name: 'display_name')
  final String? displayName;
  @override
  @JsonKey(name: 'avatar_url')
  final String? avatarUrl;
  @override
  @JsonKey(name: 'selected_language')
  final String selectedLanguage;
  @override
  @JsonKey(name: 'learning_path')
  final String learningPath;
  @override
  @JsonKey(name: 'total_xp')
  final int totalXp;
  @override
  @JsonKey(name: 'current_streak')
  final int currentStreak;
  @override
  @JsonKey(name: 'longest_streak')
  final int longestStreak;
  @override
  @JsonKey(name: 'daily_goal')
  final int dailyGoal;
  @override
  @JsonKey(name: 'lessons_completed')
  final int lessonsCompleted;
  @override
  @JsonKey(name: 'ayahs_read')
  final int ayahsRead;
  @override
  @JsonKey(name: 'flashcards_reviewed')
  final int flashcardsReviewed;
  @override
  @JsonKey(name: 'recitation_sessions')
  final int recitationSessions;
  @override
  @JsonKey(name: 'created_at')
  final DateTime createdAt;

  /// Create a copy of UserModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$UserModelCopyWith<_UserModel> get copyWith =>
      __$UserModelCopyWithImpl<_UserModel>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$UserModelToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _UserModel &&
            (identical(other.userId, userId) || other.userId == userId) &&
            (identical(other.email, email) || other.email == email) &&
            (identical(other.displayName, displayName) ||
                other.displayName == displayName) &&
            (identical(other.avatarUrl, avatarUrl) ||
                other.avatarUrl == avatarUrl) &&
            (identical(other.selectedLanguage, selectedLanguage) ||
                other.selectedLanguage == selectedLanguage) &&
            (identical(other.learningPath, learningPath) ||
                other.learningPath == learningPath) &&
            (identical(other.totalXp, totalXp) || other.totalXp == totalXp) &&
            (identical(other.currentStreak, currentStreak) ||
                other.currentStreak == currentStreak) &&
            (identical(other.longestStreak, longestStreak) ||
                other.longestStreak == longestStreak) &&
            (identical(other.dailyGoal, dailyGoal) ||
                other.dailyGoal == dailyGoal) &&
            (identical(other.lessonsCompleted, lessonsCompleted) ||
                other.lessonsCompleted == lessonsCompleted) &&
            (identical(other.ayahsRead, ayahsRead) ||
                other.ayahsRead == ayahsRead) &&
            (identical(other.flashcardsReviewed, flashcardsReviewed) ||
                other.flashcardsReviewed == flashcardsReviewed) &&
            (identical(other.recitationSessions, recitationSessions) ||
                other.recitationSessions == recitationSessions) &&
            (identical(other.createdAt, createdAt) ||
                other.createdAt == createdAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      userId,
      email,
      displayName,
      avatarUrl,
      selectedLanguage,
      learningPath,
      totalXp,
      currentStreak,
      longestStreak,
      dailyGoal,
      lessonsCompleted,
      ayahsRead,
      flashcardsReviewed,
      recitationSessions,
      createdAt);

  @override
  String toString() {
    return 'UserModel(userId: $userId, email: $email, displayName: $displayName, avatarUrl: $avatarUrl, selectedLanguage: $selectedLanguage, learningPath: $learningPath, totalXp: $totalXp, currentStreak: $currentStreak, longestStreak: $longestStreak, dailyGoal: $dailyGoal, lessonsCompleted: $lessonsCompleted, ayahsRead: $ayahsRead, flashcardsReviewed: $flashcardsReviewed, recitationSessions: $recitationSessions, createdAt: $createdAt)';
  }
}

/// @nodoc
abstract mixin class _$UserModelCopyWith<$Res>
    implements $UserModelCopyWith<$Res> {
  factory _$UserModelCopyWith(
          _UserModel value, $Res Function(_UserModel) _then) =
      __$UserModelCopyWithImpl;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'user_id') String userId,
      @JsonKey(name: 'email') String? email,
      @JsonKey(name: 'display_name') String? displayName,
      @JsonKey(name: 'avatar_url') String? avatarUrl,
      @JsonKey(name: 'selected_language') String selectedLanguage,
      @JsonKey(name: 'learning_path') String learningPath,
      @JsonKey(name: 'total_xp') int totalXp,
      @JsonKey(name: 'current_streak') int currentStreak,
      @JsonKey(name: 'longest_streak') int longestStreak,
      @JsonKey(name: 'daily_goal') int dailyGoal,
      @JsonKey(name: 'lessons_completed') int lessonsCompleted,
      @JsonKey(name: 'ayahs_read') int ayahsRead,
      @JsonKey(name: 'flashcards_reviewed') int flashcardsReviewed,
      @JsonKey(name: 'recitation_sessions') int recitationSessions,
      @JsonKey(name: 'created_at') DateTime createdAt});
}

/// @nodoc
class __$UserModelCopyWithImpl<$Res> implements _$UserModelCopyWith<$Res> {
  __$UserModelCopyWithImpl(this._self, this._then);

  final _UserModel _self;
  final $Res Function(_UserModel) _then;

  /// Create a copy of UserModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? userId = null,
    Object? email = freezed,
    Object? displayName = freezed,
    Object? avatarUrl = freezed,
    Object? selectedLanguage = null,
    Object? learningPath = null,
    Object? totalXp = null,
    Object? currentStreak = null,
    Object? longestStreak = null,
    Object? dailyGoal = null,
    Object? lessonsCompleted = null,
    Object? ayahsRead = null,
    Object? flashcardsReviewed = null,
    Object? recitationSessions = null,
    Object? createdAt = null,
  }) {
    return _then(_UserModel(
      userId: null == userId
          ? _self.userId
          : userId // ignore: cast_nullable_to_non_nullable
              as String,
      email: freezed == email
          ? _self.email
          : email // ignore: cast_nullable_to_non_nullable
              as String?,
      displayName: freezed == displayName
          ? _self.displayName
          : displayName // ignore: cast_nullable_to_non_nullable
              as String?,
      avatarUrl: freezed == avatarUrl
          ? _self.avatarUrl
          : avatarUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      selectedLanguage: null == selectedLanguage
          ? _self.selectedLanguage
          : selectedLanguage // ignore: cast_nullable_to_non_nullable
              as String,
      learningPath: null == learningPath
          ? _self.learningPath
          : learningPath // ignore: cast_nullable_to_non_nullable
              as String,
      totalXp: null == totalXp
          ? _self.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      currentStreak: null == currentStreak
          ? _self.currentStreak
          : currentStreak // ignore: cast_nullable_to_non_nullable
              as int,
      longestStreak: null == longestStreak
          ? _self.longestStreak
          : longestStreak // ignore: cast_nullable_to_non_nullable
              as int,
      dailyGoal: null == dailyGoal
          ? _self.dailyGoal
          : dailyGoal // ignore: cast_nullable_to_non_nullable
              as int,
      lessonsCompleted: null == lessonsCompleted
          ? _self.lessonsCompleted
          : lessonsCompleted // ignore: cast_nullable_to_non_nullable
              as int,
      ayahsRead: null == ayahsRead
          ? _self.ayahsRead
          : ayahsRead // ignore: cast_nullable_to_non_nullable
              as int,
      flashcardsReviewed: null == flashcardsReviewed
          ? _self.flashcardsReviewed
          : flashcardsReviewed // ignore: cast_nullable_to_non_nullable
              as int,
      recitationSessions: null == recitationSessions
          ? _self.recitationSessions
          : recitationSessions // ignore: cast_nullable_to_non_nullable
              as int,
      createdAt: null == createdAt
          ? _self.createdAt
          : createdAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// @nodoc
mixin _$HomeResponse {
  UserModel get user;
  @JsonKey(name: 'streak_count')
  int get streakCount;
  @JsonKey(name: 'xp_today')
  int get xpToday;
  @JsonKey(name: 'xp_weekly_goal')
  int get xpWeeklyGoal;
  @JsonKey(name: 'daily_goal')
  int get dailyGoal;
  @JsonKey(name: 'daily_goal_progress')
  int get dailyGoalProgress;
  @JsonKey(name: 'continue_lesson')
  LessonProgress? get continueLesson;
  @JsonKey(name: 'flashcards_due')
  int get flashcardsDue;
  @JsonKey(name: 'learning_path')
  List<PathNode> get learningPath;
  @JsonKey(name: 'recent_achievements')
  List<Achievement> get recentAchievements;

  /// Create a copy of HomeResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $HomeResponseCopyWith<HomeResponse> get copyWith =>
      _$HomeResponseCopyWithImpl<HomeResponse>(
          this as HomeResponse, _$identity);

  /// Serializes this HomeResponse to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is HomeResponse &&
            (identical(other.user, user) || other.user == user) &&
            (identical(other.streakCount, streakCount) ||
                other.streakCount == streakCount) &&
            (identical(other.xpToday, xpToday) || other.xpToday == xpToday) &&
            (identical(other.xpWeeklyGoal, xpWeeklyGoal) ||
                other.xpWeeklyGoal == xpWeeklyGoal) &&
            (identical(other.dailyGoal, dailyGoal) ||
                other.dailyGoal == dailyGoal) &&
            (identical(other.dailyGoalProgress, dailyGoalProgress) ||
                other.dailyGoalProgress == dailyGoalProgress) &&
            (identical(other.continueLesson, continueLesson) ||
                other.continueLesson == continueLesson) &&
            (identical(other.flashcardsDue, flashcardsDue) ||
                other.flashcardsDue == flashcardsDue) &&
            const DeepCollectionEquality()
                .equals(other.learningPath, learningPath) &&
            const DeepCollectionEquality()
                .equals(other.recentAchievements, recentAchievements));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      user,
      streakCount,
      xpToday,
      xpWeeklyGoal,
      dailyGoal,
      dailyGoalProgress,
      continueLesson,
      flashcardsDue,
      const DeepCollectionEquality().hash(learningPath),
      const DeepCollectionEquality().hash(recentAchievements));

  @override
  String toString() {
    return 'HomeResponse(user: $user, streakCount: $streakCount, xpToday: $xpToday, xpWeeklyGoal: $xpWeeklyGoal, dailyGoal: $dailyGoal, dailyGoalProgress: $dailyGoalProgress, continueLesson: $continueLesson, flashcardsDue: $flashcardsDue, learningPath: $learningPath, recentAchievements: $recentAchievements)';
  }
}

/// @nodoc
abstract mixin class $HomeResponseCopyWith<$Res> {
  factory $HomeResponseCopyWith(
          HomeResponse value, $Res Function(HomeResponse) _then) =
      _$HomeResponseCopyWithImpl;
  @useResult
  $Res call(
      {UserModel user,
      @JsonKey(name: 'streak_count') int streakCount,
      @JsonKey(name: 'xp_today') int xpToday,
      @JsonKey(name: 'xp_weekly_goal') int xpWeeklyGoal,
      @JsonKey(name: 'daily_goal') int dailyGoal,
      @JsonKey(name: 'daily_goal_progress') int dailyGoalProgress,
      @JsonKey(name: 'continue_lesson') LessonProgress? continueLesson,
      @JsonKey(name: 'flashcards_due') int flashcardsDue,
      @JsonKey(name: 'learning_path') List<PathNode> learningPath,
      @JsonKey(name: 'recent_achievements')
      List<Achievement> recentAchievements});

  $UserModelCopyWith<$Res> get user;
  $LessonProgressCopyWith<$Res>? get continueLesson;
}

/// @nodoc
class _$HomeResponseCopyWithImpl<$Res> implements $HomeResponseCopyWith<$Res> {
  _$HomeResponseCopyWithImpl(this._self, this._then);

  final HomeResponse _self;
  final $Res Function(HomeResponse) _then;

  /// Create a copy of HomeResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? user = null,
    Object? streakCount = null,
    Object? xpToday = null,
    Object? xpWeeklyGoal = null,
    Object? dailyGoal = null,
    Object? dailyGoalProgress = null,
    Object? continueLesson = freezed,
    Object? flashcardsDue = null,
    Object? learningPath = null,
    Object? recentAchievements = null,
  }) {
    return _then(_self.copyWith(
      user: null == user
          ? _self.user
          : user // ignore: cast_nullable_to_non_nullable
              as UserModel,
      streakCount: null == streakCount
          ? _self.streakCount
          : streakCount // ignore: cast_nullable_to_non_nullable
              as int,
      xpToday: null == xpToday
          ? _self.xpToday
          : xpToday // ignore: cast_nullable_to_non_nullable
              as int,
      xpWeeklyGoal: null == xpWeeklyGoal
          ? _self.xpWeeklyGoal
          : xpWeeklyGoal // ignore: cast_nullable_to_non_nullable
              as int,
      dailyGoal: null == dailyGoal
          ? _self.dailyGoal
          : dailyGoal // ignore: cast_nullable_to_non_nullable
              as int,
      dailyGoalProgress: null == dailyGoalProgress
          ? _self.dailyGoalProgress
          : dailyGoalProgress // ignore: cast_nullable_to_non_nullable
              as int,
      continueLesson: freezed == continueLesson
          ? _self.continueLesson
          : continueLesson // ignore: cast_nullable_to_non_nullable
              as LessonProgress?,
      flashcardsDue: null == flashcardsDue
          ? _self.flashcardsDue
          : flashcardsDue // ignore: cast_nullable_to_non_nullable
              as int,
      learningPath: null == learningPath
          ? _self.learningPath
          : learningPath // ignore: cast_nullable_to_non_nullable
              as List<PathNode>,
      recentAchievements: null == recentAchievements
          ? _self.recentAchievements
          : recentAchievements // ignore: cast_nullable_to_non_nullable
              as List<Achievement>,
    ));
  }

  /// Create a copy of HomeResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $UserModelCopyWith<$Res> get user {
    return $UserModelCopyWith<$Res>(_self.user, (value) {
      return _then(_self.copyWith(user: value));
    });
  }

  /// Create a copy of HomeResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $LessonProgressCopyWith<$Res>? get continueLesson {
    if (_self.continueLesson == null) {
      return null;
    }

    return $LessonProgressCopyWith<$Res>(_self.continueLesson!, (value) {
      return _then(_self.copyWith(continueLesson: value));
    });
  }
}

/// Adds pattern-matching-related methods to [HomeResponse].
extension HomeResponsePatterns on HomeResponse {
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
    TResult Function(_HomeResponse value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _HomeResponse() when $default != null:
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
    TResult Function(_HomeResponse value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _HomeResponse():
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
    TResult? Function(_HomeResponse value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _HomeResponse() when $default != null:
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
            UserModel user,
            @JsonKey(name: 'streak_count') int streakCount,
            @JsonKey(name: 'xp_today') int xpToday,
            @JsonKey(name: 'xp_weekly_goal') int xpWeeklyGoal,
            @JsonKey(name: 'daily_goal') int dailyGoal,
            @JsonKey(name: 'daily_goal_progress') int dailyGoalProgress,
            @JsonKey(name: 'continue_lesson') LessonProgress? continueLesson,
            @JsonKey(name: 'flashcards_due') int flashcardsDue,
            @JsonKey(name: 'learning_path') List<PathNode> learningPath,
            @JsonKey(name: 'recent_achievements')
            List<Achievement> recentAchievements)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _HomeResponse() when $default != null:
        return $default(
            _that.user,
            _that.streakCount,
            _that.xpToday,
            _that.xpWeeklyGoal,
            _that.dailyGoal,
            _that.dailyGoalProgress,
            _that.continueLesson,
            _that.flashcardsDue,
            _that.learningPath,
            _that.recentAchievements);
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
            UserModel user,
            @JsonKey(name: 'streak_count') int streakCount,
            @JsonKey(name: 'xp_today') int xpToday,
            @JsonKey(name: 'xp_weekly_goal') int xpWeeklyGoal,
            @JsonKey(name: 'daily_goal') int dailyGoal,
            @JsonKey(name: 'daily_goal_progress') int dailyGoalProgress,
            @JsonKey(name: 'continue_lesson') LessonProgress? continueLesson,
            @JsonKey(name: 'flashcards_due') int flashcardsDue,
            @JsonKey(name: 'learning_path') List<PathNode> learningPath,
            @JsonKey(name: 'recent_achievements')
            List<Achievement> recentAchievements)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _HomeResponse():
        return $default(
            _that.user,
            _that.streakCount,
            _that.xpToday,
            _that.xpWeeklyGoal,
            _that.dailyGoal,
            _that.dailyGoalProgress,
            _that.continueLesson,
            _that.flashcardsDue,
            _that.learningPath,
            _that.recentAchievements);
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
            UserModel user,
            @JsonKey(name: 'streak_count') int streakCount,
            @JsonKey(name: 'xp_today') int xpToday,
            @JsonKey(name: 'xp_weekly_goal') int xpWeeklyGoal,
            @JsonKey(name: 'daily_goal') int dailyGoal,
            @JsonKey(name: 'daily_goal_progress') int dailyGoalProgress,
            @JsonKey(name: 'continue_lesson') LessonProgress? continueLesson,
            @JsonKey(name: 'flashcards_due') int flashcardsDue,
            @JsonKey(name: 'learning_path') List<PathNode> learningPath,
            @JsonKey(name: 'recent_achievements')
            List<Achievement> recentAchievements)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _HomeResponse() when $default != null:
        return $default(
            _that.user,
            _that.streakCount,
            _that.xpToday,
            _that.xpWeeklyGoal,
            _that.dailyGoal,
            _that.dailyGoalProgress,
            _that.continueLesson,
            _that.flashcardsDue,
            _that.learningPath,
            _that.recentAchievements);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _HomeResponse implements HomeResponse {
  const _HomeResponse(
      {required this.user,
      @JsonKey(name: 'streak_count') this.streakCount = 0,
      @JsonKey(name: 'xp_today') this.xpToday = 0,
      @JsonKey(name: 'xp_weekly_goal') this.xpWeeklyGoal = 100,
      @JsonKey(name: 'daily_goal') this.dailyGoal = 5,
      @JsonKey(name: 'daily_goal_progress') this.dailyGoalProgress = 0,
      @JsonKey(name: 'continue_lesson') this.continueLesson,
      @JsonKey(name: 'flashcards_due') this.flashcardsDue = 0,
      @JsonKey(name: 'learning_path')
      final List<PathNode> learningPath = const [],
      @JsonKey(name: 'recent_achievements')
      final List<Achievement> recentAchievements = const []})
      : _learningPath = learningPath,
        _recentAchievements = recentAchievements;
  factory _HomeResponse.fromJson(Map<String, dynamic> json) =>
      _$HomeResponseFromJson(json);

  @override
  final UserModel user;
  @override
  @JsonKey(name: 'streak_count')
  final int streakCount;
  @override
  @JsonKey(name: 'xp_today')
  final int xpToday;
  @override
  @JsonKey(name: 'xp_weekly_goal')
  final int xpWeeklyGoal;
  @override
  @JsonKey(name: 'daily_goal')
  final int dailyGoal;
  @override
  @JsonKey(name: 'daily_goal_progress')
  final int dailyGoalProgress;
  @override
  @JsonKey(name: 'continue_lesson')
  final LessonProgress? continueLesson;
  @override
  @JsonKey(name: 'flashcards_due')
  final int flashcardsDue;
  final List<PathNode> _learningPath;
  @override
  @JsonKey(name: 'learning_path')
  List<PathNode> get learningPath {
    if (_learningPath is EqualUnmodifiableListView) return _learningPath;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_learningPath);
  }

  final List<Achievement> _recentAchievements;
  @override
  @JsonKey(name: 'recent_achievements')
  List<Achievement> get recentAchievements {
    if (_recentAchievements is EqualUnmodifiableListView)
      return _recentAchievements;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_recentAchievements);
  }

  /// Create a copy of HomeResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$HomeResponseCopyWith<_HomeResponse> get copyWith =>
      __$HomeResponseCopyWithImpl<_HomeResponse>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$HomeResponseToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _HomeResponse &&
            (identical(other.user, user) || other.user == user) &&
            (identical(other.streakCount, streakCount) ||
                other.streakCount == streakCount) &&
            (identical(other.xpToday, xpToday) || other.xpToday == xpToday) &&
            (identical(other.xpWeeklyGoal, xpWeeklyGoal) ||
                other.xpWeeklyGoal == xpWeeklyGoal) &&
            (identical(other.dailyGoal, dailyGoal) ||
                other.dailyGoal == dailyGoal) &&
            (identical(other.dailyGoalProgress, dailyGoalProgress) ||
                other.dailyGoalProgress == dailyGoalProgress) &&
            (identical(other.continueLesson, continueLesson) ||
                other.continueLesson == continueLesson) &&
            (identical(other.flashcardsDue, flashcardsDue) ||
                other.flashcardsDue == flashcardsDue) &&
            const DeepCollectionEquality()
                .equals(other._learningPath, _learningPath) &&
            const DeepCollectionEquality()
                .equals(other._recentAchievements, _recentAchievements));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      user,
      streakCount,
      xpToday,
      xpWeeklyGoal,
      dailyGoal,
      dailyGoalProgress,
      continueLesson,
      flashcardsDue,
      const DeepCollectionEquality().hash(_learningPath),
      const DeepCollectionEquality().hash(_recentAchievements));

  @override
  String toString() {
    return 'HomeResponse(user: $user, streakCount: $streakCount, xpToday: $xpToday, xpWeeklyGoal: $xpWeeklyGoal, dailyGoal: $dailyGoal, dailyGoalProgress: $dailyGoalProgress, continueLesson: $continueLesson, flashcardsDue: $flashcardsDue, learningPath: $learningPath, recentAchievements: $recentAchievements)';
  }
}

/// @nodoc
abstract mixin class _$HomeResponseCopyWith<$Res>
    implements $HomeResponseCopyWith<$Res> {
  factory _$HomeResponseCopyWith(
          _HomeResponse value, $Res Function(_HomeResponse) _then) =
      __$HomeResponseCopyWithImpl;
  @override
  @useResult
  $Res call(
      {UserModel user,
      @JsonKey(name: 'streak_count') int streakCount,
      @JsonKey(name: 'xp_today') int xpToday,
      @JsonKey(name: 'xp_weekly_goal') int xpWeeklyGoal,
      @JsonKey(name: 'daily_goal') int dailyGoal,
      @JsonKey(name: 'daily_goal_progress') int dailyGoalProgress,
      @JsonKey(name: 'continue_lesson') LessonProgress? continueLesson,
      @JsonKey(name: 'flashcards_due') int flashcardsDue,
      @JsonKey(name: 'learning_path') List<PathNode> learningPath,
      @JsonKey(name: 'recent_achievements')
      List<Achievement> recentAchievements});

  @override
  $UserModelCopyWith<$Res> get user;
  @override
  $LessonProgressCopyWith<$Res>? get continueLesson;
}

/// @nodoc
class __$HomeResponseCopyWithImpl<$Res>
    implements _$HomeResponseCopyWith<$Res> {
  __$HomeResponseCopyWithImpl(this._self, this._then);

  final _HomeResponse _self;
  final $Res Function(_HomeResponse) _then;

  /// Create a copy of HomeResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? user = null,
    Object? streakCount = null,
    Object? xpToday = null,
    Object? xpWeeklyGoal = null,
    Object? dailyGoal = null,
    Object? dailyGoalProgress = null,
    Object? continueLesson = freezed,
    Object? flashcardsDue = null,
    Object? learningPath = null,
    Object? recentAchievements = null,
  }) {
    return _then(_HomeResponse(
      user: null == user
          ? _self.user
          : user // ignore: cast_nullable_to_non_nullable
              as UserModel,
      streakCount: null == streakCount
          ? _self.streakCount
          : streakCount // ignore: cast_nullable_to_non_nullable
              as int,
      xpToday: null == xpToday
          ? _self.xpToday
          : xpToday // ignore: cast_nullable_to_non_nullable
              as int,
      xpWeeklyGoal: null == xpWeeklyGoal
          ? _self.xpWeeklyGoal
          : xpWeeklyGoal // ignore: cast_nullable_to_non_nullable
              as int,
      dailyGoal: null == dailyGoal
          ? _self.dailyGoal
          : dailyGoal // ignore: cast_nullable_to_non_nullable
              as int,
      dailyGoalProgress: null == dailyGoalProgress
          ? _self.dailyGoalProgress
          : dailyGoalProgress // ignore: cast_nullable_to_non_nullable
              as int,
      continueLesson: freezed == continueLesson
          ? _self.continueLesson
          : continueLesson // ignore: cast_nullable_to_non_nullable
              as LessonProgress?,
      flashcardsDue: null == flashcardsDue
          ? _self.flashcardsDue
          : flashcardsDue // ignore: cast_nullable_to_non_nullable
              as int,
      learningPath: null == learningPath
          ? _self._learningPath
          : learningPath // ignore: cast_nullable_to_non_nullable
              as List<PathNode>,
      recentAchievements: null == recentAchievements
          ? _self._recentAchievements
          : recentAchievements // ignore: cast_nullable_to_non_nullable
              as List<Achievement>,
    ));
  }

  /// Create a copy of HomeResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $UserModelCopyWith<$Res> get user {
    return $UserModelCopyWith<$Res>(_self.user, (value) {
      return _then(_self.copyWith(user: value));
    });
  }

  /// Create a copy of HomeResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $LessonProgressCopyWith<$Res>? get continueLesson {
    if (_self.continueLesson == null) {
      return null;
    }

    return $LessonProgressCopyWith<$Res>(_self.continueLesson!, (value) {
      return _then(_self.copyWith(continueLesson: value));
    });
  }
}

/// @nodoc
mixin _$LessonProgress {
  @JsonKey(name: 'lesson_id')
  int get lessonId;
  String get title;
  @JsonKey(name: 'module_number')
  int get moduleNumber;
  @JsonKey(name: 'lesson_number')
  int get lessonNumber;
  @JsonKey(name: 'progress_percent')
  double get progressPercent;
  @JsonKey(name: 'icon_name')
  String get iconName;

  /// Create a copy of LessonProgress
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $LessonProgressCopyWith<LessonProgress> get copyWith =>
      _$LessonProgressCopyWithImpl<LessonProgress>(
          this as LessonProgress, _$identity);

  /// Serializes this LessonProgress to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is LessonProgress &&
            (identical(other.lessonId, lessonId) ||
                other.lessonId == lessonId) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.moduleNumber, moduleNumber) ||
                other.moduleNumber == moduleNumber) &&
            (identical(other.lessonNumber, lessonNumber) ||
                other.lessonNumber == lessonNumber) &&
            (identical(other.progressPercent, progressPercent) ||
                other.progressPercent == progressPercent) &&
            (identical(other.iconName, iconName) ||
                other.iconName == iconName));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, lessonId, title, moduleNumber,
      lessonNumber, progressPercent, iconName);

  @override
  String toString() {
    return 'LessonProgress(lessonId: $lessonId, title: $title, moduleNumber: $moduleNumber, lessonNumber: $lessonNumber, progressPercent: $progressPercent, iconName: $iconName)';
  }
}

/// @nodoc
abstract mixin class $LessonProgressCopyWith<$Res> {
  factory $LessonProgressCopyWith(
          LessonProgress value, $Res Function(LessonProgress) _then) =
      _$LessonProgressCopyWithImpl;
  @useResult
  $Res call(
      {@JsonKey(name: 'lesson_id') int lessonId,
      String title,
      @JsonKey(name: 'module_number') int moduleNumber,
      @JsonKey(name: 'lesson_number') int lessonNumber,
      @JsonKey(name: 'progress_percent') double progressPercent,
      @JsonKey(name: 'icon_name') String iconName});
}

/// @nodoc
class _$LessonProgressCopyWithImpl<$Res>
    implements $LessonProgressCopyWith<$Res> {
  _$LessonProgressCopyWithImpl(this._self, this._then);

  final LessonProgress _self;
  final $Res Function(LessonProgress) _then;

  /// Create a copy of LessonProgress
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? lessonId = null,
    Object? title = null,
    Object? moduleNumber = null,
    Object? lessonNumber = null,
    Object? progressPercent = null,
    Object? iconName = null,
  }) {
    return _then(_self.copyWith(
      lessonId: null == lessonId
          ? _self.lessonId
          : lessonId // ignore: cast_nullable_to_non_nullable
              as int,
      title: null == title
          ? _self.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      moduleNumber: null == moduleNumber
          ? _self.moduleNumber
          : moduleNumber // ignore: cast_nullable_to_non_nullable
              as int,
      lessonNumber: null == lessonNumber
          ? _self.lessonNumber
          : lessonNumber // ignore: cast_nullable_to_non_nullable
              as int,
      progressPercent: null == progressPercent
          ? _self.progressPercent
          : progressPercent // ignore: cast_nullable_to_non_nullable
              as double,
      iconName: null == iconName
          ? _self.iconName
          : iconName // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// Adds pattern-matching-related methods to [LessonProgress].
extension LessonProgressPatterns on LessonProgress {
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
    TResult Function(_LessonProgress value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _LessonProgress() when $default != null:
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
    TResult Function(_LessonProgress value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonProgress():
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
    TResult? Function(_LessonProgress value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonProgress() when $default != null:
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
            String title,
            @JsonKey(name: 'module_number') int moduleNumber,
            @JsonKey(name: 'lesson_number') int lessonNumber,
            @JsonKey(name: 'progress_percent') double progressPercent,
            @JsonKey(name: 'icon_name') String iconName)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _LessonProgress() when $default != null:
        return $default(_that.lessonId, _that.title, _that.moduleNumber,
            _that.lessonNumber, _that.progressPercent, _that.iconName);
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
            String title,
            @JsonKey(name: 'module_number') int moduleNumber,
            @JsonKey(name: 'lesson_number') int lessonNumber,
            @JsonKey(name: 'progress_percent') double progressPercent,
            @JsonKey(name: 'icon_name') String iconName)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonProgress():
        return $default(_that.lessonId, _that.title, _that.moduleNumber,
            _that.lessonNumber, _that.progressPercent, _that.iconName);
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
            String title,
            @JsonKey(name: 'module_number') int moduleNumber,
            @JsonKey(name: 'lesson_number') int lessonNumber,
            @JsonKey(name: 'progress_percent') double progressPercent,
            @JsonKey(name: 'icon_name') String iconName)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _LessonProgress() when $default != null:
        return $default(_that.lessonId, _that.title, _that.moduleNumber,
            _that.lessonNumber, _that.progressPercent, _that.iconName);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _LessonProgress implements LessonProgress {
  const _LessonProgress(
      {@JsonKey(name: 'lesson_id') required this.lessonId,
      required this.title,
      @JsonKey(name: 'module_number') required this.moduleNumber,
      @JsonKey(name: 'lesson_number') required this.lessonNumber,
      @JsonKey(name: 'progress_percent') this.progressPercent = 0,
      @JsonKey(name: 'icon_name') this.iconName = 'book'});
  factory _LessonProgress.fromJson(Map<String, dynamic> json) =>
      _$LessonProgressFromJson(json);

  @override
  @JsonKey(name: 'lesson_id')
  final int lessonId;
  @override
  final String title;
  @override
  @JsonKey(name: 'module_number')
  final int moduleNumber;
  @override
  @JsonKey(name: 'lesson_number')
  final int lessonNumber;
  @override
  @JsonKey(name: 'progress_percent')
  final double progressPercent;
  @override
  @JsonKey(name: 'icon_name')
  final String iconName;

  /// Create a copy of LessonProgress
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$LessonProgressCopyWith<_LessonProgress> get copyWith =>
      __$LessonProgressCopyWithImpl<_LessonProgress>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$LessonProgressToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _LessonProgress &&
            (identical(other.lessonId, lessonId) ||
                other.lessonId == lessonId) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.moduleNumber, moduleNumber) ||
                other.moduleNumber == moduleNumber) &&
            (identical(other.lessonNumber, lessonNumber) ||
                other.lessonNumber == lessonNumber) &&
            (identical(other.progressPercent, progressPercent) ||
                other.progressPercent == progressPercent) &&
            (identical(other.iconName, iconName) ||
                other.iconName == iconName));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, lessonId, title, moduleNumber,
      lessonNumber, progressPercent, iconName);

  @override
  String toString() {
    return 'LessonProgress(lessonId: $lessonId, title: $title, moduleNumber: $moduleNumber, lessonNumber: $lessonNumber, progressPercent: $progressPercent, iconName: $iconName)';
  }
}

/// @nodoc
abstract mixin class _$LessonProgressCopyWith<$Res>
    implements $LessonProgressCopyWith<$Res> {
  factory _$LessonProgressCopyWith(
          _LessonProgress value, $Res Function(_LessonProgress) _then) =
      __$LessonProgressCopyWithImpl;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'lesson_id') int lessonId,
      String title,
      @JsonKey(name: 'module_number') int moduleNumber,
      @JsonKey(name: 'lesson_number') int lessonNumber,
      @JsonKey(name: 'progress_percent') double progressPercent,
      @JsonKey(name: 'icon_name') String iconName});
}

/// @nodoc
class __$LessonProgressCopyWithImpl<$Res>
    implements _$LessonProgressCopyWith<$Res> {
  __$LessonProgressCopyWithImpl(this._self, this._then);

  final _LessonProgress _self;
  final $Res Function(_LessonProgress) _then;

  /// Create a copy of LessonProgress
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? lessonId = null,
    Object? title = null,
    Object? moduleNumber = null,
    Object? lessonNumber = null,
    Object? progressPercent = null,
    Object? iconName = null,
  }) {
    return _then(_LessonProgress(
      lessonId: null == lessonId
          ? _self.lessonId
          : lessonId // ignore: cast_nullable_to_non_nullable
              as int,
      title: null == title
          ? _self.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      moduleNumber: null == moduleNumber
          ? _self.moduleNumber
          : moduleNumber // ignore: cast_nullable_to_non_nullable
              as int,
      lessonNumber: null == lessonNumber
          ? _self.lessonNumber
          : lessonNumber // ignore: cast_nullable_to_non_nullable
              as int,
      progressPercent: null == progressPercent
          ? _self.progressPercent
          : progressPercent // ignore: cast_nullable_to_non_nullable
              as double,
      iconName: null == iconName
          ? _self.iconName
          : iconName // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
mixin _$PathNode {
  String get id;
  String get label;
  @JsonKey(name: 'label_urdu')
  String? get labelUrdu;
  PathNodeType get type;
  @JsonKey(name: 'is_completed')
  bool get isCompleted;
  @JsonKey(name: 'is_current')
  bool get isCurrent;
  @JsonKey(name: 'is_locked')
  bool get isLocked;
  @JsonKey(name: 'xp_reward')
  int get xpReward;
  @JsonKey(name: 'icon_name')
  String get iconName;
  @JsonKey(name: 'lesson_id')
  int? get lessonId;

  /// Create a copy of PathNode
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $PathNodeCopyWith<PathNode> get copyWith =>
      _$PathNodeCopyWithImpl<PathNode>(this as PathNode, _$identity);

  /// Serializes this PathNode to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is PathNode &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.label, label) || other.label == label) &&
            (identical(other.labelUrdu, labelUrdu) ||
                other.labelUrdu == labelUrdu) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.isCompleted, isCompleted) ||
                other.isCompleted == isCompleted) &&
            (identical(other.isCurrent, isCurrent) ||
                other.isCurrent == isCurrent) &&
            (identical(other.isLocked, isLocked) ||
                other.isLocked == isLocked) &&
            (identical(other.xpReward, xpReward) ||
                other.xpReward == xpReward) &&
            (identical(other.iconName, iconName) ||
                other.iconName == iconName) &&
            (identical(other.lessonId, lessonId) ||
                other.lessonId == lessonId));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, id, label, labelUrdu, type,
      isCompleted, isCurrent, isLocked, xpReward, iconName, lessonId);

  @override
  String toString() {
    return 'PathNode(id: $id, label: $label, labelUrdu: $labelUrdu, type: $type, isCompleted: $isCompleted, isCurrent: $isCurrent, isLocked: $isLocked, xpReward: $xpReward, iconName: $iconName, lessonId: $lessonId)';
  }
}

/// @nodoc
abstract mixin class $PathNodeCopyWith<$Res> {
  factory $PathNodeCopyWith(PathNode value, $Res Function(PathNode) _then) =
      _$PathNodeCopyWithImpl;
  @useResult
  $Res call(
      {String id,
      String label,
      @JsonKey(name: 'label_urdu') String? labelUrdu,
      PathNodeType type,
      @JsonKey(name: 'is_completed') bool isCompleted,
      @JsonKey(name: 'is_current') bool isCurrent,
      @JsonKey(name: 'is_locked') bool isLocked,
      @JsonKey(name: 'xp_reward') int xpReward,
      @JsonKey(name: 'icon_name') String iconName,
      @JsonKey(name: 'lesson_id') int? lessonId});
}

/// @nodoc
class _$PathNodeCopyWithImpl<$Res> implements $PathNodeCopyWith<$Res> {
  _$PathNodeCopyWithImpl(this._self, this._then);

  final PathNode _self;
  final $Res Function(PathNode) _then;

  /// Create a copy of PathNode
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? label = null,
    Object? labelUrdu = freezed,
    Object? type = null,
    Object? isCompleted = null,
    Object? isCurrent = null,
    Object? isLocked = null,
    Object? xpReward = null,
    Object? iconName = null,
    Object? lessonId = freezed,
  }) {
    return _then(_self.copyWith(
      id: null == id
          ? _self.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      label: null == label
          ? _self.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      labelUrdu: freezed == labelUrdu
          ? _self.labelUrdu
          : labelUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      type: null == type
          ? _self.type
          : type // ignore: cast_nullable_to_non_nullable
              as PathNodeType,
      isCompleted: null == isCompleted
          ? _self.isCompleted
          : isCompleted // ignore: cast_nullable_to_non_nullable
              as bool,
      isCurrent: null == isCurrent
          ? _self.isCurrent
          : isCurrent // ignore: cast_nullable_to_non_nullable
              as bool,
      isLocked: null == isLocked
          ? _self.isLocked
          : isLocked // ignore: cast_nullable_to_non_nullable
              as bool,
      xpReward: null == xpReward
          ? _self.xpReward
          : xpReward // ignore: cast_nullable_to_non_nullable
              as int,
      iconName: null == iconName
          ? _self.iconName
          : iconName // ignore: cast_nullable_to_non_nullable
              as String,
      lessonId: freezed == lessonId
          ? _self.lessonId
          : lessonId // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

/// Adds pattern-matching-related methods to [PathNode].
extension PathNodePatterns on PathNode {
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
    TResult Function(_PathNode value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _PathNode() when $default != null:
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
    TResult Function(_PathNode value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _PathNode():
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
    TResult? Function(_PathNode value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _PathNode() when $default != null:
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
            String label,
            @JsonKey(name: 'label_urdu') String? labelUrdu,
            PathNodeType type,
            @JsonKey(name: 'is_completed') bool isCompleted,
            @JsonKey(name: 'is_current') bool isCurrent,
            @JsonKey(name: 'is_locked') bool isLocked,
            @JsonKey(name: 'xp_reward') int xpReward,
            @JsonKey(name: 'icon_name') String iconName,
            @JsonKey(name: 'lesson_id') int? lessonId)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _PathNode() when $default != null:
        return $default(
            _that.id,
            _that.label,
            _that.labelUrdu,
            _that.type,
            _that.isCompleted,
            _that.isCurrent,
            _that.isLocked,
            _that.xpReward,
            _that.iconName,
            _that.lessonId);
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
            String label,
            @JsonKey(name: 'label_urdu') String? labelUrdu,
            PathNodeType type,
            @JsonKey(name: 'is_completed') bool isCompleted,
            @JsonKey(name: 'is_current') bool isCurrent,
            @JsonKey(name: 'is_locked') bool isLocked,
            @JsonKey(name: 'xp_reward') int xpReward,
            @JsonKey(name: 'icon_name') String iconName,
            @JsonKey(name: 'lesson_id') int? lessonId)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _PathNode():
        return $default(
            _that.id,
            _that.label,
            _that.labelUrdu,
            _that.type,
            _that.isCompleted,
            _that.isCurrent,
            _that.isLocked,
            _that.xpReward,
            _that.iconName,
            _that.lessonId);
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
            String label,
            @JsonKey(name: 'label_urdu') String? labelUrdu,
            PathNodeType type,
            @JsonKey(name: 'is_completed') bool isCompleted,
            @JsonKey(name: 'is_current') bool isCurrent,
            @JsonKey(name: 'is_locked') bool isLocked,
            @JsonKey(name: 'xp_reward') int xpReward,
            @JsonKey(name: 'icon_name') String iconName,
            @JsonKey(name: 'lesson_id') int? lessonId)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _PathNode() when $default != null:
        return $default(
            _that.id,
            _that.label,
            _that.labelUrdu,
            _that.type,
            _that.isCompleted,
            _that.isCurrent,
            _that.isLocked,
            _that.xpReward,
            _that.iconName,
            _that.lessonId);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _PathNode implements PathNode {
  const _PathNode(
      {required this.id,
      required this.label,
      @JsonKey(name: 'label_urdu') this.labelUrdu,
      required this.type,
      @JsonKey(name: 'is_completed') this.isCompleted = false,
      @JsonKey(name: 'is_current') this.isCurrent = false,
      @JsonKey(name: 'is_locked') this.isLocked = false,
      @JsonKey(name: 'xp_reward') this.xpReward = 10,
      @JsonKey(name: 'icon_name') this.iconName = 'star',
      @JsonKey(name: 'lesson_id') this.lessonId});
  factory _PathNode.fromJson(Map<String, dynamic> json) =>
      _$PathNodeFromJson(json);

  @override
  final String id;
  @override
  final String label;
  @override
  @JsonKey(name: 'label_urdu')
  final String? labelUrdu;
  @override
  final PathNodeType type;
  @override
  @JsonKey(name: 'is_completed')
  final bool isCompleted;
  @override
  @JsonKey(name: 'is_current')
  final bool isCurrent;
  @override
  @JsonKey(name: 'is_locked')
  final bool isLocked;
  @override
  @JsonKey(name: 'xp_reward')
  final int xpReward;
  @override
  @JsonKey(name: 'icon_name')
  final String iconName;
  @override
  @JsonKey(name: 'lesson_id')
  final int? lessonId;

  /// Create a copy of PathNode
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$PathNodeCopyWith<_PathNode> get copyWith =>
      __$PathNodeCopyWithImpl<_PathNode>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$PathNodeToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _PathNode &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.label, label) || other.label == label) &&
            (identical(other.labelUrdu, labelUrdu) ||
                other.labelUrdu == labelUrdu) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.isCompleted, isCompleted) ||
                other.isCompleted == isCompleted) &&
            (identical(other.isCurrent, isCurrent) ||
                other.isCurrent == isCurrent) &&
            (identical(other.isLocked, isLocked) ||
                other.isLocked == isLocked) &&
            (identical(other.xpReward, xpReward) ||
                other.xpReward == xpReward) &&
            (identical(other.iconName, iconName) ||
                other.iconName == iconName) &&
            (identical(other.lessonId, lessonId) ||
                other.lessonId == lessonId));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, id, label, labelUrdu, type,
      isCompleted, isCurrent, isLocked, xpReward, iconName, lessonId);

  @override
  String toString() {
    return 'PathNode(id: $id, label: $label, labelUrdu: $labelUrdu, type: $type, isCompleted: $isCompleted, isCurrent: $isCurrent, isLocked: $isLocked, xpReward: $xpReward, iconName: $iconName, lessonId: $lessonId)';
  }
}

/// @nodoc
abstract mixin class _$PathNodeCopyWith<$Res>
    implements $PathNodeCopyWith<$Res> {
  factory _$PathNodeCopyWith(_PathNode value, $Res Function(_PathNode) _then) =
      __$PathNodeCopyWithImpl;
  @override
  @useResult
  $Res call(
      {String id,
      String label,
      @JsonKey(name: 'label_urdu') String? labelUrdu,
      PathNodeType type,
      @JsonKey(name: 'is_completed') bool isCompleted,
      @JsonKey(name: 'is_current') bool isCurrent,
      @JsonKey(name: 'is_locked') bool isLocked,
      @JsonKey(name: 'xp_reward') int xpReward,
      @JsonKey(name: 'icon_name') String iconName,
      @JsonKey(name: 'lesson_id') int? lessonId});
}

/// @nodoc
class __$PathNodeCopyWithImpl<$Res> implements _$PathNodeCopyWith<$Res> {
  __$PathNodeCopyWithImpl(this._self, this._then);

  final _PathNode _self;
  final $Res Function(_PathNode) _then;

  /// Create a copy of PathNode
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? id = null,
    Object? label = null,
    Object? labelUrdu = freezed,
    Object? type = null,
    Object? isCompleted = null,
    Object? isCurrent = null,
    Object? isLocked = null,
    Object? xpReward = null,
    Object? iconName = null,
    Object? lessonId = freezed,
  }) {
    return _then(_PathNode(
      id: null == id
          ? _self.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      label: null == label
          ? _self.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      labelUrdu: freezed == labelUrdu
          ? _self.labelUrdu
          : labelUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      type: null == type
          ? _self.type
          : type // ignore: cast_nullable_to_non_nullable
              as PathNodeType,
      isCompleted: null == isCompleted
          ? _self.isCompleted
          : isCompleted // ignore: cast_nullable_to_non_nullable
              as bool,
      isCurrent: null == isCurrent
          ? _self.isCurrent
          : isCurrent // ignore: cast_nullable_to_non_nullable
              as bool,
      isLocked: null == isLocked
          ? _self.isLocked
          : isLocked // ignore: cast_nullable_to_non_nullable
              as bool,
      xpReward: null == xpReward
          ? _self.xpReward
          : xpReward // ignore: cast_nullable_to_non_nullable
              as int,
      iconName: null == iconName
          ? _self.iconName
          : iconName // ignore: cast_nullable_to_non_nullable
              as String,
      lessonId: freezed == lessonId
          ? _self.lessonId
          : lessonId // ignore: cast_nullable_to_non_nullable
              as int?,
    ));
  }
}

/// @nodoc
mixin _$Achievement {
  String get id;
  String get title;
  @JsonKey(name: 'title_urdu')
  String? get titleUrdu;
  String get description;
  @JsonKey(name: 'description_urdu')
  String? get descriptionUrdu;
  @JsonKey(name: 'icon_name')
  String get iconName;
  @JsonKey(name: 'earned_at')
  DateTime? get earnedAt;
  @JsonKey(name: 'is_earned')
  bool get isEarned;
  @JsonKey(name: 'progress')
  double get progress;

  /// Create a copy of Achievement
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $AchievementCopyWith<Achievement> get copyWith =>
      _$AchievementCopyWithImpl<Achievement>(this as Achievement, _$identity);

  /// Serializes this Achievement to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is Achievement &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.titleUrdu, titleUrdu) ||
                other.titleUrdu == titleUrdu) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.descriptionUrdu, descriptionUrdu) ||
                other.descriptionUrdu == descriptionUrdu) &&
            (identical(other.iconName, iconName) ||
                other.iconName == iconName) &&
            (identical(other.earnedAt, earnedAt) ||
                other.earnedAt == earnedAt) &&
            (identical(other.isEarned, isEarned) ||
                other.isEarned == isEarned) &&
            (identical(other.progress, progress) ||
                other.progress == progress));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, id, title, titleUrdu,
      description, descriptionUrdu, iconName, earnedAt, isEarned, progress);

  @override
  String toString() {
    return 'Achievement(id: $id, title: $title, titleUrdu: $titleUrdu, description: $description, descriptionUrdu: $descriptionUrdu, iconName: $iconName, earnedAt: $earnedAt, isEarned: $isEarned, progress: $progress)';
  }
}

/// @nodoc
abstract mixin class $AchievementCopyWith<$Res> {
  factory $AchievementCopyWith(
          Achievement value, $Res Function(Achievement) _then) =
      _$AchievementCopyWithImpl;
  @useResult
  $Res call(
      {String id,
      String title,
      @JsonKey(name: 'title_urdu') String? titleUrdu,
      String description,
      @JsonKey(name: 'description_urdu') String? descriptionUrdu,
      @JsonKey(name: 'icon_name') String iconName,
      @JsonKey(name: 'earned_at') DateTime? earnedAt,
      @JsonKey(name: 'is_earned') bool isEarned,
      @JsonKey(name: 'progress') double progress});
}

/// @nodoc
class _$AchievementCopyWithImpl<$Res> implements $AchievementCopyWith<$Res> {
  _$AchievementCopyWithImpl(this._self, this._then);

  final Achievement _self;
  final $Res Function(Achievement) _then;

  /// Create a copy of Achievement
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? title = null,
    Object? titleUrdu = freezed,
    Object? description = null,
    Object? descriptionUrdu = freezed,
    Object? iconName = null,
    Object? earnedAt = freezed,
    Object? isEarned = null,
    Object? progress = null,
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
      titleUrdu: freezed == titleUrdu
          ? _self.titleUrdu
          : titleUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      description: null == description
          ? _self.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      descriptionUrdu: freezed == descriptionUrdu
          ? _self.descriptionUrdu
          : descriptionUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      iconName: null == iconName
          ? _self.iconName
          : iconName // ignore: cast_nullable_to_non_nullable
              as String,
      earnedAt: freezed == earnedAt
          ? _self.earnedAt
          : earnedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      isEarned: null == isEarned
          ? _self.isEarned
          : isEarned // ignore: cast_nullable_to_non_nullable
              as bool,
      progress: null == progress
          ? _self.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// Adds pattern-matching-related methods to [Achievement].
extension AchievementPatterns on Achievement {
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
    TResult Function(_Achievement value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _Achievement() when $default != null:
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
    TResult Function(_Achievement value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _Achievement():
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
    TResult? Function(_Achievement value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _Achievement() when $default != null:
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
            @JsonKey(name: 'title_urdu') String? titleUrdu,
            String description,
            @JsonKey(name: 'description_urdu') String? descriptionUrdu,
            @JsonKey(name: 'icon_name') String iconName,
            @JsonKey(name: 'earned_at') DateTime? earnedAt,
            @JsonKey(name: 'is_earned') bool isEarned,
            @JsonKey(name: 'progress') double progress)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _Achievement() when $default != null:
        return $default(
            _that.id,
            _that.title,
            _that.titleUrdu,
            _that.description,
            _that.descriptionUrdu,
            _that.iconName,
            _that.earnedAt,
            _that.isEarned,
            _that.progress);
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
            @JsonKey(name: 'title_urdu') String? titleUrdu,
            String description,
            @JsonKey(name: 'description_urdu') String? descriptionUrdu,
            @JsonKey(name: 'icon_name') String iconName,
            @JsonKey(name: 'earned_at') DateTime? earnedAt,
            @JsonKey(name: 'is_earned') bool isEarned,
            @JsonKey(name: 'progress') double progress)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _Achievement():
        return $default(
            _that.id,
            _that.title,
            _that.titleUrdu,
            _that.description,
            _that.descriptionUrdu,
            _that.iconName,
            _that.earnedAt,
            _that.isEarned,
            _that.progress);
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
            @JsonKey(name: 'title_urdu') String? titleUrdu,
            String description,
            @JsonKey(name: 'description_urdu') String? descriptionUrdu,
            @JsonKey(name: 'icon_name') String iconName,
            @JsonKey(name: 'earned_at') DateTime? earnedAt,
            @JsonKey(name: 'is_earned') bool isEarned,
            @JsonKey(name: 'progress') double progress)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _Achievement() when $default != null:
        return $default(
            _that.id,
            _that.title,
            _that.titleUrdu,
            _that.description,
            _that.descriptionUrdu,
            _that.iconName,
            _that.earnedAt,
            _that.isEarned,
            _that.progress);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _Achievement implements Achievement {
  const _Achievement(
      {required this.id,
      required this.title,
      @JsonKey(name: 'title_urdu') this.titleUrdu,
      required this.description,
      @JsonKey(name: 'description_urdu') this.descriptionUrdu,
      @JsonKey(name: 'icon_name') this.iconName = 'emoji_events',
      @JsonKey(name: 'earned_at') this.earnedAt,
      @JsonKey(name: 'is_earned') this.isEarned = false,
      @JsonKey(name: 'progress') this.progress = 0});
  factory _Achievement.fromJson(Map<String, dynamic> json) =>
      _$AchievementFromJson(json);

  @override
  final String id;
  @override
  final String title;
  @override
  @JsonKey(name: 'title_urdu')
  final String? titleUrdu;
  @override
  final String description;
  @override
  @JsonKey(name: 'description_urdu')
  final String? descriptionUrdu;
  @override
  @JsonKey(name: 'icon_name')
  final String iconName;
  @override
  @JsonKey(name: 'earned_at')
  final DateTime? earnedAt;
  @override
  @JsonKey(name: 'is_earned')
  final bool isEarned;
  @override
  @JsonKey(name: 'progress')
  final double progress;

  /// Create a copy of Achievement
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$AchievementCopyWith<_Achievement> get copyWith =>
      __$AchievementCopyWithImpl<_Achievement>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$AchievementToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _Achievement &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.titleUrdu, titleUrdu) ||
                other.titleUrdu == titleUrdu) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.descriptionUrdu, descriptionUrdu) ||
                other.descriptionUrdu == descriptionUrdu) &&
            (identical(other.iconName, iconName) ||
                other.iconName == iconName) &&
            (identical(other.earnedAt, earnedAt) ||
                other.earnedAt == earnedAt) &&
            (identical(other.isEarned, isEarned) ||
                other.isEarned == isEarned) &&
            (identical(other.progress, progress) ||
                other.progress == progress));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, id, title, titleUrdu,
      description, descriptionUrdu, iconName, earnedAt, isEarned, progress);

  @override
  String toString() {
    return 'Achievement(id: $id, title: $title, titleUrdu: $titleUrdu, description: $description, descriptionUrdu: $descriptionUrdu, iconName: $iconName, earnedAt: $earnedAt, isEarned: $isEarned, progress: $progress)';
  }
}

/// @nodoc
abstract mixin class _$AchievementCopyWith<$Res>
    implements $AchievementCopyWith<$Res> {
  factory _$AchievementCopyWith(
          _Achievement value, $Res Function(_Achievement) _then) =
      __$AchievementCopyWithImpl;
  @override
  @useResult
  $Res call(
      {String id,
      String title,
      @JsonKey(name: 'title_urdu') String? titleUrdu,
      String description,
      @JsonKey(name: 'description_urdu') String? descriptionUrdu,
      @JsonKey(name: 'icon_name') String iconName,
      @JsonKey(name: 'earned_at') DateTime? earnedAt,
      @JsonKey(name: 'is_earned') bool isEarned,
      @JsonKey(name: 'progress') double progress});
}

/// @nodoc
class __$AchievementCopyWithImpl<$Res> implements _$AchievementCopyWith<$Res> {
  __$AchievementCopyWithImpl(this._self, this._then);

  final _Achievement _self;
  final $Res Function(_Achievement) _then;

  /// Create a copy of Achievement
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? id = null,
    Object? title = null,
    Object? titleUrdu = freezed,
    Object? description = null,
    Object? descriptionUrdu = freezed,
    Object? iconName = null,
    Object? earnedAt = freezed,
    Object? isEarned = null,
    Object? progress = null,
  }) {
    return _then(_Achievement(
      id: null == id
          ? _self.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _self.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      titleUrdu: freezed == titleUrdu
          ? _self.titleUrdu
          : titleUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      description: null == description
          ? _self.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      descriptionUrdu: freezed == descriptionUrdu
          ? _self.descriptionUrdu
          : descriptionUrdu // ignore: cast_nullable_to_non_nullable
              as String?,
      iconName: null == iconName
          ? _self.iconName
          : iconName // ignore: cast_nullable_to_non_nullable
              as String,
      earnedAt: freezed == earnedAt
          ? _self.earnedAt
          : earnedAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
      isEarned: null == isEarned
          ? _self.isEarned
          : isEarned // ignore: cast_nullable_to_non_nullable
              as bool,
      progress: null == progress
          ? _self.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
mixin _$StatsModel {
  @JsonKey(name: 'total_xp')
  int get totalXp;
  @JsonKey(name: 'current_streak')
  int get currentStreak;
  @JsonKey(name: 'longest_streak')
  int get longestStreak;
  @JsonKey(name: 'lessons_completed')
  int get lessonsCompleted;
  @JsonKey(name: 'ayahs_read')
  int get ayahsRead;
  @JsonKey(name: 'flashcards_reviewed')
  int get flashcardsReviewed;
  @JsonKey(name: 'recitation_sessions')
  int get recitationSessions;
  @JsonKey(name: 'words_learned')
  int get wordsLearned;
  @JsonKey(name: 'accuracy_rate')
  double get accuracyRate;
  @JsonKey(name: 'streak_calendar')
  List<StreakDay> get streakCalendar;

  /// Create a copy of StatsModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $StatsModelCopyWith<StatsModel> get copyWith =>
      _$StatsModelCopyWithImpl<StatsModel>(this as StatsModel, _$identity);

  /// Serializes this StatsModel to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is StatsModel &&
            (identical(other.totalXp, totalXp) || other.totalXp == totalXp) &&
            (identical(other.currentStreak, currentStreak) ||
                other.currentStreak == currentStreak) &&
            (identical(other.longestStreak, longestStreak) ||
                other.longestStreak == longestStreak) &&
            (identical(other.lessonsCompleted, lessonsCompleted) ||
                other.lessonsCompleted == lessonsCompleted) &&
            (identical(other.ayahsRead, ayahsRead) ||
                other.ayahsRead == ayahsRead) &&
            (identical(other.flashcardsReviewed, flashcardsReviewed) ||
                other.flashcardsReviewed == flashcardsReviewed) &&
            (identical(other.recitationSessions, recitationSessions) ||
                other.recitationSessions == recitationSessions) &&
            (identical(other.wordsLearned, wordsLearned) ||
                other.wordsLearned == wordsLearned) &&
            (identical(other.accuracyRate, accuracyRate) ||
                other.accuracyRate == accuracyRate) &&
            const DeepCollectionEquality()
                .equals(other.streakCalendar, streakCalendar));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      totalXp,
      currentStreak,
      longestStreak,
      lessonsCompleted,
      ayahsRead,
      flashcardsReviewed,
      recitationSessions,
      wordsLearned,
      accuracyRate,
      const DeepCollectionEquality().hash(streakCalendar));

  @override
  String toString() {
    return 'StatsModel(totalXp: $totalXp, currentStreak: $currentStreak, longestStreak: $longestStreak, lessonsCompleted: $lessonsCompleted, ayahsRead: $ayahsRead, flashcardsReviewed: $flashcardsReviewed, recitationSessions: $recitationSessions, wordsLearned: $wordsLearned, accuracyRate: $accuracyRate, streakCalendar: $streakCalendar)';
  }
}

/// @nodoc
abstract mixin class $StatsModelCopyWith<$Res> {
  factory $StatsModelCopyWith(
          StatsModel value, $Res Function(StatsModel) _then) =
      _$StatsModelCopyWithImpl;
  @useResult
  $Res call(
      {@JsonKey(name: 'total_xp') int totalXp,
      @JsonKey(name: 'current_streak') int currentStreak,
      @JsonKey(name: 'longest_streak') int longestStreak,
      @JsonKey(name: 'lessons_completed') int lessonsCompleted,
      @JsonKey(name: 'ayahs_read') int ayahsRead,
      @JsonKey(name: 'flashcards_reviewed') int flashcardsReviewed,
      @JsonKey(name: 'recitation_sessions') int recitationSessions,
      @JsonKey(name: 'words_learned') int wordsLearned,
      @JsonKey(name: 'accuracy_rate') double accuracyRate,
      @JsonKey(name: 'streak_calendar') List<StreakDay> streakCalendar});
}

/// @nodoc
class _$StatsModelCopyWithImpl<$Res> implements $StatsModelCopyWith<$Res> {
  _$StatsModelCopyWithImpl(this._self, this._then);

  final StatsModel _self;
  final $Res Function(StatsModel) _then;

  /// Create a copy of StatsModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalXp = null,
    Object? currentStreak = null,
    Object? longestStreak = null,
    Object? lessonsCompleted = null,
    Object? ayahsRead = null,
    Object? flashcardsReviewed = null,
    Object? recitationSessions = null,
    Object? wordsLearned = null,
    Object? accuracyRate = null,
    Object? streakCalendar = null,
  }) {
    return _then(_self.copyWith(
      totalXp: null == totalXp
          ? _self.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      currentStreak: null == currentStreak
          ? _self.currentStreak
          : currentStreak // ignore: cast_nullable_to_non_nullable
              as int,
      longestStreak: null == longestStreak
          ? _self.longestStreak
          : longestStreak // ignore: cast_nullable_to_non_nullable
              as int,
      lessonsCompleted: null == lessonsCompleted
          ? _self.lessonsCompleted
          : lessonsCompleted // ignore: cast_nullable_to_non_nullable
              as int,
      ayahsRead: null == ayahsRead
          ? _self.ayahsRead
          : ayahsRead // ignore: cast_nullable_to_non_nullable
              as int,
      flashcardsReviewed: null == flashcardsReviewed
          ? _self.flashcardsReviewed
          : flashcardsReviewed // ignore: cast_nullable_to_non_nullable
              as int,
      recitationSessions: null == recitationSessions
          ? _self.recitationSessions
          : recitationSessions // ignore: cast_nullable_to_non_nullable
              as int,
      wordsLearned: null == wordsLearned
          ? _self.wordsLearned
          : wordsLearned // ignore: cast_nullable_to_non_nullable
              as int,
      accuracyRate: null == accuracyRate
          ? _self.accuracyRate
          : accuracyRate // ignore: cast_nullable_to_non_nullable
              as double,
      streakCalendar: null == streakCalendar
          ? _self.streakCalendar
          : streakCalendar // ignore: cast_nullable_to_non_nullable
              as List<StreakDay>,
    ));
  }
}

/// Adds pattern-matching-related methods to [StatsModel].
extension StatsModelPatterns on StatsModel {
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
    TResult Function(_StatsModel value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _StatsModel() when $default != null:
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
    TResult Function(_StatsModel value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _StatsModel():
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
    TResult? Function(_StatsModel value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _StatsModel() when $default != null:
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
            @JsonKey(name: 'total_xp') int totalXp,
            @JsonKey(name: 'current_streak') int currentStreak,
            @JsonKey(name: 'longest_streak') int longestStreak,
            @JsonKey(name: 'lessons_completed') int lessonsCompleted,
            @JsonKey(name: 'ayahs_read') int ayahsRead,
            @JsonKey(name: 'flashcards_reviewed') int flashcardsReviewed,
            @JsonKey(name: 'recitation_sessions') int recitationSessions,
            @JsonKey(name: 'words_learned') int wordsLearned,
            @JsonKey(name: 'accuracy_rate') double accuracyRate,
            @JsonKey(name: 'streak_calendar') List<StreakDay> streakCalendar)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _StatsModel() when $default != null:
        return $default(
            _that.totalXp,
            _that.currentStreak,
            _that.longestStreak,
            _that.lessonsCompleted,
            _that.ayahsRead,
            _that.flashcardsReviewed,
            _that.recitationSessions,
            _that.wordsLearned,
            _that.accuracyRate,
            _that.streakCalendar);
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
            @JsonKey(name: 'total_xp') int totalXp,
            @JsonKey(name: 'current_streak') int currentStreak,
            @JsonKey(name: 'longest_streak') int longestStreak,
            @JsonKey(name: 'lessons_completed') int lessonsCompleted,
            @JsonKey(name: 'ayahs_read') int ayahsRead,
            @JsonKey(name: 'flashcards_reviewed') int flashcardsReviewed,
            @JsonKey(name: 'recitation_sessions') int recitationSessions,
            @JsonKey(name: 'words_learned') int wordsLearned,
            @JsonKey(name: 'accuracy_rate') double accuracyRate,
            @JsonKey(name: 'streak_calendar') List<StreakDay> streakCalendar)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _StatsModel():
        return $default(
            _that.totalXp,
            _that.currentStreak,
            _that.longestStreak,
            _that.lessonsCompleted,
            _that.ayahsRead,
            _that.flashcardsReviewed,
            _that.recitationSessions,
            _that.wordsLearned,
            _that.accuracyRate,
            _that.streakCalendar);
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
            @JsonKey(name: 'total_xp') int totalXp,
            @JsonKey(name: 'current_streak') int currentStreak,
            @JsonKey(name: 'longest_streak') int longestStreak,
            @JsonKey(name: 'lessons_completed') int lessonsCompleted,
            @JsonKey(name: 'ayahs_read') int ayahsRead,
            @JsonKey(name: 'flashcards_reviewed') int flashcardsReviewed,
            @JsonKey(name: 'recitation_sessions') int recitationSessions,
            @JsonKey(name: 'words_learned') int wordsLearned,
            @JsonKey(name: 'accuracy_rate') double accuracyRate,
            @JsonKey(name: 'streak_calendar') List<StreakDay> streakCalendar)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _StatsModel() when $default != null:
        return $default(
            _that.totalXp,
            _that.currentStreak,
            _that.longestStreak,
            _that.lessonsCompleted,
            _that.ayahsRead,
            _that.flashcardsReviewed,
            _that.recitationSessions,
            _that.wordsLearned,
            _that.accuracyRate,
            _that.streakCalendar);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _StatsModel implements StatsModel {
  const _StatsModel(
      {@JsonKey(name: 'total_xp') this.totalXp = 0,
      @JsonKey(name: 'current_streak') this.currentStreak = 0,
      @JsonKey(name: 'longest_streak') this.longestStreak = 0,
      @JsonKey(name: 'lessons_completed') this.lessonsCompleted = 0,
      @JsonKey(name: 'ayahs_read') this.ayahsRead = 0,
      @JsonKey(name: 'flashcards_reviewed') this.flashcardsReviewed = 0,
      @JsonKey(name: 'recitation_sessions') this.recitationSessions = 0,
      @JsonKey(name: 'words_learned') this.wordsLearned = 0,
      @JsonKey(name: 'accuracy_rate') this.accuracyRate = 0.0,
      @JsonKey(name: 'streak_calendar')
      final List<StreakDay> streakCalendar = const []})
      : _streakCalendar = streakCalendar;
  factory _StatsModel.fromJson(Map<String, dynamic> json) =>
      _$StatsModelFromJson(json);

  @override
  @JsonKey(name: 'total_xp')
  final int totalXp;
  @override
  @JsonKey(name: 'current_streak')
  final int currentStreak;
  @override
  @JsonKey(name: 'longest_streak')
  final int longestStreak;
  @override
  @JsonKey(name: 'lessons_completed')
  final int lessonsCompleted;
  @override
  @JsonKey(name: 'ayahs_read')
  final int ayahsRead;
  @override
  @JsonKey(name: 'flashcards_reviewed')
  final int flashcardsReviewed;
  @override
  @JsonKey(name: 'recitation_sessions')
  final int recitationSessions;
  @override
  @JsonKey(name: 'words_learned')
  final int wordsLearned;
  @override
  @JsonKey(name: 'accuracy_rate')
  final double accuracyRate;
  final List<StreakDay> _streakCalendar;
  @override
  @JsonKey(name: 'streak_calendar')
  List<StreakDay> get streakCalendar {
    if (_streakCalendar is EqualUnmodifiableListView) return _streakCalendar;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_streakCalendar);
  }

  /// Create a copy of StatsModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$StatsModelCopyWith<_StatsModel> get copyWith =>
      __$StatsModelCopyWithImpl<_StatsModel>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$StatsModelToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _StatsModel &&
            (identical(other.totalXp, totalXp) || other.totalXp == totalXp) &&
            (identical(other.currentStreak, currentStreak) ||
                other.currentStreak == currentStreak) &&
            (identical(other.longestStreak, longestStreak) ||
                other.longestStreak == longestStreak) &&
            (identical(other.lessonsCompleted, lessonsCompleted) ||
                other.lessonsCompleted == lessonsCompleted) &&
            (identical(other.ayahsRead, ayahsRead) ||
                other.ayahsRead == ayahsRead) &&
            (identical(other.flashcardsReviewed, flashcardsReviewed) ||
                other.flashcardsReviewed == flashcardsReviewed) &&
            (identical(other.recitationSessions, recitationSessions) ||
                other.recitationSessions == recitationSessions) &&
            (identical(other.wordsLearned, wordsLearned) ||
                other.wordsLearned == wordsLearned) &&
            (identical(other.accuracyRate, accuracyRate) ||
                other.accuracyRate == accuracyRate) &&
            const DeepCollectionEquality()
                .equals(other._streakCalendar, _streakCalendar));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      totalXp,
      currentStreak,
      longestStreak,
      lessonsCompleted,
      ayahsRead,
      flashcardsReviewed,
      recitationSessions,
      wordsLearned,
      accuracyRate,
      const DeepCollectionEquality().hash(_streakCalendar));

  @override
  String toString() {
    return 'StatsModel(totalXp: $totalXp, currentStreak: $currentStreak, longestStreak: $longestStreak, lessonsCompleted: $lessonsCompleted, ayahsRead: $ayahsRead, flashcardsReviewed: $flashcardsReviewed, recitationSessions: $recitationSessions, wordsLearned: $wordsLearned, accuracyRate: $accuracyRate, streakCalendar: $streakCalendar)';
  }
}

/// @nodoc
abstract mixin class _$StatsModelCopyWith<$Res>
    implements $StatsModelCopyWith<$Res> {
  factory _$StatsModelCopyWith(
          _StatsModel value, $Res Function(_StatsModel) _then) =
      __$StatsModelCopyWithImpl;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'total_xp') int totalXp,
      @JsonKey(name: 'current_streak') int currentStreak,
      @JsonKey(name: 'longest_streak') int longestStreak,
      @JsonKey(name: 'lessons_completed') int lessonsCompleted,
      @JsonKey(name: 'ayahs_read') int ayahsRead,
      @JsonKey(name: 'flashcards_reviewed') int flashcardsReviewed,
      @JsonKey(name: 'recitation_sessions') int recitationSessions,
      @JsonKey(name: 'words_learned') int wordsLearned,
      @JsonKey(name: 'accuracy_rate') double accuracyRate,
      @JsonKey(name: 'streak_calendar') List<StreakDay> streakCalendar});
}

/// @nodoc
class __$StatsModelCopyWithImpl<$Res> implements _$StatsModelCopyWith<$Res> {
  __$StatsModelCopyWithImpl(this._self, this._then);

  final _StatsModel _self;
  final $Res Function(_StatsModel) _then;

  /// Create a copy of StatsModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? totalXp = null,
    Object? currentStreak = null,
    Object? longestStreak = null,
    Object? lessonsCompleted = null,
    Object? ayahsRead = null,
    Object? flashcardsReviewed = null,
    Object? recitationSessions = null,
    Object? wordsLearned = null,
    Object? accuracyRate = null,
    Object? streakCalendar = null,
  }) {
    return _then(_StatsModel(
      totalXp: null == totalXp
          ? _self.totalXp
          : totalXp // ignore: cast_nullable_to_non_nullable
              as int,
      currentStreak: null == currentStreak
          ? _self.currentStreak
          : currentStreak // ignore: cast_nullable_to_non_nullable
              as int,
      longestStreak: null == longestStreak
          ? _self.longestStreak
          : longestStreak // ignore: cast_nullable_to_non_nullable
              as int,
      lessonsCompleted: null == lessonsCompleted
          ? _self.lessonsCompleted
          : lessonsCompleted // ignore: cast_nullable_to_non_nullable
              as int,
      ayahsRead: null == ayahsRead
          ? _self.ayahsRead
          : ayahsRead // ignore: cast_nullable_to_non_nullable
              as int,
      flashcardsReviewed: null == flashcardsReviewed
          ? _self.flashcardsReviewed
          : flashcardsReviewed // ignore: cast_nullable_to_non_nullable
              as int,
      recitationSessions: null == recitationSessions
          ? _self.recitationSessions
          : recitationSessions // ignore: cast_nullable_to_non_nullable
              as int,
      wordsLearned: null == wordsLearned
          ? _self.wordsLearned
          : wordsLearned // ignore: cast_nullable_to_non_nullable
              as int,
      accuracyRate: null == accuracyRate
          ? _self.accuracyRate
          : accuracyRate // ignore: cast_nullable_to_non_nullable
              as double,
      streakCalendar: null == streakCalendar
          ? _self._streakCalendar
          : streakCalendar // ignore: cast_nullable_to_non_nullable
              as List<StreakDay>,
    ));
  }
}

/// @nodoc
mixin _$StreakDay {
  DateTime get date;
  @JsonKey(name: 'is_active')
  bool get isActive;
  @JsonKey(name: 'xp_earned')
  int get xpEarned;
  @JsonKey(name: 'goal_met')
  bool get goalMet;

  /// Create a copy of StreakDay
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  $StreakDayCopyWith<StreakDay> get copyWith =>
      _$StreakDayCopyWithImpl<StreakDay>(this as StreakDay, _$identity);

  /// Serializes this StreakDay to a JSON map.
  Map<String, dynamic> toJson();

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is StreakDay &&
            (identical(other.date, date) || other.date == date) &&
            (identical(other.isActive, isActive) ||
                other.isActive == isActive) &&
            (identical(other.xpEarned, xpEarned) ||
                other.xpEarned == xpEarned) &&
            (identical(other.goalMet, goalMet) || other.goalMet == goalMet));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, date, isActive, xpEarned, goalMet);

  @override
  String toString() {
    return 'StreakDay(date: $date, isActive: $isActive, xpEarned: $xpEarned, goalMet: $goalMet)';
  }
}

/// @nodoc
abstract mixin class $StreakDayCopyWith<$Res> {
  factory $StreakDayCopyWith(StreakDay value, $Res Function(StreakDay) _then) =
      _$StreakDayCopyWithImpl;
  @useResult
  $Res call(
      {DateTime date,
      @JsonKey(name: 'is_active') bool isActive,
      @JsonKey(name: 'xp_earned') int xpEarned,
      @JsonKey(name: 'goal_met') bool goalMet});
}

/// @nodoc
class _$StreakDayCopyWithImpl<$Res> implements $StreakDayCopyWith<$Res> {
  _$StreakDayCopyWithImpl(this._self, this._then);

  final StreakDay _self;
  final $Res Function(StreakDay) _then;

  /// Create a copy of StreakDay
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? date = null,
    Object? isActive = null,
    Object? xpEarned = null,
    Object? goalMet = null,
  }) {
    return _then(_self.copyWith(
      date: null == date
          ? _self.date
          : date // ignore: cast_nullable_to_non_nullable
              as DateTime,
      isActive: null == isActive
          ? _self.isActive
          : isActive // ignore: cast_nullable_to_non_nullable
              as bool,
      xpEarned: null == xpEarned
          ? _self.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      goalMet: null == goalMet
          ? _self.goalMet
          : goalMet // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// Adds pattern-matching-related methods to [StreakDay].
extension StreakDayPatterns on StreakDay {
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
    TResult Function(_StreakDay value)? $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _StreakDay() when $default != null:
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
    TResult Function(_StreakDay value) $default,
  ) {
    final _that = this;
    switch (_that) {
      case _StreakDay():
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
    TResult? Function(_StreakDay value)? $default,
  ) {
    final _that = this;
    switch (_that) {
      case _StreakDay() when $default != null:
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
            DateTime date,
            @JsonKey(name: 'is_active') bool isActive,
            @JsonKey(name: 'xp_earned') int xpEarned,
            @JsonKey(name: 'goal_met') bool goalMet)?
        $default, {
    required TResult orElse(),
  }) {
    final _that = this;
    switch (_that) {
      case _StreakDay() when $default != null:
        return $default(
            _that.date, _that.isActive, _that.xpEarned, _that.goalMet);
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
            DateTime date,
            @JsonKey(name: 'is_active') bool isActive,
            @JsonKey(name: 'xp_earned') int xpEarned,
            @JsonKey(name: 'goal_met') bool goalMet)
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _StreakDay():
        return $default(
            _that.date, _that.isActive, _that.xpEarned, _that.goalMet);
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
            DateTime date,
            @JsonKey(name: 'is_active') bool isActive,
            @JsonKey(name: 'xp_earned') int xpEarned,
            @JsonKey(name: 'goal_met') bool goalMet)?
        $default,
  ) {
    final _that = this;
    switch (_that) {
      case _StreakDay() when $default != null:
        return $default(
            _that.date, _that.isActive, _that.xpEarned, _that.goalMet);
      case _:
        return null;
    }
  }
}

/// @nodoc
@JsonSerializable()
class _StreakDay implements StreakDay {
  const _StreakDay(
      {required this.date,
      @JsonKey(name: 'is_active') this.isActive = false,
      @JsonKey(name: 'xp_earned') this.xpEarned = 0,
      @JsonKey(name: 'goal_met') this.goalMet = false});
  factory _StreakDay.fromJson(Map<String, dynamic> json) =>
      _$StreakDayFromJson(json);

  @override
  final DateTime date;
  @override
  @JsonKey(name: 'is_active')
  final bool isActive;
  @override
  @JsonKey(name: 'xp_earned')
  final int xpEarned;
  @override
  @JsonKey(name: 'goal_met')
  final bool goalMet;

  /// Create a copy of StreakDay
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  @pragma('vm:prefer-inline')
  _$StreakDayCopyWith<_StreakDay> get copyWith =>
      __$StreakDayCopyWithImpl<_StreakDay>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$StreakDayToJson(
      this,
    );
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _StreakDay &&
            (identical(other.date, date) || other.date == date) &&
            (identical(other.isActive, isActive) ||
                other.isActive == isActive) &&
            (identical(other.xpEarned, xpEarned) ||
                other.xpEarned == xpEarned) &&
            (identical(other.goalMet, goalMet) || other.goalMet == goalMet));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, date, isActive, xpEarned, goalMet);

  @override
  String toString() {
    return 'StreakDay(date: $date, isActive: $isActive, xpEarned: $xpEarned, goalMet: $goalMet)';
  }
}

/// @nodoc
abstract mixin class _$StreakDayCopyWith<$Res>
    implements $StreakDayCopyWith<$Res> {
  factory _$StreakDayCopyWith(
          _StreakDay value, $Res Function(_StreakDay) _then) =
      __$StreakDayCopyWithImpl;
  @override
  @useResult
  $Res call(
      {DateTime date,
      @JsonKey(name: 'is_active') bool isActive,
      @JsonKey(name: 'xp_earned') int xpEarned,
      @JsonKey(name: 'goal_met') bool goalMet});
}

/// @nodoc
class __$StreakDayCopyWithImpl<$Res> implements _$StreakDayCopyWith<$Res> {
  __$StreakDayCopyWithImpl(this._self, this._then);

  final _StreakDay _self;
  final $Res Function(_StreakDay) _then;

  /// Create a copy of StreakDay
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $Res call({
    Object? date = null,
    Object? isActive = null,
    Object? xpEarned = null,
    Object? goalMet = null,
  }) {
    return _then(_StreakDay(
      date: null == date
          ? _self.date
          : date // ignore: cast_nullable_to_non_nullable
              as DateTime,
      isActive: null == isActive
          ? _self.isActive
          : isActive // ignore: cast_nullable_to_non_nullable
              as bool,
      xpEarned: null == xpEarned
          ? _self.xpEarned
          : xpEarned // ignore: cast_nullable_to_non_nullable
              as int,
      goalMet: null == goalMet
          ? _self.goalMet
          : goalMet // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

// dart format on
