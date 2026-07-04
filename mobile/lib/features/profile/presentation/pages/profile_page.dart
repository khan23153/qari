import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/local_storage_service.dart';
import '../../../data/services/audio_service.dart';
import '../widgets/streak_calendar.dart';
import '../widgets/badges_grid.dart';
import '../widgets/settings_section.dart';
import 'attribution_page.dart';

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

  // Stats
  int _totalXp = 1240;
  int _currentStreak = 7;
  int _lessonsCompleted = 12;
  int _ayahsRead = 45;
  int _flashcardsReviewed = 89;
  int _recitationSessions = 5;

  @override
  void initState() {
    super.initState();
    _loadSettings();
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
    await Haptics.selection();
    setState(() => _selectedLanguage = code);
    final storage = LocalStorageService();
    await storage.setSelectedLanguage(code);

    // Update locale
    final lang = AppConstants.supportedLanguages.where((l) => l.code == code).first;
    ref.read(appLocaleProvider.notifier).state = lang.locale;
  }

  Future<void> _updateQari(String qari) async {
    await Haptics.selection();
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
    await Haptics.selection();
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
    await Haptics.selection();
    setState(() => _audioConsent = value);
    final storage = LocalStorageService();
    await storage.setAudioConsent(value);
  }

  Future<void> _toggleGrammarColors(bool value) async {
    await Haptics.selection();
    setState(() {
      _grammarColors = value;
      if (value) _tajweedColors = false;
    });
    final storage = LocalStorageService();
    await storage.setGrammarColorsEnabled(value);
    await storage.setTajweedColorsEnabled(_tajweedColors);
  }

  Future<void> _toggleTajweedColors(bool value) async {
    await Haptics.selection();
    setState(() {
      _tajweedColors = value;
      if (value) _grammarColors = false;
    });
    final storage = LocalStorageService();
    await storage.setTajweedColorsEnabled(value);
    await storage.setGrammarColorsEnabled(_grammarColors);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ─── Profile Header ─────────────────────────────────────
              _ProfileHeader(
                name: 'Affan',
                totalXp: _totalXp,
                currentStreak: _currentStreak,
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
    );
  }
}

/// Profile header with avatar, name, and key stats.
class _ProfileHeader extends StatelessWidget {
  final String name;
  final int totalXp;
  final int currentStreak;
  final ThemeData theme;

  const _ProfileHeader({
    required this.name,
    required this.totalXp,
    required this.currentStreak,
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
          Row(
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
