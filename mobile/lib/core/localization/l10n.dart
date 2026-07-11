import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../constants/app_constants.dart';
import '../providers.dart';

/// Lightweight, dependency-free localization for the three supported UI
/// languages: English (en), Urdu (ur), and Arabic (ar).
///
/// Use [tr] at any widget's build site to pick the right string for the
/// current app locale (read from [appLocaleProvider]). Missing translations
/// fall back to English.
///
/// Example:
/// ```dart
/// Text(tr(context, 'Home', ur: 'گھر', ar: 'الرئيسية'))
/// ```
String tr(BuildContext context, String en, {String? ur, String? ar}) {
  final code = _currentLanguageCode(context);
  switch (code) {
    case 'ar':
      return ar ?? ur ?? en;
    case 'ur':
      return ur ?? en;
    default:
      return en;
  }
}

/// Text direction for the active locale — RTL for Arabic and Urdu.
TextDirection appTextDirection(BuildContext context) {
  final code = _currentLanguageCode(context);
  return (code == 'ar' || code == 'ur') ? TextDirection.rtl : TextDirection.ltr;
}

/// Whether the active locale lays out right-to-left.
bool isAppRtl(BuildContext context) =>
    appTextDirection(context) == TextDirection.rtl;

/// The [AppLanguage] object for the active locale, or English if unknown.
AppLanguage currentAppLanguage(BuildContext context) {
  final code = _currentLanguageCode(context);
  final match = AppConstants.supportedLanguages.where((l) => l.code == code);
  return match.isNotEmpty ? match.first : AppConstants.supportedLanguages.first;
}

String _currentLanguageCode(BuildContext context) {
  try {
    final locale = ProviderScope.containerOf(context).read(appLocaleProvider);
    return locale.languageCode;
  } catch (_) {
    return 'en';
  }
}
