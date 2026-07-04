import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../services/api_client.dart';
import '../models/flashcard_model.dart';
import '../../core/constants/app_constants.dart';

/// Repository for flashcard operations: due cards, review, SM-2 updates.
class FlashcardRepository {
  final ApiClient _client;

  FlashcardRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Fetches due flashcards for review (up to session cap).
  Future<List<FlashcardModel>> getDueCards({
    int? limit,
  }) async {
    try {
      final response = await _client.get(
        '/flashcards/due',
        queryParameters: {
          'limit': limit ?? AppConstants.flashcardSessionCap,
        },
      );
      final data = response.data as List<dynamic>;
      return data
          .map((json) => FlashcardModel.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Saves a word to the user's flashcard collection.
  Future<FlashcardModel> saveCard({
    required int wordId,
    required int surahNumber,
    required int ayahNumber,
  }) async {
    try {
      final response = await _client.post(
        '/flashcards',
        data: {
          'word_id': wordId,
          'surah_number': surahNumber,
          'ayah_number': ayahNumber,
        },
      );
      return FlashcardModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Submits a flashcard review with SM-2 grade.
  /// grade: 1 = Again (Bhool gaya), 3 = Hard (Mushkil), 5 = Easy (Aasaan)
  Future<FlashcardModel> reviewCard({
    required int cardId,
    required int grade,
  }) async {
    try {
      final response = await _client.post(
        '/flashcards/$cardId/review',
        data: {'grade': grade},
      );
      return FlashcardModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Fetches all flashcards for the user.
  Future<List<FlashcardModel>> getAllCards() async {
    try {
      final response = await _client.get('/flashcards');
      final data = response.data as List<dynamic>;
      return data
          .map((json) => FlashcardModel.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Deletes a flashcard.
  Future<void> deleteCard(int cardId) async {
    try {
      await _client.delete('/flashcards/$cardId');
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Gets the count of due cards (for home screen badge).
  Future<int> getDueCount() async {
    try {
      final response = await _client.get('/flashcards/due/count');
      final data = response.data as Map<String, dynamic>;
      return data['count'] as int? ?? 0;
    } on DioException catch (e) {
      // Non-fatal: return 0 if count can't be fetched
      debugPrint('Flashcard count fetch failed: ${e.message}');
      return 0;
    }
  }

  /// Gets the session result summary after a review session.
  Future<FlashcardSessionResult> getSessionResult(String sessionId) async {
    try {
      final response = await _client.get('/flashcards/sessions/$sessionId');
      return FlashcardSessionResult.fromJson(
          response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}
