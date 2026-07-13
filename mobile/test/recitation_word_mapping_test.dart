import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../lib/data/models/recitation_model.dart';
import '../lib/features/recitation/presentation/widgets/recitation_results.dart';

// The real target ayah words (e.g. Surah 1:1) would resolve to this script.
const _ayahWords = ['بِسْمِ', 'ٱللَّهِ', 'ٱلرَّحْمَٰنِ', 'ٱلرَّحِيمِ'];

WordVerdict _stubVerdict(int index) => WordVerdict(
      word: 'word_1_1_${index + 1}',
      wordIndex: index,
      isCorrect: true,
    );

RecitationResult _stubResult() => RecitationResult(
      sessionId: 's1',
      surahNumber: 1,
      ayahNumber: 1,
      overallScore: 1.0,
      createdAt: DateTime.utc(2026, 1, 1),
      wordVerdicts: [_stubVerdict(0), _stubVerdict(1), _stubVerdict(2)],
    );

void main() {
  group('WordVerdict.displayWord', () {
    test('resolves arabic from ayah words when backend sends a key', () {
      final v = _stubVerdict(0);
      expect(v.word, 'word_1_1_1');
      expect(v.displayWord(_ayahWords), 'بِسْمِ');
    });

    test('prefers real arabic already present on the verdict', () {
      final v = WordVerdict(
        word: 'ٱللَّهِ',
        wordIndex: 99,
        isCorrect: true,
      );
      expect(v.displayWord(_ayahWords), 'ٱللَّهِ');
    });

    test('falls back to the key when out of ayah range', () {
      final v = WordVerdict(
        word: 'word_1_1_99',
        wordIndex: 99,
        isCorrect: true,
      );
      expect(v.displayWord(_ayahWords), 'word_1_1_99');
    });
  });

  group('RecitationResults word grid', () {
    testWidgets('shows real arabic script, not backend keys', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: RecitationResults(
              result: _stubResult(),
              ayahWords: _ayahWords,
              onWordTapped: (_) {},
              onRetry: () {},
              theme: ThemeData.light(),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Real arabic words are rendered.
      expect(find.text('بِسْمِ'), findsWidgets);
      expect(find.text('ٱللَّهِ'), findsWidgets);

      // Raw backend keys must NOT be shown.
      expect(find.text('word_1_1_1'), findsNothing);
      expect(find.text('word_1_1_2'), findsNothing);
    });
  });
}
