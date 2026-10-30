import 'package:dio/dio.dart';

import '../../../data/services/api_client.dart';
import 'library_models.dart';

/// Read access to the Islamic Library (`/v1/library/...`).
abstract class LibraryRepository {
  Future<List<LibraryCategory>> categories();

  Future<LibraryPage<LibraryCollection>> collections({
    String? category,
    int page = 1,
    int pageSize = 50,
  });

  Future<LibraryPage<LibraryBook>> books(String slug, {int page = 1, int pageSize = 100});

  Future<LibraryPage<HadithSummary>> bookHadiths(
    String slug,
    int book, {
    int page = 1,
    int pageSize = 20,
  });

  /// [graded] is `all`, `weak` (any scholar graded it da'if/mawdu') or
  /// `fabricated` (any scholar graded it mawdu').
  Future<LibraryPage<HadithSummary>> hadiths({String graded = 'all', int page = 1, int pageSize = 20});

  Future<HadithDetail> hadith(String id);

  Future<NarratorProfile> narrator(String id);

  /// The classical entry for [word], or null when none is catalogued yet.
  Future<GharibEntry?> gharib(String word);

  Future<LibrarySearchResult> search(String query);
}

/// [LibraryRepository] over the core API. Paths are relative to
/// `AppConstants.baseUrl`, which already ends in `/v1`.
class ApiLibraryRepository implements LibraryRepository {
  ApiLibraryRepository({Dio? dio}) : _dioOverride = dio;

  final Dio? _dioOverride;
  late final Dio _dio = _dioOverride ?? ApiClient().dio;

  Future<Map<String, dynamic>> _object(String path, [Map<String, dynamic>? query]) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(path, queryParameters: query);
      return response.data!;
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  @override
  Future<List<LibraryCategory>> categories() async {
    try {
      final response = await _dio.get<List<dynamic>>('/library/categories');
      return [
        for (final e in response.data!) LibraryCategory.fromJson(e as Map<String, dynamic>),
      ];
    } on DioException catch (e) {
      throw ApiException.fromDioError(e);
    }
  }

  @override
  Future<LibraryPage<LibraryCollection>> collections({
    String? category,
    int page = 1,
    int pageSize = 50,
  }) async =>
      LibraryPage.fromJson(
        await _object('/library/collections', {
          if (category != null) 'category': category,
          'page': page,
          'page_size': pageSize,
        }),
        LibraryCollection.fromJson,
      );

  @override
  Future<LibraryPage<LibraryBook>> books(String slug, {int page = 1, int pageSize = 100}) async =>
      LibraryPage.fromJson(
        await _object('/library/collections/${Uri.encodeComponent(slug)}/books', {
          'page': page,
          'page_size': pageSize,
        }),
        LibraryBook.fromJson,
      );

  @override
  Future<LibraryPage<HadithSummary>> bookHadiths(
    String slug,
    int book, {
    int page = 1,
    int pageSize = 20,
  }) async =>
      LibraryPage.fromJson(
        await _object('/library/collections/${Uri.encodeComponent(slug)}/books/$book/hadiths', {
          'page': page,
          'page_size': pageSize,
        }),
        HadithSummary.fromJson,
      );

  @override
  Future<LibraryPage<HadithSummary>> hadiths({String graded = 'all', int page = 1, int pageSize = 20}) async =>
      LibraryPage.fromJson(
        await _object('/library/hadiths', {'graded': graded, 'page': page, 'page_size': pageSize}),
        HadithSummary.fromJson,
      );

  @override
  Future<HadithDetail> hadith(String id) async =>
      HadithDetail.fromJson(await _object('/library/hadiths/$id'));

  @override
  Future<NarratorProfile> narrator(String id) async =>
      NarratorProfile.fromJson(await _object('/library/narrators/${Uri.encodeComponent(id)}'));

  @override
  Future<GharibEntry?> gharib(String word) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/library/gharib/${Uri.encodeComponent(word)}',
      );
      return GharibEntry.fromJson(response.data!);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      throw ApiException.fromDioError(e);
    }
  }

  @override
  Future<LibrarySearchResult> search(String query) async =>
      LibrarySearchResult.fromJson(await _object('/library/search', {'q': query}));
}
