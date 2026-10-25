import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/models/recitation_stream_event.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:qari/features/recitation/presentation/widgets/mushaf_reveal_view.dart';
import 'package:qari/features/recitation/presentation/word_view_state.dart';

import 'mushaf_text_helpers.dart';

RecitationStreamEvent mistakeEvent({
  String status = 'error_skipped',
  String? errorType = 'missed',
  bool confirmed = true,
  String spoken = '',
  double confidence = .95,
  int index = 1,
}) =>
    RecitationStreamEvent.fromJson({
      'type': 'word',
      'word_index': index,
      'status': status,
      'error_type': errorType,
      'expected': 'لله',
      'spoken': spoken,
      'confidence': confidence,
      'evidence_confirmed': confirmed,
    });

void main() {
  test('confirmed missed word needs no invented spoken text', () {
    expect(mistakeEvent(confidence: 0).liveStatus, LiveWordStatus.error);
    expect(mistakeEvent(status: 'skipped').liveStatus, LiveWordStatus.error);
    expect(mistakeEvent(status: 'error').liveStatus, LiveWordStatus.error);
    expect(mistakeEvent(confirmed: false).liveStatus, LiveWordStatus.pending);
    // The acoustic floor applies to a heard word, not a confirmed omission.
    expect(
        mistakeEvent(errorType: 'substituted', spoken: 'الناس', confidence: .2)
            .liveStatus,
        LiveWordStatus.pending);
  });

  for (final type in ['substituted', 'harakat_mistake']) {
    test('$type evidence is visible at current cursor but never ahead', () {
      final event = mistakeEvent(errorType: type, spoken: 'لِلَّهُ');
      expect(event.errorType, type);
      expect(
          resolveWordViewState(
              serverStatus: event.liveStatus, index: 1, cursor: 1),
          LiveWordViewState.mismatch);
      expect(
          resolveWordViewState(
              serverStatus: event.liveStatus, index: 2, cursor: 1),
          LiveWordViewState.unspoken);
      expect(
          mistakeEvent(errorType: type, confirmed: false, spoken: 'لِلَّهُ')
              .liveStatus,
          LiveWordStatus.pending);
    });
  }

  test('observed diacritics count as text evidence without a spoken alias', () {
    final event = RecitationStreamEvent.fromJson({
      'type': 'word',
      'word_index': 1,
      'status': 'error_skipped',
      'error_type': 'harakat_mistake',
      'evidence_confirmed': true,
      'evidence_source': 'asr_diacritic',
      'observed_text': 'لِلَّهُ',
      'confidence': .95,
    });
    expect(event.liveStatus.isMistake, isTrue);
  });

  for (final type in ['substituted', 'harakat_mistake']) {
    testWidgets(
        'Hifz shows current confirmed $type in pure red, not unread text',
        (tester) async {
      final event = mistakeEvent(errorType: type, spoken: 'لِلَّهُ');
      await tester.pumpWidget(MaterialApp(
          home: Scaffold(
              body: MushafRevealView(
        words: const ['الحمد', 'لِلَّهِ', 'رب', 'العالمين'],
        statuses: [
          LiveWordStatus.matched,
          event.liveStatus,
          LiveWordStatus.pending,
          LiveWordStatus.error
        ],
        cursor: 1,
        mushaf: MushafTheme.night,
        hideUnspoken: true,
        ayahBoundaries: const [1, 3],
        ayahLabels: const ['1', '2'],
      ))));
      expect(inkOf(tester, 'لِلَّهِ'), const Color(0xFFEF4444));
      expect(spanOf(tester, 'لِلَّهِ')!.style!.decoration,
          TextDecoration.underline);
      expect(inkOf(tester, 'رب')!.a, 0);
      expect(inkOf(tester, 'العالمين')!.a, 0);
      expect(inkOf(tester, ayahMarkerText('1'))!.a, 1);
      expect(inkOf(tester, ayahMarkerText('2'))!.a, 1);
    });
  }

  for (final palette in MushafTheme.all) {
    testWidgets(
        'missed لله رب are pure red in ${palette.id}, unread stays normal',
        (tester) async {
      await tester.pumpWidget(MaterialApp(
          home: Scaffold(
              body: MushafRevealView(
        words: const ['الحمد', 'لله', 'رب', 'العالمين', 'الرحمن'],
        statuses: [
          LiveWordStatus.matched,
          mistakeEvent(confidence: 0).liveStatus,
          mistakeEvent(index: 2, confidence: 0).liveStatus,
          LiveWordStatus.pending,
          LiveWordStatus.error
        ],
        cursor: 3,
        mushaf: palette,
      ))));
      expect(inkOf(tester, 'لله'), const Color(0xFFEF4444));
      expect(inkOf(tester, 'رب'), const Color(0xFFEF4444));
      expect(inkOf(tester, 'العالمين'), palette.text);
      expect(inkOf(tester, 'الرحمن'), palette.text);
      expect(spanOf(tester, 'الرحمن')!.style!.decoration, isNull);
    });
  }
}
