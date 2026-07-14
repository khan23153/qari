import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Badges grid — shows achievement badges with earned/locked states.
///
/// The earned set is driven by data: [earnedIds] holds the badge ids the
/// backend reports as unlocked for this user. A brand-new account passes an
/// empty set, so every badge starts locked (no mock "earned" state).
class BadgesGrid extends StatelessWidget {
  final ThemeData theme;
  final Set<String> earnedIds;

  const BadgesGrid({
    super.key,
    required this.theme,
    this.earnedIds = const {},
  });

  static const _badges = [
    _Badge(id: 'first_lesson', icon: 'school', title: 'First Lesson', desc: 'Complete your first lesson'),
    _Badge(id: '7_day_streak', icon: 'fire', title: '7-Day Streak', desc: '7 day learning streak'),
    _Badge(id: 'quran_reader', icon: 'book', title: 'Quran Reader', desc: 'Read 50 ayahs'),
    _Badge(id: 'first_recitation', icon: 'mic', title: 'First Recitation', desc: 'Complete a recitation session'),
    _Badge(id: 'flashcard_pro', icon: 'style', title: 'Flashcard Pro', desc: 'Review 100 flashcards'),
    _Badge(id: 'perfect_score', icon: 'star', title: 'Perfect Score', desc: 'Get 100% on a recitation'),
    _Badge(id: 'root_explorer', icon: 'root', title: 'Root Explorer', desc: 'Explore 10 roots'),
    _Badge(id: 'tajweed_master', icon: 'tajweed', title: 'Tajweed Master', desc: 'Learn all tajweed rules'),
    _Badge(id: '30_day_streak', icon: 'streak30', title: '30-Day Streak', desc: '30 day learning streak'),
  ];

  @override
  Widget build(BuildContext context) {
    final earnedCount = _badges.where((b) => earnedIds.contains(b.id)).length;
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
          Row(
            children: [
              Icon(Icons.emoji_events_rounded, color: Colors.amber.shade700, size: 24),
              const SizedBox(width: 8),
              Text(
                'Badges',
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const Spacer(),
              Text(
                '$earnedCount/${_badges.length}',
                style: theme.textTheme.labelMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 3,
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 0.85,
            children: _badges.map((badge) {
              final earned = earnedIds.contains(badge.id);
              return _BadgeTile(badge: badge, earned: earned, theme: theme)
                  .animate()
                  .fadeIn(
                    delay: Duration(milliseconds: _badges.indexOf(badge) * 50),
                    duration: 300.ms,
                  );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

class _Badge {
  final String id;
  final String icon;
  final String title;
  final String desc;

  const _Badge({
    required this.id,
    required this.icon,
    required this.title,
    required this.desc,
  });
}

class _BadgeTile extends StatelessWidget {
  final _Badge badge;
  final bool earned;
  final ThemeData theme;

  const _BadgeTile({
    required this.badge,
    required this.earned,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    final color = earned ? Colors.amber.shade700 : theme.colorScheme.outline.withValues(alpha: 0.3);

    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: earned
            ? Colors.amber.withValues(alpha: 0.08)
            : theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: earned
              ? Colors.amber.withValues(alpha: 0.3)
              : theme.colorScheme.outline.withValues(alpha: 0.1),
        ),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            _iconData(badge.icon),
            size: 32,
            color: color,
          ),
          const SizedBox(height: 4),
          Text(
            badge.title,
            style: theme.textTheme.labelSmall?.copyWith(
              fontWeight: FontWeight.w600,
              color: earned
                  ? theme.colorScheme.onSurface
                  : theme.colorScheme.onSurface.withValues(alpha: 0.4),
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          if (!earned)
            Icon(Icons.lock_outline_rounded, size: 12, color: color.withValues(alpha: 0.5)),
        ],
      ),
    );
  }

  IconData _iconData(String name) {
    switch (name) {
      case 'school':
        return Icons.school_rounded;
      case 'fire':
        return Icons.local_fire_department_rounded;
      case 'book':
        return Icons.menu_book_rounded;
      case 'mic':
        return Icons.mic_rounded;
      case 'style':
        return Icons.style_rounded;
      case 'star':
        return Icons.star_rounded;
      case 'root':
        return Icons.park_rounded;
      case 'tajweed':
        return Icons.colorize_rounded;
      case 'streak30':
        return Icons.whatshot_rounded;
      default:
        return Icons.emoji_events_rounded;
    }
  }
}
