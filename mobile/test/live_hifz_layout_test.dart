import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_stream_event.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:qari/features/recitation/presentation/widgets/mushaf_reveal_view.dart';

import 'mushaf_text_helpers.dart';

const _words = ['بِسْمِ', 'اللَّهِ', 'الرَّحْمَٰنِ', 'الرَّحِيمِ', 'الْحَمْدُ', 'رَبِّ'];
const _statuses = [
  LiveWordStatus.matched,
  LiveWordStatus.pending,
  LiveWordStatus.error,
  LiveWordStatus.pending,
  LiveWordStatus.skipped,
  LiveWordStatus.pending,
];

Widget _page({bool review = false, bool context = false, int cursor = 3}) => MaterialApp(
      home: Scaffold(
        body: MushafRevealView(
          words: _words,
          statuses: _statuses,
          cursor: cursor,
          reviewMode: review,
          hideUnspoken: true,
          showUnspokenContext: context,
          lineNumbers: const [1, 1, 1, 2, 2, 2],
          ayahBoundaries: const [2, 5],
          ayahLabels: const ['1', '2'],
          ayahLineNumbers: const [1, 2],
          lineCount: 2,
          minimumHeight: 180,
          mushaf: MushafTheme.classic,
        ),
      ),
    );

void main() {
  testWidgets('live context shows all pending words without claiming recognition',
      (tester) async {
    await tester.pumpWidget(_page(context: true));
    for (final index in [1, 3, 4, 5]) {
      expect(inkOf(tester, _words[index]), MushafTheme.classic.ghostInk);
    }
    expect(inkOf(tester, _words[2]), MushafTheme.classic.mismatchInk);
    expect(underlineCount(tester, MushafTheme.classic.mismatchInk), 1);
    expect(washOf(tester, _words[4]), isNull);
    expect(inkOf(tester, ayahMarkerText('2')), MushafTheme.classic.ghostInk);
  });

  testWidgets('unrecognised words behind the live cursor leave no invisible hole',
      (tester) async {
    await tester.pumpWidget(_page());
    expect(inkOf(tester, _words[0]), MushafTheme.classic.text);
    expect(inkOf(tester, _words[1]), MushafTheme.classic.ghostInk);
    expect(inkOf(tester, _words[2]), MushafTheme.classic.mismatchInk);
    expect(washOf(tester, _words[1]), isNull);
    expect(underlineCount(tester, MushafTheme.classic.mismatchInk), 1);
    // A stale skipped verdict ahead of the cursor must not reveal a future word.
    expect(inkOf(tester, _words[4])!.a, 0);
  });

  testWidgets('Hifz markers do not float without their unreached verse ending',
      (tester) async {
    await tester.pumpWidget(_page());
    expect(inkOf(tester, ayahMarkerText('1'))!.a, greaterThan(0));
    expect(inkOf(tester, ayahMarkerText('2'))!.a, 0);
    expect(washOf(tester, _words[3]), isNull,
        reason: 'a concealed listening word must not paint an empty rectangle');
    await tester.pumpWidget(_page(cursor: 6));
    expect(inkOf(tester, _words[5]), MushafTheme.classic.ghostInk);
    expect(inkOf(tester, ayahMarkerText('2'))!.a, greaterThan(0));
  });

  testWidgets('live and review retain identical RTL words and inline marker geometry',
      (tester) async {
    tester.view.physicalSize = const Size(360, 740);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(_page(review: true));
    final texts = [..._words, ayahMarkerText('1'), ayahMarkerText('2')];
    final reviewRects = [for (final text in texts) rectOf(tester, text)];
    await tester.pumpWidget(_page(context: true));
    expect([for (final text in texts) rectOf(tester, text)], reviewRects);
    final first = rectOf(tester, _words[0]);
    final second = rectOf(tester, _words[1]);
    final ending = rectOf(tester, _words[2]);
    final marker = rectOf(tester, ayahMarkerText('1'));
    expect(first.left, greaterThan(second.right));
    expect(ending.left, greaterThan(marker.right));
    expect(marker.center.dy, closeTo(ending.center.dy, 1));
    expect(find.byType(Wrap), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
