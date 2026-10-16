import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_model.dart';
import 'package:qari/data/models/recitation_stream_event.dart';
import 'package:qari/features/recitation/presentation/recitation_review.dart';

RecitationReview terminalReview(Map<String, dynamic> evidence,
    {int targetCount = 4, int terminalIndex = 3}) {
  final words = List.generate(targetCount, (index) => 'word$index');
  return buildRecitationReview(
    words: words,
    liveCursor: terminalIndex,
    liveStatuses: [
      for (var index = 0; index < targetCount; index++)
        index < terminalIndex ? LiveWordStatus.matched : LiveWordStatus.pending,
    ],
    serverResult: RecitationResult.fromJson({
      'session_id': 'terminal-evidence',
      'surah_number': 112,
      'ayah_number': 1,
      'overall_score': .75,
      'created_at': '2026-10-10T00:00:00Z',
      'word_verdicts': [
        for (var index = 0; index < terminalIndex; index++)
          {'word': words[index], 'word_index': index, 'is_correct': true},
        {
          'word': words[terminalIndex],
          'word_index': terminalIndex,
          'is_correct': false,
          ...evidence,
        },
        if (targetCount > terminalIndex + 1)
          {
            'word': words.last,
            'word_index': targetCount - 1,
            'is_correct': false,
            'error_type': 'skipped',
          },
      ],
    }),
  );
}

void main() {
  test('explicitly confirmed terminal mistake extends reach and stays red', () {
    final review = terminalReview({
      'evidence_confirmed': true,
      'confidence': .9,
      'actual_text': 'الناس',
      'error_type': 'error',
    });
    expect(review.reach, 4);
    expect(review.statuses[3], LiveWordStatus.error);
    expect(review.result.wordVerdicts.map((verdict) => verdict.wordIndex),
        [0, 1, 2, 3]);
    expect(review.result.overallScore, .75);
  });

  test('confirmed last Ikhlas word leaves the remaining page suffix pending',
      () {
    final review = terminalReview({
      'evidence_confirmed': true,
      'confidence': .9,
      'actual_text': 'الناس',
      'error_type': 'error',
    }, targetCount: 58, terminalIndex: 14);
    expect(review.reach, 15);
    expect(review.statuses[14], LiveWordStatus.error);
    expect(review.unreachedCount, 43);
    expect(review.statuses.skip(15), everyElement(LiveWordStatus.pending));
    expect(review.result.wordVerdicts.map((verdict) => verdict.wordIndex),
        List.generate(15, (i) => i));
  });

  final unconfirmed = <Map<String, dynamic>>[
    {},
    {'evidence_confirmed': false},
    {'confidence': .2},
    {'actual_text': ''},
    {'actual_text': '   '},
    {'actual_text': null},
    {'error_type': 'skipped'},
    {'error_type': 'unknown'},
    {'error_type': null},
  ];
  for (var index = 0; index < unconfirmed.length; index++) {
    test('unsupported terminal verdict $index cannot extend reach', () {
      final evidence = {
        'evidence_confirmed': true,
        'confidence': .9,
        'actual_text': 'الناس',
        'error_type': 'error',
        ...unconfirmed[index],
      };
      if (index == 0) evidence.remove('evidence_confirmed');
      final review = terminalReview(evidence);
      expect(review.reach, 3);
      expect(review.statuses[3], LiveWordStatus.pending);
      expect(review.result.wordVerdicts.length, 3);
    });
  }

  test('final evidence confirmation round-trips and legacy JSON defaults false',
      () {
    final legacy = {'word': 'الرحيم', 'word_index': 3, 'is_correct': false};
    expect(WordVerdict.fromJson(legacy).toJson()['evidence_confirmed'], false);
    expect(
        WordVerdict.fromJson({...legacy, 'evidence_confirmed': true})
            .toJson()['evidence_confirmed'],
        true);
    expect(
        () => WordVerdict.fromJson({...legacy, 'evidence_confirmed': 'true'}),
        throwsA(isA<TypeError>()));
  });

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
