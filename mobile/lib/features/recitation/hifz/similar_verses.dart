import 'dart:convert';

import 'package:flutter/services.dart';

/// The mutashabihat index: ayahs that share most of their words in order
/// with another ayah, so a reciter can start one and slide into the other
/// (2:58 and 7:161, 2:35 and 7:19, ...).
///
/// Built offline from the bundled corpus by
/// `scripts/build_similar_verses.py` into `assets/similar_verses.json`.
class SimilarVerseIndex {
  SimilarVerseIndex({
    required Map<String, List<String>> similar,
    required Map<String, List<String>> words,
  })  : _similar = similar,
        _words = words;

  final Map<String, List<String>> _similar;
  final Map<String, List<String>> _words;

  static const assetPath = 'assets/similar_verses.json';

  static Future<SimilarVerseIndex>? _loading;

  /// Loads the bundled index once per app run.
  static Future<SimilarVerseIndex> load({AssetBundle? bundle}) {
    return _loading ??= (bundle ?? rootBundle)
        .loadString(assetPath)
        .then((raw) => SimilarVerseIndex.fromJson(
              jsonDecode(raw) as Map<String, dynamic>,
            ));
  }

  factory SimilarVerseIndex.fromJson(Map<String, dynamic> json) {
    Map<String, List<String>> lists(Object? raw) => {
          for (final e in (raw as Map<String, dynamic>? ?? const {}).entries)
            e.key: (e.value as List<dynamic>).cast<String>(),
        };
    return SimilarVerseIndex(
      similar: lists(json['similar']),
      words: lists(json['words']),
    );
  }

  /// Ayahs similar to [ref] ("surah:ayah"), nearest first by mushaf order.
  List<String> similarTo(String ref) => _similar[ref] ?? const [];

  /// The skeleton words of an ayah that has a similar partner.
  List<String>? wordsOf(String ref) => _words[ref];

  static final RegExp _marks =
      RegExp('[ؐ-ًؚ-ٰٟۖ-ۭـ]');
  static final RegExp _nonLetter = RegExp('[^ء-ي]');

  /// Letters only, with the spelling differences between the Uthmani text,
  /// the simple text and speech recognisers removed (alif in all its forms
  /// is dropped). Must match `skeleton` in the build script.
  static String skeleton(String word) {
    var w = word.replaceAll(_marks, '');
    for (final a in const ['آ', 'أ', 'إ', 'ٱ']) {
      w = w.replaceAll(a, 'ا');
    }
    w = w
        .replaceAll('ى', 'ي')
        .replaceAll('ة', 'ه')
        .replaceAll('ؤ', 'و')
        .replaceAll('ئ', 'ي')
        .replaceAll('ء', '')
        .replaceAll('ا', '');
    return w.replaceAll(_nonLetter, '');
  }
}

/// The reciter started [from] but the words heard belong to [to].
class SimilarVerseSlip {
  const SimilarVerseSlip({required this.from, required this.to});

  final String from;
  final String to;

  @override
  bool operator ==(Object other) =>
      other is SimilarVerseSlip && other.from == from && other.to == to;

  @override
  int get hashCode => Object.hash(from, to);

  @override
  String toString() => 'SimilarVerseSlip($from -> $to)';
}

/// Watches live word verdicts and notices when the words heard stop fitting
/// the expected ayah but fit one of its similar ayahs.
///
/// It works only from what the live engine already sends (each word's
/// verdict and, for a mistake, the word it heard); it changes nothing in
/// recognition. Each slip is reported once per session.
class SimilarVerseDetector {
  SimilarVerseDetector(this.index, {this.window = 3});

  final SimilarVerseIndex index;

  /// How many heard words, ending at the current one, must sit together in
  /// the similar ayah. Three is enough to tell real slips from chance.
  final int window;

  final List<String> _heard = [];
  int _lastIndex = -1;
  final Set<SimilarVerseSlip> _reported = {};

  void reset() {
    _heard.clear();
    _lastIndex = -1;
    _reported.clear();
  }

  /// One verdict for the word at [wordIndex] of the session, which is word
  /// [position] (0-based) of the ayah [expectedRef]. [heard] is the text the
  /// engine reported hearing for a mistake.
  SimilarVerseSlip? onWord({
    required int wordIndex,
    required String expectedRef,
    required int position,
    required bool matched,
    String? heard,
  }) {
    // A later verdict for an earlier word is a revision, not new speech.
    if (wordIndex < _lastIndex) return null;

    final expected = index.wordsOf(expectedRef);
    final token = matched
        ? (expected != null && position >= 0 && position < expected.length
            ? expected[position]
            : SimilarVerseIndex.skeleton(heard ?? ''))
        : SimilarVerseIndex.skeleton(heard ?? '');

    if (wordIndex == _lastIndex && _heard.isNotEmpty) {
      _heard.removeLast();
    }
    _lastIndex = wordIndex;
    if (token.isEmpty) {
      // Nothing usable was heard: start the window again.
      _heard.clear();
      return null;
    }
    _heard.add(token);
    if (_heard.length > 12) _heard.removeAt(0);

    if (matched || expected == null || _heard.length < window) return null;
    final tail = _heard.sublist(_heard.length - window);
    if (_containsRun(expected, tail)) return null;

    for (final other in index.similarTo(expectedRef)) {
      final words = index.wordsOf(other);
      if (words == null || !_containsRun(words, tail)) continue;
      final slip = SimilarVerseSlip(from: expectedRef, to: other);
      if (_reported.add(slip)) return slip;
      return null;
    }
    return null;
  }

  static bool _containsRun(List<String> words, List<String> run) {
    for (var i = 0; i + run.length <= words.length; i++) {
      var ok = true;
      for (var j = 0; j < run.length; j++) {
        if (words[i + j] != run[j]) {
          ok = false;
          break;
        }
      }
      if (ok) return true;
    }
    return false;
  }
}

/// Maps a session word index to (ayah slot, word position in that ayah)
/// using the last word index of each ayah, as the live page keeps them.
/// Returns null when the index is outside every ayah.
(int, int)? locateWord(int wordIndex, List<int> ayahLastWordIndex) {
  var start = 0;
  for (var i = 0; i < ayahLastWordIndex.length; i++) {
    final last = ayahLastWordIndex[i];
    if (wordIndex <= last) {
      return wordIndex >= start ? (i, wordIndex - start) : null;
    }
    start = last + 1;
  }
  return null;
}
