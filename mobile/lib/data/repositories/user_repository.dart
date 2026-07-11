import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../services/api_client.dart';
import '../models/user_model.dart';

/// Repository for user data: onboarding, home, progress.
class UserRepository {
  final ApiClient _client;

  UserRepository({ApiClient? client}) : _client = client ?? ApiClient();

  // ─── Onboarding ──────────────────────────────────────────────────────────

  /// Saves the user's language selection.
  Future<UserModel> selectLanguage(String languageCode) async {
    try {
      final response = await _client.post(
        '/users/onboarding/language',
        data: {'language': languageCode},
      );
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Saves the user's learning path selection.
  Future<UserModel> selectPath(String path) async {
    try {
      final response = await _client.post(
        '/users/onboarding/path',
        data: {'learning_path': path},
      );
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Completes onboarding by sending the chosen language + learning path.
  ///
  /// The backend [startingPath] values are the canonical ones
  /// ('foundation', 'quran_direct', ...); the UI [LearningPath] enum maps
  /// onto these directly by name.
  Future<void> finishOnboarding({
    required String appLanguage,
    required String startingPath,
  }) async {
    try {
      await _client.post(
        '/users/onboarding',
        data: {
          'app_language': appLanguage,
          'starting_path': startingPath,
        },
      );
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ─── Home ────────────────────────────────────────────────────────────────

  /// Fetches the home screen data (streak, XP, continue lesson, path).
  Future<HomeResponse> getHomeData() async {
    try {
      final response = await _client.get('/me/home');
      return HomeResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ─── Profile / Stats ─────────────────────────────────────────────────────

  /// Fetches the current user profile.
  Future<UserModel> getProfile() async {
    try {
      final response = await _client.get('/me');
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Fetches detailed statistics.
  Future<StatsModel> getStats() async {
    try {
      final response = await _client.get('/me/stats');
      return StatsModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Updates the daily goal.
  Future<void> updateDailyGoal(int goal) async {
    try {
      await _client.patch('/me/settings', data: {'daily_goal': goal});
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Updates the selected language.
  Future<void> updateLanguage(String languageCode) async {
    try {
      await _client.patch('/me/settings', data: {'language': languageCode});
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Updates the learning path.
  Future<void> updateLearningPath(String path) async {
    try {
      await _client.patch('/me/settings', data: {'learning_path': path});
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Updates the selected reciter (qari).
  Future<void> updateReciter(String reciter) async {
    try {
      await _client.patch('/me/settings', data: {'reciter': reciter});
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Updates audio consent.
  Future<void> updateAudioConsent(bool consent) async {
    try {
      await _client.patch('/me/settings', data: {'audio_consent': consent});
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Updates the theme preference.
  Future<void> updateTheme(String theme) async {
    try {
      await _client.patch('/me/settings', data: {'theme': theme});
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Fetches all achievements/badges.
  Future<List<Achievement>> getAchievements() async {
    try {
      final response = await _client.get('/me/achievements');
      final data = response.data as List<dynamic>;
      return data
          .map((json) => Achievement.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}
