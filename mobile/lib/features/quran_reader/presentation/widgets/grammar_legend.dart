import 'package:flutter/material.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';

/// Grammar legend — explains the color-coding system for pos_groups.
/// Shown as a bottom sheet from the Quran Reader settings bar.
class GrammarLegend extends StatelessWidget {
  const GrammarLegend({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Drag handle
          Center(
            child: Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: theme.colorScheme.outline.withValues(alpha: 0.3),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          Text(
            'Grammar Color Legend',
            style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          Text(
            'Words are color-coded by their grammatical role (part of speech).',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
            ),
          ),

          const SizedBox(height: 20),

          // Grammar color entries
          ..._buildLegendEntries(theme),

          const SizedBox(height: 16),
          const Divider(),
          const SizedBox(height: 12),

          // Tajweed note
          Text(
            'Tajweed Colors',
            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          Text(
            'When Tajweed colors are enabled, words are colored by their tajweed rule (Idgham, Ghunnah, Iqlab, etc.). Grammar and Tajweed colors are mutually exclusive.',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              height: 1.5,
            ),
          ),

          const SizedBox(height: 12),
          // Tajweed color samples
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: AppConstants.tajweedColors.entries
                .where((e) => e.key != 'normal')
                .map((e) => _TajweedChip(rule: e.key, color: e.value, theme: theme))
                .toList(),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildLegendEntries(ThemeData theme) {
    // Show only the main 3 categories
    final mainGroups = ['fiil', 'ism', 'harf'];
    return mainGroups.map((group) {
      final config = AppConstants.getGrammarConfig(group);
      return Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Row(
          children: [
            // Color sample with underline
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: config.color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: config.color.withValues(alpha: 0.3)),
              ),
              child: Center(
                child: Directionality(
                  textDirection: TextDirection.rtl,
                  child: Text(
                    'كَتَبَ',
                    style: AppTheme.arabicTextStyle(
                      fontSize: 18,
                      color: config.color,
                      decoration: AppTheme.toTextDecoration(config.underlineStyle),
                      decorationColor: config.color,
                      decorationStyle: config.underlineStyle == UnderlineStyle.dotted
                          ? TextDecorationStyle.dotted
                          : TextDecorationStyle.solid,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        config.label,
                        style: theme.textTheme.titleMedium?.copyWith(
                          color: config.color,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Directionality(
                        textDirection: TextDirection.rtl,
                        child: Text(
                          config.labelUrdu,
                          style: AppTheme.arabicTextStyle(
                            fontSize: 16,
                            color: config.color,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _underlineDescription(config.underlineStyle),
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }).toList();
  }

  String _underlineDescription(UnderlineStyle style) {
    switch (style) {
      case UnderlineStyle.solid:
        return 'Solid underline';
      case UnderlineStyle.dotted:
        return 'Dotted underline';
      case UnderlineStyle.none:
        return 'No underline';
    }
  }
}

/// Tajweed rule color chip.
class _TajweedChip extends StatelessWidget {
  final String rule;
  final Color color;
  final ThemeData theme;

  const _TajweedChip({required this.rule, required this.color, required this.theme});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            rule,
            style: theme.textTheme.labelSmall?.copyWith(
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
