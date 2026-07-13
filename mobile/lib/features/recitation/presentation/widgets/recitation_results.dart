import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/recitation_model.dart';

/// Recitation results widget — shows score header, word-by-word display
/// with green/red tinting, and feedback. Red words are tappable.
class RecitationResults extends StatelessWidget {
  final RecitationResult result;
  final List<String> ayahWords;
  final void Function(WordVerdict verdict) onWordTapped;
  final VoidCallback onRetry;
  final ThemeData theme;

  const RecitationResults({
    super.key,
    required this.result,
    this.ayahWords = const [],
    required this.onWordTapped,
    required this.onRetry,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // ─── Score Header ──────────────────────────────────────────
          _ScoreHeader(result: result, theme: theme)
              .animate()
              .fadeIn(duration: 400.ms)
              .slideY(begin: 0.05, end: 0),

          const SizedBox(height: 20),

          // ─── Sub-scores ────────────────────────────────────────────
          _SubScores(result: result, theme: theme)
              .animate()
              .fadeIn(delay: 200.ms, duration: 400.ms),

          const SizedBox(height: 24),

          // ─── Word-by-word display ──────────────────────────────────
          Text(
            'Word by Word',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 12),

          _WordByWordDisplay(
            result: result,
            ayahWords: ayahWords,
            onWordTapped: onWordTapped,
            theme: theme,
          )
              .animate()
              .fadeIn(delay: 400.ms, duration: 400.ms),

          const SizedBox(height: 20),

          // ─── Feedback ──────────────────────────────────────────────
          if (result.feedback != null)
            _FeedbackCard(
              feedback: result.feedback!,
              theme: theme,
            )
                .animate()
                .fadeIn(delay: 600.ms, duration: 400.ms),

          const SizedBox(height: 24),

          // ─── Actions ───────────────────────────────────────────────
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: onRetry,
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size.fromHeight(52),
                  ),
                  child: const Text('Try Again'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton(
                  onPressed: () => Navigator.of(context).pop(),
                  style: FilledButton.styleFrom(
                    minimumSize: const Size.fromHeight(52),
                  ),
                  child: const Text('Done'),
                ),
              ),
            ],
          )
              .animate()
              .fadeIn(delay: 800.ms, duration: 400.ms),

          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

/// Score header with circular progress and grade.
class _ScoreHeader extends StatelessWidget {
  final RecitationResult result;
  final ThemeData theme;

  const _ScoreHeader({required this.result, required this.theme});

  @override
  Widget build(BuildContext context) {
    final scoreColor = _scoreColor(result.overallScore);

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: scoreColor.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: scoreColor.withValues(alpha: 0.2)),
      ),
      child: Row(
        children: [
          // Circular score
          SizedBox(
            width: 80,
            height: 80,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: result.overallScore,
                  strokeWidth: 8,
                  backgroundColor: scoreColor.withValues(alpha: 0.15),
                  valueColor: AlwaysStoppedAnimation(scoreColor),
                ),
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      '${(result.overallScore * 100).toInt()}',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                        color: scoreColor,
                      ),
                    ),
                    Text(
                      '/ 100',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  result.gradeLabel,
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: scoreColor,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${result.correctCount} of ${result.wordVerdicts.length} words correct',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Duration: ${result.durationSeconds}s',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _scoreColor(double score) {
    if (score >= 0.9) return Colors.green;
    if (score >= 0.75) return Colors.lightGreen;
    if (score >= 0.6) return Colors.orange;
    return Colors.red;
  }
}

/// Sub-score breakdown.
class _SubScores extends StatelessWidget {
  final RecitationResult result;
  final ThemeData theme;

  const _SubScores({required this.result, required this.theme});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _SubScoreCard(
            label: 'Pronunciation',
            score: result.pronunciationScore,
            theme: theme,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _SubScoreCard(
            label: 'Tajweed',
            score: result.tajweedScore,
            theme: theme,
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _SubScoreCard(
            label: 'Fluency',
            score: result.fluencyScore,
            theme: theme,
          ),
        ),
      ],
    );
  }
}

class _SubScoreCard extends StatelessWidget {
  final String label;
  final double score;
  final ThemeData theme;

  const _SubScoreCard({
    required this.label,
    required this.score,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: theme.colorScheme.outline.withValues(alpha: 0.15),
        ),
      ),
      child: Column(
        children: [
          Text(
            label,
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 6),
          Text(
            '${(score * 100).toInt()}%',
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: score,
              minHeight: 4,
            ),
          ),
        ],
      ),
    );
  }
}

/// Word-by-word display with green/red tinting.
class _WordByWordDisplay extends StatelessWidget {
  final RecitationResult result;
  final List<String> ayahWords;
  final void Function(WordVerdict verdict) onWordTapped;
  final ThemeData theme;

  const _WordByWordDisplay({
    required this.result,
    required this.ayahWords,
    required this.onWordTapped,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: theme.colorScheme.outline.withValues(alpha: 0.15),
        ),
      ),
      child: Directionality(
        textDirection: TextDirection.rtl,
        child: Wrap(
          alignment: WrapAlignment.center,
          spacing: 4,
          runSpacing: 12,
          children: result.wordVerdicts.map((verdict) {
            final isCorrect = verdict.isCorrect;
            final color = isCorrect ? Colors.green : Colors.red;

            return GestureDetector(
              onTap: isCorrect
                  ? null
                  : () async {
                      await Haptics.vibrate(HapticsType.medium);
                      onWordTapped(verdict);
                    },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: color.withValues(alpha: 0.3),
                  ),
                ),
                child: Column(
                  children: [
                    Text(
                      verdict.displayWord(ayahWords),
                      style: AppTheme.arabicTextStyle(
                        fontSize: 26,
                        color: color,
                      ),
                    ),
                    if (!isCorrect) ...[
                      const SizedBox(height: 2),
                      Icon(
                        Icons.touch_app_rounded,
                        size: 12,
                        color: color.withValues(alpha: 0.5),
                      ),
                    ],
                  ],
                ),
              ),
            )
                .animate()
                .fadeIn(
                  delay: Duration(
                    milliseconds: verdict.wordIndex * 100,
                  ),
                  duration: 300.ms,
                );
          }).toList(),
        ),
      ),
    );
  }
}

/// Feedback card.
class _FeedbackCard extends StatelessWidget {
  final String feedback;
  final ThemeData theme;

  const _FeedbackCard({required this.feedback, required this.theme});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.primary.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: theme.colorScheme.primary.withValues(alpha: 0.2),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.lightbulb_rounded, color: theme.colorScheme.primary, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'AI Feedback',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: theme.colorScheme.primary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  feedback,
                  style: theme.textTheme.bodyMedium?.copyWith(height: 1.5),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
