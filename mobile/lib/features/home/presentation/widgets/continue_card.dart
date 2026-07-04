import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

/// Continue card — shows the last lesson in progress with a resume button.
class ContinueCard extends StatelessWidget {
  final String lessonTitle;
  final int moduleNumber;
  final double progressPercent;
  final VoidCallback onTap;

  const ContinueCard({
    super.key,
    required this.lessonTitle,
    required this.moduleNumber,
    required this.progressPercent,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () async {
          await Haptics.selection();
          onTap();
        },
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: theme.colorScheme.primary.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
            border: Border.all(
              color: theme.colorScheme.primary.withValues(alpha: 0.2),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      'Module $moduleNumber',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Icon(
                    Icons.play_circle_fill_rounded,
                    color: theme.colorScheme.primary,
                    size: 32,
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                lessonTitle,
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 12),
              // Progress bar
              Row(
                children: [
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: LinearProgressIndicator(
                        value: progressPercent,
                        minHeight: 6,
                        backgroundColor:
                            theme.colorScheme.primary.withValues(alpha: 0.15),
                        valueColor: AlwaysStoppedAnimation(
                          theme.colorScheme.primary,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${(progressPercent * 100).toInt()}%',
                    style: theme.textTheme.labelMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    )
        .animate()
        .fadeIn(duration: 400.ms)
        .slideY(begin: 0.05, end: 0);
  }
}
