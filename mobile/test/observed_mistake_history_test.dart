import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:qari/data/models/recitation_session_record.dart';
import 'package:qari/data/services/local_storage_service.dart';
import 'package:qari/data/services/recitation_history_service.dart';
import 'package:qari/features/recitation/presentation/pages/recitation_history_page.dart';

void main() {
  testWidgets(
      'history missed, skipped, wrong and harakat words all use pure red',
      (tester) async {
    tester.view.physicalSize = const Size(800, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    SharedPreferences.setMockInitialValues({});
    final storage = await LocalStorageService.getInstance();
    RecitationHistoryService(storage.prefs).saveSession(
      scope: 'surah',
      surahNumber: 1,
      ayahFrom: 2,
      ayahTo: 2,
      overallScore: .2,
      correctCount: 1,
      totalCount: 6,
      durationSeconds: 5,
      mistakes: [
        for (final (word, type) in [
          ('لله', 'missed'),
          ('رب', 'skipped'),
          ('العالمين', 'substituted'),
          ('الرحمن', 'harakat_mistake'),
          ('الرحيم', 'error_skipped'),
        ])
          RecitationMistake(word: word, expectedText: word, errorType: type),
      ],
    );
    await tester.pumpWidget(const MaterialApp(home: RecitationHistoryPage()));
    await tester.pumpAndSettle();
    await tester.tap(find.text('1:2'));
    await tester.pumpAndSettle();
    for (final word in ['لله', 'رب', 'العالمين', 'الرحمن', 'الرحيم']) {
      expect(tester.widget<Text>(find.text(word)).style!.color,
          const Color(0xFFEF4444));
    }
    expect(find.text('Mispronounced'), findsNothing);
    expect(find.text('Observed harakat difference'), findsOneWidget);
  });
}
