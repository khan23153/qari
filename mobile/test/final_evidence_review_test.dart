import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_model.dart';
import 'package:qari/data/models/recitation_stream_event.dart';
import 'package:qari/features/recitation/presentation/recitation_review.dart';

void main() {
  test(
      'omitted uncertain verdict stays pending without shifting global indices',
      () {
    final result = RecitationResult.fromJson({
      'session_id': 'final-evidence',
      'surah_number': 1,
      'ayah_number': 1,
      'overall_score': 1.0,
      'confidence': .85,
      'created_at': '2026-10-10T00:00:00Z',
      'word_verdicts': [
        {'word': 'بسم', 'word_index': 0, 'is_correct': true, 'confidence': .8},
        {
          'word': 'الرحمن',
          'word_index': 2,
          'is_correct': true,
          'confidence': .9
        },
      ],
    });
    final review = buildRecitationReview(
      words: ['بسم', 'الله', 'الرحمن', 'الرحيم'],
      liveCursor: 3,
      liveStatuses: [
        LiveWordStatus.matched,
        LiveWordStatus.pending,
        LiveWordStatus.matched,
        LiveWordStatus.pending,
      ],
      serverResult: result,
    );
    expect(review.statuses, [
      LiveWordStatus.matched,
      LiveWordStatus.pending,
      LiveWordStatus.matched,
      LiveWordStatus.pending,
    ]);
    expect(review.result.wordVerdicts.map((v) => v.wordIndex), [0, 2]);
    expect(review.result.confidence, .85);
    expect(review.correctCount, 2);
    expect(review.mistakeCount, 0);
    expect(review.unreachedCount, 1);
  });

  test('confirmed wrong word stays red while page tail remains unreached', () {
    final words = List.generate(58, (i) => 'word$i');
    final verdicts = [
      for (var i = 0; i < 15; i++)
        WordVerdict(
          word: words[i],
          wordIndex: i,
          isCorrect: i != 1,
          confidence: .9,
          errorType: i == 1 ? 'error' : null,
        ),
    ];
    final review = buildRecitationReview(
      words: words,
      liveCursor: 15,
      liveStatuses: List.filled(58, LiveWordStatus.pending),
      serverResult: RecitationResult(
        sessionId: 'page604',
        surahNumber: 112,
        ayahNumber: 1,
        overallScore: 14 / 15,
        confidence: .9,
        createdAt: DateTime(2026),
        wordVerdicts: verdicts,
      ),
    );
    expect(review.statuses[1], LiveWordStatus.error);
    expect(review.verdictAt(1)?.errorType, 'error');
    expect(review.reach, 15);
    expect(review.correctCount, 14);
    expect(review.mistakeCount, 1);
    expect(review.unreachedCount, 43);
    expect(review.statuses.skip(15), everyElement(LiveWordStatus.pending));
    expect(review.result.wordVerdicts.map((v) => v.wordIndex),
        List.generate(15, (i) => i));
  });
}
