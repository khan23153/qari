import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../lib/data/models/lesson_model.dart';
import '../lib/data/services/curriculum_service.dart';
import '../lib/data/services/local_storage_service.dart';
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
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Module screen build smoke (issue 2)', () {
    testWidgets('LessonListPage builds', (tester) async {
      // Asset and plugin-backed futures perform real asynchronous I/O that is
      // not advanced merely by moving the widget test's fake clock. Resolve
      // them outside fake_async first; the page then reads cached curriculum
      // data and an initialized preferences instance during its bounded pumps.
      await tester.runAsync(() async {
        await CurriculumService.instance.vocabLessons();
        await LocalStorageService.getInstance();
      });
      await tester.pumpWidget(
        const ProviderScope(child: MaterialApp(home: LessonListPage())),
      );
      // Do not use pumpAndSettle while the page's indeterminate loading
      // spinner is present: that animation deliberately schedules frames
      // forever and makes pumpAndSettle hit its ten-minute/frame timeout on
      // slower CI hosts. Pump a bounded number of frames until async asset and
      // SharedPreferences loading has produced the actual curriculum instead.
      for (var i = 0;
          i < 50 && find.text('Foundation').evaluate().isEmpty;
          i++) {
        await tester.pump(const Duration(milliseconds: 100));
      }
      expect(find.text('Learn Quran'), findsOneWidget);
      expect(find.text('Foundation'), findsOneWidget);
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

    testWidgets('QuizWidget clears answered state when question changes',
        (tester) async {
      const first = QuizQuestionModel(
        id: 'first',
        type: QuizType.mcq,
        question: 'First?',
        options: ['Wrong', 'First correct'],
        correctAnswer: 'First correct',
        explanation: 'First explanation',
      );
      const second = QuizQuestionModel(
        id: 'second',
        type: QuizType.mcq,
        question: 'Second?',
        options: ['Wrong', 'Second correct'],
        correctAnswer: 'Second correct',
        explanation: 'Second explanation',
      );

      var question = first;
      late StateSetter rebuild;
      await tester.pumpWidget(MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(builder: (context, setState) {
            rebuild = setState;
            // Deliberately no key: didUpdateWidget must still reset state.
            return QuizWidget(question: question, onAnswered: (_) {});
          }),
        ),
      ));

      await tester.tap(find.text('First correct'));
      await tester.pumpAndSettle();
      expect(find.text('Correct!'), findsOneWidget);

      rebuild(() {
        question = second;
      });
      await tester.pump();

      expect(find.text('Second?'), findsOneWidget);
      expect(find.text('Correct!'), findsNothing);
      expect(find.text('Second explanation'), findsNothing);

      await tester.tap(find.text('Second correct'));
      await tester.pumpAndSettle();
      expect(find.text('Correct!'), findsOneWidget);
      expect(find.text('Second explanation'), findsOneWidget);
    });

    testWidgets('GrammarCardWidget builds', (tester) async {
      await tester.pumpWidget(
        MaterialApp(home: Scaffold(body: GrammarCardWidget(arabicText: 'بِسْمِ'))),
      );
      await tester.pumpAndSettle();
    });
  });
}
