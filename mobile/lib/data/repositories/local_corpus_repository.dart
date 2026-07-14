import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/word_model.dart';

/// Loads the full Quran corpus from a bundled, gzipped asset
/// (`assets/quran_corpus.json.gz`). This makes the reader fully functional
/// offline and immune to the (frequently empty/unreachable) backend corpus DB,
/// which previously left the reader showing a blank screen.
///
/// The JSON is shaped to match [AyahModel.fromJson] / [WordModel.fromJson] keys
/// so it can be parsed with zero mapping glue.
class LocalCorpusRepository {
  static const _assetPath = 'assets/quran_corpus.json.gz';

  Map<int, List<AyahModel>>? _allBySurah;

  /// Returns all ayahs (with word-by-word data) for a surah from the bundled
  /// asset. Returns an empty list if the surah is not present.
  Future<List<AyahModel>> getAyahs(int surahNumber) async {
    final all = await _loadAll();
    return all[surahNumber] ?? const <AyahModel>[];
  }

  /// Returns every ayah whose `page_number` matches [page] (a standard 15-line
  /// Madani Mushaf page), ordered by surah then ayah. Used for continuous
  /// full-page (Mushaf) recitation. Returns an empty list if the page has no
  /// ayahs in the bundle.
  Future<List<AyahModel>> getAyahsByPage(int page) async {
    final all = await _loadAll();
    final result = <AyahModel>[];
    for (final ayahs in all.values) {
      for (final a in ayahs) {
        if (a.pageNumber == page) result.add(a);
      }
    }
    result.sort((x, y) {
      if (x.surahNumber != y.surahNumber) {
        return x.surahNumber.compareTo(y.surahNumber);
      }
      return x.ayahNumber.compareTo(y.ayahNumber);
    });
    return result;
  }

  Future<Map<int, List<AyahModel>>> _loadAll() async {
    if (_allBySurah != null) return _allBySurah!;
    _allBySurah = await _loadBundle();
    return _allBySurah!;
  }

  Future<Map<int, List<AyahModel>>> _loadBundle() async {
    final ByteData data = await rootBundle.load(_assetPath);
    final bytes = data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);
    // Decode gzip on the caller (fast enough for a 4.4 MB asset and avoids the
    // fragile background-isolate path that could otherwise fail silently and
    // leave the reader blank).
    final decoded = gzip.decode(bytes);
    final jsonStr = utf8.decode(decoded);
    final Map<String, dynamic> root = jsonDecode(jsonStr) as Map<String, dynamic>;

    final surahs = root['surahs'] as List<dynamic>;
    final Map<int, List<AyahModel>> bySurah = {};
    for (final s in surahs) {
      final map = s as Map<String, dynamic>;
      final num = map['surah_number'] as int;
      // Parse each ayah defensively so a single malformed item can't blank the
      // whole surah.
      final ayahs = <AyahModel>[];
      for (final a in (map['ayahs'] as List<dynamic>)) {
        try {
          ayahs.add(AyahModel.fromJson(a as Map<String, dynamic>));
        } catch (e) {
          debugPrint('LocalCorpus: skipping bad ayah in surah $num: $e');
        }
      }
      bySurah[num] = ayahs;
    }
    return bySurah;
  }
}

/// Provider for the local corpus repository.
final localCorpusRepositoryProvider = Provider<LocalCorpusRepository>(
  (ref) => LocalCorpusRepository(),
);
