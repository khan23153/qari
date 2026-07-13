import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../lib/data/models/lesson_model.dart';
import '../lib/features/lessons/presentation/pages/lesson_list_page.dart';
import '../lib/features/lessons/presentation/pages/lesson_player_page.dart';
import '../lib/features/lessons/presentation/widgets/quiz_widget.dart';
import '../lib/features/lessons/presentation/widgets/grammar_card_widget.dart';

QuizQuestionModel q(QuizType type) => QuizQuestionModel(
      id: 'q1',
      type: type,
      question: 'Test question?',
      questionArabic: '؟ اختبار',
      options: ['A', 'B', 'C', 'D'],
      correctAnswer: 'A',
      matchPairs: const [MatchPair(left: 'كَتَبَ', right: 'he wrote')],
      blankAnswer: 'test',
      explanation: 'Because.',
    );

final _concept = LessonConcept(
  id: 'c1',
  title: 'Concept',
  explanation: 'An explanation.',
  explanationUrdu: 'اردو وضاحت',
  arabicExample: 'بِسْمِ ٱللَّهِ',
  transliteration: 'bismillah',
  translation: 'in the name of Allah',
  posGroup: 'fiil',
  grammarNote: 'note',
);

void main() {
  group('Module screen build smoke (issue 2)', () {
    testWidgets('LessonListPage builds', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(child: MaterialApp(home: LessonListPage())),
      );
      await tester.pumpAndSettle();
    });

    testWidgets('LessonPlayerPage builds each quiz type', (tester) async {
      for (final type in QuizType.values) {
        final lesson = LessonModel(
          lessonId: 1,
          moduleNumber: 1,
          lessonNumber: 1,
          title: 'T',
          description: 'D',
          concepts: [_concept],
          quizQuestions: [q(type)],
        );
        await tester.pumpWidget(
          ProviderScope(child: MaterialApp(home: LessonPlayerPage(lesson: lesson))),
        );
        await tester.pumpAndSettle();
        // Advance through concept -> quiz -> complete
        for (var i = 0; i < 3; i++) {
          await tester.pumpAndSettle();
          final next = find.text('Continue');
          final done = find.text('Done');
          if (next.evaluate().isNotEmpty) {
            await tester.tap(next.first);
          } else if (done.evaluate().isNotEmpty) {
            await tester.tap(done.first);
          }
          await tester.pumpAndSettle();
        }
      }
    });

    testWidgets('QuizWidget builds each type', (tester) async {
      for (final type in QuizType.values) {
        await tester.pumpWidget(
          ProviderScope(
            child: MaterialApp(home: Scaffold(body: QuizWidget(question: q(type), onAnswered: (_) {}))),
          ),
        );
        await tester.pumpAndSettle();
      }
    });

    testWidgets('GrammarCardWidget builds', (tester) async {
      await tester.pumpWidget(
        MaterialApp(home: Scaffold(body: GrammarCardWidget(arabicText: 'بِسْمِ'))),
      );
      await tester.pumpAndSettle();
    });
  });
}
