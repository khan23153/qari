import 'dart:ui' as ui;
import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/recitation_stream_event.dart';

/// Renders the target ayah with per-word live feedback.
///
/// * **Memorization (Hifz) Mode** — unresolved words are masked (blurred behind
///   a placeholder). As the ML engine confirms each spoken word it is revealed
///   sequentially (green when correct).
/// * **Tracking Mode** — all words are visible from the start and simply tint
///   as they resolve.
///
/// In both modes a mispronounced word turns **red** and a skipped word is
/// flagged amber with an underline, in real time.
class MemorizationAyahView extends StatelessWidget {
  final List<String> words;
  final Map<int, LiveWordStatus> statuses;
  final bool memorizationMode;
  final double fontSize;

  /// The word index the reciter is currently expected to say next (for a subtle
  /// "you are here" highlight). -1 to disable.
  final int activeIndex;

  const MemorizationAyahView({
    super.key,
    required this.words,
    required this.statuses,
    required this.memorizationMode,
    this.fontSize = 30,
    this.activeIndex = -1,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Wrap(
        alignment: WrapAlignment.center,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 6,
        runSpacing: 12,
        children: [
          for (var i = 0; i < words.length; i++)
            _WordChip(
              text: words[i],
              status: statuses[i] ?? LiveWordStatus.pending,
              memorizationMode: memorizationMode,
              fontSize: fontSize,
              isActive: i == activeIndex,
              theme: theme,
            ),
        ],
      ),
    );
  }
}

class _WordChip extends StatelessWidget {
  final String text;
  final LiveWordStatus status;
  final bool memorizationMode;
  final double fontSize;
  final bool isActive;
  final ThemeData theme;

  const _WordChip({
    required this.text,
    required this.status,
    required this.memorizationMode,
    required this.fontSize,
    required this.isActive,
    required this.theme,
  });

  static const _green = Color(0xFF2E7D32);
  static const _amber = Color(0xFFEF6C00);

  Color get _color {
    switch (status) {
      case LiveWordStatus.matched:
        return _green;
      case LiveWordStatus.error:
        return theme.colorScheme.error;
      case LiveWordStatus.skipped:
        return _amber;
      case LiveWordStatus.pending:
        return theme.colorScheme.onSurface;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isMasked = memorizationMode && status == LiveWordStatus.pending;

    final textWidget = Text(
      text,
      style: AppTheme.arabicTextStyle(
        fontSize: fontSize,
        color: _color,
      ).copyWith(
        decoration:
            status == LiveWordStatus.skipped ? TextDecoration.underline : null,
        decorationColor: _amber,
        decorationThickness: 2,
      ),
      textAlign: TextAlign.center,
    );

    Widget content;
    if (isMasked) {
      // Blur the actual glyphs behind a subtle placeholder so the shape hints
      // at length but the word can't be read until it's confirmed.
      content = Stack(
        alignment: Alignment.center,
        children: [
          ImageFiltered(
            imageFilter: ui.ImageFilter.blur(sigmaX: 7, sigmaY: 7),
            child: Opacity(
              opacity: 0.55,
              child: Text(
                text,
                style: AppTheme.arabicTextStyle(
                  fontSize: fontSize,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest
                    .withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
        ],
      );
    } else {
      content = textWidget;
    }

    final decoration = BoxDecoration(
      color: _backgroundColor(isMasked),
      borderRadius: BorderRadius.circular(8),
      border: isActive
          ? Border.all(color: theme.colorScheme.primary, width: 1.5)
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

  Color? _backgroundColor(bool isMasked) {
    switch (status) {
      case LiveWordStatus.matched:
        return _green.withValues(alpha: 0.08);
      case LiveWordStatus.error:
        return theme.colorScheme.error.withValues(alpha: 0.10);
      case LiveWordStatus.skipped:
        return _amber.withValues(alpha: 0.10);
      case LiveWordStatus.pending:
        return isMasked
            ? theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.25)
            : null;
    }
  }
}
