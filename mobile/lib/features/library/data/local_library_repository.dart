import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/services.dart' show rootBundle;

import 'library_arabic.dart';
import 'library_models.dart';
import 'library_repository.dart';

/// Thrown when the bundled library has no record for a request (for example
/// a hadith that is only available from the server).
class LibraryNotBundledException implements Exception {
  const LibraryNotBundledException(this.what);

  final String what;

  @override
  String toString() => 'LibraryNotBundledException: $what is not in the offline library';
}

/// Serves the library snapshot bundled in the APK
/// (`assets/library/library_seed.json`, exported from the backend in API
/// response shape by scripts/export_library_mobile_seed.py).
class LocalLibraryRepository implements LibraryRepository {
  LocalLibraryRepository({Future<String> Function()? loadJson})
      : _loadJson = loadJson ?? (() => rootBundle.loadString(assetPath));

  static const assetPath = 'assets/library/library_seed.json';
  static const _searchLimit = 20;

  final Future<String> Function() _loadJson;
  Future<_Snapshot>? _snapshot;

  Future<_Snapshot> get _data => _snapshot ??= _loadJson().then(
        (raw) => _Snapshot(jsonDecode(raw) as Map<String, dynamic>),
      );

  static LibraryPage<T> _page<T>(List<T> all, int page, int pageSize) {
    final start = (page - 1) * pageSize;
    final items = start >= all.length
        ? <T>[]
        : all.sublist(start, math.min(start + pageSize, all.length));
    return LibraryPage(
      items: items,
      total: all.length,
      page: page,
      hasNext: start + pageSize < all.length,
    );
  }

  @override
  Future<List<LibraryCategory>> categories() async =>
      [for (final c in (await _data).categories) LibraryCategory.fromJson(c)];

  @override
  Future<LibraryPage<LibraryCollection>> collections({
    String? category,
    int page = 1,
    int pageSize = 50,
  }) async {
    final all = [
      for (final c in (await _data).collections)
        if (category == null || c['category'] == category) LibraryCollection.fromJson(c),
    ];
    return _page(all, page, pageSize);
  }

  @override
  Future<LibraryPage<LibraryBook>> books(String slug, {int page = 1, int pageSize = 100}) async {
    final c = (await _data).collection(slug);
    final all = [
      for (final b in c['books'] as List<dynamic>) LibraryBook.fromJson(b as Map<String, dynamic>),
    ];
    return _page(all, page, pageSize);
  }

  @override
  Future<LibraryPage<HadithSummary>> bookHadiths(
    String slug,
    int book, {
    int page = 1,
    int pageSize = 20,
  }) async {
    final data = await _data;
    data.collection(slug);
    final all = [
      for (final s in data.summaries)
        if (s['collection'] == slug && s['book_number'] == book) HadithSummary.fromJson(s),
    ];
    return _page(all, page, pageSize);
  }

  @override
  Future<LibraryPage<HadithSummary>> hadiths({String graded = 'all', int page = 1, int pageSize = 20}) async {
    final wanted = switch (graded) {
      'weak' => {RulingType.daif, RulingType.mawdu},
      'fabricated' => {RulingType.mawdu},
      _ => null,
    };
    final all = [
      for (final s in (await _data).summaries) HadithSummary.fromJson(s),
    ].where((h) => wanted == null || h.grades.any((g) => wanted.contains(g.rulingType))).toList();
    return _page(all, page, pageSize);
  }

  @override
  Future<HadithDetail> hadith(String id) async {
    final h = (await _data).hadiths[id];
    if (h == null) throw LibraryNotBundledException('hadith $id');
    return HadithDetail.fromJson(h as Map<String, dynamic>);
  }

  @override
  Future<NarratorProfile> narrator(String id) async {
    final n = (await _data).narrators[id];
    if (n == null) throw LibraryNotBundledException('narrator $id');
    return NarratorProfile.fromJson(n as Map<String, dynamic>);
  }

  @override
  Future<GharibEntry?> gharib(String word) async {
    final data = await _data;
    final normalized = normalizeArabic(word);
    final tokens = normalized.isEmpty ? <String>[] : normalized.split(' ');
    for (final token in tokens) {
      for (final stem in stripClitics(token)) {
        final entry = data.gharibByForm[stem];
        if (entry != null) return GharibEntry.fromJson({...entry, 'matched_form': stem});
      }
    }
    return null;
  }

  @override
  Future<LibrarySearchResult> search(String query) async {
    final data = await _data;
    final qAr = normalizeArabic(query);
    final qEn = query.trim().toLowerCase();

    bool hit(List<Object?> fields) => fields.whereType<String>().any(
          (f) => (qAr.isNotEmpty && normalizeArabic(f).contains(qAr)) || f.toLowerCase().contains(qEn),
        );

    final hadiths = [
      for (final s in data.summaries)
        if (hit([s['matn_ar'], s['translation_text']])) s,
    ];
    final narrators = [
      for (final n in data.narrators.values.cast<Map<String, dynamic>>())
        if (hit([n['name_ar'], n['name_en']]))
          {'id': n['id'], 'name_ar': n['name_ar'], 'name_en': n['name_en'], 'reliability': n['reliability']},
    ];
    final collections = [
      for (final c in data.collections)
        if (hit([c['name_en'], c['name_ar'], c['author_en'], c['author_ar']])) c,
    ];
    return LibrarySearchResult.fromJson({
      'query': query,
      'hadiths': hadiths.take(_searchLimit).toList(),
      'narrators': narrators.take(_searchLimit).toList(),
      'collections': collections.take(_searchLimit).toList(),
    });
  }
}

class _Snapshot {
  _Snapshot(Map<String, dynamic> json)
      : categories = (json['categories'] as List<dynamic>).cast<Map<String, dynamic>>(),
        collections = (json['collections'] as List<dynamic>).cast<Map<String, dynamic>>(),
        hadiths = json['hadiths'] as Map<String, dynamic>,
        summaries = (json['hadith_summaries'] as List<dynamic>).cast<Map<String, dynamic>>(),
        narrators = json['narrators'] as Map<String, dynamic>,
        gharibByForm = {
          for (final g in (json['gharib'] as List<dynamic>).cast<Map<String, dynamic>>())
            for (final form in (g['forms'] as List<dynamic>).cast<String>()) form: g,
        };

  final List<Map<String, dynamic>> categories;
  final List<Map<String, dynamic>> collections;
  final Map<String, dynamic> hadiths;
  final List<Map<String, dynamic>> summaries;
  final Map<String, dynamic> narrators;
  final Map<String, Map<String, dynamic>> gharibByForm;

  Map<String, dynamic> collection(String slug) => collections.firstWhere(
        (c) => c['slug'] == slug,
        orElse: () => throw LibraryNotBundledException('collection $slug'),
      );
}
