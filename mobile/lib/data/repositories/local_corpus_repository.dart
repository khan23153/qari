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

  final Map<int, List<AyahModel>> _cache = {};

  /// Returns all ayahs (with word-by-word data) for a surah from the bundled
  /// asset. Returns an empty list if the surah is not present.
  Future<List<AyahModel>> getAyahs(int surahNumber) async {
    if (_cache.containsKey(surahNumber)) return _cache[surahNumber]!;

    final all = await _loadBundle();
    final result = all[surahNumber] ?? const <AyahModel>[];
    _cache[surahNumber] = result;
    return result;
  }

  Future<Map<int, List<AyahModel>>> _loadBundle() async {
    final ByteData data = await rootBundle.load(_assetPath);
    // Decode gzip off the UI thread to avoid jank on the (large) payload.
    final bytes = data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);
    final decoded = await _decode(bytes);
    final jsonStr = utf8.decode(decoded);
    final Map<String, dynamic> root = jsonDecode(jsonStr) as Map<String, dynamic>;

    final surahs = root['surahs'] as List<dynamic>;
    final Map<int, List<AyahModel>> bySurah = {};
    for (final s in surahs) {
      final map = s as Map<String, dynamic>;
      final num = map['surah_number'] as int;
      final ayahs = (map['ayahs'] as List<dynamic>)
          .map((a) => AyahModel.fromJson(a as Map<String, dynamic>))
          .toList();
      bySurah[num] = ayahs;
    }
    return bySurah;
  }

  Future<Uint8List> _decode(Uint8List bytes) async {
    // Run gzip decoding in a background isolate via compute.
    try {
      return await compute(gzipDecode, bytes);
    } catch (_) {
      // Fallback on platforms where compute is unavailable (e.g. tests).
      return gzipDecode(bytes);
    }
  }
}

/// Decodes a gzipped payload. Exposed at top level so it can run in a
/// background isolate via [compute].
Uint8List gzipDecode(Uint8List bytes) => Uint8List.fromList(gzip.decode(bytes));

/// Provider for the local corpus repository.
final localCorpusRepositoryProvider = Provider<LocalCorpusRepository>(
  (ref) => LocalCorpusRepository(),
);
