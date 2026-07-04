import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// Live waveform widget — displays real-time audio amplitude as animated bars.
class LiveWaveform extends StatelessWidget {
  final List<double> samples;
  final Color color;
  final double height;
  final int maxBars;

  const LiveWaveform({
    super.key,
    required this.samples,
    required this.color,
    this.height = 100,
    this.maxBars = 50,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SizedBox(
      height: height,
      width: double.infinity,
      child: CustomPaint(
        painter: _WaveformPainter(
          samples: samples,
          color: color,
          maxBars: maxBars,
          backgroundColor: theme.colorScheme.outline.withValues(alpha: 0.1),
        ),
      ),
    );
  }
}

/// Custom painter for the waveform visualization.
class _WaveformPainter extends CustomPainter {
  final List<double> samples;
  final Color color;
  final int maxBars;
  final Color backgroundColor;

  _WaveformPainter({
    required this.samples,
    required this.color,
    required this.maxBars,
    required this.backgroundColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final barWidth = size.width / maxBars;
    final centerY = size.height / 2;

    // Draw background bars (idle state)
    final bgPaint = Paint()
      ..color = backgroundColor
      ..style = PaintingStyle.fill;

    for (var i = 0; i < maxBars; i++) {
      final x = i * barWidth;
      final barHeight = 4.0;
      final rect = RRect.fromRectAndRadius(
        Rect.fromCenter(
          center: Offset(x + barWidth / 2, centerY),
          width: barWidth * 0.6,
          height: barHeight,
        ),
        const Radius.circular(2),
      );
      canvas.drawRRect(rect, bgPaint);
    }

    // Draw active bars from samples
    final activePaint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final sampleCount = samples.length.clamp(0, maxBars);
    final startIndex = samples.length > maxBars ? samples.length - maxBars : 0;

    for (var i = 0; i < sampleCount; i++) {
      final sample = samples[startIndex + i];
      final x = i * barWidth;
      final barHeight = (sample * size.height * 0.8).clamp(4.0, size.height * 0.9);

      final rect = RRect.fromRectAndRadius(
        Rect.fromCenter(
          center: Offset(x + barWidth / 2, centerY),
          width: barWidth * 0.6,
          height: barHeight,
        ),
        const Radius.circular(2),
      );
      canvas.drawRRect(rect, activePaint);
    }

    // Draw center line
    final linePaint = Paint()
      ..color = color.withValues(alpha: 0.2)
      ..strokeWidth = 1;
    canvas.drawLine(
      Offset(0, centerY),
      Offset(size.width, centerY),
      linePaint,
    );
  }

  @override
  bool shouldRepaint(_WaveformPainter oldDelegate) =>
      oldDelegate.samples != samples;
}

/// Static waveform for playback visualization (non-live).
class StaticWaveform extends StatelessWidget {
  final List<double> samples;
  final Color color;
  final double height;
  final double progress; // 0.0 to 1.0

  const StaticWaveform({
    super.key,
    required this.samples,
    required this.color,
    this.height = 60,
    this.progress = 0,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: height,
      width: double.infinity,
      child: CustomPaint(
        painter: _StaticWaveformPainter(
          samples: samples,
          color: color,
          progress: progress,
        ),
      ),
    );
  }
}

class _StaticWaveformPainter extends CustomPainter {
  final List<double> samples;
  final Color color;
  final double progress;

  _StaticWaveformPainter({
    required this.samples,
    required this.color,
    required this.progress,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (samples.isEmpty) return;

    final barWidth = size.width / samples.length;
    final centerY = size.height / 2;
    final progressX = size.width * progress;

    for (var i = 0; i < samples.length; i++) {
      final sample = samples[i];
      final x = i * barWidth;
      final barHeight = (sample * size.height * 0.8).clamp(2.0, size.height * 0.9);
      final isPlayed = x < progressX;

      final paint = Paint()
        ..color = isPlayed ? color : color.withValues(alpha: 0.3)
        ..style = PaintingStyle.fill;

      final rect = RRect.fromRectAndRadius(
        Rect.fromCenter(
          center: Offset(x + barWidth / 2, centerY),
          width: barWidth * 0.7,
          height: barHeight,
        ),
        const Radius.circular(1.5),
      );
      canvas.drawRRect(rect, paint);
    }
  }

  @override
  bool shouldRepaint(_StaticWaveformPainter oldDelegate) =>
      oldDelegate.progress != progress || oldDelegate.samples != samples;
}
