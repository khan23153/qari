import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_stream_event.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:qari/features/recitation/presentation/widgets/mushaf_reveal_view.dart';

import 'mushaf_text_helpers.dart';

void main() {
  testWidgets('uncertain word stays hidden as later confirmed word reveals',
      (tester) async {
    final event = RecitationStreamEvent.fromJson({
      'type': 'word',
      'word_index': 1,
      'status': 'error_skipped',
      'expected': 'الله',
      'spoken': 'الله',
      'confidence': .2,
      'evidence_confirmed': false,
    });
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(
            body: MushafRevealView(
      words: const ['بسم', 'الله', 'الرحمن', 'الرحيم'],
      statuses: [
        LiveWordStatus.matched,
        event.liveStatus,
        LiveWordStatus.matched,
        LiveWordStatus.pending
      ],
      cursor: 3,
      hideUnspoken: true,
      mushaf: MushafTheme.classic,
    ))));
    expect(inkOf(tester, 'الله')!.a, 0);
    expect(inkOf(tester, 'الرحمن'), MushafTheme.classic.text);
    expect(underlineCount(tester, MushafTheme.classic.mismatchInk), 0);
  });

  test('only confirmed high-confidence spoken mistakes become live errors', () {
    RecitationStreamEvent event(
            {bool confirmed = true,
            double confidence = .95,
            String spoken = 'الناس'}) =>
        RecitationStreamEvent.fromJson({
          'type': 'word',
          'status': 'error_skipped',
          'word_index': 1,
          'expected': 'الله',
          'spoken': spoken,
          'confidence': confidence,
          'evidence_confirmed': confirmed,
        });
    expect(event().liveStatus, LiveWordStatus.error);
    expect(event(confirmed: false).liveStatus, LiveWordStatus.pending);
    expect(event(confidence: .2).liveStatus, LiveWordStatus.pending);
    expect(event(spoken: '').liveStatus, LiveWordStatus.pending);
  });
}
