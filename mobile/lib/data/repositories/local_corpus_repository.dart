import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:isolate';
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

  /// One parse for the whole app. The corpus is ~48 MB of JSON once
  /// unzipped; screens create their own [LocalCorpusRepository], and each
  /// used to parse it again (two or three times when live recitation opens),
  /// which ran low-memory phones out of RAM and killed the app.
  static Future<Map<int, List<AyahModel>>>? _shared;

  /// Drops the shared parse (tests only).
  @visibleForTesting
  static void resetSharedCache() => _shared = null;

  /// How many times the bundle was actually parsed (tests only).
  @visibleForTesting
  static int parseCount = 0;

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
    final pending = _shared ??= _loadBundle();
    try {
      return await pending;
    } catch (_) {
      // A failed load is retried next time instead of being cached.
      if (identical(_shared, pending)) _shared = null;
      rethrow;
    }
  }

  static Future<Map<int, List<AyahModel>>> _loadBundle() async {
    final ByteData data = await rootBundle.load(_assetPath);
    final bytes =
        data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);
    parseCount++;
    // On users' phones parse in a background isolate so the UI never
    // freezes ("app not responding"). Debug builds and tests parse inline:
    // widget tests run in fake time, where an isolate's reply never arrives.
    if (!kDebugMode) {
      try {
        return await Isolate.run(() => parseCorpusBundle(bytes));
      } catch (e) {
        debugPrint('LocalCorpus: background parse failed, parsing inline: $e');
      }
    }
    return parseCorpusBundle(bytes);
  }
}

/// Gzipped corpus bytes -> ayahs by surah. Top level so it can run in an
/// isolate. Decodes JSON straight from the UTF-8 bytes (no 48 MB
/// intermediate string) and parses each ayah defensively so one malformed
/// item can't blank a whole surah.
Map<int, List<AyahModel>> parseCorpusBundle(Uint8List gzipped) {
  final root = const Utf8Decoder()
      .fuse(const JsonDecoder())
      .convert(gzip.decode(gzipped)) as Map<String, dynamic>;
  final surahs = root['surahs'] as List<dynamic>;
  final Map<int, List<AyahModel>> bySurah = {};
  for (final s in surahs) {
    final map = s as Map<String, dynamic>;
    final num = map['surah_number'] as int;
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

/// Provider for the local corpus repository.
final localCorpusRepositoryProvider = Provider<LocalCorpusRepository>(
  (ref) => LocalCorpusRepository(),
);
