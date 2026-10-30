// Hifz on Madani page 1 (Al-Fatihah) with every word still unsaid.
//
// Reported symptom: "uneven spacing — a huge gap between ayah 6 and 7".
// Diagnosis: on the printed page ayah 7 spans rows 6–8, so row 7 holds words
// but NO ayah marker. With those words hidden the row looks empty, but it is
// the real printed row, not lost layout. These tests lock that in: hidden
// words keep their exact width, every row has the same pitch, markers sit at
// the same place as in Tilawat, and each row boundary is a single faint rule.
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_stream_event.dart';
import 'package:qari/data/models/word_model.dart';
import 'package:qari/data/repositories/local_corpus_repository.dart';
import 'package:qari/data/repositories/mushaf_layout_repository.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:qari/features/recitation/presentation/widgets/mushaf_reveal_view.dart';

import 'mushaf_text_helpers.dart';

void main() {
  final words = <String>[];
  final lines = <int>[];
  final boundaries = <int>[];
  final labels = <String>[];
  final markerLines = <int>[];

  setUpAll(() async {
    await (FontLoader('KFGQPCUthmanicHafs')
          ..addFont(
              rootBundle.load('assets/fonts/KFGQPCUthmanicHafs-Regular.otf')))
        .load();
    final layout = await MushafLayoutRepository().load();
    final ayahs = await LocalCorpusRepository().getAyahsByPage(1);
    for (final ayah in ayahs) {
      final printed = layout[ayah.reference]!;
      words.addAll(ayah.words.take(printed.words.length).map((w) => w.text));
      lines.addAll(printed.words.map((w) => w.line));
      boundaries.add(words.length - 1);
      labels.add(ayah.ayahNumber.toString());
      markerLines.add(printed.marker.line);
    }
  });

  Widget page(MushafTheme theme, {required bool hifz}) => MaterialApp(
        theme: theme.toThemeData(),
        home: Scaffold(
          body: MushafRevealView(
            words: words,
            statuses: List.filled(words.length, LiveWordStatus.pending),
            cursor: 0,
            mushaf: theme,
            hideUnspoken: hifz,
            lineNumbers: lines,
            ayahBoundaries: boundaries,
            ayahLabels: labels,
            ayahLineNumbers: markerLines,
            // Exactly what LiveRecitationPage passes for pages 1–2.
            lineCount: 8,
            centeredLines: true,
            minimumHeight: 680,
          ),
        ),
      );

  test('page 1 printed layout: ayah 7 leaves row 7 without a marker', () {
    expect(labels, ['1', '2', '3', '4', '5', '6', '7']);
    expect(markerLines.last, 8);
    expect(markerLines, isNot(contains(7)));
    expect(lines, contains(7), reason: 'row 7 still carries ayah-7 words');
  });

  for (final theme in [MushafTheme.night, MushafTheme.parchment]) {
    testWidgets('${theme.id}: Hifz keeps Tilawat geometry on page 1',
        (tester) async {
      tester.view.physicalSize = const Size(360, 740);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(page(theme, hifz: false));
      final markers = [for (final l in labels) ayahMarkerText(l)];
      final tilawatMarkers = [for (final m in markers) rectOf(tester, m)];
      final tilawatWords = [for (final w in words.toSet()) rectOf(tester, w)];

      await tester.pumpWidget(page(theme, hifz: true));

      // Every ayah marker ١–٧ stays visible and in its printed position.
      for (var i = 0; i < markers.length; i++) {
        expect(rectOf(tester, markers[i]), tilawatMarkers[i],
            reason: 'marker ${markers[i]} moved in Hifz');
        expect(inkOf(tester, markers[i])!.a, greaterThan(0));
      }
      // Hidden words are transparent but keep their exact width/position.
      expect([for (final w in words.toSet()) rectOf(tester, w)], tilawatWords);
      final rowSevenWord = words[lines.indexOf(7)];
      expect(inkOf(tester, rowSevenWord)!.a, 0);
      expect(rectOf(tester, rowSevenWord).width, greaterThan(8),
          reason: 'row 7 is occupied by hidden ayah-7 words, not empty');

      // Uniform row pitch and a single faint rule per row boundary.
      final pitch = tester.getSize(find.byKey(const ValueKey('mushaf-line-2')));
      for (var row = 2; row <= 8; row++) {
        final rowFinder = find.byKey(ValueKey('mushaf-line-$row'));
        expect(tester.getSize(rowFinder).height,
            closeTo(pitch.height, 0.01),
            reason: 'row $row pitch');
        final decoration = tester
            .widget<DecoratedBox>(find
                .descendant(of: rowFinder, matching: find.byType(DecoratedBox))
                .first)
            .decoration as BoxDecoration;
        final border = decoration.border! as Border;
        expect(border.top, BorderSide.none,
            reason: 'no second, dark divider edge on row $row');
      }
      expect(tester.takeException(), isNull);
    });
  }
}
