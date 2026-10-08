import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
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
  setUpAll(() async {
    await (FontLoader('KFGQPCUthmanicHafs')
          ..addFont(
              rootBundle.load('assets/fonts/KFGQPCUthmanicHafs-Regular.otf')))
        .load();
  });

  for (final page in [1, 3, 8]) {
    for (final theme in [MushafTheme.minimal, MushafTheme.night]) {
      testWidgets(
          'live page $page in ${theme.id} hides unreached words and retains review geometry',
          (tester) async {
        tester.view.physicalSize = const Size(360, 740);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        final layout = await MushafLayoutRepository().load();
        final ayahs = await LocalCorpusRepository().getAyahsByPage(page);
        final words = <String>[];
        final lines = <int>[];
        final boundaries = <int>[];
        final labels = <String>[];
        final markerLines = <int>[];
        for (final ayah in ayahs) {
          final printed = layout[ayah.reference]!;
          // The corpus includes a trailing verse-number token. The printed
          // layout counts only Arabic words; markers are supplied separately.
          words
              .addAll(ayah.words.take(printed.words.length).map((w) => w.text));
          lines.addAll(printed.words.map((w) => w.line));
          boundaries.add(words.length - 1);
          labels.add(ayah.ayahNumber.toString());
          markerLines.add(printed.marker.line);
        }
        final statuses = List.filled(words.length, LiveWordStatus.pending);
        for (final i in [0, 1, 3, 4]) {
          statuses[i] = LiveWordStatus.matched;
        }
        statuses[5] = LiveWordStatus.error;
        // Stale backend evidence ahead of the cursor must stay neutral.
        statuses[words.length - 1] = LiveWordStatus.skipped;
        final preview = GlobalKey();
        Widget view(bool review) => RepaintBoundary(
              key: preview,
              child: MaterialApp(
                debugShowCheckedModeBanner: false,
                theme: theme.toThemeData(),
                home: Scaffold(
                  body: Padding(
                    padding: const EdgeInsets.all(12),
                    child: MushafRevealView(
                      words: words,
                      statuses: statuses,
                      cursor: 6,
                      mushaf: theme,
                      hideUnspoken: true,
                      reviewMode: review,
                      lineNumbers: lines,
                      ayahBoundaries: boundaries,
                      ayahLabels: labels,
                      ayahLineNumbers: markerLines,
                      lineCount: page == 1 ? 8 : 15,
                      centeredLines: page == 1,
                      minimumHeight: 680,
                    ),
                  ),
                ),
              ),
            );
        final texts = words.toSet().toList();
        await tester.pumpWidget(view(true));
        final reviewRects = [for (final text in texts) rectOf(tester, text)];
        for (final review in [true, false]) {
          await tester.pumpWidget(view(review));
          expect([for (final text in texts) rectOf(tester, text)], reviewRects);
          if (review) {
            expect(inkOf(tester, words[2]), theme.ghostInk);
            expect(inkOf(tester, words.last, last: true), theme.ghostInk);
            expect(inkOf(tester, words[5]), theme.mismatchInk);
            expect(underlineCount(tester, theme.mismatchInk), 1);
            expect(mushafUnits(tester).every((s) => s.style!.color!.a > 0),
                isTrue);
          } else {
            expect(inkOf(tester, words[2])!.a, 0);
            expect(inkOf(tester, words[5]), theme.mismatchInk);
            expect(inkOf(tester, words.last, last: true)!.a, 0);
            expect(underlineCount(tester, theme.mismatchInk), 1);
          }
          for (final label in labels) {
            expect(inkOf(tester, ayahMarkerText(label))!.a, 1);
          }
          expect(tester.takeException(), isNull);
          if (const bool.fromEnvironment('CAPTURE_QURAN_UI')) {
            final boundary = preview.currentContext!.findRenderObject()!
                as RenderRepaintBoundary;
            await tester.runAsync(() async {
              final image = await boundary.toImage(pixelRatio: 2);
              final data =
                  await image.toByteData(format: ui.ImageByteFormat.png);
              final mode = review ? 'review' : 'live';
              final file =
                  File('build/review/hifz-$mode-$page-${theme.id}.png');
              await file.parent.create(recursive: true);
              await file.writeAsBytes(data!.buffer.asUint8List());
              image.dispose();
            });
          }
        }
      });
    }
  }
}
