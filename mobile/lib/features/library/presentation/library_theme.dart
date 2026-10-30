import 'package:flutter/material.dart';

import '../../../core/utils/arabic_text_utils.dart';
import '../../recitation/presentation/mushaf/mushaf_theme.dart';
import '../data/library_models.dart';
import '../data/library_repository.dart';

/// What every library screen needs. Passed explicitly to each route and sheet
/// because pushed routes and modal sheets do NOT inherit widgets placed inside
/// the page that opened them (the cause of the dark-sheet-on-cream bugs).
class LibraryEnv {
  LibraryEnv({required this.repository, required this.themeController});

  final LibraryRepository repository;

  /// The same persisted paper preset the Mushaf uses (Classic, Night,
  /// Parchment, Minimal), so Light / Sepia / Dark stay consistent app-wide.
  final MushafThemeController themeController;

  LibraryPalette get palette => LibraryPalette(themeController.theme);
}

/// Colour tokens for library UI, derived from the active [MushafTheme].
///
/// Semantic hues (grades, narrator reliability) have one light-paper and one
/// dark-paper variant, chosen so text on a [badge] tint stays >= 4.5:1 and a
/// reliability stripe stays >= 3:1 on every preset (see library_theme_test).
@immutable
class LibraryPalette {
  const LibraryPalette(this.mushaf);

  final MushafTheme mushaf;

  bool get isDark => mushaf.isDark;
  Color get paper => mushaf.background;
  Color get ink => mushaf.text;
  Color get muted => mushaf.text.withValues(alpha: 0.72);
  Color get accent => mushaf.accent;
  Color get border => mushaf.border;
  Color get onAccent => isDark ? const Color(0xFF1A1409) : Colors.white;

  /// A raised surface: a faint ink tint over the paper, never a fixed block.
  Color get card => Color.alphaBlend(
        mushaf.text.withValues(alpha: isDark ? 0.07 : 0.05),
        mushaf.background,
      );

  static const _light = {
    'sahih': Color(0xFF14572E),
    'hasan': Color(0xFF094A70),
    'daif': Color(0xFF703800),
    'mawdu': Color(0xFF8C1C15),
    'sahabi': Color(0xFF52367D),
  };
  static const _dark = {
    'sahih': Color(0xFF7FD9A0),
    'hasan': Color(0xFF8CC8F0),
    'daif': Color(0xFFF2B66D),
    'mawdu': Color(0xFFFF8A80),
    'sahabi': Color(0xFFC9A8FF),
  };

  Color _hue(String key) => (isDark ? _dark : _light)[key]!;

  Color ruling(RulingType type) => switch (type) {
        RulingType.sahih => _hue('sahih'),
        RulingType.hasan => _hue('hasan'),
        RulingType.daif => _hue('daif'),
        RulingType.mawdu => _hue('mawdu'),
        RulingType.other => muted,
      };

  Color reliability(Reliability r) => switch (r) {
        Reliability.prophet => accent,
        Reliability.compiler => muted,
        Reliability.sahabi => _hue('sahabi'),
        Reliability.thiqah => _hue('sahih'),
        Reliability.saduq => _hue('hasan'),
        Reliability.daif => _hue('daif'),
        Reliability.matruk || Reliability.kadhdhab => _hue('mawdu'),
        Reliability.unknown => muted,
      };

  /// Tinted background for a chip/badge in [color].
  Color badge(Color color) => Color.alphaBlend(color.withValues(alpha: 0.12), card);

  ThemeData get themeData {
    final base = mushaf.toThemeData();
    return base.copyWith(
      cardColor: card,
      iconTheme: IconThemeData(color: ink),
      listTileTheme: ListTileThemeData(iconColor: muted, textColor: ink),
      tabBarTheme: TabBarThemeData(
        labelColor: ink,
        unselectedLabelColor: muted,
        indicatorColor: accent,
        dividerColor: border,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: card,
        hintStyle: TextStyle(color: muted),
        prefixIconColor: muted,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: accent, width: 1.6),
        ),
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(color: accent),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(foregroundColor: ink),
      ),
    );
  }
}

/// Rebuilds [builder] under the library theme whenever the preset changes.
class LibraryThemed extends StatelessWidget {
  const LibraryThemed({super.key, required this.env, required this.builder});

  final LibraryEnv env;
  final Widget Function(BuildContext context, LibraryPalette palette) builder;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: env.themeController,
      builder: (context, _) {
        final palette = env.palette;
        return Theme(
          data: palette.themeData,
          child: Builder(builder: (context) => builder(context, palette)),
        );
      },
    );
  }
}

/// Arabic display text for hadith bodies.
const libraryArabicFont = 'KFGQPCUthmanicHafs';

/// A matn token reduced to bare letters, for matching gharib forms.
String bareArabicWord(String token) => ArabicTextUtils.removeTashkeel(token)
    .replaceAll(RegExp(r'[‎‏؜]'), '')
    .replaceAll(RegExp(r'[^ء-ي]'), '');

/// Whether a matn [token] carries one of the hadith's catalogued gharib
/// words, allowing a short leading clitic (و ف ب ل ال).
bool isGharibToken(String token, List<String> gharibWords) {
  final bare = bareArabicWord(token);
  if (bare.isEmpty) return false;
  for (final w in gharibWords) {
    if (bare == w) return true;
    if (bare.endsWith(w) && bare.length - w.length <= 3) return true;
  }
  return false;
}

String reliabilityLabel(Reliability r) => switch (r) {
      Reliability.prophet => 'The Prophet ﷺ',
      Reliability.compiler => 'Compiler',
      Reliability.sahabi => 'Sahabi · Companion',
      Reliability.thiqah => 'Thiqah · trustworthy',
      Reliability.saduq => 'Saduq · truthful',
      Reliability.daif => "Da'if · weak",
      Reliability.matruk => 'Matruk · abandoned',
      Reliability.kadhdhab => 'Kadhdhab · liar',
      Reliability.unknown => 'Not yet identified',
    };
