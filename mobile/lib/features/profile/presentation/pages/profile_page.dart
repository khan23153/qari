import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/serene_decorations.dart';
import '../../../../core/providers.dart';
import '../../../../data/services/local_storage_service.dart';
import '../../../../data/services/audio_service.dart';
import '../widgets/streak_calendar.dart';
import '../widgets/badges_grid.dart';
import '../widgets/settings_section.dart';
import 'attribution_page.dart';
import '../../../onboarding/presentation/pages/language_select_page.dart';
import '../../../auth/presentation/pages/login_page.dart';
import '../../../home/presentation/pages/home_page.dart';
import '../../../../data/repositories/user_repository.dart';

/// S11: Profile/Settings — streak calendar, badges grid, stats,
/// language switcher, qari picker, font-size slider with live Arabic preview,
/// theme, download manager, audio-consent toggle, attribution & licenses page.
class ProfilePage extends ConsumerStatefulWidget {
  const ProfilePage({super.key});

  @override
  ConsumerState<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends ConsumerState<ProfilePage> {
  String _selectedLanguage = 'en';
  String _selectedQari = 'abdul_basit';
  double _fontScale = 1.0;
  String _themeMode = 'system';
  bool _audioConsent = false;
  bool _grammarColors = true;
  bool _tajweedColors = false;

  // Stats — start at zero (fresh-user defaults) and are filled from the
  // server. We NEVER hardcode fake progress; mismatched numbers between the
  // Home and Profile screens came from hardcoded values here.
  String _displayName = 'Learner';
  bool _isLoadingStats = true;
  int _totalXp = 0;
  int _currentStreak = 0;
  int _lessonsCompleted = 0;
  int _ayahsRead = 0;
  int _flashcardsReviewed = 0;
  int _recitationSessions = 0;

  @override
  void initState() {
    super.initState();
    _loadSettings();
    _loadProfileAndStats();
  }

  /// Fetches the real profile + stats from the backend so the Profile screen
  /// shows the same source of truth as Home (zero for brand-new accounts,
  /// live numbers for returning users). Falls back to zeros on failure.
  Future<void> _loadProfileAndStats() async {
    try {
      final user = await UserRepository().getProfile();
      final stats = await UserRepository().getStats();
      if (mounted) {
        setState(() {
          _displayName = user.displayName?.isNotEmpty == true
              ? user.displayName!
              : 'Learner';
          _totalXp = stats.totalXp;
          _currentStreak = stats.currentStreak;
          _lessonsCompleted = stats.lessonsCompleted;
          _ayahsRead = stats.ayahsRead;
          _flashcardsReviewed = stats.flashcardsReviewed;
          _recitationSessions = stats.recitationSessions;
          _isLoadingStats = false;
        });
      }
    } catch (e) {
      debugPrint('Profile: failed to load profile/stats: $e');
      // Keep the zero defaults — never show fabricated progress.
      if (mounted) setState(() => _isLoadingStats = false);
    }
  }

  Future<void> _loadSettings() async {
    final storage = LocalStorageService();
    await storage.ensureInitialized();
    final lang = await storage.getSelectedLanguage();
    final qari = await storage.getSelectedQari();
    final fontScale = await storage.getFontScale();
    final theme = await storage.getThemeMode();
    final consent = await storage.getAudioConsent();
    final grammar = await storage.getGrammarColorsEnabled();
    final tajweed = await storage.getTajweedColorsEnabled();

    if (mounted) {
      setState(() {
        _selectedLanguage = lang ?? 'en';
        _selectedQari = qari;
        _fontScale = fontScale;
        _themeMode = theme;
        _audioConsent = consent;
        _grammarColors = grammar;
        _tajweedColors = tajweed;
      });
    }
  }

  Future<void> _updateLanguage(String code) async {
    await Haptics.vibrate(HapticsType.selection);
    setState(() => _selectedLanguage = code);
    final storage = LocalStorageService();
    await storage.setSelectedLanguage(code);

    // Update locale
    final lang = AppConstants.supportedLanguages.where((l) => l.code == code).first;
    ref.read(appLocaleProvider.notifier).state = lang.locale;
  }

  Future<void> _updateQari(String qari) async {
    await Haptics.vibrate(HapticsType.selection);
    setState(() => _selectedQari = qari);
    final storage = LocalStorageService();
    await storage.setSelectedQari(qari);
  }

  Future<void> _updateFontScale(double scale) async {
    setState(() => _fontScale = scale);
    final storage = LocalStorageService();
    await storage.setFontScale(scale);
  }

  Future<void> _updateTheme(String mode) async {
    await Haptics.vibrate(HapticsType.selection);
    setState(() => _themeMode = mode);
    final storage = LocalStorageService();
    await storage.setThemeMode(mode);

    ThemeMode themeMode;
    switch (mode) {
      case 'light':
        themeMode = ThemeMode.light;
        break;
      case 'dark':
        themeMode = ThemeMode.dark;
        break;
      case 'high_contrast':
        themeMode = ThemeMode.light; // High contrast uses light with custom colors
        break;
      default:
        themeMode = ThemeMode.system;
    }
    ref.read(themeModeProvider.notifier).state = themeMode;
  }

  Future<void> _toggleAudioConsent(bool value) async {
    await Haptics.vibrate(HapticsType.selection);
    setState(() => _audioConsent = value);
    final storage = LocalStorageService();
    await storage.setAudioConsent(value);
  }

  Future<void> _toggleGrammarColors(bool value) async {
    await Haptics.vibrate(HapticsType.selection);
    setState(() {
      _grammarColors = value;
      if (value) _tajweedColors = false;
    });
    final storage = LocalStorageService();
    await storage.setGrammarColorsEnabled(value);
    await storage.setTajweedColorsEnabled(_tajweedColors);
  }

  Future<void> _toggleTajweedColors(bool value) async {
    await Haptics.vibrate(HapticsType.selection);
    setState(() {
      _tajweedColors = value;
      if (value) _grammarColors = false;
    });
    final storage = LocalStorageService();
    await storage.setTajweedColorsEnabled(value);
    await storage.setGrammarColorsEnabled(_grammarColors);
  }

  Future<void> _resetLocalData() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Reset & Start Fresh?'),
        content: const Text(
          'This erases all your local progress, settings, and account data on '
          'this device and restarts onboarding from zero. This cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(dialogContext).colorScheme.error,
            ),
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Reset Everything'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    await Haptics.vibrate(HapticsType.success);
    final storage = LocalStorageService();
    await storage.clearAll();

    // Reset in-memory app state back to defaults.
    ref.read(appLocaleProvider.notifier).state = const Locale('en');
    ref.read(themeModeProvider.notifier).state = ThemeMode.system;

    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(
        builder: (_) => LoginPage(
          onAuthenticated: (result) {
            if (!mounted) return;
            Navigator.of(context).pushAndRemoveUntil(
              MaterialPageRoute(
                builder: (_) => result.isOnboarded
                    ? const HomePage()
                    : const LanguageSelectPage(),
              ),
              (route) => false,
            );
          },
        ),
      ),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SereneBackground(
        child: SafeArea(
          child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ─── Profile Header ─────────────────────────────────────
              _ProfileHeader(
                name: _displayName,
                totalXp: _totalXp,
                currentStreak: _currentStreak,
                isLoading: _isLoadingStats,
                theme: theme,
              ),

              const SizedBox(height: 24),

              // ─── Stats Grid ─────────────────────────────────────────
              _StatsGrid(
                lessonsCompleted: _lessonsCompleted,
                ayahsRead: _ayahsRead,
                flashcardsReviewed: _flashcardsReviewed,
                recitationSessions: _recitationSessions,
                theme: theme,
              ),

              const SizedBox(height: 24),

              // ─── Streak Calendar ────────────────────────────────────
              StreakCalendar(
                currentStreak: _currentStreak,
                theme: theme,
              ),

              const SizedBox(height: 24),

              // ─── Badges Grid ────────────────────────────────────────
              BadgesGrid(theme: theme),

              const SizedBox(height: 24),

              // ─── Settings Section ───────────────────────────────────
              SettingsSection(
                selectedLanguage: _selectedLanguage,
                onLanguageChanged: _updateLanguage,
                selectedQari: _selectedQari,
                onQariChanged: _updateQari,
                fontScale: _fontScale,
                onFontScaleChanged: _updateFontScale,
                themeMode: _themeMode,
                onThemeChanged: _updateTheme,
                audioConsent: _audioConsent,
                onAudioConsentChanged: _toggleAudioConsent,
                grammarColors: _grammarColors,
                onGrammarColorsChanged: _toggleGrammarColors,
                tajweedColors: _tajweedColors,
                onTajweedColorsChanged: _toggleTajweedColors,
                onResetLocalData: _resetLocalData,
                theme: theme,
              ),

              const SizedBox(height: 16),

              // ─── Attribution & Licenses ─────────────────────────────
              ListTile(
                leading: const Icon(Icons.description_outlined),
                title: const Text('Attribution & Licenses'),
                subtitle: const Text('Fonts, audio sources, and credits'),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const AttributionPage()),
                  );
                },
              ),

              const SizedBox(height: 16),

              // ─── Version ────────────────────────────────────────────
              Center(
                child: Text(
                  'Qari v1.0.0',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.3),
                  ),
                ),
              ),

              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
      ),
    );
  }
}

/// Profile header with avatar, name, and key stats.
class _ProfileHeader extends StatelessWidget {
  final String name;
  final int totalXp;
  final int currentStreak;
  final bool isLoading;
  final ThemeData theme;

  const _ProfileHeader({
    required this.name,
    required this.totalXp,
    required this.currentStreak,
    this.isLoading = false,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            theme.colorScheme.primary.withValues(alpha: 0.1),
            theme.colorScheme.primary.withValues(alpha: 0.03),
          ],
        ),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        children: [
          // Avatar
          Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              color: theme.colorScheme.primary,
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                name.isNotEmpty ? name[0].toUpperCase() : '?',
                style: const TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            name,
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 16),
          // Key stats row
          isLoading
              ? const SizedBox(
                  height: 32,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _StatChip(
                icon: Icons.bolt_rounded,
                label: 'XP',
                value: '$totalXp',
                color: Colors.amber.shade700,
              ),
              _StatChip(
                icon: Icons.local_fire_department_rounded,
                label: 'Streak',
                value: '$currentStreak',
                color: Colors.orange,
              ),
              _StatChip(
                icon: Icons.school_rounded,
                label: 'Level',
                value: '${(totalXp / 100).floor() + 1}',
                color: theme.colorScheme.primary,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _StatChip({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: color,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: Colors.grey,
          ),
        ),
      ],
    );
  }
}

/// Stats grid showing learning progress.
class _StatsGrid extends StatelessWidget {
  final int lessonsCompleted;
  final int ayahsRead;
  final int flashcardsReviewed;
  final int recitationSessions;
  final ThemeData theme;

  const _StatsGrid({
    required this.lessonsCompleted,
    required this.ayahsRead,
    required this.flashcardsReviewed,
    required this.recitationSessions,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 2.2,
      children: [
        _StatCard(
          icon: Icons.book_rounded,
          label: 'Lessons',
          value: '$lessonsCompleted',
          theme: theme,
        ),
        _StatCard(
          icon: Icons.menu_book_rounded,
          label: 'Ayahs Read',
          value: '$ayahsRead',
          theme: theme,
        ),
        _StatCard(
          icon: Icons.style_rounded,
          label: 'Flashcards',
          value: '$flashcardsReviewed',
          theme: theme,
        ),
        _StatCard(
          icon: Icons.mic_rounded,
          label: 'Recitations',
          value: '$recitationSessions',
          theme: theme,
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final ThemeData theme;

  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        border: Border.all(
          color: theme.colorScheme.outline.withValues(alpha: 0.15),
        ),
      ),
      child: Row(
        children: [
          Icon(icon, color: theme.colorScheme.primary, size: 28),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                value,
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
              ),
              Text(
                label,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
