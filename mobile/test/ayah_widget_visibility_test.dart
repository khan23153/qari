import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:qari/data/models/word_model.dart';
import 'package:qari/features/quran_reader/presentation/widgets/ayah_widget.dart';

AyahModel _sampleAyah() {
  return AyahModel(
    ayahId: 1,
    surahNumber: 24,
    ayahNumber: 1,
    ayahText: 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ',
    translationEn: 'In the name of Allah, the Entirely Merciful.',
    transliteration: 'bismi llāhi r-raḥmāni r-raḥīmi',
    words: [
      WordModel(wordId: 1, surahNumber: 24, ayahNumber: 1, wordNumber: 1, text: 'بِسْمِ', transliteration: 'bismi', translationEn: 'In the name', posGroup: 'harf_jarr', rootArabic: 'سم'),
      WordModel(wordId: 2, surahNumber: 24, ayahNumber: 1, wordNumber: 2, text: 'ٱللَّهِ', transliteration: 'Allāhi', translationEn: 'of Allah', posGroup: 'ism', rootArabic: 'اله'),
    ],
  );
}

void main() {
  testWidgets('AyahWidget renders visible ayah text (no blank screen)',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.light(),
        home: Scaffold(
          body: AyahWidget(
            ayah: _sampleAyah(),
            languageCode: 'en',
            arabicFontSize: 24,
            densityLevel: 3,
            grammarColorsEnabled: true,
            tajweedColorsEnabled: false,
            isPlaying: false, // the state that previously hid everything
            onWordTapped: (_) {},
            onPlayTapped: () {},
            onReciteTapped: () {},
            onContextStoryTapped: () {},
            onShareTapped: () {},
            onSpeedTapped: () {},
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // The Arabic words must be present in the tree (ayah text is rendered
    // word-by-word, not as one string).
    expect(find.text('بِسْمِ'), findsOneWidget);
    expect(find.text('ٱللَّهِ'), findsOneWidget);

    // And the first word must actually be painted (visible), not hidden at
    // opacity 0.
    final context = tester.element(find.text('بِسْمِ'));
    final renderObject = context.findRenderObject() as RenderBox;
    expect(renderObject.hasSize, isTrue);
    expect(renderObject.size.width, greaterThan(0));
    expect(renderObject.size.height, greaterThan(0));

    // There must be no ancestor RenderAnimatedOpacity effectively hiding the
    // content (opacity ~0). This is the exact bug: the old code wrapped the
    // ayah in `.animate(target: 0).fadeIn()`, leaving it painted at opacity 0.
    bool hiddenByOpacity = false;
    RenderObject? ancestor = context.findRenderObject();
    while (ancestor != null) {
      if (ancestor is RenderAnimatedOpacity &&
          ancestor.opacity.value < 0.01) {
        hiddenByOpacity = true;
        break;
      }
      ancestor = ancestor.parent;
    }
    expect(hiddenByOpacity, isFalse,
        reason: 'Ayah content is hidden by an opacity-0 animation.');
  });
}
