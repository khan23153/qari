import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:qari/core/constants/app_constants.dart';
import 'package:qari/features/onboarding/onboarding_answers.dart';
import 'package:qari/features/onboarding/presentation/pages/path_select_page.dart';

void main() {
  group('OnboardingAnswers', () {
    test('a learner who cannot read the script yet starts with Foundation', () {
      const a = OnboardingAnswers(reading: ArabicReading.notYet);
      expect(a.path, LearningPath.foundation);
      expect(a.backendPath, 'foundation');
    });

    test('a learner who can read goes straight to the Quran', () {
      for (final r in [ArabicReading.slowly, ArabicReading.fluent]) {
        final a = OnboardingAnswers(reading: r);
        expect(a.path, LearningPath.quranDirect);
        expect(a.backendPath, 'quran_direct');
      }
    });

    test('the focus picks the tab Home opens on', () {
      expect(const OnboardingAnswers(focus: StudyFocus.read).homeTab, 1);
      expect(const OnboardingAnswers(focus: StudyFocus.memorize).homeTab, 1);
      expect(const OnboardingAnswers(focus: StudyFocus.understand).homeTab, 0);
      expect(const OnboardingAnswers(focus: StudyFocus.hadith).homeTab, 2);
    });

    test('someone who cannot read yet lands on the lessons, not the Mushaf',
        () {
      const a = OnboardingAnswers(
        reading: ArabicReading.notYet,
        focus: StudyFocus.read,
      );
      expect(a.homeTab, 0);
    });

    test('saving writes every answer where the app reads it', () async {
      SharedPreferences.setMockInitialValues({});
      await saveOnboardingAnswers(const OnboardingAnswers(
        reading: ArabicReading.notYet,
        focus: StudyFocus.hadith,
        dailyGoal: 5,
        mushafThemeId: 'parchment',
      ));
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('selected_path'), 'foundation');
      expect(prefs.getString('arabic_reading'), 'notYet');
      expect(prefs.getString('study_focus'), 'hadith');
      expect(prefs.getInt('daily_goal'), 5);
      expect(prefs.getString('mushaf_theme_id'), 'parchment');
      expect(prefs.getBool('is_onboarded'), isTrue);
      expect(prefs.getBool('onboarding_complete'), isTrue);
    });

    test('choosing Night overwrites an earlier paper choice', () async {
      SharedPreferences.setMockInitialValues({'mushaf_theme_id': 'minimal'});
      await saveOnboardingAnswers(
        const OnboardingAnswers(mushafThemeId: 'night'),
      );
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('mushaf_theme_id'), 'night');
    });
  });

  group('Set up Safha flow', () {
    const english = AppLanguage(
      code: 'en',
      name: 'English',
      nativeName: 'English',
      script: 'Latin',
      textDirection: TextDirection.ltr,
      locale: Locale('en'),
    );

    Future<OnboardingAnswers?> pumpFlow(
      WidgetTester tester,
      Future<void> Function() drive,
    ) async {
      SharedPreferences.setMockInitialValues({});
      OnboardingAnswers? finished;
      await tester.pumpWidget(ProviderScope(
        child: MaterialApp(
          home: PathSelectPage(
            selectedLanguage: english,
            syncWithServer: (_) async {},
            onFinished: (a) => finished = a,
          ),
        ),
      ));
      await tester.pumpAndSettle();
      await drive();
      return finished;
    }

    Future<void> choose(WidgetTester tester, String label) async {
      await tester.ensureVisible(find.text(label));
      await tester.tap(find.text(label));
      await tester.pumpAndSettle();
    }

    testWidgets('asks four questions and saves the answers', (tester) async {
      final answers = await pumpFlow(tester, () async {
        expect(
            find.text('Can you read the Arabic of the Quran?'), findsOneWidget);
        expect(find.text('Step 1 of 4'), findsOneWidget);
        await choose(tester, 'Not yet');
        await choose(tester, 'Continue');

        expect(find.text('What do you want to do most?'), findsOneWidget);
        await choose(tester, 'Study hadith');
        await choose(tester, 'Continue');

        expect(find.text('How many lessons a day?'), findsOneWidget);
        await choose(tester, '5 lessons');
        await choose(tester, 'Continue');

        expect(find.text('Choose your Mushaf paper'), findsOneWidget);
        await choose(tester, 'Parchment / Sepia');
        await choose(tester, 'Start');
      });

      expect(answers, isNotNull);
      expect(answers!.reading, ArabicReading.notYet);
      expect(answers.focus, StudyFocus.hadith);
      expect(answers.dailyGoal, 5);
      expect(answers.mushafThemeId, 'parchment');
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getInt('daily_goal'), 5);
      expect(prefs.getString('mushaf_theme_id'), 'parchment');
      expect(prefs.getBool('is_onboarded'), isTrue);
    });

    testWidgets('Continue stays disabled until an answer is chosen',
        (tester) async {
      await pumpFlow(tester, () async {
        final button = find.widgetWithText(FilledButton, 'Continue');
        expect(tester.widget<FilledButton>(button).onPressed, isNull);
        await choose(tester, 'Slowly');
        expect(tester.widget<FilledButton>(button).onPressed, isNotNull);
      });
    });

    testWidgets('Back returns to the previous question with its answer',
        (tester) async {
      await pumpFlow(tester, () async {
        await choose(tester, 'Yes, fluently');
        await choose(tester, 'Continue');
        await choose(tester, 'Back');
        expect(
            find.text('Can you read the Arabic of the Quran?'), findsOneWidget);
        final button = find.widgetWithText(FilledButton, 'Continue');
        expect(tester.widget<FilledButton>(button).onPressed, isNotNull);
      });
    });

    testWidgets('Skip finishes with the defaults for unanswered questions',
        (tester) async {
      final answers = await pumpFlow(tester, () async {
        await choose(tester, 'Not yet');
        await choose(tester, 'Continue');
        await choose(tester, 'Skip');
      });
      expect(answers, isNotNull);
      expect(answers!.reading, ArabicReading.notYet);
      expect(answers.focus, const OnboardingAnswers().focus);
      expect(answers.dailyGoal, const OnboardingAnswers().dailyGoal);
      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getBool('is_onboarded'), isTrue);
    });
  });
}
