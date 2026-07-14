import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/recitation_stream_event.dart';

/// Granular, per-word state for live recitation tracking (Hifz / follow-along).
///
/// Each word owns its own [ValueNotifier]s so that updating a single word only
/// rebuilds *that* word widget — never the whole [Wrap]. This satisfies the
/// Hifz performance contract (don't rebuild the entire Wrap on every WebSocket
/// event).
class HifzWordState {
  final ValueNotifier<LiveWordStatus> status;
  final ValueNotifier<bool> isActive;
  final ValueNotifier<bool> isFlashing;

  HifzWordState()
      : status = ValueNotifier(LiveWordStatus.pending),
        isActive = ValueNotifier(false),
        isFlashing = ValueNotifier(false);

  void dispose() {
    status.dispose();
    isActive.dispose();
    isFlashing.dispose();
  }
}

/// Renders the target ayah with per-word live feedback.
///
/// * **Memorization (Hifz) Mode** — unresolved words are shown as subtle
///   circular placeholder dots. As the engine confirms each correctly spoken
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
  final List<HifzWordState> wordStates;
  final bool memorizationMode;
  final double fontSize;

  /// Stable keys, one per word, used by the parent to scroll a word to center.
  final List<GlobalKey>? wordKeys;

  /// Indices (into [words]) of the LAST word of each ayah. When set, a circular
  /// end-of-ayah marker (the ayah number) is rendered right after that word, so
  /// the user can see where one ayah ends and the next begins while reciting a
  /// continuous full-page / full-surah block.
  final List<int>? ayahBoundaries;

  /// Labels (typically the ayah number within its surah) shown inside each
  /// end-of-ayah marker. Must align 1:1 with [ayahBoundaries].
  final List<String>? ayahLabels;

  const MemorizationAyahView({
    super.key,
    required this.words,
    required this.wordStates,
    required this.memorizationMode,
    this.fontSize = 30,
    this.wordKeys,
    this.ayahBoundaries,
    this.ayahLabels,
  }) : assert(words.length == wordStates.length,
            'words and wordStates must be the same length');

  bool _isBoundary(int wordIndex) =>
      ayahBoundaries != null && ayahBoundaries!.contains(wordIndex);

  String? _boundaryLabel(int wordIndex) {
    if (ayahBoundaries == null || ayahLabels == null) return null;
    final pos = ayahBoundaries!.indexOf(wordIndex);
    return pos >= 0 && pos < ayahLabels!.length ? ayahLabels![pos] : null;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // Directionality(rtl) → Wrap: items flow right-to-left matching Arabic
    // reading order. Each word cell listens ONLY to its own HifzWordState, so a
    // status change rebuilds a single cell, not the whole Wrap.
    final children = <Widget>[];
    for (var i = 0; i < words.length; i++) {
      children.add(
        _WordCell(
          key: wordKeys != null && i < wordKeys!.length ? wordKeys![i] : null,
          text: words[i],
          state: wordStates[i],
          memorizationMode: memorizationMode,
          fontSize: fontSize,
          theme: theme,
        ),
      );
      // End-of-ayah marker rendered immediately after the ayah's last word.
      if (_isBoundary(i)) {
        children.add(_AyahMarker(label: _boundaryLabel(i) ?? '', theme: theme));
      }
    }

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Wrap(
        alignment: WrapAlignment.center,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 6,
        runSpacing: 12,
        children: children,
      ),
    );
  }
}

class _WordCell extends StatelessWidget {
  final String text;
  final HifzWordState state;
  final bool memorizationMode;
  final double fontSize;
  final ThemeData theme;

  const _WordCell({
    super.key,
    required this.text,
    required this.state,
    required this.memorizationMode,
    required this.fontSize,
    required this.theme,
  });

  static const _green = Color(0xFF2E7D32);
  static const _amber = Color(0xFFEF6C00);

  /// In Memorization Mode a still-pending word is a hidden placeholder dot.
  bool get _isHiddenDot =>
      memorizationMode && state.status.value == LiveWordStatus.pending;

  /// Ink colour of the revealed Arabic text. Revealed (correct) words inherit
  /// the exact same colour as the reader's ayah text ([onSurface]); only
  /// mistakes are tinted so the highlight reads as feedback, not theme change.
  Color get _textColor {
    if (state.isFlashing.value || state.status.value == LiveWordStatus.error) {
      return theme.colorScheme.error;
    }
    if (state.status.value == LiveWordStatus.skipped) return _amber;
    return theme.colorScheme.onSurface;
  }

  @override
  Widget build(BuildContext context) {
    // Rebuild ONLY this cell when any of its own notifiers change.
    return AnimatedBuilder(
      animation: Listenable.merge([state.status, state.isActive, state.isFlashing]),
      builder: (context, _) {
        final isFlashing = state.isFlashing.value;
        final isActive = state.isActive.value;
        final status = state.status.value;

        final Widget content;
        if (_isHiddenDot) {
          // Subtle circular placeholder — the primary text colour at low
          // opacity so it blends into the dark theme (a "page of empty dots").
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
          // Revealed word — identical TextStyle/size/colour to the reader's
          // ayah text, tinted only when it is a mistake.
          content = Text(
            text,
            style: AppTheme.arabicTextStyle(
              fontSize: fontSize,
              color: _textColor,
            ),
            textAlign: TextAlign.center,
          );
        }

        final decoration = BoxDecoration(
          color: _backgroundColor(status, isActive, isFlashing),
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
      },
    );
  }

  Color? _backgroundColor(
    LiveWordStatus status,
    bool isActive,
    bool isFlashing,
  ) {
    if (isFlashing) return theme.colorScheme.error.withValues(alpha: 0.10);
    switch (status) {
      case LiveWordStatus.matched:
        // Correct words in Memorization Mode read as plain ayah text; in
        // Tracking Mode a faint green confirms the match.
        return memorizationMode ? null : _green.withValues(alpha: 0.08);
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

/// Circular end-of-ayah marker (the ayah number) shown at the boundary between
/// two ayahs in a continuous full-page / full-surah recitation. Uses the theme
/// primary colour so it blends into the dark Mushaf-style theme.
class _AyahMarker extends StatelessWidget {
  final String label;
  final ThemeData theme;

  const _AyahMarker({required this.label, required this.theme});

  @override
  Widget build(BuildContext context) {
    final size = (30 * 0.92).clamp(18.0, 30.0);
    return Container(
      width: size,
      height: size,
      margin: const EdgeInsets.symmetric(horizontal: 4),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(
          color: theme.colorScheme.primary.withValues(alpha: 0.55),
          width: 1.5,
        ),
      ),
      child: Center(
        child: Text(
          label,
          style: theme.textTheme.labelSmall?.copyWith(
            color: theme.colorScheme.primary,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}
