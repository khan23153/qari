import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:flutter_compass/flutter_compass.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/serene_decorations.dart';

/// Qibla screen — the hero is a glowing amber compass that points to the
/// direction of prayer. Uses the "Serene Path" glass + glow primitives.
///
/// The Qibla bearing is computed from the device's real GPS location, and the
/// compass dial is rotated in real time by the magnetometer (via
/// [FlutterCompass]) so the needle always settles on the Qibla as the user
/// turns the phone.
class QiblaPage extends ConsumerStatefulWidget {
  const QiblaPage({super.key});

  @override
  ConsumerState<QiblaPage> createState() => _QiblaPageState();
}

class _QiblaPageState extends ConsumerState<QiblaPage>
    with TickerProviderStateMixin {
  /// Qibla bearing in degrees from North (computed from device location).
  double _qiblaBearing = 0.0;

  /// Current device heading from the magnetometer (0 = North).
  double _deviceHeading = 0.0;

  bool _isLoading = true;
  bool _hasLocation = false;
  String? _error;

  late final AnimationController _pulse;
  StreamSubscription<CompassEvent>? _compassSubscription;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
    )..repeat(reverse: true);
    _initQibla();
  }

  /// Requests location permission, resolves the device position, computes the
  /// Qibla bearing, and subscribes to live compass (magnetometer) updates.
  Future<void> _initQibla() async {
    setState(() => _isLoading = true);

    // 1. GPS permission — Qibla cannot be calculated without a location.
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _error = 'Location permission is required to find the Qibla '
              'direction. Please enable it in your device settings.';
        });
      }
      return;
    }

    // 2. Resolve the device location and compute the Qibla bearing.
    try {
      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          // Best accuracy so the bearing is computed from a precise fix
          // (a coarse fix is what makes the needle point the wrong way).
          accuracy: LocationAccuracy.best,
          timeLimit: Duration(seconds: 20),
        ),
      );
      _qiblaBearing = _computeQiblaBearing(
        position.latitude,
        position.longitude,
      );
      _hasLocation = true;
    } catch (e) {
      // Fall back to an approximate bearing so the compass still renders.
      _qiblaBearing = 255.0;
      if (mounted) {
        setState(() {
          _error = 'Could not determine your location. Showing an '
              'approximate Qibla direction.';
        });
      }
    }

    // 3. Live magnetometer updates — rotate the dial as the phone turns.
    // Wrap-aware low-pass smoothing: raw magnetometer readings jitter by
    // several degrees per event, which made the needle tremble and "feel
    // wrong". Blend each reading toward the previous one along the SHORTEST
    // angular path (so 359°→1° doesn't spin the dial the long way round).
    _compassSubscription = FlutterCompass.events?.listen((event) {
      final h = event.heading;
      if (h != null && mounted) {
        final delta = ((h - _deviceHeading + 540) % 360) - 180;
        setState(() =>
            _deviceHeading = (_deviceHeading + delta * 0.25 + 360) % 360);
      }
    });

    if (mounted) setState(() => _isLoading = false);
  }

  /// Great-circle initial bearing from the user's location to the Kaaba.
  /// This is the standard haversine/initial-bearing formula and yields the
  /// TRUE-north bearing. For reference, for Mumbai (~19.08°N, 72.88°E) it
  /// returns ~280°, which is correct — do NOT "fix" it to ~261° (that would
  /// point the wrong way). Subtract the local magnetic declination only if
  /// you specifically want a magnetic-compass reading.
  double _computeQiblaBearing(double lat, double lon) {
    const kaabaLat = 21.4225 * math.pi / 180;
    const kaabaLon = 39.8262 * math.pi / 180;
    final pLat = lat * math.pi / 180;
    final pLon = lon * math.pi / 180;
    final dLon = kaabaLon - pLon;
    final y = math.sin(dLon) * math.cos(kaabaLat);
    final x = math.cos(pLat) * math.sin(kaabaLat) -
        math.sin(pLat) * math.cos(kaabaLat) * math.cos(dLon);
    final brng = math.atan2(y, x);
    return (brng * 180 / math.pi + 360) % 360;
  }

  Future<void> _retry() => _initQibla();

  @override
  void dispose() {
    _pulse.dispose();
    _compassSubscription?.cancel();
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
              if (_error != null)
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.error.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color:
                              theme.colorScheme.error.withValues(alpha: 0.3),
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.info_outline_rounded,
                              color: theme.colorScheme.error, size: 18),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _error!,
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: theme.colorScheme.error,
                              ),
                            ),
                          ),
                          TextButton(
                            onPressed: _retry,
                            child: const Text('Retry'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 28),
                  child: Center(
                    child: _isLoading
                        ? const CircularProgressIndicator()
                        : QiblaCompass(
                            bearing: _qiblaBearing,
                            deviceHeading: _deviceHeading,
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
                          _hasLocation
                              ? 'Rotate until the glowing needle settles on Qibla.'
                              : 'Using an approximate location — enable GPS for a precise bearing.',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Hold the phone FLAT (screen up). If the direction '
                          'looks off, wave the phone in a figure-8 to '
                          'calibrate the compass, and move away from metal '
                          'objects, magnets and chargers.',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurface.withValues(alpha: 0.45),
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
/// cardinal markers, a luminous needle that points to the Qibla bearing, and a
/// pulsing central orb. The whole dial rotates with the device heading so the
/// needle always points at the real-world Qibla.
class QiblaCompass extends StatelessWidget {
  final double bearing;
  final double deviceHeading;
  final Animation<double> pulse;

  const QiblaCompass({
    super.key,
    required this.bearing,
    required this.deviceHeading,
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
          // Rotate the dial by the negative device heading so North aligns
          // with the real world — the needle (drawn at [bearing]) then points
          // at the actual Qibla direction as the user turns the phone.
          child: Transform.rotate(
            angle: -deviceHeading * math.pi / 180,
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
                  animation: pulse,
                  builder: (_, __) => CustomPaint(
                    size: Size(size, size),
                    painter: _CompassPainter(
                      bearing: bearing,
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

    // Needle — points to the Qibla bearing.
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
