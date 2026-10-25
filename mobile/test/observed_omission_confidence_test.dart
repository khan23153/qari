import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_model.dart';
import 'package:qari/data/models/recitation_stream_event.dart';
import 'package:qari/features/recitation/presentation/recitation_review.dart';
import 'package:qari/features/recitation/presentation/widgets/recitation_results.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:qari/features/recitation/presentation/widgets/mushaf_reveal_view.dart';
import 'package:qari/features/recitation/presentation/word_view_state.dart';

import 'mushaf_text_helpers.dart';

// Literal wire shape emitted by StreamingRecitationSession._diff_events for a
// lexically confirmed omission. There is no acoustic observation to score.
const backendMissedWordJson = '''
{
  "type": "word",
  "session_id": "confirmed-omission",
  "status": "error_skipped",
  "word_id": 2,
  "word_index": 1,
  "expected": "لله",
  "spoken": "",
  "confidence": 0.0,
  "error_type": "missed",
  "evidence_source": "lexical_asr",
  "observed_text": "",
  "harakat_conflicts": [],
  "display_color": "#EF4444",
  "evidence_confirmed": true,
  "timestamp_ms": 2400
}
''';

Map<String, dynamic> backendMissedWordPayload() =>
    jsonDecode(backendMissedWordJson) as Map<String, dynamic>;

RecitationReview omissionReview(
        {double confidence = 0, bool confirmed = true}) =>
    buildRecitationReview(
      words: const ['الحمد', 'لله', 'رب', 'العالمين'],
      liveCursor: 3,
      liveStatuses: const [
        LiveWordStatus.matched,
        LiveWordStatus.error,
        LiveWordStatus.matched,
        LiveWordStatus.pending,
      ],
      serverResult: RecitationResult.fromJson({
        'session_id': 'confirmed-omission',
        'surah_number': 1,
        'ayah_number': 2,
        'overall_score': 0,
        'created_at': '2026-10-24T00:00:00Z',
        'word_verdicts': [
          {
            'word': 'لله',
            'word_index': 1,
            'is_correct': false,
            'error_type': 'missed',
            'actual_text': '',
            'confidence': confidence,
            'evidence_confirmed': confirmed,
          },
        ],
      }),
    );

void main() {
  test(
      'zero-confidence omission survives final review without scoring unread tail',
      () {
    final review = omissionReview();
    expect(review.reach, 3);
    expect(review.statuses[1], LiveWordStatus.error);
    expect(review.statuses[3], LiveWordStatus.pending);
    expect(review.mistakeCount, 1);
    expect(review.result.overallScore, closeTo(2 / 3, .0001));
    expect(review.verdictAt(1)!.confidence, 0);
    expect(review.verdictAt(1)!.isReviewMistake, isTrue);
    expect(
        omissionReview(confirmed: false).statuses[1], LiveWordStatus.pending);
  });

  testWidgets('final zero-confidence omission remains pure red in results',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: RecitationResults(
          result: omissionReview().result,
          ayahWords: const ['الحمد', 'لله', 'رب', 'العالمين'],
          onWordTapped: (_) {},
          onRetry: () {},
          theme: ThemeData.light(),
        ),
      ),
    ));
    await tester.pumpAndSettle();
    expect(tester.widget<Text>(find.text('لله')).style!.color,
        const Color(0xFFEF4444));
    expect(tester.widget<Text>(find.text('العالمين')).style!.color,
        isNot(const Color(0xFFEF4444)));
  });

  test('real backend zero-confidence omission parses as a confirmed mistake',
      () {
    final event = RecitationStreamEvent.fromJson(backendMissedWordPayload());
    expect(event.wordIndex, 1);
    expect(event.spoken, '');
    expect(event.observedText, '');
    expect(event.confidence, 0.0); // Never manufacture an acoustic probability.
    expect(event.evidenceConfirmed, isTrue);
    expect(event.liveStatus, LiveWordStatus.error);
    expect(
        resolveWordViewState(
            serverStatus: event.liveStatus, index: 1, cursor: 1),
        LiveWordViewState.active);
    expect(
        resolveWordViewState(
            serverStatus: event.liveStatus, index: 2, cursor: 1),
        LiveWordViewState.unspoken);
  });

  testWidgets('real backend omission is exact red only behind the live cursor',
      (tester) async {
    final event = RecitationStreamEvent.fromJson(backendMissedWordPayload());
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: MushafRevealView(
      words: const ['الحمد', 'لله', 'رب', 'العالمين'],
      statuses: [
        LiveWordStatus.matched,
        event.liveStatus,
        event.liveStatus,
        event.liveStatus,
      ],
      cursor: 2,
      mushaf: MushafTheme.night,
      hideUnspoken: true,
    ))));
    expect(inkOf(tester, 'لله'), const Color(0xFFEF4444));
    expect(inkOf(tester, 'رب'), isNot(const Color(0xFFEF4444)));
    expect(inkOf(tester, 'العالمين')!.a, 0);
  });

  for (final confidence in [0.0, .2, .55, 1.0]) {
    test('confirmed omission does not use acoustic floor at $confidence', () {
      final event = RecitationStreamEvent.fromJson({
        ...backendMissedWordPayload(),
        'confidence': confidence,
      });
      expect(event.confidence, confidence);
      expect(event.liveStatus.isMistake, isTrue);
    });
  }

  test('zero-confidence omission without explicit confirmation stays pending',
      () {
    for (final confirmation in [false, null]) {
      final event = RecitationStreamEvent.fromJson({
        ...backendMissedWordPayload(),
        'evidence_confirmed': confirmation,
      });
      expect(event.liveStatus, LiveWordStatus.pending);
    }
  });

  for (final type in ['missed', 'substituted', 'harakat_mistake']) {
    for (final confidence in [
      double.nan,
      double.infinity,
      -double.infinity,
      -.1,
      1.1
    ]) {
      test('live $type rejects invalid confidence $confidence', () {
        final event = RecitationStreamEvent.fromJson({
          ...backendMissedWordPayload(),
          'error_type': type,
          'spoken': type == 'missed' ? '' : 'لِلَّهُ',
          'observed_text': type == 'missed' ? '' : 'لِلَّهُ',
          'confidence': confidence,
        });
        expect(event.liveStatus, LiveWordStatus.pending);
      });
    }
  }

  for (final type in ['substituted', 'harakat_mistake']) {
    for (final confidence in [0.0, .2, .549]) {
      test('actually spoken $type keeps .55 floor at $confidence', () {
        final event = RecitationStreamEvent.fromJson({
          ...backendMissedWordPayload(),
          'error_type': type,
          'spoken': 'لِلَّهُ',
          'observed_text': 'لِلَّهُ',
          'confidence': confidence,
        });
        expect(event.liveStatus, LiveWordStatus.pending);
      });
    }
    test('actually spoken $type accepts the .55 boundary', () {
      final event = RecitationStreamEvent.fromJson({
        ...backendMissedWordPayload(),
        'error_type': type,
        'spoken': 'لِلَّهُ',
        'observed_text': 'لِلَّهُ',
        'confidence': .55,
      });
      expect(event.liveStatus, LiveWordStatus.observedError);
    });
  }
}
