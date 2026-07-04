import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../core/constants/app_constants.dart';

/// Learning path map — Duolingo-style vertical path with nodes.
/// Shows completed, current, and locked lessons as a winding path.
class LearningPathMap extends StatelessWidget {
  const LearningPathMap({super.key});

  // Sample path nodes for demonstration
  static const _pathNodes = [
    _PathNodeData(id: '1', label: 'Arabic Letters', type: 'lesson', state: 'completed', xp: 10),
    _PathNodeData(id: '2', label: 'Harakat', type: 'lesson', state: 'completed', xp: 10),
    _PathNodeData(id: '3', label: 'Quiz 1', type: 'quiz', state: 'completed', xp: 15),
    _PathNodeData(id: '4', label: 'Ism (Nouns)', type: 'lesson', state: 'completed', xp: 10),
    _PathNodeData(id: '5', label: "Fi'l (Verbs)", type: 'lesson', state: 'current', xp: 10),
    _PathNodeData(id: '6', label: 'Harf (Particles)', type: 'lesson', state: 'locked', xp: 10),
    _PathNodeData(id: '7', label: 'Quiz 2', type: 'quiz', state: 'locked', xp: 15),
    _PathNodeData(id: '8', label: 'Checkpoint', type: 'checkpoint', state: 'locked', xp: 25),
    _PathNodeData(id: '9', label: 'Sentence Structure', type: 'lesson', state: 'locked', xp: 10),
    _PathNodeData(id: '10', label: 'Bonus: Root Words', type: 'bonus', state: 'locked', xp: 20),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      children: List.generate(_pathNodes.length, (index) {
        final node = _pathNodes[index];
        // Zigzag pattern: offset left, center, right
        final alignment = index % 3 == 0
            ? CrossAxisAlignment.start
            : index % 3 == 1
                ? CrossAxisAlignment.center
                : CrossAxisAlignment.end;

        return Column(
          children: [
            _PathNode(node: node, alignment: alignment),
            if (index < _pathNodes.length - 1) _PathConnector(),
          ],
        );
      }),
    );
  }
}

/// Data for a path node.
class _PathNodeData {
  final String id;
  final String label;
  final String type;
  final String state; // completed, current, locked
  final int xp;

  const _PathNodeData({
    required this.id,
    required this.label,
    required this.type,
    required this.state,
    required this.xp,
  });
}

/// A single node in the learning path.
class _PathNode extends StatelessWidget {
  final _PathNodeData node;
  final CrossAxisAlignment alignment;

  const _PathNode({required this.node, required this.alignment});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isCompleted = node.state == 'completed';
    final isCurrent = node.state == 'current';
    final isLocked = node.state == 'locked';

    Color color;
    IconData icon;
    switch (node.type) {
      case 'quiz':
        color = theme.colorScheme.secondary;
        icon = Icons.quiz_rounded;
        break;
      case 'checkpoint':
        color = Colors.purple;
        icon = Icons.flag_rounded;
        break;
      case 'bonus':
        color = Colors.amber.shade700;
        icon = Icons.star_rounded;
        break;
      default:
        color = theme.colorScheme.primary;
        icon = Icons.book_rounded;
    }

    if (isLocked) {
      color = theme.colorScheme.outline.withValues(alpha: 0.3);
      icon = Icons.lock_rounded;
    }

    return Align(
      alignment: alignment,
      child: GestureDetector(
        onTap: () async {
          if (isLocked) return;
          await Haptics.selection();
          // Navigate to lesson
        },
        child: Column(
          children: [
            // Node circle
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: isCompleted
                    ? color
                    : isCurrent
                        ? color.withValues(alpha: 0.15)
                        : theme.colorScheme.surface,
                shape: BoxShape.circle,
                border: Border.all(
                  color: isCurrent ? color : Colors.transparent,
                  width: 3,
                ),
                boxShadow: isCurrent
                    ? [
                        BoxShadow(
                          color: color.withValues(alpha: 0.3),
                          blurRadius: 12,
                          spreadRadius: 2,
                        ),
                      ]
                    : [],
              ),
              child: Icon(
                isCompleted ? Icons.check_rounded : icon,
                color: isCompleted
                    ? Colors.white
                    : isLocked
                        ? theme.colorScheme.outline
                        : color,
                size: 32,
              ),
            )
                .animate(
                  autoPlay: isCurrent,
                  onComplete: (c) => c.repeat(),
                )
                .scale(
                  begin: const Offset(1, 1),
                  end: const Offset(1.05, 1.05),
                  duration: 1.seconds,
                ),
            const SizedBox(height: 6),
            // Label
            Text(
              node.label,
              style: theme.textTheme.labelMedium?.copyWith(
                fontWeight: FontWeight.w600,
                color: isLocked
                    ? theme.colorScheme.onSurface.withValues(alpha: 0.4)
                    : theme.colorScheme.onSurface,
              ),
              textAlign: TextAlign.center,
            ),
            Text(
              '+${node.xp} XP',
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// The connecting line between path nodes.
class _PathConnector extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SizedBox(
      height: 40,
      child: Center(
        child: Container(
          width: 4,
          height: 40,
          decoration: BoxDecoration(
            color: theme.colorScheme.outline.withValues(alpha: 0.2),
            borderRadius: BorderRadius.circular(2),
          ),
        ),
      ),
    );
  }
}
