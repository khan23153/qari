import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../services/api_client.dart';
import '../models/lesson_model.dart';

/// Repository for lessons and learning modules.
class LessonRepository {
  final ApiClient _client;

  LessonRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Fetches all lessons for the foundation path.
  Future<List<LessonModel>> getLessons({
    int? moduleNumber,
    String? path,
  }) async {
    try {
      final response = await _client.get(
        '/lessons',
        queryParameters: {
          if (moduleNumber != null) 'module': moduleNumber,
          if (path != null) 'path': path,
        },
      );
      final data = response.data as List<dynamic>;
      return data
          .map((json) => LessonModel.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Fetches a single lesson with full content (concepts + quizzes).
  Future<LessonModel> getLesson(int lessonId) async {
    try {
      final response = await _client.get('/lessons/$lessonId');
      return LessonModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Marks a lesson as started (records progress).
  Future<void> startLesson(int lessonId) async {
    try {
      await _client.post('/lessons/$lessonId/start');
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Marks a lesson as completed and awards XP.
  Future<LessonCompletionResult> completeLesson(
    int lessonId, {
    required int correctAnswers,
    required int totalQuestions,
  }) async {
    try {
      final response = await _client.post(
        '/lessons/$lessonId/complete',
        data: {
          'correct_answers': correctAnswers,
          'total_questions': totalQuestions,
        },
      );
      return LessonCompletionResult.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Records progress on a specific concept screen.
  Future<void> recordConceptProgress(
    int lessonId,
    String conceptId,
  ) async {
    try {
      await _client.post(
        '/lessons/$lessonId/progress',
        data: {'concept_id': conceptId},
      );
    } on DioException catch (e) {
      // Non-fatal: don't block lesson flow for progress tracking
      debugPrint('Lesson progress recording failed: ${e.message}');
    }
  }

  /// Records a quiz answer.
  Future<void> recordQuizAnswer(
    int lessonId,
    String questionId,
    String answer,
    bool isCorrect,
  ) async {
    try {
      await _client.post(
        '/lessons/$lessonId/quiz',
        data: {
          'question_id': questionId,
          'answer': answer,
          'is_correct': isCorrect,
        },
      );
    } on DioException catch (e) {
      debugPrint('Quiz answer recording failed: ${e.message}');
    }
  }
}

/// Represents the result of completing a lesson.
class LessonCompletionResult {
  final int xpEarned;
  final int totalXp;
  final bool newAchievement;
  final String? achievementName;

  LessonCompletionResult({
    required this.xpEarned,
    required this.totalXp,
    this.newAchievement = false,
    this.achievementName,
  });

  factory LessonCompletionResult.fromJson(Map<String, dynamic> json) {
    return LessonCompletionResult(
      xpEarned: json['xp_earned'] as int? ?? 0,
      totalXp: json['total_xp'] as int? ?? 0,
      newAchievement: json['new_achievement'] as bool? ?? false,
      achievementName: json['achievement_name'] as String?,
    );
  }
}
