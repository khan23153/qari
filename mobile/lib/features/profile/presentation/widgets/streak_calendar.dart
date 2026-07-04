import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Streak calendar — shows a monthly view of active days.
class StreakCalendar extends StatelessWidget {
  final int currentStreak;
  final ThemeData theme;

  const StreakCalendar({
    super.key,
    required this.currentStreak,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final daysInMonth = DateTime(now.year, now.month + 1, 0).day;
    final firstWeekday = DateTime(now.year, now.month, 1).weekday;

    // Sample active days (every day this week + some previous)
    final activeDays = <int>{};
    for (var i = 0; i < currentStreak; i++) {
      final day = now.day - i;
      if (day > 0) activeDays.add(day);
    }
    // Add some historical active days
    activeDays.addAll([3, 7, 10, 14, 18, 22, 25]);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: theme.colorScheme.outline.withValues(alpha: 0.15),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Icon(Icons.local_fire_department_rounded,
                  color: Colors.orange, size: 24),
              const SizedBox(width: 8),
              Text(
                '$currentStreak day streak',
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const Spacer(),
              Text(
                _monthName(now.month),
                style: theme.textTheme.labelMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Weekday labels
          Row(
            children: ['M', 'T', 'W', 'T', 'F', 'S', 'S']
                .map((d) => Expanded(
                      child: Center(
                        child: Text(
                          d,
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
                          ),
                        ),
                      ),
                    ))
                .toList(),
          ),
          const SizedBox(height: 8),

          // Calendar grid
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 7,
            mainAxisSpacing: 4,
            crossAxisSpacing: 4,
            childAspectRatio: 1,
            children: List.generate(daysInMonth + firstWeekday - 1, (index) {
              if (index < firstWeekday - 1) {
                return const SizedBox.shrink();
              }
              final day = index - firstWeekday + 2;
              final isActive = activeDays.contains(day);
              final isToday = day == now.day;

              return Container(
                decoration: BoxDecoration(
                  color: isActive
                      ? Colors.orange.withValues(alpha: 0.15)
                      : theme.colorScheme.surface,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: isToday
                        ? Colors.orange
                        : isActive
                            ? Colors.orange.withValues(alpha: 0.3)
                            : theme.colorScheme.outline.withValues(alpha: 0.1),
                    width: isToday ? 2 : 1,
                  ),
                ),
                child: Center(
                  child: isActive
                      ? Icon(
                          Icons.local_fire_department_rounded,
                          size: 16,
                          color: Colors.orange.shade700,
                        )
                      : Text(
                          '$day',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: theme.colorScheme.onSurface.withValues(alpha: 0.3),
                          ),
                        ),
                ),
              );
            }),
          ),
        ],
      ),
    )
        .animate()
        .fadeIn(duration: 400.ms);
  }

  String _monthName(int month) {
    const names = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return names[month - 1];
  }
}
