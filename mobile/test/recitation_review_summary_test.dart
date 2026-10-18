import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_model.dart';
import 'package:qari/data/models/recitation_stream_event.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:qari/features/recitation/presentation/recitation_review.dart';
import 'package:qari/features/recitation/presentation/widgets/recitation_review_summary.dart';

Widget summary({bool pronunciationAvailable = false}) {
  final result = RecitationResult(
    sessionId: 'review',
    surahNumber: 1,
    ayahNumber: 1,
    overallScore: .5,
    createdAt: DateTime.utc(2026, 10, 18),
    pronunciationAvailable: pronunciationAvailable,
    wordVerdicts: const [
      WordVerdict(word: 'الحمد', wordIndex: 0, isCorrect: true),
      WordVerdict(word: 'لله', wordIndex: 1, isCorrect: false),
    ],
  );
  return MaterialApp(
      home: Scaffold(
          body: RecitationReviewSummary(
    review: RecitationReview(
      statuses: const [
        LiveWordStatus.matched,
        LiveWordStatus.error,
        LiveWordStatus.pending
      ],
      reach: 2,
      result: result,
    ),
    mushaf: MushafTheme.classic,
    theme: ThemeData(),
  )));
}

void main() {
  testWidgets('word score does not imply assessed pronunciation',
      (tester) async {
    tester.view.physicalSize = const Size(360, 640);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(summary());
    expect(find.text('1 matched · 1 mistake · 1 not reached'), findsOneWidget);
    expect(find.text('Word matching · Pronunciation not assessed'),
        findsOneWidget);
    expect(find.text('Tap an underlined word to compare'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('availability flag controls pronunciation disclosure',
      (tester) async {
    await tester.pumpWidget(summary(pronunciationAvailable: true));
    expect(
        find.text('Word matching · Pronunciation not assessed'), findsNothing);
    expect(find.text('Word matching'), findsOneWidget);
  });
}
