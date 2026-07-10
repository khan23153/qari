// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'user_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_UserModel _$UserModelFromJson(Map<String, dynamic> json) => _UserModel(
      userId: json['user_id'] as String,
      email: json['email'] as String?,
      displayName: json['display_name'] as String?,
      avatarUrl: json['avatar_url'] as String?,
      selectedLanguage: json['selected_language'] as String? ?? 'en',
      learningPath: json['learning_path'] as String? ?? 'foundation',
      totalXp: (json['total_xp'] as num?)?.toInt() ?? 0,
      currentStreak: (json['current_streak'] as num?)?.toInt() ?? 0,
      longestStreak: (json['longest_streak'] as num?)?.toInt() ?? 0,
      dailyGoal: (json['daily_goal'] as num?)?.toInt() ?? 5,
      lessonsCompleted: (json['lessons_completed'] as num?)?.toInt() ?? 0,
      ayahsRead: (json['ayahs_read'] as num?)?.toInt() ?? 0,
      flashcardsReviewed: (json['flashcards_reviewed'] as num?)?.toInt() ?? 0,
      recitationSessions: (json['recitation_sessions'] as num?)?.toInt() ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
    );

Map<String, dynamic> _$UserModelToJson(_UserModel instance) =>
    <String, dynamic>{
      'user_id': instance.userId,
      'email': instance.email,
      'display_name': instance.displayName,
      'avatar_url': instance.avatarUrl,
      'selected_language': instance.selectedLanguage,
      'learning_path': instance.learningPath,
      'total_xp': instance.totalXp,
      'current_streak': instance.currentStreak,
      'longest_streak': instance.longestStreak,
      'daily_goal': instance.dailyGoal,
      'lessons_completed': instance.lessonsCompleted,
      'ayahs_read': instance.ayahsRead,
      'flashcards_reviewed': instance.flashcardsReviewed,
      'recitation_sessions': instance.recitationSessions,
      'created_at': instance.createdAt.toIso8601String(),
    };

_HomeResponse _$HomeResponseFromJson(Map<String, dynamic> json) =>
    _HomeResponse(
      user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
      streakCount: (json['streak_count'] as num?)?.toInt() ?? 0,
      xpToday: (json['xp_today'] as num?)?.toInt() ?? 0,
      xpWeeklyGoal: (json['xp_weekly_goal'] as num?)?.toInt() ?? 100,
      dailyGoal: (json['daily_goal'] as num?)?.toInt() ?? 5,
      dailyGoalProgress: (json['daily_goal_progress'] as num?)?.toInt() ?? 0,
      continueLesson: json['continue_lesson'] == null
          ? null
          : LessonProgress.fromJson(
              json['continue_lesson'] as Map<String, dynamic>),
      flashcardsDue: (json['flashcards_due'] as num?)?.toInt() ?? 0,
      learningPath: (json['learning_path'] as List<dynamic>?)
              ?.map((e) => PathNode.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      recentAchievements: (json['recent_achievements'] as List<dynamic>?)
              ?.map((e) => Achievement.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$HomeResponseToJson(_HomeResponse instance) =>
    <String, dynamic>{
      'user': instance.user,
      'streak_count': instance.streakCount,
      'xp_today': instance.xpToday,
      'xp_weekly_goal': instance.xpWeeklyGoal,
      'daily_goal': instance.dailyGoal,
      'daily_goal_progress': instance.dailyGoalProgress,
      'continue_lesson': instance.continueLesson,
      'flashcards_due': instance.flashcardsDue,
      'learning_path': instance.learningPath,
      'recent_achievements': instance.recentAchievements,
    };

_LessonProgress _$LessonProgressFromJson(Map<String, dynamic> json) =>
    _LessonProgress(
      lessonId: (json['lesson_id'] as num).toInt(),
      title: json['title'] as String,
      moduleNumber: (json['module_number'] as num).toInt(),
      lessonNumber: (json['lesson_number'] as num).toInt(),
      progressPercent: (json['progress_percent'] as num?)?.toDouble() ?? 0,
      iconName: json['icon_name'] as String? ?? 'book',
    );

Map<String, dynamic> _$LessonProgressToJson(_LessonProgress instance) =>
    <String, dynamic>{
      'lesson_id': instance.lessonId,
      'title': instance.title,
      'module_number': instance.moduleNumber,
      'lesson_number': instance.lessonNumber,
      'progress_percent': instance.progressPercent,
      'icon_name': instance.iconName,
    };

_PathNode _$PathNodeFromJson(Map<String, dynamic> json) => _PathNode(
      id: json['id'] as String,
      label: json['label'] as String,
      labelUrdu: json['label_urdu'] as String?,
      type: $enumDecode(_$PathNodeTypeEnumMap, json['type']),
      isCompleted: json['is_completed'] as bool? ?? false,
      isCurrent: json['is_current'] as bool? ?? false,
      isLocked: json['is_locked'] as bool? ?? false,
      xpReward: (json['xp_reward'] as num?)?.toInt() ?? 10,
      iconName: json['icon_name'] as String? ?? 'star',
      lessonId: (json['lesson_id'] as num?)?.toInt(),
    );

Map<String, dynamic> _$PathNodeToJson(_PathNode instance) => <String, dynamic>{
      'id': instance.id,
      'label': instance.label,
      'label_urdu': instance.labelUrdu,
      'type': _$PathNodeTypeEnumMap[instance.type]!,
      'is_completed': instance.isCompleted,
      'is_current': instance.isCurrent,
      'is_locked': instance.isLocked,
      'xp_reward': instance.xpReward,
      'icon_name': instance.iconName,
      'lesson_id': instance.lessonId,
    };

const _$PathNodeTypeEnumMap = {
  PathNodeType.lesson: 'lesson',
  PathNodeType.quiz: 'quiz',
  PathNodeType.practice: 'practice',
  PathNodeType.checkpoint: 'checkpoint',
  PathNodeType.bonus: 'bonus',
};

_Achievement _$AchievementFromJson(Map<String, dynamic> json) => _Achievement(
      id: json['id'] as String,
      title: json['title'] as String,
      titleUrdu: json['title_urdu'] as String?,
      description: json['description'] as String,
      descriptionUrdu: json['description_urdu'] as String?,
      iconName: json['icon_name'] as String? ?? 'emoji_events',
      earnedAt: json['earned_at'] == null
          ? null
          : DateTime.parse(json['earned_at'] as String),
      isEarned: json['is_earned'] as bool? ?? false,
      progress: (json['progress'] as num?)?.toDouble() ?? 0,
    );

Map<String, dynamic> _$AchievementToJson(_Achievement instance) =>
    <String, dynamic>{
      'id': instance.id,
      'title': instance.title,
      'title_urdu': instance.titleUrdu,
      'description': instance.description,
      'description_urdu': instance.descriptionUrdu,
      'icon_name': instance.iconName,
      'earned_at': instance.earnedAt?.toIso8601String(),
      'is_earned': instance.isEarned,
      'progress': instance.progress,
    };

_StatsModel _$StatsModelFromJson(Map<String, dynamic> json) => _StatsModel(
      totalXp: (json['total_xp'] as num?)?.toInt() ?? 0,
      currentStreak: (json['current_streak'] as num?)?.toInt() ?? 0,
      longestStreak: (json['longest_streak'] as num?)?.toInt() ?? 0,
      lessonsCompleted: (json['lessons_completed'] as num?)?.toInt() ?? 0,
      ayahsRead: (json['ayahs_read'] as num?)?.toInt() ?? 0,
      flashcardsReviewed: (json['flashcards_reviewed'] as num?)?.toInt() ?? 0,
      recitationSessions: (json['recitation_sessions'] as num?)?.toInt() ?? 0,
      wordsLearned: (json['words_learned'] as num?)?.toInt() ?? 0,
      accuracyRate: (json['accuracy_rate'] as num?)?.toDouble() ?? 0.0,
      streakCalendar: (json['streak_calendar'] as List<dynamic>?)
              ?.map((e) => StreakDay.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$StatsModelToJson(_StatsModel instance) =>
    <String, dynamic>{
      'total_xp': instance.totalXp,
      'current_streak': instance.currentStreak,
      'longest_streak': instance.longestStreak,
      'lessons_completed': instance.lessonsCompleted,
      'ayahs_read': instance.ayahsRead,
      'flashcards_reviewed': instance.flashcardsReviewed,
      'recitation_sessions': instance.recitationSessions,
      'words_learned': instance.wordsLearned,
      'accuracy_rate': instance.accuracyRate,
      'streak_calendar': instance.streakCalendar,
    };

_StreakDay _$StreakDayFromJson(Map<String, dynamic> json) => _StreakDay(
      date: DateTime.parse(json['date'] as String),
      isActive: json['is_active'] as bool? ?? false,
      xpEarned: (json['xp_earned'] as num?)?.toInt() ?? 0,
      goalMet: json['goal_met'] as bool? ?? false,
    );

Map<String, dynamic> _$StreakDayToJson(_StreakDay instance) =>
    <String, dynamic>{
      'date': instance.date.toIso8601String(),
      'is_active': instance.isActive,
      'xp_earned': instance.xpEarned,
      'goal_met': instance.goalMet,
    };
