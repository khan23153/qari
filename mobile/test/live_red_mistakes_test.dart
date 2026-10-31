// Every live mistake renders the same pure red (#EF4444): a skipped word,
// a wrong word and a wrong zabar/zer/pesh. Words not yet reached stay plain.
// Events are shaped exactly as the recitation server sends them.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_stream_event.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:qari/features/recitation/presentation/widgets/mushaf_reveal_view.dart';
import 'package:qari/features/recitation/presentation/word_view_state.dart';

import 'mushaf_text_helpers.dart';

const red = Color(0xFFEF4444);

RecitationStreamEvent _event(int index, String status,
        {String? errorType, String spoken = '', double confidence = .95}) =>
    RecitationStreamEvent.fromJson({
      'type': 'word',
      'word_index': index,
      'word_id': index + 1,
      'status': status,
      'expected': 'x',
      'spoken': spoken,
      'observed_text': spoken,
      'confidence': confidence,
      'error_type': errorType,
      'evidence_confirmed': true,
      if (status == 'error_skipped') 'display_color': '#EF4444',
    });

void main() {
  test('every theme draws mistakes in the same pure red', () {
    for (final theme in MushafTheme.all) {
      expect(theme.mismatchInk, red, reason: theme.id);
    }
  });

  test('missed, wrong word and wrong harakat are all red mistakes', () {
    final missed =
        _event(1, 'error_skipped', errorType: 'missed', confidence: 0);
    final wrong =
        _event(2, 'error_skipped', errorType: 'substituted', spoken: 'الناس');
    final harakat = _event(3, 'error_skipped',
        errorType: 'harakat_mistake', spoken: 'أَنْعَمْتُ');
    for (final e in [missed, wrong, harakat]) {
      final view = resolveWordViewState(
        serverStatus: e.liveStatus,
        index: e.wordIndex!,
        cursor: 4,
      );
      expect(view, LiveWordViewState.mismatch, reason: e.errorType);
      expect(isErrorStyle(view), isTrue);
    }
  });

  test('a word not reached yet is never red, whatever the wire says', () {
    final ahead =
        _event(5, 'error_skipped', errorType: 'missed', confidence: 0);
    expect(
      resolveWordViewState(serverStatus: ahead.liveStatus, index: 5, cursor: 2),
      LiveWordViewState.unspoken,
    );
  });

  testWidgets(
      'صراط الذين انعمت عليهم: wrong harakat is red, unreached words plain',
      (tester) async {
    const words = ['صِرَاطَ', 'الَّذِينَ', 'أَنْعَمْتَ', 'عَلَيْهِمْ'];
    final statuses = [
      _event(0, 'match').liveStatus,
      _event(1, 'match').liveStatus,
      _event(2, 'error_skipped',
              errorType: 'harakat_mistake', spoken: 'أَنْعَمْتُ')
          .liveStatus,
      LiveWordStatus.pending,
    ];
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: MushafRevealView(
          words: words,
          statuses: statuses,
          cursor: 3,
          hideUnspoken: false,
          mushaf: MushafTheme.classic,
        ),
      ),
    ));
    expect(inkOf(tester, 'أَنْعَمْتَ'), red);
    expect(inkOf(tester, 'صِرَاطَ'), isNot(red));
    expect(inkOf(tester, 'عَلَيْهِمْ'), isNot(red));
  });
}
