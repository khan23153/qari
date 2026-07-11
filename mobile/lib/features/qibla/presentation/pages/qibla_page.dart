import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/serene_decorations.dart';

/// Qibla screen — the hero is a glowing amber compass that points to the
/// direction of prayer. Uses the "Serene Path" glass + glow primitives.
class QiblaPage extends ConsumerStatefulWidget {
  const QiblaPage({super.key});

  @override
  ConsumerState<QiblaPage> createState() => _QiblaPageState();
}

class _QiblaPageState extends ConsumerState<QiblaPage>
    with TickerProviderStateMixin {
  /// Illustrative Qibla bearing (degrees from North). In production this is
  /// derived from the device's location vs. the Kaaba's coordinates.
  static const double _qiblaBearing = 255.0;

  late final AnimationController _pulse;
  late final AnimationController _sweep;
  late final Animation<double> _bearing;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
    )..repeat(reverse: true);
    _sweep = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1300),
    );
    _bearing = Tween<double>(begin: 0, end: _qiblaBearing).animate(
      CurvedAnimation(parent: _sweep, curve: Curves.easeOutCubic),
    );
    _sweep.forward();
  }

  @override
  void dispose() {
    _pulse.dispose();
    _sweep.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SereneBackground(
        child: SafeArea(
          child: CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 20, 20, 8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Qibla Direction',
                        style: theme.textTheme.displaySmall
                            ?.copyWith(fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'Find the direction of prayer',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 28),
                  child: Center(
                    child: QiblaCompass(
                      bearing: _bearing,
                      pulse: _pulse,
                    ),
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: SereneGlass(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      children: [
                        Text(
                          'Your Qibla',
                          style: theme.textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          '${_qiblaBearing.toInt()}° from North',
                          style: theme.textTheme.headlineSmall?.copyWith(
                            color: theme.colorScheme.primary,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Rotate until the glowing needle settles on Qibla.',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SliverToBoxAdapter(child: SizedBox(height: 24)),
            ],
          ),
        ),
      ),
    );
  }
}

/// The glowing amber Qibla compass — concentric amber rings, minimalist
/// cardinal markers, a luminous needle that sweeps to the Qibla bearing, and a
/// pulsing central orb.
class QiblaCompass extends StatelessWidget {
  final Animation<double> bearing;
  final Animation<double> pulse;

  const QiblaCompass({
    super.key,
    required this.bearing,
    required this.pulse,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final amber = isDark ? SereneColors.amberDark : SereneColors.amberLight;

    return LayoutBuilder(
      builder: (context, constraints) {
        final size = math.min(constraints.maxWidth, 320.0);
        return SizedBox(
          width: size,
          height: size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Ambient amber glow
              AnimatedBuilder(
                animation: pulse,
                builder: (_, __) => Container(
                  width: size,
                  height: size,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: amber.withValues(alpha: 0.22 + 0.22 * pulse.value),
                        blurRadius: 40 + 30 * pulse.value,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                ),
              ),
              // Dial
              AnimatedBuilder(
                animation: Listenable.merge([bearing, pulse]),
                builder: (_, __) => CustomPaint(
                  size: Size(size, size),
                  painter: _CompassPainter(
                    bearing: bearing.value,
                    glow: pulse.value,
                    amber: amber,
                    isDark: isDark,
                  ),
                ),
              ),
              // Central glowing orb
              AnimatedBuilder(
                animation: pulse,
                builder: (_, __) {
                  final orbSize = size * (0.15 + 0.02 * pulse.value);
                  return Container(
                    width: orbSize,
                    height: orbSize,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: RadialGradient(
                        colors: [
                          amber.withValues(alpha: 0.95),
                          amber.withValues(alpha: 0.2),
                        ],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: amber.withValues(alpha: 0.5),
                          blurRadius: 20,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: Center(
                      child: Container(
                        width: orbSize * 0.4,
                        height: orbSize * 0.4,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: isDark ? SereneColors.charcoal : Colors.white,
                        ),
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
        );
      },
    );
  }
}

class _CompassPainter extends CustomPainter {
  final double bearing;
  final double glow;
  final Color amber;
  final bool isDark;

  const _CompassPainter({
    required this.bearing,
    required this.glow,
    required this.amber,
    required this.isDark,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final c = Offset(size.width / 2, size.height / 2);
    final r = size.width / 2;
    final paint = Paint()..style = PaintingStyle.stroke;

    // Outer rings
    paint.color = amber.withValues(alpha: 0.5);
    paint.strokeWidth = r * 0.02;
    canvas.drawCircle(c, r * 0.96, paint);
    paint.color = amber.withValues(alpha: 0.2);
    paint.strokeWidth = r * 0.012;
    canvas.drawCircle(c, r * 0.86, paint);

    // Tick marks
    for (int i = 0; i < 72; i++) {
      final a = i * 5 * math.pi / 180;
      final isCardinal = i % 18 == 0;
      final isMajor = i % 9 == 0;
      final inner = isCardinal ? r * 0.78 : (isMajor ? r * 0.82 : r * 0.88);
      final outer = r * 0.92;
      final dx = math.cos(a - math.pi / 2);
      final dy = math.sin(a - math.pi / 2);
      paint.color = isCardinal ? amber : amber.withValues(alpha: 0.35);
      paint.strokeWidth =
          isCardinal ? r * 0.02 : (isMajor ? r * 0.012 : r * 0.006);
      canvas.drawLine(
        c + Offset(dx * inner, dy * inner),
        c + Offset(dx * outer, dy * outer),
        paint,
      );
    }

    // Cardinal letters
    final labelColor =
        (isDark ? SereneColors.ivory : SereneColors.ink).withValues(alpha: 0.7);
    final drawLabel = (String s, Offset pos) {
      final tp = TextPainter(
        text: TextSpan(
          text: s,
          style: TextStyle(
            color: s == 'N' ? amber : labelColor,
            fontSize: r * (s == 'N' ? 0.12 : 0.1),
            fontWeight: s == 'N' ? FontWeight.w800 : FontWeight.w600,
          ),
        ),
        textAlign: TextAlign.center,
        textDirection: TextDirection.ltr,
      );
      tp.layout();
      tp.paint(canvas, pos - Offset(tp.width / 2, tp.height / 2));
    };

    const ring = 0.62;
    drawLabel('N', c + Offset(0, -r * ring));
    drawLabel('E', c + Offset(r * ring, 0));
    drawLabel('S', c + Offset(0, r * ring));
    drawLabel('W', c + Offset(-r * ring, 0));

    // Needle — sweeps to the Qibla bearing
    canvas.save();
    canvas.translate(c.dx, c.dy);
    canvas.rotate(bearing * math.pi / 180);

    // Qibla tip (glowing amber)
    final tipPaint = Paint()
      ..style = PaintingStyle.fill
      ..color = amber
      ..maskFilter = MaskFilter.blur(
        BlurStyle.normal,
        r * 0.02 * (1 + glow),
      );
    final tip = Path()
      ..moveTo(0, -r * 0.66)
      ..lineTo(r * 0.05, 0)
      ..lineTo(-r * 0.05, 0)
      ..close();
    canvas.drawPath(tip, tipPaint);

    // Tail (muted)
    final tailPaint = Paint()
      ..style = PaintingStyle.fill
      ..color = (isDark ? Colors.white : SereneColors.ink)
          .withValues(alpha: 0.35);
    final tail = Path()
      ..moveTo(0, r * 0.5)
      ..lineTo(r * 0.04, 0)
      ..lineTo(-r * 0.04, 0)
      ..close();
    canvas.drawPath(tail, tailPaint);
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _CompassPainter old) =>
      old.bearing != bearing || old.glow != glow;
}
