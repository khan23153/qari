import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/material.dart';

/// Local storage service for app preferences and onboarding state.
class LocalStorageService {
  LocalStorageService._();
  static final LocalStorageService instance = LocalStorageService._();

  late SharedPreferences _prefs;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // Onboarding
  bool get hasOnboarded => _prefs.getBool('has_onboarded') ?? false;
  Future<void> setOnboarded(bool value) => _prefs.setBool('has_onboarded', value);

  // Language
  String get appLanguage => _prefs.getString('app_language') ?? 'hi_latn';
  Future<void> setAppLanguage(String lang) => _prefs.setString('app_language', lang);

  // Starting path
  String get startingPath => _prefs.getString('starting_path') ?? 'foundation';
  Future<void> setStartingPath(String path) => _prefs.setString('starting_path', path);

  // Theme
  ThemeMode get themeMode {
    final theme = _prefs.getString('theme') ?? 'system';
    return switch (theme) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      'high_contrast' => ThemeMode.light, // handled separately
      _ => ThemeMode.system,
    };
  }
  Future<void> setTheme(String theme) => _prefs.setString('theme', theme);

  // Font scale
  double get fontScale => _prefs.getDouble('font_scale') ?? 1.0;
  Future<void> setFontScale(double scale) => _prefs.setDouble('font_scale', scale);

  // Preferred qari
  int get preferredQari => _prefs.getInt('preferred_qari') ?? 1;
  Future<void> setPreferredQari(int qariId) => _prefs.setInt('preferred_qari', qariId);

  // Auth token
  String? get authToken => _prefs.getString('auth_token');
  Future<void> setAuthToken(String token) => _prefs.setString('auth_token', token);
  Future<void> clearAuthToken() => _prefs.remove('auth_token');

  // Audio consent
  bool get audioTrainingConsent => _prefs.getBool('audio_consent') ?? false;
  Future<void> setAudioTrainingConsent(bool value) =>
      _prefs.setBool('audio_consent', value);
}
