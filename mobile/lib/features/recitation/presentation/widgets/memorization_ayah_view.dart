import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/recitation_stream_event.dart';

/// Renders the target ayah with per-word live feedback.
///
/// * **Memorization (Hifz) Mode** — unresolved words are shown as subtle
///   circular placeholder dots. As the ML engine confirms each correctly spoken
///   word it is revealed sequentially as real Arabic text (in the exact same
///   style as the reader's ayah text).
/// * **Tracking Mode** — all words are visible from the start and simply tint
///   as they resolve.
///
/// In both modes a mispronounced word flashes **red** and a skipped word flashes
/// **amber**, in real time. The view uses a [Wrap] with [TextDirection.rtl] so
/// the (right-to-left) Arabic flows correctly, and each word is given a stable
/// [GlobalKey] (via [wordKeys]) so the parent can scroll it into view.
class MemorizationAyahView extends StatelessWidget {
  final List<String> words;
  final Map<int, LiveWordStatus> statuses;
  final bool memorizationMode;
  final double fontSize;

  /// The word index the reciter is currently expected to say next (for a subtle
  /// "you are here" highlight). -1 to disable.
  final int activeIndex;

  /// Word index to flash (temporarily highlight in red/amber) on a mistake. -1
  /// to disable.
  final int flashIndex;

  /// Stable keys, one per word, used by the parent to scroll a word to center.
  final List<GlobalKey>? wordKeys;

  const MemorizationAyahView({
    super.key,
    required this.words,
    required this.statuses,
    required this.memorizationMode,
    this.fontSize = 30,
    this.activeIndex = -1,
    this.flashIndex = -1,
    this.wordKeys,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // SingleChildScrollView(controller) → Wrap(rtl): items flow right-to-left
    // matching Arabic reading order.
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Wrap(
        alignment: WrapAlignment.center,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 6,
        runSpacing: 12,
        children: [
          for (var i = 0; i < words.length; i++)
            _WordCell(
              key: wordKeys != null && i < wordKeys!.length ? wordKeys![i] : null,
              text: words[i],
              status: statuses[i] ?? LiveWordStatus.pending,
              memorizationMode: memorizationMode,
              fontSize: fontSize,
              isActive: i == activeIndex,
              isFlashing: i == flashIndex,
              theme: theme,
            ),
        ],
      ),
    );
  }
}

class _WordCell extends StatelessWidget {
  final String text;
  final LiveWordStatus status;
  final bool memorizationMode;
  final double fontSize;
  final bool isActive;
  final bool isFlashing;
  final ThemeData theme;

  const _WordCell({
    super.key,
    required this.text,
    required this.status,
    required this.memorizationMode,
    required this.fontSize,
    required this.isActive,
    required this.isFlashing,
    required this.theme,
  });

  static const _green = Color(0xFF2E7D32);
  static const _amber = Color(0xFFEF6C00);

  /// In Memorization Mode a still-pending word is a hidden placeholder dot.
  bool get _isHiddenDot =>
      memorizationMode && status == LiveWordStatus.pending;

  /// Ink colour of the revealed Arabic text. Revealed (correct) words inherit
  /// the exact same colour as the reader's ayah text ([onSurface]); only
  /// mistakes are tinted so the highlight reads as feedback, not theme change.
  Color get _textColor {
    if (isFlashing || status == LiveWordStatus.error) {
      return theme.colorScheme.error;
    }
    if (status == LiveWordStatus.skipped) return _amber;
    return theme.colorScheme.onSurface;
  }

  @override
  Widget build(BuildContext context) {
    final Widget content;
    if (_isHiddenDot) {
      // Subtle circular placeholder — the primary text colour at low opacity so
      // it blends into the dark theme (a "page of empty dots").
      final dotColor = isFlashing
          ? theme.colorScheme.error
          : theme.colorScheme.onSurface.withValues(alpha: 0.3);
      final dotSize = (fontSize * 0.32).clamp(7.0, 22.0);
      content = SizedBox(
        height: fontSize,
        child: Center(
          child: Container(
            width: dotSize,
            height: dotSize,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: dotColor,
            ),
          ),
        ),
      );
    } else {
      // Revealed word — identical TextStyle/size/colour to the reader's ayah
      // text, tinted only when it is a mistake.
      content = Text(
        text,
        style: AppTheme.arabicTextStyle(fontSize: fontSize, color: _textColor),
        textAlign: TextAlign.center,
      );
    }

    final decoration = BoxDecoration(
      color: _backgroundColor,
      borderRadius: BorderRadius.circular(8),
      border: isActive || isFlashing
          ? Border.all(
              color: isFlashing
                  ? theme.colorScheme.error
                  : theme.colorScheme.primary,
              width: 1.5,
            )
          : null,
    );

    return AnimatedContainer(
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeOut,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: decoration,
      child: content,
    );
  }

  Color? get _backgroundColor {
    if (isFlashing) return theme.colorScheme.error.withValues(alpha: 0.10);
    switch (status) {
      case LiveWordStatus.matched:
        // Correct words in Memorization Mode read as plain ayah text; in
        // Tracking Mode a faint green confirms the match.
        return memorizationMode
            ? null
            : _green.withValues(alpha: 0.08);
      case LiveWordStatus.error:
        return theme.colorScheme.error.withValues(alpha: 0.10);
      case LiveWordStatus.skipped:
        return _amber.withValues(alpha: 0.10);
      case LiveWordStatus.pending:
        return isActive
            ? theme.colorScheme.primary.withValues(alpha: 0.10)
            : null;
    }
  }
}
