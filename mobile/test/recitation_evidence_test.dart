import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:qari/data/models/recitation_model.dart';
import 'package:qari/data/models/recitation_session_record.dart';
import 'package:qari/data/services/streaming_recitation_service.dart';
import 'package:qari/data/services/recitation_auth.dart';
import 'package:qari/data/services/local_storage_service.dart';
import 'package:qari/data/services/recitation_history_service.dart';
import 'package:qari/features/recitation/presentation/pages/recitation_history_page.dart';
import 'package:qari/features/recitation/presentation/widgets/recitation_results.dart';

Map<String, dynamic> payload() => {
      'session_id': 'verified',
      'surah_number': 1,
      'ayah_number': 1,
      'overall_score': .8,
      'created_at': '2026-09-30T00:00:00Z',
      'pronunciation_score': 0,
      'tajweed_score': 0,
      'fluency_score': 0,
      'pronunciation_available': false,
      'tajweed_available': false,
      'fluency_available': false,
    };

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('assessment availability survives JSON and history round trips', () {
    final raw = payload()..['tajweed_available'] = true;
    final result = RecitationResult.fromJson(raw);
    expect(result.toJson()['tajweed_available'], true);
    expect(
        result.copyWith(feedback: 'Saved').toJson()['pronunciation_available'],
        false);
  });

  test('recording authentication never leaks to a CDN or another origin', () {
    const base = 'https://qari.example/v1';
    Map<String, String> headers(String url) =>
        recitationAudioHeaders(url, 'user-jwt', apiBaseUrl: base);
    expect(headers('$base/recitations/session/audio'),
        {'Authorization': 'Bearer user-jwt'});
    for (final url in [
      'https://everyayah.com/data/001001.mp3',
      'http://qari.example/v1/recitations/session/audio',
      'https://qari.example:8443/v1/recitations/session/audio',
      'https://other.example/v1/recitations/session/audio',
      '$base/unrelated/audio',
    ]) {
      expect(headers(url), isEmpty, reason: url);
    }
  });

  testWidgets('unassessed metrics are never presented as failed scores',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: RecitationResults(
      result: RecitationResult.fromJson(payload()),
      ayahWords: const [],
      onWordTapped: (_) {},
      onRetry: () {},
      theme: ThemeData(),
    ))));
    await tester.pumpAndSettle();
    expect(find.text('Pronunciation'), findsNothing);
    expect(find.text('Tajweed'), findsNothing);
    expect(find.text('Fluency'), findsNothing);
    expect(find.text('Word matching'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('perfect word matches do not certify pronunciation',
      (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final raw = payload()
      ..['overall_score'] = 1.0
      ..['word_verdicts'] = [
        {'word': 'الله', 'word_index': 0, 'is_correct': true},
      ];
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: RecitationResults(
          result: RecitationResult.fromJson(raw),
          onWordTapped: (_) {},
          onRetry: () {},
          theme: ThemeData(),
        ),
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Excellent'), findsNothing);
    expect(find.text('Word matching'), findsOneWidget);
    expect(find.text('1 matched'), findsOneWidget);
    expect(find.textContaining('were not assessed'), findsOneWidget);
    expect(find.textContaining('words correct'), findsNothing);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('saved matches without mistakes do not claim perfect recitation',
      (tester) async {
    SharedPreferences.setMockInitialValues({});
    final storage = await LocalStorageService.getInstance();
    await storage.prefs.clear();
    RecitationHistoryService(storage.prefs).saveSession(
      scope: 'range',
      surahNumber: 1,
      ayahFrom: 1,
      ayahTo: 1,
      overallScore: 1,
      correctCount: 4,
      totalCount: 4,
      durationSeconds: 10,
    );
    await tester.pumpWidget(const MaterialApp(home: RecitationHistoryPage()));
    await tester.pumpAndSettle();
    await tester.tap(find.text('1:1'));
    await tester.pumpAndSettle();
    expect(find.text('No mistakes — perfect recitation!'), findsNothing);
    expect(find.textContaining('4/4 matched'), findsWidgets);
    expect(find.text('No word mismatches to review'), findsOneWidget);
    expect(find.text('Word matching only'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
    await storage.prefs.clear();
  });

  testWidgets('saved session with mistakes labels mismatches honestly',
      (tester) async {
    SharedPreferences.setMockInitialValues({});
    final storage = await LocalStorageService.getInstance();
    await storage.prefs.clear();
    RecitationHistoryService(storage.prefs).saveSession(
      scope: 'range',
      surahNumber: 1,
      ayahFrom: 1,
      ayahTo: 1,
      overallScore: 0.75,
      correctCount: 3,
      totalCount: 4,
      durationSeconds: 10,
      mistakes: [
        RecitationMistake(
          word: 'مستقيم',
          expectedText: 'المستقيم',
          errorType: 'substitution',
        ),
      ],
    );
    await tester.pumpWidget(const MaterialApp(home: RecitationHistoryPage()));
    await tester.pumpAndSettle();
    await tester.tap(find.text('1:1'));
    await tester.pumpAndSettle();
    expect(find.text('Mispronounced'), findsNothing);
    expect(find.text('Mismatch'), findsOneWidget);
    expect(find.textContaining('3/4 matched'), findsWidgets);
    expect(find.textContaining('1 to review'), findsWidgets);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
    await storage.prefs.clear();
  });

  test('signed-out live recording fails before asking for microphone access',
      () async {
    SharedPreferences.setMockInitialValues({});
    final service = StreamingRecitationService();
    try {
      await expectLater(
          service.start(surahNumber: 1, ayahNumber: 1, memorizationMode: false),
          throwsA(predicate<Object>((e) => e.toString().contains('Sign in'))));
      expect(service.state, LiveConnectionState.error);
    } finally {
      await service.dispose();
    }
  });
}
