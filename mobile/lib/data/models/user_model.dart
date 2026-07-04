import 'package:freezed_annotation/freezed_annotation.dart';

part 'user_model.freezed.dart';
part 'user_model.g.dart';

/// Represents the authenticated user.
@freezed
class UserModel with _$UserModel {
  const factory UserModel({
    @JsonKey(name: 'user_id') required String userId,
    @JsonKey(name: 'email') String? email,
    @JsonKey(name: 'display_name') String? displayName,
    @JsonKey(name: 'avatar_url') String? avatarUrl,
    @JsonKey(name: 'selected_language') @Default('en') String selectedLanguage,
    @JsonKey(name: 'learning_path') @Default('foundation') String learningPath,
    @JsonKey(name: 'total_xp') @Default(0) int totalXp,
    @JsonKey(name: 'current_streak') @Default(0) int currentStreak,
    @JsonKey(name: 'longest_streak') @Default(0) int longestStreak,
    @JsonKey(name: 'daily_goal') @Default(5) int dailyGoal,
    @JsonKey(name: 'lessons_completed') @Default(0) int lessonsCompleted,
    @JsonKey(name: 'ayahs_read') @Default(0) int ayahsRead,
    @JsonKey(name: 'flashcards_reviewed') @Default(0) int flashcardsReviewed,
    @JsonKey(name: 'recitation_sessions') @Default(0) int recitationSessions,
    @JsonKey(name: 'created_at') required DateTime createdAt,
  }) = _UserModel;

  factory UserModel.fromJson(Map<String, dynamic> json) =>
      _$UserModelFromJson(json);
}

/// Represents the home screen response data.
@freezed
class HomeResponse with _$HomeResponse {
  const factory HomeResponse({
    required UserModel user,
    @JsonKey(name: 'streak_count') @Default(0) int streakCount,
    @JsonKey(name: 'xp_today') @Default(0) int xpToday,
    @JsonKey(name: 'xp_weekly_goal') @Default(100) int xpWeeklyGoal,
    @JsonKey(name: 'daily_goal') @Default(5) int dailyGoal,
    @JsonKey(name: 'daily_goal_progress') @Default(0) int dailyGoalProgress,
    @JsonKey(name: 'continue_lesson') LessonProgress? continueLesson,
    @JsonKey(name: 'flashcards_due') @Default(0) int flashcardsDue,
    @JsonKey(name: 'learning_path') @Default([]) List<PathNode> learningPath,
    @JsonKey(name: 'recent_achievements') @Default([]) List<Achievement> recentAchievements,
  }) = _HomeResponse;

  factory HomeResponse.fromJson(Map<String, dynamic> json) =>
      _$HomeResponseFromJson(json);
}

/// Represents a lesson progress item for the Continue card.
@freezed
class LessonProgress with _$LessonProgress {
  const factory LessonProgress({
    @JsonKey(name: 'lesson_id') required int lessonId,
    required String title,
    @JsonKey(name: 'module_number') required int moduleNumber,
    @JsonKey(name: 'lesson_number') required int lessonNumber,
    @JsonKey(name: 'progress_percent') @Default(0) double progressPercent,
    @JsonKey(name: 'icon_name') @Default('book') String iconName,
  }) = _LessonProgress;

  factory LessonProgress.fromJson(Map<String, dynamic> json) =>
      _$LessonProgressFromJson(json);
}

/// Represents a node in the learning path map.
@freezed
class PathNode with _$PathNode {
  const factory PathNode({
    required String id,
    required String label,
    @JsonKey(name: 'label_urdu') String? labelUrdu,
    required PathNodeType type,
    @JsonKey(name: 'is_completed') @Default(false) bool isCompleted,
    @JsonKey(name: 'is_current') @Default(false) bool isCurrent,
    @JsonKey(name: 'is_locked') @Default(false) bool isLocked,
    @JsonKey(name: 'xp_reward') @Default(10) int xpReward,
    @JsonKey(name: 'icon_name') @Default('star') String iconName,
    @JsonKey(name: 'lesson_id') int? lessonId,
  }) = _PathNode;

  factory PathNode.fromJson(Map<String, dynamic> json) =>
      _$PathNodeFromJson(json);
}

/// Types of nodes in the learning path.
enum PathNodeType {
  @JsonValue('lesson') lesson,
  @JsonValue('quiz') quiz,
  @JsonValue('practice') practice,
  @JsonValue('checkpoint') checkpoint,
  @JsonValue('bonus') bonus,
}

/// Represents an achievement/badge.
@freezed
class Achievement with _$Achievement {
  const factory Achievement({
    required String id,
    required String title,
    @JsonKey(name: 'title_urdu') String? titleUrdu,
    required String description,
    @JsonKey(name: 'description_urdu') String? descriptionUrdu,
    @JsonKey(name: 'icon_name') @Default('emoji_events') String iconName,
    @JsonKey(name: 'earned_at') DateTime? earnedAt,
    @JsonKey(name: 'is_earned') @Default(false) bool isEarned,
    @JsonKey(name: 'progress') @Default(0) double progress,
  }) = _Achievement;

  factory Achievement.fromJson(Map<String, dynamic> json) =>
      _$AchievementFromJson(json);
}

/// Represents user statistics.
@freezed
class StatsModel with _$StatsModel {
  const factory StatsModel({
    @JsonKey(name: 'total_xp') @Default(0) int totalXp,
    @JsonKey(name: 'current_streak') @Default(0) int currentStreak,
    @JsonKey(name: 'longest_streak') @Default(0) int longestStreak,
    @JsonKey(name: 'lessons_completed') @Default(0) int lessonsCompleted,
    @JsonKey(name: 'ayahs_read') @Default(0) int ayahsRead,
    @JsonKey(name: 'flashcards_reviewed') @Default(0) int flashcardsReviewed,
    @JsonKey(name: 'recitation_sessions') @Default(0) int recitationSessions,
    @JsonKey(name: 'words_learned') @Default(0) int wordsLearned,
    @JsonKey(name: 'accuracy_rate') @Default(0.0) double accuracyRate,
    @JsonKey(name: 'streak_calendar') @Default([]) List<StreakDay> streakCalendar,
  }) = _StatsModel;

  factory StatsModel.fromJson(Map<String, dynamic> json) =>
      _$StatsModelFromJson(json);
}

/// Represents a single day in the streak calendar.
@freezed
class StreakDay with _$StreakDay {
  const factory StreakDay({
    required DateTime date,
    @JsonKey(name: 'is_active') @Default(false) bool isActive,
    @JsonKey(name: 'xp_earned') @Default(0) int xpEarned,
    @JsonKey(name: 'goal_met') @Default(false) bool goalMet,
  }) = _StreakDay;

  factory StreakDay.fromJson(Map<String, dynamic> json) =>
      _$StreakDayFromJson(json);
}
