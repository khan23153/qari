import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/recitation_stream_event.dart';

/// A continuous, book-like (Mushaf) render of the recitation as it is revealed
/// in real time.
///
/// Unlike the old per-word grid, this view never shows placeholder dots or
/// empty boxes. It starts as a **completely blank canvas** and, as the live
/// engine confirms words, the caller appends them to [words]. The view lays
/// them out as one uninterrupted RTL paragraph that wraps line-by-line exactly
/// like a printed Quran — no artificial per-ayah containers or breaks.
///
/// When an ayah is completed (i.e. when a revealed word is the last word of an
/// ayah) the standard inline ayah marker (۝ + the verse number) is rendered
/// directly in the flow at that point, just like a real Mushaf.
///
/// A stable [caretKey] is attached to a zero-width anchor at the very end of
/// the flow, so the parent page can measure the latest revealed word's
/// position and auto-scroll it back into the upper half of the viewport.
class MushafRevealView extends StatelessWidget {
  /// Words revealed so far, in recitation order. Starts empty → blank canvas.
  final List<String> words;

  /// Per-word live status, aligned 1:1 with [words]. Only used for tinting
  /// mispronounced / skipped words; correct words read as plain book ink.
  final List<LiveWordStatus> statuses;

  /// 0-based indices (into [words]) of the LAST word of each ayah. When a word
  /// at position `i` is revealed and `i - 1` is in this list, an inline ayah
  /// marker is rendered right before word `i`.
  final List<int> ayahBoundaries;

  /// Verse numbers, aligned 1:1 with [ayahBoundaries].
  final List<String> ayahLabels;

  final double fontSize;

  /// Anchor key for the newest revealed word (placed at the end of the flow).
  final Key? caretKey;

  const MushafRevealView({
    super.key,
    required this.words,
    required this.statuses,
    this.ayahBoundaries = const [],
    this.ayahLabels = const [],
    this.fontSize = 32,
    this.caretKey,
  });

  String? _labelForBoundary(int wordIndex) {
    if (ayahBoundaries.isEmpty || ayahLabels.isEmpty) return null;
    final pos = ayahBoundaries.indexOf(wordIndex);
    return pos >= 0 && pos < ayahLabels.length ? ayahLabels[pos] : null;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // A single RTL Wrap flowing right→left, wrapping line-by-line like a book.
    // Appending a word only adds one child, so this rebuilds cheaply even for
    // a full surah (hundreds of words) at human recitation cadence.
    final children = <Widget>[];
    for (var i = 0; i < words.length; i++) {
      // Inline ayah marker sits right after the previous ayah's last word.
      if (i > 0) {
        final prevBoundaryLabel = _labelForBoundary(i - 1);
        if (prevBoundaryLabel != null) {
          children.add(_AyahMarker(label: prevBoundaryLabel, theme: theme));
        }
      }
      children.add(
        _RevealedWord(
          text: words[i],
          status: i < statuses.length ? statuses[i] : LiveWordStatus.matched,
          fontSize: fontSize,
          theme: theme,
        ),
      );
    }
    // Trailing anchor so the parent can scroll the latest word into view.
    children.add(
      SizedBox(key: caretKey, width: 0, height: fontSize),
    );

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Wrap(
        direction: Axis.horizontal,
        alignment: WrapAlignment.start,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 4,
        runSpacing: 14,
        children: children,
      ),
    );
  }
}

/// A single revealed Arabic word in the continuous book flow.
class _RevealedWord extends StatelessWidget {
  final String text;
  final LiveWordStatus status;
  final double fontSize;
  final ThemeData theme;

  const _RevealedWord({
    required this.text,
    required this.status,
    required this.fontSize,
    required this.theme,
  });

  static const _amber = Color(0xFFEF6C00);

  Color get _ink {
    if (status == LiveWordStatus.error) return theme.colorScheme.error;
    if (status == LiveWordStatus.skipped) return _amber;
    // Correct words read as the exact same book ink as the reader's ayah text.
    return theme.colorScheme.onSurface;
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 2),
      child: Text(
        text,
        style: AppTheme.arabicTextStyle(fontSize: fontSize, color: _ink),
        textAlign: TextAlign.right,
      ),
    );
  }
}

/// Inline end-of-ayah marker (۝ + verse number), rendered directly in the
/// reading flow — exactly like a printed Mushaf. Uses the theme primary so it
/// blends into the dark brown/orange theme.
class _AyahMarker extends StatelessWidget {
  final String label;
  final ThemeData theme;

  const _AyahMarker({required this.label, required this.theme});

  @override
  Widget build(BuildContext context) {
    final size = (32 * 0.92).clamp(20.0, 34.0);
    return Container(
      width: size,
      height: size,
      margin: const EdgeInsets.symmetric(horizontal: 6),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(
          color: theme.colorScheme.primary.withValues(alpha: 0.6),
          width: 1.5,
        ),
      ),
      child: Center(
        child: Text(
          // ۝ (Arabic end-of-ayah) followed by the verse number.
          '۝$label',
          style: theme.textTheme.labelSmall?.copyWith(
            color: theme.colorScheme.primary,
            fontWeight: FontWeight.w700,
            height: 1.0,
          ),
        ),
      ),
    );
  }
}
