import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../services/api_client.dart';
import '../models/surah_model.dart';
import '../models/word_model.dart';

/// Repository for Quran corpus data: surahs, ayahs, words, roots.
class CorpusRepository {
  final ApiClient _client;

  CorpusRepository({ApiClient? client}) : _client = client ?? ApiClient();

  // ─── Surahs ──────────────────────────────────────────────────────────────

  /// Fetches all surahs (metadata only, no ayah text).
  Future<List<SurahModel>> getSurahs() async {
    try {
      final response = await _client.get('/surahs');
      final data = response.data as List<dynamic>;
      return data
          .map((json) => SurahModel.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Fetches a single surah by number.
  Future<SurahModel> getSurah(int surahNumber) async {
    try {
      final response = await _client.get('/surahs/$surahNumber');
      return SurahModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ─── Ayahs ───────────────────────────────────────────────────────────────

  /// Fetches all ayahs for a surah with word-level data.
  Future<List<AyahModel>> getAyahs(int surahNumber) async {
    try {
      final response = await _client.get(
        '/surahs/$surahNumber/ayahs',
        queryParameters: {'include_words': true},
      );
      // The backend normally returns a JSON array, but be defensive: some
      // responses (or future versions) wrap the list under a key such as
      // `ayahs` / `data` / `items`. Extract the array either way so the
      // reader never silently gets an empty/blank screen.
      final dynamic payload = response.data;
      final List<dynamic> list;
      if (payload is List) {
        list = payload;
      } else if (payload is Map) {
        list = (payload['ayahs'] ??
                payload['data'] ??
                payload['items']) as List<dynamic>? ??
            const [];
      } else {
        list = const [];
      }
      return list
          .map((json) => AyahModel.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Fetches a single ayah with word-level data.
  Future<AyahModel> getAyah(int surahNumber, int ayahNumber) async {
    try {
      final response = await _client.get(
        '/surahs/$surahNumber/ayahs/$ayahNumber',
        queryParameters: {'include_words': true},
      );
      return AyahModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Fetches a range of ayahs.
  Future<List<AyahModel>> getAyahRange(
    int surahNumber, {
    int? startAyah,
    int? endAyah,
  }) async {
    try {
      final response = await _client.get(
        '/surahs/$surahNumber/ayahs',
        queryParameters: {
          'include_words': true,
          'start': startAyah,
          'end': endAyah,
        },
      );
      final data = response.data as List<dynamic>;
      return data
          .map((json) => AyahModel.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ─── Words ───────────────────────────────────────────────────────────────

  /// Fetches word details by word ID.
  Future<WordModel> getWord(int wordId) async {
    try {
      final response = await _client.get('/words/$wordId');
      return WordModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  // ─── Roots ───────────────────────────────────────────────────────────────

  /// Fetches all derived words from a root.
  Future<RootDetail> getRoot(int rootId) async {
    try {
      final response = await _client.get('/roots/$rootId');
      return RootDetail.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  /// Searches roots by Arabic text.
  Future<List<RootSummary>> searchRoots(String query) async {
    try {
      final response = await _client.get(
        '/roots/search',
        queryParameters: {'q': query},
      );
      final data = response.data as List<dynamic>;
      return data
          .map((json) => RootSummary.fromJson(json as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }
}

/// Represents a root with its derived words (for Root Explorer).
class RootDetail {
  final int rootId;
  final String rootArabic;
  final String rootTransliteration;
  final String coreMeaning;
  final String? coreMeaningUrdu;
  final List<DerivedWord> derivedWords;

  RootDetail({
    required this.rootId,
    required this.rootArabic,
    required this.rootTransliteration,
    required this.coreMeaning,
    this.coreMeaningUrdu,
    required this.derivedWords,
  });

  factory RootDetail.fromJson(Map<String, dynamic> json) {
    return RootDetail(
      rootId: json['root_id'] as int,
      rootArabic: json['root_arabic'] as String,
      rootTransliteration: json['root_transliteration'] as String? ?? '',
      coreMeaning: json['core_meaning'] as String? ?? '',
      coreMeaningUrdu: json['core_meaning_urdu'] as String?,
      derivedWords: (json['derived_words'] as List<dynamic>?)
              ?.map((w) => DerivedWord.fromJson(w as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

/// Represents a derived word from a root.
class DerivedWord {
  final String word;
  final String transliteration;
  final String? meaning;
  final String? posGroup;
  final int? surahNumber;
  final int? ayahNumber;
  final int frequency;

  DerivedWord({
    required this.word,
    required this.transliteration,
    this.meaning,
    this.posGroup,
    this.surahNumber,
    this.ayahNumber,
    this.frequency = 1,
  });

  factory DerivedWord.fromJson(Map<String, dynamic> json) {
    return DerivedWord(
      word: json['word'] as String,
      transliteration: json['transliteration'] as String? ?? '',
      meaning: json['meaning'] as String?,
      posGroup: json['pos_group'] as String?,
      surahNumber: json['surah_number'] as int?,
      ayahNumber: json['ayah_number'] as int?,
      frequency: json['frequency'] as int? ?? 1,
    );
  }
}

/// Represents a root search result summary.
class RootSummary {
  final int rootId;
  final String rootArabic;
  final String rootTransliteration;
  final String coreMeaning;
  final int derivedCount;

  RootSummary({
    required this.rootId,
    required this.rootArabic,
    required this.rootTransliteration,
    required this.coreMeaning,
    this.derivedCount = 0,
  });

  factory RootSummary.fromJson(Map<String, dynamic> json) {
    return RootSummary(
      rootId: json['root_id'] as int,
      rootArabic: json['root_arabic'] as String,
      rootTransliteration: json['root_transliteration'] as String? ?? '',
      coreMeaning: json['core_meaning'] as String? ?? '',
      derivedCount: json['derived_count'] as int? ?? 0,
    );
  }
}
