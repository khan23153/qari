import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../lib/data/models/lesson_model.dart';
import '../lib/features/lessons/presentation/pages/lesson_player_page.dart';

void main() {
  testWidgets('fill-blank TextField with no concept screen', (tester) async {
    final lesson = LessonModel(
      lessonId: 99,
      moduleNumber: 1,
      lessonNumber: 99,
      title: 'T',
      description: 'D',
      concepts: const [],
      quizQuestions: [
        QuizQuestionModel(
          id: 'q1',
          type: QuizType.fillBlank,
          question: 'The vowel mark is called ____',
          blankAnswer: 'Fatha',
          explanation: 'x',
        ),
      ],
    );
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          localizationsDelegates: const [
            DefaultMaterialLocalizations.delegate,
            DefaultWidgetsLocalizations.delegate,
          ],
          supportedLocales: const [Locale('en'), Locale('ur'), Locale('ar')],
          home: LessonPlayerPage(lesson: lesson),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byType(TextField), findsWidgets,
        reason: 'fill-blank TextField should build without MaterialLocalizations error');
  });
}
