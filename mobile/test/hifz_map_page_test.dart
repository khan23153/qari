import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:qari/data/models/recitation_session_record.dart';
import 'package:qari/features/recitation/hifz/hifz_map.dart';
import 'package:qari/features/recitation/hifz/similar_verses.dart';
import 'package:qari/features/recitation/hifz/slip_store.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:qari/features/recitation/presentation/pages/hifz_map_page.dart';
import 'package:qari/features/recitation/presentation/widgets/similar_verse_widgets.dart';

void main() {
  final now = DateTime.now();

  RecitationSessionRecord session(DateTime at, List<int> pages,
          [Map<int, int> mistakes = const {}]) =>
      RecitationSessionRecord(
        id: '$at',
        scope: 'page',
        surahNumber: 1,
        ayahFrom: 1,
        ayahTo: 1,
        recordedAt: at,
        overallScore: 1,
        correctCount: 1,
        totalCount: 1,
        durationSeconds: 60,
        pages: pages,
        mistakes: [
          for (final e in mistakes.entries)
            for (var i = 0; i < e.value; i++)
              RecitationMistake(
                word: 'x',
                expectedText: 'x',
                errorType: 'error',
                page: e.key,
              ),
        ],
      );

  HifzMapData data({List<SlipRecord> slips = const []}) => HifzMapData(
        map: HifzMap.fromHistory([
          session(now.subtract(const Duration(days: 1)), [1]),
          session(now.subtract(const Duration(days: 2)), [2], {2: 3}),
        ]),
        slips: slips,
        pageStart: const {1: (1, 1), 2: (2, 1)},
      );

  Future<void> pump(WidgetTester tester, HifzMapData d,
      {void Function(int page)? onRecite}) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(
      home: HifzMapPage(
        load: () async => d,
        onRecitePage: (_, page, __) => onRecite?.call(page),
      ),
    ));
    await tester.pumpAndSettle();
  }

  testWidgets('shows how many pages are recited and due', (tester) async {
    await pump(tester, data());
    expect(find.text('2 of 604'), findsOneWidget);
    expect(find.text('pages recited'), findsOneWidget);
    expect(find.text('Revise today'), findsOneWidget);
    // Page 2 had three mistakes: it is the first revision pick.
    expect(find.text('Page 2 · Al-Baqarah'), findsOneWidget);
    expect(find.textContaining('3 mistakes last time'), findsWidgets);
  });

  testWidgets('every page has a tile', (tester) async {
    await pump(tester, data());
    expect(find.byKey(const ValueKey('hifz-page-1')), findsOneWidget);
    await tester.scrollUntilVisible(
      find.byKey(const ValueKey('hifz-page-604')),
      300,
    );
    expect(find.byKey(const ValueKey('hifz-page-604')), findsOneWidget);
  });

  testWidgets('tapping a tile offers to recite that page', (tester) async {
    int? recited;
    await pump(tester, data(), onRecite: (p) => recited = p);
    await tester.tap(find.byKey(const ValueKey('hifz-page-1')));
    await tester.pumpAndSettle();
    expect(find.text('Page 1 · Al-Fatihah'), findsWidgets);
    expect(find.textContaining('No mistakes last time'), findsOneWidget);
    await tester.tap(find.text('Recite this page'));
    await tester.pumpAndSettle();
    expect(recited, 1);
  });

  testWidgets('lists the similar verses the reciter mixes up', (tester) async {
    await pump(
      tester,
      data(slips: [
        SlipRecord(
          from: '2:58',
          to: '7:161',
          count: 2,
          lastAt: DateTime(2026, 10, 30),
        ),
      ]),
    );
    await tester.scrollUntilVisible(find.text('2:58 → 7:161'), 300);
    expect(find.text('2:58 → 7:161'), findsOneWidget);
    expect(find.textContaining('2 times'), findsOneWidget);
  });

  testWidgets('the live banner names the verse the reciter slid into',
      (tester) async {
    var dismissed = false;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: SimilarVerseBanner(
          slip: const SimilarVerseSlip(from: '2:58', to: '7:161'),
          theme: MushafTheme.night,
          onDismiss: () => dismissed = true,
        ),
      ),
    ));
    expect(find.text('Similar verse'), findsOneWidget);
    expect(find.textContaining("Al-A'raf 7:161"), findsOneWidget);
    expect(find.text('Compare'), findsOneWidget);
    await tester.tap(find.byTooltip('Dismiss'));
    expect(dismissed, isTrue);
  });
}
