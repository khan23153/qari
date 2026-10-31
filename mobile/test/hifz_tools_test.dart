import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:qari/data/models/recitation_session_record.dart';
import 'package:qari/features/recitation/hifz/hifz_map.dart';
import 'package:qari/features/recitation/hifz/similar_verses.dart';
import 'package:qari/features/recitation/hifz/slip_store.dart';

/// The real bundled index (read from disk; rootBundle is slow in tests).
SimilarVerseIndex _realIndex() => SimilarVerseIndex.fromJson(
      jsonDecode(File('assets/similar_verses.json').readAsStringSync())
          as Map<String, dynamic>,
    );

List<String> _sk(String text) => text
    .split(' ')
    .map(SimilarVerseIndex.skeleton)
    .where((w) => w.isNotEmpty)
    .toList();

void main() {
  group('skeleton', () {
    test('Uthmani, simple and recogniser spellings meet', () {
      // Uthmani with dagger alif / alif wasla vs plain recogniser text.
      expect(SimilarVerseIndex.skeleton('ٱلْكِتَـٰبِ'),
          SimilarVerseIndex.skeleton('الكتاب'));
      expect(SimilarVerseIndex.skeleton('خَطَـٰيَـٰكُمْ'),
          SimilarVerseIndex.skeleton('خطاياكم'));
      expect(SimilarVerseIndex.skeleton('هَـٰذِهِ'),
          SimilarVerseIndex.skeleton('هذه'));
      expect(SimilarVerseIndex.skeleton('حِطَّةٌ'),
          SimilarVerseIndex.skeleton('حطه'));
    });

    test('waqf signs and numbers leave nothing', () {
      expect(SimilarVerseIndex.skeleton('ۚ'), '');
      expect(SimilarVerseIndex.skeleton('١٢'), '');
    });
  });

  group('bundled similar-verse index', () {
    final index = _realIndex();

    test('knows the classic pairs', () {
      expect(index.similarTo('2:58'), contains('7:161'));
      expect(index.similarTo('7:161'), contains('2:58'));
      expect(index.similarTo('2:35'), contains('7:19'));
    });

    test('keeps the words of every ayah it links', () {
      expect(index.wordsOf('2:58'), isNotNull);
      expect(index.wordsOf('7:161'), isNotNull);
    });
  });

  group('locateWord', () {
    test('maps a session index to ayah slot and position', () {
      // Ayah 0 = words 0..3, ayah 1 = 4..9, ayah 2 = 10..12.
      const last = [3, 9, 12];
      expect(locateWord(0, last), (0, 0));
      expect(locateWord(3, last), (0, 3));
      expect(locateWord(4, last), (1, 0));
      expect(locateWord(12, last), (2, 2));
      expect(locateWord(13, last), isNull);
    });
  });

  group('SimilarVerseDetector', () {
    // 2:58 "وإذ قلنا ادخلوا هذه القرية فكلوا منها حيث شئتم رغدا ..."
    // 7:161 "وإذ قيل لهم اسكنوا هذه القرية وكلوا منها حيث شئتم وقولوا حطة ..."
    final index = SimilarVerseIndex(
      similar: {
        '2:58': ['7:161'],
        '7:161': ['2:58'],
      },
      words: {
        '2:58': _sk('وإذ قلنا ادخلوا هذه القرية فكلوا منها حيث شئتم رغدا '
            'وادخلوا الباب سجدا وقولوا حطة نغفر لكم خطاياكم وسنزيد المحسنين'),
        '7:161': _sk('وإذ قيل لهم اسكنوا هذه القرية وكلوا منها حيث شئتم '
            'وقولوا حطة وادخلوا الباب سجدا نغفر لكم خطيئاتكم سنزيد المحسنين'),
      },
    );

    SimilarVerseSlip? feed(
      SimilarVerseDetector d,
      int idx,
      int pos, {
      bool matched = true,
      String? heard,
    }) =>
        d.onWord(
          wordIndex: idx,
          expectedRef: '2:58',
          position: pos,
          matched: matched,
          heard: heard,
        );

    test('a reciter who slides into 7:161 is told once', () {
      final d = SimilarVerseDetector(index);
      // "منها حيث شئتم" correct (positions 6..8), then 7:161's "وقولوا حطة"
      // instead of 2:58's "رغدا وادخلوا".
      expect(feed(d, 6, 6), isNull);
      expect(feed(d, 7, 7), isNull);
      expect(feed(d, 8, 8), isNull);
      // "حيث شئتم وقولوا" is in 7:161 and not in 2:58.
      final slip = feed(d, 9, 9, matched: false, heard: 'وقولوا');
      expect(slip, const SimilarVerseSlip(from: '2:58', to: '7:161'));
      // The same slip is not repeated in the session.
      expect(feed(d, 10, 10, matched: false, heard: 'حطة'), isNull);
    });

    test('a correct recitation never raises a slip', () {
      final d = SimilarVerseDetector(index);
      for (var i = 0; i < 17; i++) {
        expect(feed(d, i, i), isNull);
      }
    });

    test('an ordinary mistake that fits no similar ayah is ignored', () {
      final d = SimilarVerseDetector(index);
      feed(d, 6, 6);
      feed(d, 7, 7);
      feed(d, 8, 8);
      expect(feed(d, 9, 9, matched: false, heard: 'كتاب'), isNull);
      expect(feed(d, 10, 10, matched: false, heard: 'قلم'), isNull);
    });

    test('a mistake with nothing heard restarts the window', () {
      final d = SimilarVerseDetector(index);
      feed(d, 6, 6);
      feed(d, 7, 7);
      feed(d, 8, 8);
      feed(d, 9, 9, matched: false);
      expect(feed(d, 10, 10, matched: false, heard: 'حطة'), isNull);
    });

    test('a later verdict for an earlier word is not new speech', () {
      final d = SimilarVerseDetector(index);
      feed(d, 6, 6);
      feed(d, 7, 7);
      // A late revision of word 6 is ignored; the window stays in order.
      expect(feed(d, 6, 6), isNull);
      feed(d, 8, 8);
      expect(feed(d, 9, 9, matched: false, heard: 'وقولوا'), isNotNull);
    });

    test('reset forgets reported slips for a new session', () {
      final d = SimilarVerseDetector(index);
      feed(d, 6, 6);
      feed(d, 7, 7);
      feed(d, 8, 8);
      expect(feed(d, 9, 9, matched: false, heard: 'وقولوا'), isNotNull);
      d.reset();
      feed(d, 6, 6);
      feed(d, 7, 7);
      feed(d, 8, 8);
      expect(feed(d, 9, 9, matched: false, heard: 'وقولوا'), isNotNull);
    });
  });

  group('SlipStore', () {
    test('counts repeats and lists the most frequent first', () async {
      SharedPreferences.setMockInitialValues({});
      final store = SlipStore();
      const a = SimilarVerseSlip(from: '2:58', to: '7:161');
      const b = SimilarVerseSlip(from: '2:35', to: '7:19');
      await store.record(a, at: DateTime(2026, 10, 1));
      await store.record(b, at: DateTime(2026, 10, 2));
      await store.record(a, at: DateTime(2026, 10, 3));
      final all = await store.all();
      expect(all.map((r) => '${r.from}>${r.to}:${r.count}'),
          ['2:58>7:161:2', '2:35>7:19:1']);
      expect(all.first.lastAt, DateTime(2026, 10, 3));
    });
  });

  group('HifzMap', () {
    RecitationSessionRecord session({
      required DateTime at,
      List<int> pages = const [],
      List<RecitationMistake> mistakes = const [],
      int surah = 1,
      int from = 1,
      int to = 1,
    }) =>
        RecitationSessionRecord(
          id: at.toIso8601String(),
          scope: 'page',
          surahNumber: surah,
          ayahFrom: from,
          ayahTo: to,
          recordedAt: at,
          overallScore: 1,
          correctCount: 1,
          totalCount: 1,
          durationSeconds: 60,
          mistakes: mistakes,
          pages: pages,
        );

    RecitationMistake miss(int page) => RecitationMistake(
          word: 'x',
          expectedText: 'x',
          errorType: 'error',
          page: page,
        );

    final now = DateTime(2026, 10, 31);

    test('the newest session decides how strong a page is', () {
      final map = HifzMap.fromHistory([
        session(at: DateTime(2026, 10, 30), pages: [5]),
        session(
          at: DateTime(2026, 10, 20),
          pages: [5, 6],
          mistakes: [miss(5), miss(5), miss(5), miss(6)],
        ),
      ], now: now);
      expect(map.stateOf(5).strength, PageStrength.strong);
      expect(map.stateOf(6).strength, PageStrength.shaky);
      expect(map.stateOf(7).strength, PageStrength.notRecited);
      expect(map.recitedCount, 2);
    });

    test('three or more mistakes make a page weak', () {
      final map = HifzMap.fromHistory([
        session(
          at: DateTime(2026, 10, 30),
          pages: [9],
          mistakes: [miss(9), miss(9), miss(9)],
        ),
      ], now: now);
      expect(map.stateOf(9).strength, PageStrength.weak);
      expect(map.stateOf(9).lastMistakes, 3);
    });

    test("today's revision puts the weakest and oldest pages first", () {
      final map = HifzMap.fromHistory([
        session(at: DateTime(2026, 10, 30), pages: [1]), // strong, recent
        session(at: DateTime(2026, 10, 10), pages: [2]), // strong, old
        session(
          at: DateTime(2026, 10, 29),
          pages: [3],
          mistakes: [miss(3)],
        ), // shaky
        session(
          at: DateTime(2026, 10, 28),
          pages: [4],
          mistakes: [miss(4), miss(4), miss(4)],
        ), // weak
      ], now: now);
      expect(map.todaysRevision(count: 5).map((s) => s.page), [4, 3, 2]);
      expect(map.dueCount, 3);
    });

    test('old records without pages are placed with pageOf', () {
      final map = HifzMap.fromHistory(
        [
          RecitationSessionRecord(
            id: 'old',
            scope: 'surah',
            surahNumber: 112,
            ayahFrom: 1,
            ayahTo: 4,
            recordedAt: DateTime(2026, 10, 30),
            overallScore: 1,
            correctCount: 1,
            totalCount: 1,
            durationSeconds: 30,
            mistakes: [
              RecitationMistake(
                word: 'x',
                expectedText: 'x',
                errorType: 'error',
                surahNumber: 112,
                ayahNumber: 2,
              ),
            ],
          ),
        ],
        pageOf: (s, a) => s == 112 ? 604 : null,
        now: now,
      );
      expect(map.stateOf(604).strength, PageStrength.shaky);
    });

    test('a saved record keeps its pages and mistake pages', () {
      final r = session(at: now, pages: [3, 4], mistakes: [miss(4)]);
      final back = RecitationSessionRecord.fromJson(
        jsonDecode(jsonEncode(r.toJson())) as Map<String, dynamic>,
      );
      expect(back.pages, [3, 4]);
      expect(back.mistakes.single.page, 4);
      expect(back.referenceLabel, 'Page 3');
    });
  });
}
