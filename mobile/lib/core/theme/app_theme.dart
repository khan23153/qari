import 'package:flutter/material.dart';
import '../constants/app_constants.dart';

/// Centralized theme definitions for the Qari app.
/// Supports Light, Dark (AMOLED black), and High-contrast themes.
/// All themes meet WCAG AA minimum contrast ratios.
class AppTheme {
  AppTheme._();

  // ─── Color Palettes ─────────────────────────────────────────────────────

  static const Color _primaryLight = Color(0xFF1B5E20);
  static const Color _primaryDark = Color(0xFF66BB6A);
  static const Color _primaryHighContrast = Color(0xFF00E676);
  static const Color _secondaryLight = Color(0xFFD32F2F);
  static const Color _secondaryDark = Color(0xFFEF5350);
  static const Color _secondaryHighContrast = Color(0xFFFF1744);

  // ─── Light Theme ────────────────────────────────────────────────────────
  static ThemeData get lightTheme => ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        primaryColor: _primaryLight,
        scaffoldBackgroundColor: const Color(0xFFFAFAFA),
        colorScheme: const ColorScheme.light(
          primary: _primaryLight,
          onPrimary: Colors.white,
          secondary: _secondaryLight,
          onSecondary: Colors.white,
          surface: Colors.white,
          onSurface: Color(0xFF1C1B1F),
          error: Color(0xFFB3261E),
          onError: Colors.white,
          outline: Color(0xFF79747E),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Color(0xFF1C1B1F),
          elevation: 0,
          centerTitle: true,
          titleTextStyle: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w600,
            color: Color(0xFF1C1B1F),
          ),
        ),
        cardTheme: CardTheme(
          elevation: 1,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
          ),
          color: Colors.white,
          surfaceTintColor: Colors.transparent,
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Colors.white,
          selectedItemColor: _primaryLight,
          unselectedItemColor: Color(0xFF757575),
          type: BottomNavigationBarType.fixed,
          elevation: AppConstants.bottomNavElevation,
        ),
        dividerTheme: const DividerThemeData(
          color: Color(0xFFE0E0E0),
          thickness: 1,
        ),
        textTheme: _buildTextTheme(Brightness.light),
        inputDecorationTheme: _buildInputTheme(Brightness.light),
        bottomSheetTheme: BottomSheetThemeData(
          backgroundColor: Colors.white,
          modalBackgroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(
              top: Radius.circular(AppConstants.sheetBorderRadius),
            ),
          ),
        ),
        sliderTheme: SliderThemeData(
          activeTrackColor: _primaryLight,
          inactiveTrackColor: _primaryLight.withValues(alpha: 0.2),
          thumbColor: _primaryLight,
          overlayColor: _primaryLight.withValues(alpha: 0.12),
        ),
        progressIndicatorTheme: const ProgressIndicatorThemeData(
          color: _primaryLight,
          linearTrackColor: Color(0xFFE8F5E9),
        ),
      );

  // ─── Dark Theme (AMOLED Black) ──────────────────────────────────────────
  static ThemeData get darkTheme => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        primaryColor: _primaryDark,
        scaffoldBackgroundColor: Colors.black,
        colorScheme: const ColorScheme.dark(
          primary: _primaryDark,
          onPrimary: Colors.black,
          secondary: _secondaryDark,
          onSecondary: Colors.black,
          surface: Color(0xFF121212),
          onSurface: Color(0xFFE6E1E5),
          error: Color(0xFFF2B8B5),
          onError: Colors.black,
          outline: Color(0xFF938F99),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.black,
          foregroundColor: Color(0xFFE6E1E5),
          elevation: 0,
          centerTitle: true,
          titleTextStyle: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w600,
            color: Color(0xFFE6E1E5),
          ),
        ),
        cardTheme: CardTheme(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
          ),
          color: const Color(0xFF1E1E1E),
          surfaceTintColor: Colors.transparent,
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Colors.black,
          selectedItemColor: _primaryDark,
          unselectedItemColor: Color(0xFF757575),
          type: BottomNavigationBarType.fixed,
          elevation: AppConstants.bottomNavElevation,
        ),
        dividerTheme: const DividerThemeData(
          color: Color(0xFF333333),
          thickness: 1,
        ),
        textTheme: _buildTextTheme(Brightness.dark),
        inputDecorationTheme: _buildInputTheme(Brightness.dark),
        bottomSheetTheme: BottomSheetThemeData(
          backgroundColor: const Color(0xFF1E1E1E),
          modalBackgroundColor: const Color(0xFF1E1E1E),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(
              top: Radius.circular(AppConstants.sheetBorderRadius),
            ),
          ),
        ),
        sliderTheme: SliderThemeData(
          activeTrackColor: _primaryDark,
          inactiveTrackColor: _primaryDark.withValues(alpha: 0.2),
          thumbColor: _primaryDark,
          overlayColor: _primaryDark.withValues(alpha: 0.12),
        ),
        progressIndicatorTheme: const ProgressIndicatorThemeData(
          color: _primaryDark,
          linearTrackColor: Color(0xFF1B3A1B),
        ),
      );

  // ─── High-Contrast Theme ────────────────────────────────────────────────
  static ThemeData get highContrastTheme => ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        primaryColor: Colors.black,
        scaffoldBackgroundColor: Colors.white,
        colorScheme: const ColorScheme.light(
          primary: Colors.black,
          onPrimary: Colors.white,
          secondary: Color(0xFFD32F2F),
          onSecondary: Colors.white,
          surface: Colors.white,
          onSurface: Colors.black,
          error: Color(0xFFB71C1C),
          onError: Colors.white,
          outline: Colors.black,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black,
          elevation: 0,
          centerTitle: true,
          titleTextStyle: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w700,
            color: Colors.black,
          ),
        ),
        cardTheme: CardTheme(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
            side: const BorderSide(color: Colors.black, width: 2),
          ),
          color: Colors.white,
          surfaceTintColor: Colors.transparent,
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Colors.white,
          selectedItemColor: Colors.black,
          unselectedItemColor: Color(0xFF666666),
          type: BottomNavigationBarType.fixed,
          elevation: 0,
        ),
        dividerTheme: const DividerThemeData(
          color: Colors.black,
          thickness: 2,
        ),
        textTheme: _buildHighContrastTextTheme(),
        inputDecorationTheme: _buildInputTheme(Brightness.light, highContrast: true),
        bottomSheetTheme: BottomSheetThemeData(
          backgroundColor: Colors.white,
          modalBackgroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(
              top: Radius.circular(AppConstants.sheetBorderRadius),
            ),
            side: const BorderSide(color: Colors.black, width: 2),
          ),
        ),
        sliderTheme: const SliderThemeData(
          activeTrackColor: Colors.black,
          inactiveTrackColor: Color(0xFFCCCCCC),
          thumbColor: Colors.black,
        ),
        progressIndicatorTheme: const ProgressIndicatorThemeData(
          color: Colors.black,
          linearTrackColor: Color(0xFFCCCCCC),
        ),
      );

  // ─── Text Themes ────────────────────────────────────────────────────────
  static TextTheme _buildTextTheme(Brightness brightness) {
    final baseColor =
        brightness == Brightness.light ? const Color(0xFF1C1B1F) : const Color(0xFFE6E1E5);
    return TextTheme(
      displayLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.w700, color: baseColor),
      displayMedium: TextStyle(fontSize: 28, fontWeight: FontWeight.w600, color: baseColor),
      displaySmall: TextStyle(fontSize: 24, fontWeight: FontWeight.w600, color: baseColor),
      headlineLarge: TextStyle(fontSize: 22, fontWeight: FontWeight.w600, color: baseColor),
      headlineMedium: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: baseColor),
      headlineSmall: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: baseColor),
      titleLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: baseColor),
      titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: baseColor),
      titleSmall: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: baseColor),
      bodyLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, color: baseColor),
      bodyMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.w400, color: baseColor),
      bodySmall: TextStyle(fontSize: 12, fontWeight: FontWeight.w400, color: baseColor.withValues(alpha: 0.8)),
      labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: baseColor),
      labelMedium: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: baseColor),
      labelSmall: TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: baseColor.withValues(alpha: 0.7)),
    );
  }

  static TextTheme _buildHighContrastTextTheme() {
    return TextTheme(
      displayLarge: const TextStyle(fontSize: 32, fontWeight: FontWeight.w800, color: Colors.black),
      displayMedium: const TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: Colors.black),
      displaySmall: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: Colors.black),
      headlineLarge: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: Colors.black),
      headlineMedium: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: Colors.black),
      headlineSmall: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: Colors.black),
      titleLarge: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: Colors.black),
      titleMedium: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Colors.black),
      titleSmall: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.black),
      bodyLarge: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: Colors.black),
      bodyMedium: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: Colors.black),
      bodySmall: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Color(0xFF333333)),
      labelLarge: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: Colors.black),
      labelMedium: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.black),
      labelSmall: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Color(0xFF333333)),
    );
  }

  // ─── Input Decoration ───────────────────────────────────────────────────
  static InputDecorationTheme _buildInputTheme(Brightness brightness,
      {bool highContrast = false}) {
    final outlineColor = highContrast
        ? Colors.black
        : brightness == Brightness.light
            ? const Color(0xFF79747E)
            : const Color(0xFF938F99);
    return InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: outlineColor, width: highContrast ? 2 : 1),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: outlineColor, width: highContrast ? 2 : 1),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(
          color: highContrast ? Colors.black : _primaryLight,
          width: 2,
        ),
      ),
      filled: true,
      fillColor: highContrast
          ? Colors.white
          : brightness == Brightness.light
              ? const Color(0xFFF5F5F5)
              : const Color(0xFF2C2C2C),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    );
  }

  // ─── Grammar Color Helpers ──────────────────────────────────────────────

  /// Gets the [GrammarColorConfig] for a given pos_group string.
  /// Falls back to 'default' if not found.
  static GrammarColorConfig getGrammarConfig(String posGroup) {
    return AppConstants.grammarColors[posGroup] ??
        AppConstants.grammarColors['default']!;
  }

  /// Gets the [Color] for a pos_group.
  static Color getGrammarColor(String posGroup) {
    return getGrammarConfig(posGroup).color;
  }

  /// Gets the [UnderlineStyle] for a pos_group.
  static UnderlineStyle getGrammarUnderline(String posGroup) {
    return getGrammarConfig(posGroup).underlineStyle;
  }

  /// Gets the tajweed [Color] for a tajweed rule key.
  static Color getTajweedColor(String rule) {
    return AppConstants.tajweedColors[rule] ??
        AppConstants.tajweedColors['normal']!;
  }

  /// Builds a [TextDecoration] from an [UnderlineStyle].
  static TextDecoration toTextDecoration(UnderlineStyle style) {
    switch (style) {
      case UnderlineStyle.solid:
        return TextDecoration.underline;
      case UnderlineStyle.dotted:
        return TextDecoration.underline;
      case UnderlineStyle.none:
        return TextDecoration.none;
    }
  }

  /// Builds a [Paint] for custom underline rendering (dotted style).
  static Paint? buildUnderlinePaint(UnderlineStyle style, Color color) {
    if (style == UnderlineStyle.none) return null;
    return Paint()
      ..color = color
      ..strokeWidth = style == UnderlineStyle.dotted ? 1.5 : 2.0
      ..style = PaintingStyle.stroke;
  }

  // ─── Arabic Text Style ──────────────────────────────────────────────────

  /// Returns a [TextStyle] for Arabic Quran text at a given scale.
  static TextStyle arabicTextStyle({
    double fontSize = AppConstants.arabicFontDefaultSize,
    Color? color,
    FontWeight fontWeight = FontWeight.w400,
    TextDecoration decoration = TextDecoration.none,
    Color? decorationColor,
    TextDecorationStyle decorationStyle = TextDecorationStyle.solid,
    double letterSpacing = 0,
  }) {
    return TextStyle(
      fontFamily: AppConstants.arabicFontFamily,
      fontSize: fontSize.clamp(
        AppConstants.arabicFontMinSize,
        AppConstants.arabicFontMaxSize,
      ),
      height: 1.8,
      color: color,
      fontWeight: fontWeight,
      decoration: decoration,
      decorationColor: decorationColor,
      decorationStyle: decorationStyle,
      decorationThickness: 2.0,
      letterSpacing: letterSpacing,
    );
  }

  /// Returns a [TextStyle] for Urdu text using Nastaliq font.
  static TextStyle urduTextStyle({
    double fontSize = 18,
    Color? color,
    FontWeight fontWeight = FontWeight.w400,
  }) {
    return TextStyle(
      fontFamily: AppConstants.urduFontFamily,
      fontSize: fontSize,
      height: 2.0,
      color: color,
      fontWeight: fontWeight,
    );
  }
}
