import 'package:flutter/material.dart';

/// Central configuration for the Qari app.
class AppConstants {
  AppConstants._();

  // ─── API ────────────────────────────────────────────────────────────────
  static const String baseUrl = 'http://20.244.30.169/v1';
  static const String audioCdnUrl = 'https://audio.qari.app';
  static const int apiTimeoutSeconds = 30;

  // ─── Supported Languages ────────────────────────────────────────────────
  static const List<AppLanguage> supportedLanguages = [
    AppLanguage(
      code: 'en',
      name: 'English',
      nativeName: 'English',
      script: 'Latin',
      textDirection: TextDirection.ltr,
      locale: Locale('en'),
    ),
    AppLanguage(
      code: 'ur',
      name: 'Urdu',
      nativeName: 'اردو',
      script: 'Nastaliq',
      textDirection: TextDirection.rtl,
      locale: Locale('ur'),
    ),
    AppLanguage(
      code: 'ar',
      name: 'Arabic',
      nativeName: 'العربية',
      script: 'Arabic',
      textDirection: TextDirection.rtl,
      locale: Locale('ar'),
    ),
  ];

  static List<Locale> get supportedLocales =>
      supportedLanguages.map((l) => l.locale).toList();

  /// Resolves a stored language code to its [Locale], defaulting to English.
  static Locale localeForCode(String? code) {
    if (code == null) return const Locale('en');
    final match = supportedLanguages.where((l) => l.code == code);
    return match.isNotEmpty ? match.first.locale : const Locale('en');
  }

  // ─── Quran ──────────────────────────────────────────────────────────────
  static const int totalSurahs = 114;
  static const int totalAyahs = 6236;
  static const int bismillahAyahNumber = 0;
  static const String bismillahText = 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ';

  // Arabic font
  static const String arabicFontFamily = 'KFGQPCUthmanicHafs';
  static const double arabicFontMinSize = 22.0;
  static const double arabicFontMaxSize = 40.0;
  static const double arabicFontDefaultSize = 28.0;

  // UI font
  static const String uiFontFamily = 'NotoSans';
  static const String urduFontFamily = 'NotoNastaliqUrdu';
  // Arabic UI font (clean sans for buttons/menus/labels). The bundled
  // Uthmanic font (arabicFontFamily) is reserved for actual Quran text.
  static const String arabicUiFontFamily = 'NotoSansArabic';

  // ─── Grammar Color Coding ───────────────────────────────────────────────
  /// pos_group -> (color, underlineStyle)
  /// Fi'l (verb) = green + solid underline
  /// Ism (noun) = blue + no underline
  /// Harf (particle) = amber + dotted underline
  static const Map<String, GrammarColorConfig> grammarColors = {
    'fil': GrammarColorConfig(
      posGroup: 'fil',
      label: "Fi'l",
      labelUrdu: 'فعل',
      color: Color(0xFF2E7D32),
      underlineStyle: UnderlineStyle.solid,
    ),
    'ism': GrammarColorConfig(
      posGroup: 'ism',
      label: 'Ism',
      labelUrdu: 'اسم',
      color: Color(0xFF1565C0),
      underlineStyle: UnderlineStyle.none,
    ),
    'harf': GrammarColorConfig(
      posGroup: 'harf',
      label: 'Harf',
      labelUrdu: 'حرف',
      color: Color(0xFFFF8F00),
      underlineStyle: UnderlineStyle.dotted,
    ),
    'ism_mudaf': GrammarColorConfig(
      posGroup: 'ism_mudaf',
      label: 'Ism (Mudaf)',
      labelUrdu: 'اسم (مضاف)',
      color: Color(0xFF1565C0),
      underlineStyle: UnderlineStyle.none,
    ),
    'fiil_madi': GrammarColorConfig(
      posGroup: 'fiil_madi',
      label: "Fi'l Madi",
      labelUrdu: 'فعل ماضی',
      color: Color(0xFF2E7D32),
      underlineStyle: UnderlineStyle.solid,
    ),
    'fiil_mudari': GrammarColorConfig(
      posGroup: 'fiil_mudari',
      label: "Fi'l Mudari'",
      labelUrdu: 'فعل مضارع',
      color: Color(0xFF2E7D32),
      underlineStyle: UnderlineStyle.solid,
    ),
    'fiil_amr': GrammarColorConfig(
      posGroup: 'fiil_amr',
      label: "Fi'l Amr",
      labelUrdu: 'فعل امر',
      color: Color(0xFF2E7D32),
      underlineStyle: UnderlineStyle.solid,
    ),
    'harf_jarr': GrammarColorConfig(
      posGroup: 'harf_jarr',
      label: 'Harf Jarr',
      labelUrdu: 'حرف جر',
      color: Color(0xFFFF8F00),
      underlineStyle: UnderlineStyle.dotted,
    ),
    'harf_nasb': GrammarColorConfig(
      posGroup: 'harf_nasb',
      label: 'Harf Nasb',
      labelUrdu: 'حرف نصب',
      color: Color(0xFFFF8F00),
      underlineStyle: UnderlineStyle.dotted,
    ),
    'default': GrammarColorConfig(
      posGroup: 'default',
      label: 'Other',
      labelUrdu: 'دیگر',
      color: Color(0xFF616161),
      underlineStyle: UnderlineStyle.none,
    ),
  };

  // ─── Tajweed Colors ─────────────────────────────────────────────────────
  static const Map<String, Color> tajweedColors = {
    'idgham': Color(0xFF7B1FA2),
    'ghunnah': Color(0xFF00838F),
    'iqlab': Color(0xFFEF6C00),
    'ikhfa': Color(0xFFAD1457),
    'qalqalah': Color(0xFF37474F),
    'madd': Color(0xFF1B5E20),
    'madd_wajib': Color(0xFF1B5E20),
    'madd_jaiz': Color(0xFF2E7D32),
    'silent': Color(0xFF9E9E9E),
    'normal': Color(0xFF212121),
  };

  // ─── Audio ──────────────────────────────────────────────────────────────
  static const List<double> supportedPlaybackSpeeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
  static const double defaultPlaybackSpeed = 1.0;
  static const List<String> availableReciters = [
    'abdul_basit',
    'sudais',
    'minshawi',
    'husary',
    'afasy',
  ];

  // ─── SRS (Spaced Repetition) ────────────────────────────────────────────
  static const int sm2GradeBhoolGaya = 1;   // Again
  static const int sm2GradeMushkil = 3;     // Hard
  static const int sm2GradeAasaan = 5;      // Easy
  static const int flashcardSessionCap = 20;
  static const double sm2InitialEase = 2.5;
  static const int sm2InitialInterval = 1;

  // ─── Recitation ─────────────────────────────────────────────────────────
  static const int maxRecordingDurationSeconds = 120;
  static const int recitationPollIntervalMs = 2000;
  static const int recitationMaxPollAttempts = 60;
  static const double minConfidenceThreshold = 0.55;
  static const double maxNoiseThreshold = 0.35;

  // ─── Scholar ────────────────────────────────────────────────────────────
  static const int maxScholarAudioSeconds = 120;
  static const List<String> scholarTopics = [
    'Tajweed',
    'Qirat',
    'Meaning / Tafsir',
    'Arabic Grammar',
    'Pronunciation',
    'Other',
  ];

  // ─── UI ─────────────────────────────────────────────────────────────────
  static const int bottomNavTabCount = 4;
  static const double bottomNavElevation = 8.0;
  static const double cardBorderRadius = 24.0;
  static const double sheetBorderRadius = 24.0;
}

/// Represents a supported app language.
class AppLanguage {
  final String code;
  final String name;
  final String nativeName;
  final String script;
  final TextDirection textDirection;
  final Locale locale;

  const AppLanguage({
    required this.code,
    required this.name,
    required this.nativeName,
    required this.script,
    required this.textDirection,
    required this.locale,
  });
}

/// Underline style for grammar color-coding (color-blind accessible).
enum UnderlineStyle { none, solid, dotted }

/// Configuration for a grammar part-of-speech group.
class GrammarColorConfig {
  final String posGroup;
  final String label;
  final String labelUrdu;
  final Color color;
  final UnderlineStyle underlineStyle;

  const GrammarColorConfig({
    required this.posGroup,
    required this.label,
    required this.labelUrdu,
    required this.color,
    required this.underlineStyle,
  });
}

/// Learning path types.
enum LearningPath { foundation, quranDirect }

/// App theme types.
enum AppThemeMode { light, dark, highContrast }

/// Recitation state machine states.
enum RecitationState {
  idle,
  listening,
  recording,
  analyzing,
  results,
  errorMicDenied,
  errorTooNoisy,
  errorLowConfidence,
  errorAnalysisFailed,
}
