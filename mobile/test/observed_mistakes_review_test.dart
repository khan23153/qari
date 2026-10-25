import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_stream_event.dart';
import 'package:qari/data/models/recitation_model.dart';
import 'package:qari/features/recitation/presentation/recitation_review.dart';

import 'final_evidence_review_test.dart' show terminalReview;

void main() {
  for (final type in ['missed', 'substituted', 'harakat_mistake']) {
    for (final confidence in [
      double.nan,
      double.infinity,
      -double.infinity,
      -.1,
      1.1,
    ]) {
      test('review $type rejects invalid confidence $confidence', () {
        final verdict = WordVerdict(
          word: 'لله',
          wordIndex: 0,
          isCorrect: false,
          errorType: type,
          evidenceConfirmed: true,
          confidence: confidence,
          actualText: type == 'missed' ? '' : 'لِلَّهُ',
        );
        final review = buildRecitationReview(
          words: const ['لله', 'رب'],
          liveCursor: 1,
          liveStatuses: const [LiveWordStatus.pending, LiveWordStatus.pending],
          serverResult: RecitationResult(
            sessionId: 'invalid-confidence',
            surahNumber: 1,
            ayahNumber: 2,
            overallScore: 0,
            createdAt: DateTime.utc(2026),
            wordVerdicts: [verdict],
          ),
        );
        expect(verdict.isReviewMistake, isFalse);
        expect(review.statuses, everyElement(LiveWordStatus.pending));
        expect(review.result.wordVerdicts, isEmpty);
      });
    }
  }
  for (final type in ['substituted', 'harakat_mistake', 'error']) {
    test('invalid terminal $type cannot extend reach', () {
      final review = terminalReview({
        'evidence_confirmed': true,
        'confidence': double.infinity,
        'actual_text': 'لِلَّهُ',
        'error_type': type,
      });
      expect(review.reach, 3);
      expect(review.statuses[3], LiveWordStatus.pending);
    });
  }
  for (final type in [
    'missed',
    'substituted',
    'harakat_mistake',
    'not_reached'
  ]) {
    test('unconfirmed $type stays pending even inside review reach', () {
      final review = buildRecitationReview(
        words: const ['لله', 'رب'],
        liveCursor: 2,
        liveStatuses: List.filled(2, LiveWordStatus.pending),
        serverResult: RecitationResult(
            sessionId: 'uncertain',
            surahNumber: 1,
            ayahNumber: 2,
            overallScore: 0,
            createdAt: DateTime.utc(2026),
            wordVerdicts: [
              WordVerdict(
                  word: 'لله',
                  wordIndex: 0,
                  isCorrect: false,
                  errorType: type,
                  actualText: 'لِلَّهُ')
            ]),
      );
      expect(review.statuses[0], LiveWordStatus.pending);
      expect(review.result.wordVerdicts, isEmpty);
    });
  }
  test('confirmed error beyond an unread gap cannot extend review reach', () {
    final review = buildRecitationReview(
      words: const ['الحمد', 'لله', 'رب', 'العالمين', 'الرحمن'],
      liveCursor: 1,
      liveStatuses: List.filled(5, LiveWordStatus.pending),
      serverResult: RecitationResult(
          sessionId: 'ahead',
          surahNumber: 1,
          ayahNumber: 2,
          overallScore: 0,
          createdAt: DateTime.utc(2026),
          wordVerdicts: const [
            WordVerdict(
                word: 'الرحمن',
                wordIndex: 4,
                isCorrect: false,
                errorType: 'substituted',
                evidenceConfirmed: true,
                confidence: .95,
                actualText: 'الناس')
          ]),
    );
    expect(review.reach, 1);
    expect(review.statuses.skip(1), everyElement(LiveWordStatus.pending));
  });
  for (final errorType in ['substituted', 'harakat_mistake']) {
    test('confirmed terminal $errorType extends review by one, not page suffix',
        () {
      final review = terminalReview({
        'evidence_confirmed': true,
        'confidence': .95,
        'actual_text': 'لِلَّهُ',
        'error_type': errorType,
      }, targetCount: 25);
      expect(review.reach, 4);
      expect(review.statuses[3].isMistake, isTrue);
      expect(review.verdictAt(3)!.errorType, errorType);
      expect(review.statuses.skip(4), everyElement(LiveWordStatus.pending));
    });
  }
}
