/// App-wide constants for Qari.
class AppConstants {
  AppConstants._();

  // API
  static const String coreApiBaseUrl = String.fromEnvironment(
    'CORE_API_BASE_URL',
    defaultValue: 'http://localhost:8000/v1',
  );
  static const String recitationApiBaseUrl = String.fromEnvironment(
    'RECITATION_API_BASE_URL',
    defaultValue: 'http://localhost:8001/v1',
  );

  // Languages
  static const List<String> supportedLanguages = ['en', 'ur', 'hi_latn'];
  static const String defaultLanguage = 'hi_latn';

  // Quran
  static const int totalSurahs = 114;
  static const int mvpJuz = 30;
  static const int mvpSurahStart = 78; // An-Naba (Juz 30 start)
  static const int mvpSurahEnd = 114;
  static const int fatihahSurah = 1;

  // Audio
  static const int sampleRate = 16000;
  static const int maxRecitationDurationSec = 60;

  // SRS
  static const int flashcardSessionCap = 20;
  static const int flashcardDailyCap = 20;

  // UI
  static const double minArabicFontSize = 22.0;
  static const double maxArabicFontSize = 40.0;
  static const double defaultFontScale = 1.0;

  // Grammar color-coding (pos_group → color)
  static const Map<String, GrammarColor> grammarColors = {
    'fil': GrammarColor(color: Color(0xFF4CAF50), underline: UnderlineStyle.solid),  // green
    'ism': GrammarColor(color: Color(0xFF2196F3), underline: UnderlineStyle.none),    // blue
    'harf': GrammarColor(color: Color(0xFFFFC107), underline: UnderlineStyle.dotted), // amber
  };
}

enum UnderlineStyle { none, solid, dotted }

class GrammarColor {
  final Color color;
  final UnderlineStyle underline;
  const GrammarColor({required this.color, required this.underline});
}
