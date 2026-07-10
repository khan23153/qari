import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../services/api_client.dart';
import '../models/recitation_model.dart';
import '../../core/constants/app_constants.dart';

/// Repository for recitation: upload audio, poll for results.
class RecitationRepository {
  final ApiClient _client;

  RecitationRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Uploads a recitation audio file for analysis.
  /// Returns a session ID to poll for results.
  Future<String> uploadRecitation({
    required String filePath,
    required int surahNumber,
    required int ayahNumber,
    required String idempotencyKey,
    void Function(int sent, int total)? onProgress,
  }) async {
    try {
      final response = await _client.uploadFile(
        '/recitations/upload',
        filePath: filePath,
        fieldName: 'audio',
        extraFields: {
          'surah_number': surahNumber,
          'ayah_number': ayahNumber,
        },
        idempotencyKey: idempotencyKey,
        onProgress: onProgress,
      );
      final data = response.data as Map<String, dynamic>;
      return data['session_id'] as String;
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Polls for recitation analysis results.
  /// Returns the [RecitationResult] when analysis is complete,
  /// or null if still processing.
  Future<RecitationResult?> getRecitationResult(String sessionId) async {
    try {
      final response = await _client.get('/recitations/$sessionId');
      final data = response.data as Map<String, dynamic>;

      final status = data['status'] as String?;
      if (status == 'completed') {
        return RecitationResult.fromJson(
            data['result'] as Map<String, dynamic>);
      }
      if (status == 'failed') {
        throw ApiException(
          message: data['error'] as String? ?? 'Analysis failed',
          errorCode: 'ANALYSIS_FAILED',
        );
      }
      return null; // Still processing
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Polls for recitation results with automatic retry.
  /// Calls [onPolling] for each poll attempt.
  Future<RecitationResult> pollForResult(
    String sessionId, {
    void Function(int attempt, int maxAttempts)? onPolling,
  }) async {
    for (var attempt = 0; attempt < AppConstants.recitationMaxPollAttempts; attempt++) {
      onPolling?.call(attempt, AppConstants.recitationMaxPollAttempts);

      final result = await getRecitationResult(sessionId);
      if (result != null) {
        return result;
      }

      await Future.delayed(
        Duration(milliseconds: AppConstants.recitationPollIntervalMs),
      );
    }

    throw const ApiException(
      message: 'Analysis timed out. Please try again.',
      errorCode: 'POLL_TIMEOUT',
    );
  }

  /// Fetches recitation history.
  Future<List<RecitationResult>> getHistory({int limit = 20}) async {
    try {
      final response = await _client.get(
        '/recitations/history',
        queryParameters: {'limit': limit},
      );
      final data = response.data as List<dynamic>;
      return data
          .map((json) => RecitationResult.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Gets the reference audio URL for a specific ayah.
  Future<String> getReferenceAudio({
    required int surahNumber,
    required int ayahNumber,
    String? reciter,
  }) async {
    try {
      final response = await _client.get(
        '/recitations/reference',
        queryParameters: {
          'surah_number': surahNumber,
          'ayah_number': ayahNumber,
          if (reciter != null) 'reciter': reciter,
        },
      );
      final data = response.data as Map<String, dynamic>;
      return data['audio_url'] as String;
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}
