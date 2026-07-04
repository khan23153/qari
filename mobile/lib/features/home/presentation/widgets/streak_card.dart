import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Streak card showing the current streak with a flame icon.
class StreakCard extends StatelessWidget {
  final int streakCount;
  final int longestStreak;

  const StreakCard({
    super.key,
    required this.streakCount,
    this.longestStreak = 0,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.orange.shade700,
            Colors.orange.shade500,
          ],
        ),
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
      ),
      child: Row(
        children: [
          // Flame icon with animation
          Icon(
            Icons.local_fire_department_rounded,
            color: Colors.white,
            size: 40,
          )
              .animate(
                onComplete: (controller) => controller.repeat(),
              )
              .shimmer(
                duration: 2.seconds,
                color: Colors.yellow.withValues(alpha: 0.5),
              ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '$streakCount',
                style: const TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                ),
              ),
              const Text(
                'day streak',
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.white70,
                ),
              ),
            ],
          ),
          const Spacer(),
          if (longestStreak > 0)
            Column(
              children: [
                const Text(
                  'Best',
                  style: TextStyle(fontSize: 12, color: Colors.white70),
                ),
                Text(
                  '$longestStreak',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }
}
