import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../data/models/user_model.dart';

/// Learning path map — Duolingo-style vertical path with nodes.
/// Shows completed, current, and locked lessons as a winding path.
///
/// When [nodes] (server data) is provided it is rendered; otherwise a static
/// sample path is shown. Tapping an unlocked node invokes [onNodeTap].
class LearningPathMap extends StatelessWidget {
  final List<PathNode>? nodes;
  final ValueChanged<PathNode>? onNodeTap;

  const LearningPathMap({super.key, this.nodes, this.onNodeTap});

  // Sample path nodes for demonstration when no server data is available.
  // A brand-new account starts fresh: only the first foundational lesson is
  // unlocked (current); every other module is locked until earned.
  static const _sampleNodes = [
    _PathNodeData(id: '1', label: 'Arabic Letters', type: 'lesson', state: 'current', xp: 10),
    _PathNodeData(id: '2', label: 'Harakat', type: 'lesson', state: 'locked', xp: 10),
    _PathNodeData(id: '3', label: 'Quiz 1', type: 'quiz', state: 'locked', xp: 15),
    _PathNodeData(id: '4', label: 'Ism (Nouns)', type: 'lesson', state: 'locked', xp: 10),
    _PathNodeData(id: '5', label: "Fi'l (Verbs)", type: 'lesson', state: 'locked', xp: 10),
    _PathNodeData(id: '6', label: 'Harf (Particles)', type: 'lesson', state: 'locked', xp: 10),
    _PathNodeData(id: '7', label: 'Quiz 2', type: 'quiz', state: 'locked', xp: 15),
    _PathNodeData(id: '8', label: 'Checkpoint', type: 'checkpoint', state: 'locked', xp: 25),
    _PathNodeData(id: '9', label: 'Sentence Structure', type: 'lesson', state: 'locked', xp: 10),
    _PathNodeData(id: '10', label: 'Bonus: Root Words', type: 'bonus', state: 'locked', xp: 20),
  ];

  List<_PathNodeData> get _displayNodes {
    final serverNodes = nodes;
    if (serverNodes != null && serverNodes.isNotEmpty) {
      return serverNodes
          .map(
            (n) => _PathNodeData(
              id: n.id,
              label: n.label,
              type: n.type.name,
              state: n.isLocked
                  ? 'locked'
                  : n.isCompleted
                      ? 'completed'
                      : 'current',
              xp: n.xpReward,
            ),
          )
          .toList();
    }
    return _sampleNodes;
  }

  @override
  Widget build(BuildContext context) {
    final items = _displayNodes;
    return Column(
      children: List.generate(items.length, (index) {
        final node = items[index];
        final sourceNode = (nodes != null && index < nodes!.length)
            ? nodes![index]
            : null;
        // Zigzag pattern: offset left, center, right
        final alignment = index % 3 == 0
            ? Alignment.centerLeft
            : index % 3 == 1
                ? Alignment.center
                : Alignment.centerRight;

        return Column(
          children: [
            _PathNode(
              node: node,
              alignment: alignment,
              sourceNode: sourceNode,
              onNodeTap: onNodeTap,
            ),
            if (index < items.length - 1) _PathConnector(),
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
  final Alignment alignment;
  final PathNode? sourceNode;
  final ValueChanged<PathNode>? onNodeTap;

  const _PathNode({
    required this.node,
    required this.alignment,
    this.sourceNode,
    this.onNodeTap,
  });

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

    final tappable = !isLocked && sourceNode != null && onNodeTap != null;

    return Align(
      alignment: alignment,
      child: GestureDetector(
        onTap: tappable
            ? () async {
                await Haptics.vibrate(HapticsType.selection);
                onNodeTap!(sourceNode!);
              }
            : null,
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
