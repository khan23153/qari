import 'dart:ui';

/// Utilities for Arabic text normalization and RTL handling.
class ArabicTextUtils {
  ArabicTextUtils._();

  /// Normalizes Arabic text by standardizing characters.
  /// Removes diacritics optionally, normalizes alef variants, etc.
  static String normalize(String text, {bool keepDiacritics = true}) {
    var result = text;

    if (!keepDiacritics) {
      // Remove harakat (diacritics)
      result = result
          .replaceAll(RegExp(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]'), '')
          .replaceAll('\u0640', ''); // Remove tatweel
    }

    // Normalize alef variants
    result = result
        .replaceAll('\u0622', '\u0627') // Alef madda -> alef
        .replaceAll('\u0623', '\u0627') // Alef hamza above -> alef
        .replaceAll('\u0625', '\u0627') // Alef hamza below -> alef
        .replaceAll('\u0671', '\u0627'); // Alef wasla -> alef

    // Normalize ya
    result = result.replaceAll('\u0649', '\u064A'); // Alef maksura -> ya

    // Normalize ta marbuta
    result = result.replaceAll('\u0629', '\u0647'); // Ta marbuta -> ha

    return result.trim();
  }

  /// Removes tashkeel (diacritics) from Arabic text.
  static String removeTashkeel(String text) {
    return text
        .replaceAll(RegExp(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]'), '')
        .trim();
  }

  /// Checks if a string contains Arabic characters.
  static bool containsArabic(String text) {
    return RegExp(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]').hasMatch(text);
  }

  /// Checks if a string is entirely Arabic (ignoring spaces and diacritics).
  static bool isArabic(String text) {
    final cleaned = text.replaceAll(RegExp(r'[\s\u0610-\u061A\u064B-\u065F]'), '');
    if (cleaned.isEmpty) return false;
    return RegExp(r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+$').hasMatch(cleaned);
  }

  /// Determines the text direction for a given string.
  /// Arabic text is always RTL; Latin text is LTR.
  static TextDirection getDirection(String text) {
    return containsArabic(text) ? TextDirection.rtl : TextDirection.ltr;
  }

  /// Converts a logical string to its visual (display) order using the
  /// Unicode Bidirectional Algorithm. For simple cases, Flutter handles
  /// this automatically; this is for manual processing.
  static String toVisualOrder(String text) {
    // Flutter's Text widget handles BiDi automatically via the engine.
    // For manual processing, we use the bidi algorithm.
    final bidi = Bidi.parse(text);
    return bidi.reorder(text);
  }

  /// Wraps a string with RTL markers for safe embedding in mixed-direction text.
  static String wrapRtl(String text) {
    return '\u202B$text\u202C'; // RLE ... PDF
  }

  /// Wraps a string with LTR markers for safe embedding in mixed-direction text.
  static String wrapLtr(String text) {
    return '\u202A$text\u202C'; // LRE ... PDF
  }

  /// Adds Arabic letter-spacing for Quran display (tashkeel spacing).
  static String addLetterSpacing(String text, {double spacing = 0}) {
    if (spacing <= 0) return text;
    // Insert zero-width spaces between characters for visual spacing
    // In practice, Flutter's letterSpacing handles this at the text level
    return text;
  }

  /// Extracts the root letters from a word (typically 3 letters).
  /// This is a simple heuristic; the backend provides authoritative roots.
  static String? extractRootHeuristic(String word) {
    final normalized = removeTashkeel(word);
    if (normalized.length < 3) return null;

    // Remove common prefixes (wa, al, bi, li, fa, etc.)
    var result = normalized;
    const prefixes = ['و', 'ال', 'ب', 'ل', 'ف', 'ك', 'س'];
    for (final prefix in prefixes) {
      if (result.startsWith(prefix) && result.length > prefix.length + 2) {
        result = result.substring(prefix.length);
        break;
      }
    }

    // Remove common suffixes (at, in, un, an, etc.)
    const suffixes = ['ات', 'ين', 'ون', 'ان', 'ة', 'ه', 'ي', 'ك', 'هم', 'هن'];
    for (final suffix in suffixes) {
      if (result.endsWith(suffix) && result.length > suffix.length + 2) {
        result = result.substring(0, result.length - suffix.length);
        break;
      }
    }

    // Take first 3 consonants as root (very rough heuristic)
    final consonants = result.replaceAll(RegExp(r'[ًٌٍَُِّْـ]'), '');
    if (consonants.length >= 3) {
      return consonants.substring(0, 3);
    }
    return consonants.isNotEmpty ? consonants : null;
  }

  /// Formats an ayah number with the traditional circle marker (۝).
  static String formatAyahEnd(int ayahNumber) {
    return '\u06DD${_toArabicNumerals(ayahNumber.toString())}';
  }

  /// Converts Western digits to Arabic-Indic digits.
  static String _toArabicNumerals(String input) {
    const western = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
    const arabic = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    var result = input;
    for (var i = 0; i < western.length; i++) {
      result = result.replaceAll(western[i], arabic[i]);
    }
    return result;
  }

  /// Converts Arabic-Indic digits to Western digits.
  static String toWesternNumerals(String input) {
    const western = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
    const arabic = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    var result = input;
    for (var i = 0; i < arabic.length; i++) {
      result = result.replaceAll(arabic[i], western[i]);
    }
    return result;
  }

  /// Builds a transliteration of Arabic text (romanization).
  /// This is a simple mapping; the backend provides authoritative transliteration.
  static String transliterate(String arabic) {
    const Map<String, String> map = {
      'ا': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'ḥ',
      'خ': 'kh', 'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z', 'س': 's',
      'ش': 'sh', 'ص': 'ṣ', 'ض': 'ḍ', 'ط': 'ṭ', 'ظ': 'ẓ', 'ع': 'ʿ',
      'غ': 'gh', 'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm',
      'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y', 'ى': 'a', 'ء': "'",
      'ة': 'h', 'َ': 'a', 'ُ': 'u', 'ِ': 'i', 'ً': 'an', 'ٌ': 'un',
      'ٍ': 'in', 'ّ': '', 'ْ': '', 'ـ': '',
    };
    var result = StringBuffer();
    for (final char in arabic.split('')) {
      result.write(map[char] ?? char);
    }
    return result.toString().trim();
  }
}

/// Minimal BiDi parser for visual reordering.
/// Flutter's text engine handles BiDi automatically; this is for
/// cases where manual reordering is needed (e.g., custom painting).
class Bidi {
  final List<int> _levels;

  Bidi._(this._levels);

  /// Parses a string and computes embedding levels.
  factory Bidi.parse(String text) {
    final levels = List<int>.filled(text.length, 0);
    var level = 0;
    for (var i = 0; i < text.length; i++) {
      if (ArabicTextUtils.containsArabic(text[i])) {
        level = 1;
      } else {
        level = 0;
      }
      levels[i] = level;
    }
    return Bidi._(levels);
  }

  /// Reorders characters based on embedding levels.
  String reorder(String text) {
    // Simple approach: group RTL and LTR runs
    final result = StringBuffer();
    final rtlBuffer = StringBuffer();

    for (var i = 0; i < text.length; i++) {
      if (_levels[i] == 1) {
        rtlBuffer.write(text[i]);
      } else {
        if (rtlBuffer.isNotEmpty) {
          result.write(_reverseRtl(rtlBuffer.toString()));
          rtlBuffer.clear();
        }
        result.write(text[i]);
      }
    }
    if (rtlBuffer.isNotEmpty) {
      result.write(_reverseRtl(rtlBuffer.toString()));
    }
    return result.toString();
  }

  String _reverseRtl(String text) {
    return String.fromCharCodes(text.runes.toList().reversed);
  }
}
