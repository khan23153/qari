import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../lib/data/models/recitation_stream_event.dart';
import '../lib/features/recitation/presentation/pages/live_recitation_page.dart';
import '../lib/features/recitation/presentation/widgets/memorization_ayah_view.dart';

void main() {
  group('RecitationStreamEvent parsing', () {
    test('parses a ready payload with reference words', () {
      final e = RecitationStreamEvent.fromJson({
        'type': 'ready',
        'session_id': 'abc',
        'words': [
          {'index': 0, 'text': 'بِسْمِ'},
          {'index': 1, 'text': 'ٱللَّهِ'},
        ],
      });
      expect(e.type, RecitationStreamEventType.ready);
      expect(e.sessionId, 'abc');
      expect(e.words.length, 2);
      expect(e.words.first.text, 'بِسْمِ');
    });

    test('parses a live word event with status', () {
      final e = RecitationStreamEvent.fromJson({
        'type': 'word',
        'word_index': 2,
        'status': 'error',
        'expected': 'الرحمن',
        'spoken': 'السلام',
        'confidence': 0.8,
        'timestamp_ms': 3200,
      });
      expect(e.type, RecitationStreamEventType.word);
      expect(e.wordIndex, 2);
      expect(e.status, LiveWordStatus.error);
      expect(e.status.isMistake, isTrue);
      expect(e.expected, 'الرحمن');
    });

    test('unknown status falls back to pending', () {
      final e = RecitationStreamEvent.fromJson({'type': 'word', 'status': 'weird'});
      expect(e.status, LiveWordStatus.pending);
      expect(e.status.isResolved, isFalse);
    });

    test('parses a final result payload', () {
      final e = RecitationStreamEvent.fromJson({
        'type': 'final',
        'session_id': 'abc',
        'result': {
          'session_id': 'abc',
          'surah_number': 1,
          'ayah_number': 1,
          'overall_score': 0.75,
          'created_at': '2026-01-01T00:00:00Z',
          'word_verdicts': [],
        },
      });
      expect(e.type, RecitationStreamEventType.finalResult);
      expect(e.result, isNotNull);
      expect(e.result!.overallScore, 0.75);
    });
  });

  testWidgets('LiveRecitationPage setup shows Hifz toggle + Start button',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: LiveRecitationPage(surahNumber: 1, ayahNumber: 1),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('AI Recitation'), findsOneWidget);
    expect(find.text('Memorization Mode'), findsOneWidget);
    expect(find.text('Start Reciting'), findsOneWidget);
    expect(find.text('Listen First'), findsOneWidget);
    // The Hifz toggle is on by default.
    expect(find.byType(Switch), findsOneWidget);
  });

  testWidgets('MemorizationAyahView shows dots for pending, text for matched',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MemorizationAyahView(
            words: const ['بسم', 'الله', 'الرحمن'],
            statuses: const {
              0: LiveWordStatus.matched,
              // index 1 & 2 pending → circular placeholder dots in Hifz mode
            },
            memorizationMode: true,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // Hidden (pending) words render as subtle circular placeholder dots.
    final dots = find.byWidgetPredicate(
      (w) =>
          w is Container &&
          w.decoration is BoxDecoration &&
          (w.decoration as BoxDecoration).shape == BoxShape.circle,
    );
    expect(dots, findsWidgets);

    // The matched word is revealed as visible Arabic text.
    expect(find.text('بسم'), findsWidgets);
    // Pending words are NOT yet rendered as text.
    expect(find.text('الله'), findsNothing);
    expect(find.text('الرحمن'), findsNothing);
  });

  testWidgets('MemorizationAyahView (tracking mode) shows all words unmasked',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MemorizationAyahView(
            words: const ['بسم', 'الله'],
            statuses: const {},
            memorizationMode: false,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // No dots in tracking mode — every word is shown as text.
    final dots = find.byWidgetPredicate(
      (w) =>
          w is Container &&
          w.decoration is BoxDecoration &&
          (w.decoration as BoxDecoration).shape == BoxShape.circle,
    );
    expect(dots, findsNothing);
    expect(find.text('بسم'), findsOneWidget);
    expect(find.text('الله'), findsOneWidget);
  });
}
