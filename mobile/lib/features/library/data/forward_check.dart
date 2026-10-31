import 'package:dio/dio.dart';

import '../../../data/services/api_client.dart';
import 'library_models.dart';

/// How close a forwarded text is to a hadith in the collections.
enum ForwardBand { strong, possible }

/// One hadith the forwarded text resembles.
class ForwardMatch {
  const ForwardMatch({
    required this.band,
    required this.score,
    required this.language,
    required this.collectionName,
    required this.hadith,
  });

  factory ForwardMatch.fromJson(Map<String, dynamic> json) => ForwardMatch(
        band: json['band'] == 'strong'
            ? ForwardBand.strong
            : ForwardBand.possible,
        score: (json['score'] as num).toDouble(),
        language: json['language'] as String,
        collectionName: json['collection_name'] as String? ?? '',
        hadith: HadithSummary.fromJson(json['hadith'] as Map<String, dynamic>),
      );

  final ForwardBand band;
  final double score;

  /// Which wording matched: 'ar', 'ur' or 'en'.
  final String language;
  final String collectionName;
  final HadithSummary hadith;
}

/// The server's answer. An empty [matches] means "not found in
/// [searchedCollections]": never a grade, and never "fabricated".
class ForwardCheckResult {
  const ForwardCheckResult({
    required this.queryLanguage,
    required this.matches,
    required this.searchedCollections,
    required this.note,
  });

  factory ForwardCheckResult.fromJson(Map<String, dynamic> json) =>
      ForwardCheckResult(
        queryLanguage: json['query_language'] as String,
        matches: [
          for (final m in json['matches'] as List<dynamic>)
            ForwardMatch.fromJson(m as Map<String, dynamic>),
        ],
        searchedCollections: [
          for (final c in json['searched_collections'] as List<dynamic>)
            c as String,
        ],
        note: json['note'] as String,
      );

  final String queryLanguage;
  final List<ForwardMatch> matches;
  final List<String> searchedCollections;
  final String note;
}

/// Why a check produced no answer. None of these mean "not found": the text
/// was not checked at all.
enum ForwardCheckFailure {
  /// No connection, timeout, or the server is not reachable.
  unreachable,

  /// The server is still building its search index (first run).
  preparing,

  /// The text is too short or too long to check.
  invalidText,
}

class ForwardCheckException implements Exception {
  const ForwardCheckException(this.failure);

  final ForwardCheckFailure failure;

  @override
  String toString() => 'ForwardCheckException($failure)';
}

/// Shortest text the server checks (it needs a few words to compare).
const forwardMinLength = 10;

/// Longest text the server checks.
const forwardMaxLength = 3000;

/// Checks a forwarded message against the hadith collections. Needs the
/// server: the full collections are too large to bundle with the app.
abstract class ForwardChecker {
  Future<ForwardCheckResult> check(String text);
}

/// [ForwardChecker] over `POST /v1/library/check`.
class ApiForwardChecker implements ForwardChecker {
  ApiForwardChecker({Dio? dio}) : _dioOverride = dio;

  final Dio? _dioOverride;
  late final Dio _dio = _dioOverride ?? ApiClient().dio;

  @override
  Future<ForwardCheckResult> check(String text) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/library/check',
        data: {'text': text},
      );
      return ForwardCheckResult.fromJson(response.data!);
    } on DioException catch (e) {
      throw ForwardCheckException(
          failureFor(e.response?.statusCode, e.response?.data));
    } on FormatException {
      throw const ForwardCheckException(ForwardCheckFailure.unreachable);
    } on TypeError {
      throw const ForwardCheckException(ForwardCheckFailure.unreachable);
    }
  }

  /// Maps an HTTP status (null when nothing came back) to a failure.
  static ForwardCheckFailure failureFor(int? status, Object? body) {
    if (status == 422) return ForwardCheckFailure.invalidText;
    if (status == 503 && body is Map) {
      final said = '${body['detail'] ?? ''} ${body['message'] ?? ''}';
      if (said.toLowerCase().contains('preparing')) {
        return ForwardCheckFailure.preparing;
      }
    }
    return ForwardCheckFailure.unreachable;
  }
}
