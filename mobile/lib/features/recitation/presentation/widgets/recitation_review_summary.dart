import 'package:flutter/material.dart';

import '../../../../data/models/recitation_model.dart';
import '../mushaf/mushaf_theme.dart';
import '../recitation_review.dart';

/// Compact score line above the review page. The score covers only the words
/// the reciter reached; words not reached are counted, never penalised.
class RecitationReviewSummary extends StatelessWidget {
  final RecitationReview review;
  final MushafTheme mushaf;
  final ThemeData theme;

  const RecitationReviewSummary({
    super.key,
    required this.review,
    required this.mushaf,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    final evaluated = review.result.wordVerdicts.length;
    final muted = mushaf.text.withValues(alpha: 0.6);
    final String detail;
    if (evaluated == 0) {
      detail =
          'No words were recognised. Move closer to the mic and try again.';
    } else {
      final parts = <String>[
        '${review.correctCount} matched',
        '${review.mistakeCount} ${review.mistakeCount == 1 ? 'mistake' : 'mistakes'}',
        if (review.unreachedCount > 0) '${review.unreachedCount} not reached',
      ];
      detail = parts.join(' · ');
    }
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 2, 20, 10),
      child: Row(
        children: [
          Text(
            evaluated == 0 ? '—' : review.result.scorePercentage,
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w800,
              color: review.mistakeCount == 0 ? mushaf.text : mushaf.accent,
              fontFeatures: const [FontFeature.tabularFigures()],
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  review.result.pronunciationAvailable
                      ? 'Word matching'
                      : 'Word matching · Pronunciation not assessed',
                  style: theme.textTheme.labelSmall?.copyWith(color: muted),
                ),
                Text(
                  detail,
                  style: theme.textTheme.labelLarge?.copyWith(
                    color: mushaf.text,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (review.mistakeCount > 0)
                  Text(
                    'Tap an underlined word to compare',
                    style: theme.textTheme.labelSmall?.copyWith(color: muted),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
