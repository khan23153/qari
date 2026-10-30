// Regression tests for the Mushaf sheets rendering with the WRONG theme.
//
// Production bug: the live page wraps its body in
// `Theme(data: mushaf.toThemeData())`, but opens its sheets with its own
// `State.context`, which sits ABOVE that Theme. A modal route only captures
// themes from the context it is opened with, so the sheets painted Mushaf
// paper (cream on Classic/Parchment) while their children resolved colours
// from the app-wide dark theme: a dark-filled Surah/Ayah box, a dark
// tajweed card, and white "Page theme" ink that vanished on cream.
//
// [_host] reproduces that exact structure: the app runs `AppTheme.darkTheme`
// (filled, dark input decoration) and the sheet is opened from a context
// above the page's Mushaf Theme.
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/core/theme/app_theme.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_appearance_sheet.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_jump_sheet.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';

/// WCAG relative-contrast ratio of [fg] composited over [bg].
double _contrast(Color fg, Color bg) {
  final a = Color.alphaBlend(fg, bg).computeLuminance();
  final b = bg.computeLuminance();
  return (math.max(a, b) + 0.05) / (math.min(a, b) + 0.05);
}

/// The colour a [Text] actually paints with (its merged default style).
Color _textInk(WidgetTester tester, Finder text) =>
    tester.renderObject<RenderParagraph>(text).text.style!.color!;

/// The colour an [Icon] actually paints with (explicit or inherited).
Color _iconInk(WidgetTester tester, Finder icon) =>
    tester.widget<Icon>(icon).color ??
    IconTheme.of(tester.element(icon)).color!;

Widget _host(
  MushafTheme mushaf,
  void Function(BuildContext aboveMushafTheme) open,
) {
  return MaterialApp(
    theme: AppTheme.darkTheme,
    home: Builder(
      // `outer` mirrors the page's State.context: above the Mushaf Theme.
      builder: (outer) => Theme(
        data: mushaf.toThemeData(),
        child: Scaffold(
          backgroundColor: mushaf.background,
          body: Center(
            child: ElevatedButton(
              onPressed: () => open(outer),
              child: const Text('open'),
            ),
          ),
        ),
      ),
    ),
  );
}

void main() {
  group('Mushaf appearance sheet', () {
    for (final t in MushafTheme.all) {
      testWidgets('${t.id}: page-theme row, card and switch are legible',
          (tester) async {
        await tester.pumpWidget(_host(
          t,
          (ctx) => MushafAppearanceSheet.show(
            ctx,
            theme: t,
            tajweedOn: false,
            onTajweedChanged: (_) {},
            onPageTheme: () {},
          ),
        ));
        await tester.tap(find.text('open'));
        await tester.pumpAndSettle();

        // Root cause A: "Page theme" label, palette icon and chevron must
        // read clearly on the sheet paper (was white-on-cream).
        final paper = t.background;
        expect(_contrast(_textInk(tester, find.text('Page theme')), paper),
            greaterThanOrEqualTo(4.5),
            reason: 'Page theme label on ${t.id} paper');
        for (final icon in [
          Icons.palette_outlined,
          Icons.chevron_right_rounded,
        ]) {
          expect(_contrast(_iconInk(tester, find.byIcon(icon)), paper),
              greaterThanOrEqualTo(3.0),
              reason: '$icon on ${t.id} paper');
        }

        // Root cause B: the tajweed card is a shade of the paper, never a
        // fixed dark block on light paper.
        final card = tester
            .widget<Material>(
                find.byKey(const ValueKey('mushaf-tajweed-card')))
            .color!;
        expect(ThemeData.estimateBrightnessForColor(card),
            ThemeData.estimateBrightnessForColor(paper),
            reason: 'card brightness follows ${t.id} paper');
        expect(_contrast(_textInk(tester, find.text('Tajweed colours')), card),
            greaterThanOrEqualTo(4.5));
        expect(
            _contrast(
                _textInk(tester,
                    find.text(
                        'Colour each letter by its tajweed rule as it appears')),
                card),
            greaterThanOrEqualTo(4.5));

        // The OFF switch must be visible: thumb and outline >= 3:1 on card.
        final switchFinder = find.byKey(const ValueKey('mushaf-tajweed-switch'));
        final switchTheme = Theme.of(tester.element(switchFinder)).switchTheme;
        const off = <WidgetState>{};
        expect(_contrast(switchTheme.thumbColor!.resolve(off)!, card),
            greaterThanOrEqualTo(3.0),
            reason: 'inactive thumb on ${t.id}');
        expect(_contrast(switchTheme.trackOutlineColor!.resolve(off)!, card),
            greaterThanOrEqualTo(3.0),
            reason: 'inactive outline on ${t.id}');

        expect(tester.takeException(), isNull);
      });
    }

    testWidgets('toggling updates the switch in place and reports the value',
        (tester) async {
      bool? reported;
      await tester.pumpWidget(_host(
        MushafTheme.parchment,
        (ctx) => MushafAppearanceSheet.show(
          ctx,
          theme: MushafTheme.parchment,
          tajweedOn: false,
          onTajweedChanged: (v) => reported = v,
          onPageTheme: () {},
        ),
      ));
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
      await tester.tap(find.byType(Switch));
      await tester.pumpAndSettle();
      expect(reported, isTrue);
      expect(tester.widget<Switch>(find.byType(Switch)).value, isTrue);
    });

    testWidgets('Page theme closes the sheet and requests the picker',
        (tester) async {
      var opened = 0;
      await tester.pumpWidget(_host(
        MushafTheme.classic,
        (ctx) => MushafAppearanceSheet.show(
          ctx,
          theme: MushafTheme.classic,
          tajweedOn: true,
          onTajweedChanged: (_) {},
          onPageTheme: () => opened++,
        ),
      ));
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Page theme'));
      await tester.pumpAndSettle();
      expect(opened, 1);
      expect(find.text('Tajweed colours'), findsNothing);
    });
  });

  group('Jump to a verse sheet', () {
    Future<void> openJump(WidgetTester tester, MushafTheme t,
        {int surah = 1, bool pageMode = true}) async {
      await tester.pumpWidget(_host(
        t,
        (ctx) => MushafJumpSheet.show(
          ctx,
          theme: t,
          initialSurah: surah,
          initialAyahFrom: 1,
          initialAyahTo: 1,
          initialAyahCount: 7,
          pageMode: pageMode,
        ),
      ));
      await tester.tap(find.text('open'));
      await tester.pumpAndSettle();
    }

    for (final t in MushafTheme.all) {
      testWidgets('${t.id}: labels sit above readable, paper-matched fields',
          (tester) async {
        await openJump(tester, t);
        final surahField =
            find.byKey(const ValueKey('mushaf-jump-surah-field'));
        final ayahField = find.byKey(const ValueKey('mushaf-jump-ayah-field'));

        for (final (label, field) in [('Surah', surahField), ('Ayah', ayahField)]) {
          final labelFinder = find.text(label);
          // Root cause B: the label is NOT a floating label notched into
          // the field's outline; it sits fully above the box.
          expect(
              find.ancestor(
                  of: labelFinder, matching: find.byType(InputDecorator)),
              findsNothing,
              reason: '$label must not be an InputDecorator label');
          expect(tester.getRect(labelFinder).bottom,
              lessThanOrEqualTo(tester.getRect(field).top + 0.5),
              reason: '$label above its box on ${t.id}');

          // Root cause A: the EFFECTIVE fill (after the inherited input
          // theme is applied) matches the paper, not the app's dark fill.
          final decorator = tester.widget<InputDecorator>(field);
          final effective = decorator.decoration.applyDefaults(
              Theme.of(tester.element(field)).inputDecorationTheme);
          expect(effective.filled, isTrue);
          final fill = effective.fillColor!;
          expect(ThemeData.estimateBrightnessForColor(fill),
              ThemeData.estimateBrightnessForColor(t.background),
              reason: '$label fill follows ${t.id} paper');
        }

        // Root cause C: the selected surah — number, English and Arabic
        // name — renders INSIDE the Surah box, not floating between boxes.
        final selected = surahPickerLabel(1);
        expect(selected, '1. Al-Fatihah — الفاتحة');
        final inSurah =
            find.descendant(of: surahField, matching: find.text(selected));
        expect(inSurah, findsWidgets);
        expect(tester.getRect(surahField).contains(
                tester.getRect(inSurah.first).center),
            isTrue);
        expect(find.text('الفاتحة'), findsNothing,
            reason: 'no stand-alone Arabic name between the fields');

        final fill = tester
            .widget<InputDecorator>(surahField)
            .decoration
            .applyDefaults(
                Theme.of(tester.element(surahField)).inputDecorationTheme)
            .fillColor!;
        expect(_contrast(_textInk(tester, inSurah.first), fill),
            greaterThanOrEqualTo(4.5),
            reason: 'selected surah legible on ${t.id}');

        final ayahValue =
            find.descendant(of: ayahField, matching: find.text('1'));
        expect(ayahValue, findsWidgets);
        expect(_contrast(_textInk(tester, ayahValue.first), fill),
            greaterThanOrEqualTo(4.5),
            reason: 'selected ayah legible on ${t.id}');

        expect(tester.takeException(), isNull);
      });
    }

    testWidgets('long surah names fit a narrow phone without overflow',
        (tester) async {
      tester.view.physicalSize = const Size(320, 700);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      // Surah 4 has one of the longer English names.
      await openJump(tester, MushafTheme.parchment, surah: 4, pageMode: false);
      expect(find.text('From ayah'), findsOneWidget);
      expect(find.text('To ayah'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    test('surahPickerLabel covers every surah and rejects out of range', () {
      for (var i = 1; i <= 114; i++) {
        expect(surahPickerLabel(i), startsWith('$i. '));
        expect(surahPickerLabel(i), contains('—'));
      }
      expect(surahPickerLabel(115), '115');
    });
  });
}
