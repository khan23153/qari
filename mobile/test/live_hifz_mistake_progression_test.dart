import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_stream_event.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:qari/features/recitation/presentation/widgets/mushaf_reveal_view.dart';

import 'mushaf_text_helpers.dart';

void main() {
  testWidgets('confirmed mistake stays red while later correct words reveal',
      (tester) async {
    const words = ['بِسْمِ', 'اللَّهِ', 'الرَّحْمَٰنِ'];
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: MushafRevealView(
          words: words,
          statuses: const [
            LiveWordStatus.error,
            LiveWordStatus.matched,
            LiveWordStatus.pending,
          ],
          cursor: 2,
          hideUnspoken: true,
          ayahBoundaries: const [0, 2],
          ayahLabels: const ['1', '2'],
          mushaf: MushafTheme.classic,
        ),
      ),
    ));

    expect(inkOf(tester, words[0]), MushafTheme.classic.mismatchInk);
    expect(underlineCount(tester, MushafTheme.classic.mismatchInk), 1);
    expect(inkOf(tester, words[1]), MushafTheme.classic.text);
    expect(inkOf(tester, words[2])!.a, 0);
    expect(inkOf(tester, ayahMarkerText('1')), MushafTheme.classic.accent);
    expect(inkOf(tester, ayahMarkerText('2')), MushafTheme.classic.accent);
    expect(tester.takeException(), isNull);
  });
}
