import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_model.dart';
import 'package:qari/features/recitation/presentation/widgets/recitation_results.dart';

void main() {
  for (final type in [
    'not_reached',
    'missed',
    'substituted',
    'harakat_mistake'
  ]) {
    testWidgets('unconfirmed $type verdict is never a red result word',
        (tester) async {
      final result = RecitationResult(
        sessionId: 'unread',
        surahNumber: 1,
        ayahNumber: 2,
        overallScore: 1,
        createdAt: DateTime.utc(2026),
        wordVerdicts: [
          WordVerdict(
              word: 'الرحمن',
              wordIndex: 0,
              isCorrect: false,
              errorType: type,
              actualText: 'الرحيم')
        ],
      );
      await tester.pumpWidget(MaterialApp(
          home: Scaffold(
              body: RecitationResults(
        result: result,
        ayahWords: const ['الرحمن'],
        onWordTapped: (_) {},
        onRetry: () {},
        theme: ThemeData.light(),
      ))));
      await tester.pumpAndSettle();
      final style = tester.widget<Text>(find.text('الرحمن')).style!;
      expect(style.color, isNot(const Color(0xFFEF4444)));
      expect(style.decoration, TextDecoration.none);
    });
  }
  testWidgets(
      'result words use exact red for missed, wrong and observed harakat',
      (tester) async {
    const words = ['لله', 'رب', 'العالمين', 'الرحمن'];
    final result = RecitationResult(
      sessionId: 'observed',
      surahNumber: 1,
      ayahNumber: 2,
      overallScore: 0,
      createdAt: DateTime.utc(2026),
      wordVerdicts: [
        for (var i = 0; i < 3; i++)
          WordVerdict(
              word: words[i],
              wordIndex: i,
              isCorrect: false,
              evidenceConfirmed: true,
              actualText: i == 0 ? '' : 'لِلَّهُ',
              errorType: ['missed', 'substituted', 'harakat_mistake'][i]),
      ],
    );
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: RecitationResults(
      result: result,
      ayahWords: words,
      onWordTapped: (_) {},
      onRetry: () {},
      theme: ThemeData.light(),
    ))));
    await tester.pumpAndSettle();
    for (final word in words.take(3)) {
      final style = tester.widget<Text>(find.text(word)).style!;
      expect(style.color, const Color(0xFFEF4444));
      expect(style.decorationColor, const Color(0xFFEF4444));
    }
    expect(tester.widget<Text>(find.text(words.last)).style!.color,
        isNot(const Color(0xFFEF4444)));
    expect(find.text('Pronunciation'), findsNothing);
  });
}
