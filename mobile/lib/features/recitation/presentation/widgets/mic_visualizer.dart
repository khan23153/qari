import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';

/// An always-on audio visualizer shown at the bottom of the live recitation
/// screen to indicate the microphone is continuously listening (hands-free).
///
/// It subscribes to the [amplitude] stream itself and maintains its own rolling
/// buffer of normalized (0–1) samples, so the parent page never has to
/// [setState] on every audio frame (keeping the word Wrap rebuilds isolated to
/// actual word-status changes). When [active] is false it renders a calm idle
/// baseline.
class MicVisualizer extends StatefulWidget {
  final Stream<double> amplitude;
  final bool active;
  final Color color;
  final double height;
  final int barCount;

  const MicVisualizer({
    super.key,
    required this.amplitude,
    required this.active,
    required this.color,
    this.height = 72,
    this.barCount = 40,
  });

  @override
  State<MicVisualizer> createState() => _MicVisualizerState();
}

class _MicVisualizerState extends State<MicVisualizer> {
  final List<double> _levels = [];
  StreamSubscription<double>? _sub;

  @override
  void initState() {
    super.initState();
    _sub = widget.amplitude.listen((level) {
      if (!mounted) return;
      setState(() {
        _levels.add(level);
        if (_levels.length > 240) _levels.removeAt(0);
      });
    });
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      height: widget.height,
      width: double.infinity,
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
        border: Border(
          top: BorderSide(
            color: theme.colorScheme.outline.withValues(alpha: 0.15),
          ),
        ),
      ),
      child: Row(
        children: [
          const SizedBox(width: 16),
          _LiveDot(active: widget.active, color: widget.color),
          const SizedBox(width: 12),
          Expanded(
            child: CustomPaint(
              painter: _MicBarsPainter(
                levels: _levels,
                color: widget.color,
                active: widget.active,
                barCount: widget.barCount,
                idleColor: theme.colorScheme.outline.withValues(alpha: 0.25),
              ),
              size: Size.infinite,
            ),
          ),
          const SizedBox(width: 16),
          Text(
            widget.active ? 'Listening' : 'Paused',
            style: theme.textTheme.labelMedium?.copyWith(
              color: widget.active
                  ? widget.color
                  : theme.colorScheme.onSurface.withValues(alpha: 0.4),
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(width: 16),
        ],
      ),
    );
  }
}

class _LiveDot extends StatefulWidget {
  final bool active;
  final Color color;
  const _LiveDot({required this.active, required this.color});

  @override
  State<_LiveDot> createState() => _LiveDotState();
}

class _LiveDotState extends State<_LiveDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 900),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.active) {
      return Icon(Icons.mic_off_rounded,
          size: 18, color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.4));
    }
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final t = _controller.value;
        return Stack(
          alignment: Alignment.center,
          children: [
            Container(
              width: 16 + t * 10,
              height: 16 + t * 10,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: widget.color.withValues(alpha: 0.25 * (1 - t)),
              ),
            ),
            Icon(Icons.mic_rounded, size: 18, color: widget.color),
          ],
        );
      },
    );
  }
}

class _MicBarsPainter extends CustomPainter {
  final List<double> levels;
  final Color color;
  final Color idleColor;
  final bool active;
  final int barCount;

  _MicBarsPainter({
    required this.levels,
    required this.color,
    required this.idleColor,
    required this.active,
    required this.barCount,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final barSlot = size.width / barCount;
    final barWidth = barSlot * 0.55;
    final centerY = size.height / 2;

    for (var i = 0; i < barCount; i++) {
      // Newest samples on the right.
      final sampleIndex = levels.length - barCount + i;
      double level;
      if (sampleIndex >= 0 && sampleIndex < levels.length) {
        level = levels[sampleIndex];
      } else {
        level = 0;
      }

      final double barHeight;
      if (active) {
        barHeight = (level * size.height * 0.85).clamp(3.0, size.height * 0.95);
      } else {
        // Gentle idle baseline sine so it doesn't look frozen.
        barHeight = 3.0 + 2.0 * (0.5 + 0.5 * math.sin(i * 0.6));
      }

      final paint = Paint()
        ..color = active
            ? Color.lerp(color.withValues(alpha: 0.5), color, level) ?? color
            : idleColor
        ..style = PaintingStyle.fill;

      final x = i * barSlot + (barSlot - barWidth) / 2;
      final rect = RRect.fromRectAndRadius(
        Rect.fromLTWH(x, centerY - barHeight / 2, barWidth, barHeight),
        const Radius.circular(3),
      );
      canvas.drawRRect(rect, paint);
    }
  }

  @override
  bool shouldRepaint(_MicBarsPainter oldDelegate) =>
      oldDelegate.levels != levels ||
      oldDelegate.active != active ||
      oldDelegate.color != color;
}
