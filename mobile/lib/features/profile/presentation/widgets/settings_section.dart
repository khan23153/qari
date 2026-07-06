import 'package:flutter/material.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';

/// Settings section — language switcher, qari picker, font-size slider with
/// live Arabic preview, theme selector, download manager, audio-consent toggle,
/// grammar/tajweed color toggles.
class SettingsSection extends StatelessWidget {
  final String selectedLanguage;
  final ValueChanged<String> onLanguageChanged;
  final String selectedQari;
  final ValueChanged<String> onQariChanged;
  final double fontScale;
  final ValueChanged<double> onFontScaleChanged;
  final String themeMode;
  final ValueChanged<String> onThemeChanged;
  final bool audioConsent;
  final ValueChanged<bool> onAudioConsentChanged;
  final bool grammarColors;
  final ValueChanged<bool> onGrammarColorsChanged;
  final bool tajweedColors;
  final ValueChanged<bool> onTajweedColorsChanged;
  final ThemeData theme;

  const SettingsSection({
    super.key,
    required this.selectedLanguage,
    required this.onLanguageChanged,
    required this.selectedQari,
    required this.onQariChanged,
    required this.fontScale,
    required this.onFontScaleChanged,
    required this.themeMode,
    required this.onThemeChanged,
    required this.audioConsent,
    required this.onAudioConsentChanged,
    required this.grammarColors,
    required this.onGrammarColorsChanged,
    required this.tajweedColors,
    required this.onTajweedColorsChanged,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: theme.colorScheme.outline.withValues(alpha: 0.15),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Section title
          Text(
            'Settings',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 20),

          // ─── Language Switcher ──────────────────────────────────────
          Text(
            'Language',
            style: theme.textTheme.labelLarge?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: AppConstants.supportedLanguages.map((lang) {
              final isSelected = lang.code == selectedLanguage;
              return ChoiceChip(
                label: Text(lang.nativeName),
                selected: isSelected,
                onSelected: (_) => onLanguageChanged(lang.code),
              );
            }).toList(),
          ),

          const SizedBox(height: 20),

          // ─── Qari (Reciter) Picker ──────────────────────────────────
          Text(
            'Reciter (Qari)',
            style: theme.textTheme.labelLarge?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
            ),
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            value: selectedQari,
            decoration: const InputDecoration(
              contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            ),
            items: const [
              DropdownMenuItem(value: 'abdul_basit', child: Text('Abdul Basit')),
              DropdownMenuItem(value: 'sudais', child: Text('Abdul Rahman Al-Sudais')),
              DropdownMenuItem(value: 'minshawi', child: Text('Al-Minshawi')),
              DropdownMenuItem(value: 'husary', child: Text('Al-Husary')),
              DropdownMenuItem(value: 'afasy', child: Text('Mishary Al-Afasy')),
            ],
            onChanged: (value) {
              if (value != null) onQariChanged(value);
            },
          ),

          const SizedBox(height: 20),

          // ─── Font Size Slider with Live Preview ─────────────────────
          Text(
            'Arabic Font Size',
            style: theme.textTheme.labelLarge?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
            ),
          ),
          const SizedBox(height: 8),
          // Live preview
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.colorScheme.primary.withValues(alpha: 0.05),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Directionality(
                textDirection: TextDirection.rtl,
                child: Text(
                  'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ',
                  style: AppTheme.arabicTextStyle(
                    fontSize: AppConstants.arabicFontDefaultSize * fontScale,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Text('A'),
              Expanded(
                child: Slider(
                  value: fontScale,
                  min: 0.8,
                  max: 1.8,
                  divisions: 10,
                  label: '${(fontScale * 100).toInt()}%',
                  onChanged: onFontScaleChanged,
                ),
              ),
              const Text('A', style: TextStyle(fontSize: 24)),
            ],
          ),

          const SizedBox(height: 20),

          // ─── Theme Selector ─────────────────────────────────────────
          Text(
            'Theme',
            style: theme.textTheme.labelLarge?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
            ),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              ChoiceChip(
                label: const Text('Light'),
                selected: themeMode == 'light',
                onSelected: (_) => onThemeChanged('light'),
              ),
              ChoiceChip(
                label: const Text('Dark'),
                selected: themeMode == 'dark',
                onSelected: (_) => onThemeChanged('dark'),
              ),
              ChoiceChip(
                label: const Text('High Contrast'),
                selected: themeMode == 'high_contrast',
                onSelected: (_) => onThemeChanged('high_contrast'),
              ),
              ChoiceChip(
                label: const Text('System'),
                selected: themeMode == 'system',
                onSelected: (_) => onThemeChanged('system'),
              ),
            ],
          ),

          const SizedBox(height: 20),

          // ─── Color Coding Toggles ───────────────────────────────────
          Text(
            'Color Coding',
            style: theme.textTheme.labelLarge?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
            ),
          ),
          const SizedBox(height: 8),
          SwitchListTile(
            title: const Text('Grammar Colors'),
            subtitle: const Text('Fi\'l=green, Ism=blue, Harf=amber'),
            value: grammarColors,
            onChanged: onGrammarColorsChanged,
            contentPadding: EdgeInsets.zero,
          ),
          SwitchListTile(
            title: const Text('Tajweed Colors'),
            subtitle: const Text('Color words by tajweed rules (mutually exclusive with grammar)'),
            value: tajweedColors,
            onChanged: onTajweedColorsChanged,
            contentPadding: EdgeInsets.zero,
          ),

          const SizedBox(height: 12),

          // ─── Audio Consent Toggle ───────────────────────────────────
          SwitchListTile(
            title: const Text('Audio Recording Consent'),
            subtitle: const Text('Allow app to record your recitation for AI analysis'),
            value: audioConsent,
            onChanged: onAudioConsentChanged,
            contentPadding: EdgeInsets.zero,
          ),

          const SizedBox(height: 12),

          // ─── Download Manager ───────────────────────────────────────
          ListTile(
            leading: const Icon(Icons.download_rounded),
            title: const Text('Download Manager'),
            subtitle: const Text('Manage offline content'),
            trailing: const Icon(Icons.chevron_right_rounded),
            contentPadding: EdgeInsets.zero,
            onTap: () async {
              await Haptics.selection();
              // Navigate to download manager
            },
          ),
        ],
      ),
    );
  }
}
