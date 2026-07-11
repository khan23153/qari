import 'dart:math' as math;
import 'dart:ui';

import 'package:flutter/material.dart';

/// Reusable "Serene Path" visual building blocks: the brand color tokens, the
/// atmospheric radial-gradient backdrop (with a subtle mosque silhouette), and
/// the frosted-glass surface used for elevated cards.
class SereneColors {
  SereneColors._();

  // Warm amber / bronze accents
  static const Color amberLight = Color(0xFF9C5A1C);
  static const Color amberLightSoft = Color(0xFFB3742A);
  static const Color amberDark = Color(0xFFD98C3C);
  static const Color amberDarkSoft = Color(0xFFE3AE62);

  // Light ("Warm Sunrise") surfaces
  static const Color cream = Color(0xFFFDF9E9);
  static const Color creamGlow = Color(0xFFF7E9CC);
  static const Color ink = Color(0xFF3B2F23);

  // Dark ("Contemplative Night") surfaces
  static const Color charcoal = Color(0xFF15110C);
  static const Color ember = Color(0xFF33240F);
  static const Color ivory = Color(0xFFF2ECE4);
}

/// Atmospheric backdrop for full-screen pages.
///
/// Paints a multi-stop radial gradient (the signature "glow") and, optionally,
/// a low-opacity mosque silhouette anchored to the bottom-center. Respects the
/// current [Theme] brightness so it looks right in both light and dark modes.
class SereneBackground extends StatelessWidget {
  final Widget child;
  final bool showSilhouette;

  const SereneBackground({
    super.key,
    required this.child,
    this.showSilhouette = true,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      decoration: BoxDecoration(
        gradient: RadialGradient(
          center: const Alignment(0.0, -0.35),
          radius: 1.25,
          colors: isDark
              ? [SereneColors.ember, SereneColors.charcoal]
              : [SereneColors.creamGlow, SereneColors.cream],
        ),
      ),
      child: Stack(
        children: [
          if (showSilhouette)
            Positioned.fill(
              child: CustomPaint(
                painter: MosqueSilhouettePainter(
                  color: isDark
                      ? Colors.white.withValues(alpha: 0.04)
                      : Colors.black.withValues(alpha: 0.04),
                ),
              ),
            ),
          child,
        ],
      ),
    );
  }
}

/// Frosted-glass surface — translucent fill + thin amber "shimmer" border +
/// backdrop blur. Use for elevated cards (e.g. the auth login card).
class SereneGlass extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final double borderRadius;
  final bool blur;

  const SereneGlass({
    super.key,
    required this.child,
    this.padding,
    this.borderRadius = 24,
    this.blur = true,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final borderColor = (isDark
            ? SereneColors.amberDark
            : SereneColors.amberLight)
        .withValues(alpha: 0.18);
    final fill = isDark
        ? Colors.white.withValues(alpha: 0.06)
        : Colors.white.withValues(alpha: 0.5);

    final container = Container(
      padding: padding,
      decoration: BoxDecoration(
        color: fill,
        borderRadius: BorderRadius.circular(borderRadius),
        border: Border.all(color: borderColor, width: 1),
        boxShadow: [
          BoxShadow(
            color: (isDark ? Colors.black : SereneColors.amberLight)
                .withValues(alpha: isDark ? 0.5 : 0.12),
            blurRadius: 30,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: child,
    );

    if (!blur) return container;

    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 22, sigmaY: 22),
        child: container,
      ),
    );
  }
}

/// Minimalist mosque silhouette: a base, a central dome with finial, and two
/// flanking minarets. Drawn flat in a single low-opacity color so it reads as
/// a "shadow within shadows" rather than a detailed illustration.
class MosqueSilhouettePainter extends CustomPainter {
  final Color color;

  const MosqueSilhouettePainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = color..style = PaintingStyle.fill;
    final cx = size.width / 2;
    final baseY = size.height * 0.96;
    final baseW = math.min(size.width * 0.72, 340.0);
    final baseH = 26.0;

    // Base platform
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(
          center: Offset(cx, baseY - baseH / 2),
          width: baseW,
          height: baseH,
        ),
        const Radius.circular(6),
      ),
      paint,
    );

    // Central dome
    final domeR = baseW * 0.22;
    final domeCy = baseY - baseH;
    canvas.drawArc(
      Rect.fromCenter(
        center: Offset(cx, domeCy),
        width: domeR * 2,
        height: domeR * 2,
      ),
      math.pi,
      math.pi,
      true,
      paint,
    );
    // Dome finial
    canvas.drawRect(
      Rect.fromCenter(
        center: Offset(cx, domeCy - domeR - 6),
        width: 3,
        height: 12,
      ),
      paint,
    );

    // Flanking minarets
    final minaretW = baseW * 0.05;
    final minaretTop = baseY - baseH - baseW * 0.42;
    for (final dir in const [-1.0, 1.0]) {
      final mCx = cx + dir * baseW * 0.36;
      canvas.drawRect(
        Rect.fromCenter(
          center: Offset(mCx, (baseY - baseH + minaretTop) / 2),
          width: minaretW,
          height: baseY - baseH - minaretTop,
        ),
        paint,
      );
      // Minaret cap
      canvas.drawCircle(Offset(mCx, minaretTop), minaretW * 1.1, paint);
      // Minaret finial
      canvas.drawRect(
        Rect.fromCenter(
          center: Offset(mCx, minaretTop - minaretW * 1.1 - 4),
          width: 2,
          height: 8,
        ),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => false;
}
