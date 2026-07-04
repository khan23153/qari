import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// App theme definitions — Light, Dark (AMOLED), High-contrast.
class AppTheme {
  AppTheme._();

  static const Color _primaryGreen = Color(0xFF2E7D32);
  static const Color _primaryGreenLight = Color(0xFF4CAF50);
  static const Color _accentGold = Color(0xFFFFB300);
  static const Color _arabicBlue = Color(0xFF1565C0);
  static const Color _harfAmber = Color(0xFFFFC107);

  static ThemeData get lightTheme => ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: ColorScheme.fromSeed(
      seedColor: _primaryGreen,
      brightness: Brightness.light,
    ),
    textTheme: GoogleFonts.notoSansTextTheme(),
    appBarTheme: const AppBarTheme(
      centerTitle: true,
      elevation: 0,
    ),
    cardTheme: CardThemeData(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      type: BottomNavigationBarType.fixed,
      selectedItemColor: _primaryGreen,
    ),
  );

  static ThemeData get darkTheme => ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorScheme: ColorScheme.fromSeed(
      seedColor: _primaryGreen,
      brightness: Brightness.dark,
    ),
    scaffoldBackgroundColor: Colors.black, // AMOLED black
    textTheme: GoogleFonts.notoSansTextTheme(ThemeData.dark().textTheme),
    appBarTheme: const AppBarTheme(
      centerTitle: true,
      elevation: 0,
      backgroundColor: Colors.black,
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      color: const Color(0xFF1A1A1A),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
  );

  static ThemeData get highContrastTheme => ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: const ColorScheme.highContrastLight(
      primary: Colors.black,
      onPrimary: Colors.white,
      surface: Colors.white,
      onSurface: Colors.black,
    ),
    textTheme: GoogleFonts.notoSansTextTheme().copyWith(
      bodyLarge: const TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
      bodyMedium: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
    ),
  );

  /// Grammar color-coding helpers
  static Color grammarColor(String posGroup) {
    return switch (posGroup) {
      'fil' => _primaryGreenLight,  // verb = green
      'ism' => _arabicBlue,          // noun = blue
      'harf' => _harfAmber,          // particle = amber
      _ => Colors.grey,
    };
  }
}
