import 'package:shared_preferences/shared_preferences.dart';
import '../../core/constants/app_constants.dart';

/// Wrapper around SharedPreferences for persistent app settings.
/// Handles onboarding state, language, path, theme, font scale, qari,
/// auth token, and audio consent.
class LocalStorageService {
  static LocalStorageService? _instance;
  late SharedPreferences _prefs;

  LocalStorageService._();

  static Future<LocalStorageService> getInstance() async {
    if (_instance == null) {
      _instance = LocalStorageService._();
      _instance!._prefs = await SharedPreferences.getInstance();
    }
    return _instance!;
  }

  // For synchronous access in the app widget
  LocalStorageService() {
    _init();
  }

  Future<void> _init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // Ensure prefs are loaded
  Future<void> ensureInitialized() async {
    try {
      _prefs.getString('');
    } catch (_) {
      _prefs = await SharedPreferences.getInstance();
    }
  }

  // ─── Keys ────────────────────────────────────────────────────────────────
  static const _kOnboardingComplete = 'onboarding_complete';
  static const _kSelectedLanguage = 'selected_language';
  static const _kSelectedPath = 'selected_path';
  static const _kIsOnboarded = 'is_onboarded';
  static const _kThemeMode = 'theme_mode';
  static const _kFontScale = 'font_scale';
  static const _kSelectedQari = 'selected_qari';
  static const _kAuthToken = 'auth_token';
  static const _kAudioConsent = 'audio_consent';
  static const _kGrammarColorsEnabled = 'grammar_colors_enabled';
  static const _kTajweedColorsEnabled = 'tajweed_colors_enabled';
  static const _kDensityLevel = 'density_level';
  static const _kUserId = 'user_id';
  static const _kDailyGoal = 'daily_goal';
  static const _kStreakCount = 'streak_count';
  static const _kDataVersion = 'backend_data_version';

  // ─── Onboarding ──────────────────────────────────────────────────────────
  Future<bool> isOnboardingComplete() async {
    await ensureInitialized();
    return _prefs.getBool(_kOnboardingComplete) ?? false;
  }

  Future<void> setOnboardingComplete(bool value) async {
    await ensureInitialized();
    await _prefs.setBool(_kOnboardingComplete, value);
  }

  /// Whether the server-side onboarding (language + path) is finished.
  Future<bool> isOnboarded() async {
    await ensureInitialized();
    return _prefs.getBool(_kIsOnboarded) ?? false;
  }

  Future<void> setIsOnboarded(bool value) async {
    await ensureInitialized();
    await _prefs.setBool(_kIsOnboarded, value);
  }

  // ─── Language ────────────────────────────────────────────────────────────
  Future<String?> getSelectedLanguage() async {
    await ensureInitialized();
    return _prefs.getString(_kSelectedLanguage);
  }

  Future<void> setSelectedLanguage(String code) async {
    await ensureInitialized();
    await _prefs.setString(_kSelectedLanguage, code);
  }

  // ─── Learning Path ───────────────────────────────────────────────────────
  Future<String?> getSelectedPath() async {
    await ensureInitialized();
    return _prefs.getString(_kSelectedPath);
  }

  Future<void> setSelectedPath(String path) async {
    await ensureInitialized();
    await _prefs.setString(_kSelectedPath, path);
  }

  // ─── Theme ───────────────────────────────────────────────────────────────
  Future<String> getThemeMode() async {
    await ensureInitialized();
    return _prefs.getString(_kThemeMode) ?? 'system';
  }

  Future<void> setThemeMode(String mode) async {
    await ensureInitialized();
    await _prefs.setString(_kThemeMode, mode);
  }

  // ─── Font Scale ──────────────────────────────────────────────────────────
  Future<double> getFontScale() async {
    await ensureInitialized();
    return _prefs.getDouble(_kFontScale) ?? 1.0;
  }

  Future<void> setFontScale(double scale) async {
    await ensureInitialized();
    await _prefs.setDouble(_kFontScale, scale);
  }

  // ─── Qari (Reciter) ──────────────────────────────────────────────────────
  Future<String> getSelectedQari() async {
    await ensureInitialized();
    return _prefs.getString(_kSelectedQari) ?? 'abdul_basit';
  }

  Future<void> setSelectedQari(String qari) async {
    await ensureInitialized();
    await _prefs.setString(_kSelectedQari, qari);
  }

  // ─── Auth Token ──────────────────────────────────────────────────────────
  Future<String?> getAuthToken() async {
    await ensureInitialized();
    return _prefs.getString(_kAuthToken);
  }

  Future<void> setAuthToken(String? token) async {
    await ensureInitialized();
    if (token != null) {
      await _prefs.setString(_kAuthToken, token);
    } else {
      await _prefs.remove(_kAuthToken);
    }
  }

  // ─── Audio Consent ───────────────────────────────────────────────────────
  Future<bool> getAudioConsent() async {
    await ensureInitialized();
    return _prefs.getBool(_kAudioConsent) ?? false;
  }

  Future<void> setAudioConsent(bool value) async {
    await ensureInitialized();
    await _prefs.setBool(_kAudioConsent, value);
  }

  // ─── Grammar Colors ──────────────────────────────────────────────────────
  Future<bool> getGrammarColorsEnabled() async {
    await ensureInitialized();
    return _prefs.getBool(_kGrammarColorsEnabled) ?? true;
  }

  Future<void> setGrammarColorsEnabled(bool value) async {
    await ensureInitialized();
    await _prefs.setBool(_kGrammarColorsEnabled, value);
  }

  // ─── Tajweed Colors ──────────────────────────────────────────────────────
  Future<bool> getTajweedColorsEnabled() async {
    await ensureInitialized();
    return _prefs.getBool(_kTajweedColorsEnabled) ?? false;
  }

  Future<void> setTajweedColorsEnabled(bool value) async {
    await ensureInitialized();
    await _prefs.setBool(_kTajweedColorsEnabled, value);
  }

  // ─── Density Level ───────────────────────────────────────────────────────
  /// 0 = Arabic only, 1 = +translit, 2 = +word meaning, 3 = +full translation
  Future<int> getDensityLevel() async {
    await ensureInitialized();
    return _prefs.getInt(_kDensityLevel) ?? 1;
  }

  Future<void> setDensityLevel(int level) async {
    await ensureInitialized();
    await _prefs.setInt(_kDensityLevel, level);
  }

  // ─── User ID ─────────────────────────────────────────────────────────────
  Future<String?> getUserId() async {
    await ensureInitialized();
    return _prefs.getString(_kUserId);
  }

  Future<void> setUserId(String? id) async {
    await ensureInitialized();
    if (id != null) {
      await _prefs.setString(_kUserId, id);
    } else {
      await _prefs.remove(_kUserId);
    }
  }

  // ─── Daily Goal ──────────────────────────────────────────────────────────
  Future<int> getDailyGoal() async {
    await ensureInitialized();
    return _prefs.getInt(_kDailyGoal) ?? 5;
  }

  Future<void> setDailyGoal(int goal) async {
    await ensureInitialized();
    await _prefs.setInt(_kDailyGoal, goal);
  }

  // ─── Streak ──────────────────────────────────────────────────────────────
  Future<int> getStreakCount() async {
    await ensureInitialized();
    return _prefs.getInt(_kStreakCount) ?? 0;
  }

  Future<void> setStreakCount(int count) async {
    await ensureInitialized();
    await _prefs.setInt(_kStreakCount, count);
  }

  // ─── Backend data version ─────────────────────────────────────────────────
  /// Bumped on the backend whenever corpus/content changes. The app compares
  /// this against the release manifest so it can refresh cached content when
  /// the backend data changes (the "auto-update content" behaviour).
  Future<int> getBackendDataVersion() async {
    await ensureInitialized();
    return _prefs.getInt(_kDataVersion) ?? 0;
  }

  Future<void> setBackendDataVersion(int version) async {
    await ensureInitialized();
    await _prefs.setInt(_kDataVersion, version);
  }

  // ─── Clear All ───────────────────────────────────────────────────────────
  Future<void> clearAll() async {
    await ensureInitialized();
    await _prefs.clear();
  }
}
