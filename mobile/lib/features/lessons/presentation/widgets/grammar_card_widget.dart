import 'package:flutter/material.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';

/// Grammar card widget — displays Arabic text with color-coding per pos_group.
/// Fi'l = green + solid underline, Ism = blue + no underline, Harf = amber + dotted underline.
class GrammarCardWidget extends StatelessWidget {
  final String arabicText;
  final String? transliteration;
  final String? translation;
  final String? posGroup;
  final String? grammarNote;

  const GrammarCardWidget({
    super.key,
    required this.arabicText,
    this.transliteration,
    this.translation,
    this.posGroup,
    this.grammarNote,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final config = AppTheme.getGrammarConfig(posGroup ?? 'default');

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: config.color.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        border: Border.all(
          color: config.color.withValues(alpha: 0.2),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // POS label badge
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: config.color.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  config.label,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: config.color,
                  ),
                ),
              ),
              const Spacer(),
              // Underline style indicator
              if (config.underlineStyle != UnderlineStyle.none)
                _UnderlineIndicator(style: config.underlineStyle, color: config.color),
            ],
          ),
          const SizedBox(height: 16),

          // Arabic text with color-coding and underline
          Directionality(
            textDirection: TextDirection.rtl,
            child: RichText(
              textAlign: TextAlign.center,
              text: TextSpan(
                children: [
                  TextSpan(
                    text: arabicText,
                    style: AppTheme.arabicTextStyle(
                      fontSize: 32,
                      color: config.color,
                      decoration: AppTheme.toTextDecoration(config.underlineStyle),
                      decorationColor: config.color,
                      decorationStyle: config.underlineStyle == UnderlineStyle.dotted
                          ? TextDecorationStyle.dotted
                          : TextDecorationStyle.solid,
                    ),
                  ),
                ],
              ),
            ),
          ),

          if (transliteration != null) ...[
            const SizedBox(height: 8),
            Text(
              transliteration!,
              style: theme.textTheme.bodyLarge?.copyWith(
                fontStyle: FontStyle.italic,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
              ),
              textAlign: TextAlign.center,
            ),
          ],

          if (translation != null) ...[
            const SizedBox(height: 4),
            Text(
              translation!,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
          ],

          if (grammarNote != null) ...[
            const SizedBox(height: 12),
            const Divider(),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.lightbulb_outline_rounded,
                    size: 18, color: config.color),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    grammarNote!,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                      height: 1.5,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

/// Visual indicator for the underline style.
class _UnderlineIndicator extends StatelessWidget {
  final UnderlineStyle style;
  final Color color;

  const _UnderlineIndicator({required this.style, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          style == UnderlineStyle.solid ? 'solid' : 'dotted',
          style: TextStyle(
            fontSize: 10,
            color: color.withValues(alpha: 0.6),
          ),
        ),
        const SizedBox(width: 4),
        Container(
          width: 24,
          height: 2,
          decoration: BoxDecoration(
            color: style == UnderlineStyle.dotted ? Colors.transparent : color,
            border: style == UnderlineStyle.dotted
                ? Border(
                    bottom: BorderSide(
                      color: color,
                      width: 2,
                      style: BorderStyle.solid,
                    ),
                  )
                : null,
          ),
        ),
      ],
    );
  }
}
