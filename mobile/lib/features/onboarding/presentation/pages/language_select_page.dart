import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../data/services/local_storage_service.dart';
import 'path_select_page.dart';

/// S1: Language Select — 3 large cards (English, اردو, Hinglish).
/// No login required. Each label shown in its own language/script.
class LanguageSelectPage extends ConsumerStatefulWidget {
  const LanguageSelectPage({super.key});

  @override
  ConsumerState<LanguageSelectPage> createState() => _LanguageSelectPageState();
}

class _LanguageSelectPageState extends ConsumerState<LanguageSelectPage> {
  String? _selected;
  bool _isSaving = false;

  Future<void> _selectLanguage(AppLanguage lang) async {
    if (_isSaving) return;
    setState(() {
      _selected = lang.code;
      _isSaving = true;
    });

    await Haptics.selection();

    final storage = LocalStorageService();
    await storage.setSelectedLanguage(lang.code);

    // Update locale provider
    ref.read(appLocaleProvider.notifier).state = lang.locale;

    // Small delay for visual feedback
    await Future.delayed(const Duration(milliseconds: 400));

    if (!mounted) return;

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PathSelectPage(selectedLanguage: lang),
      ),
    );

    setState(() => _isSaving = false);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ─── Header ──────────────────────────────────────────────
              const Spacer(),
              Icon(
                Icons.menu_book_rounded,
                size: 64,
                color: theme.colorScheme.primary,
              )
                  .animate()
                  .fadeIn(duration: 600.ms)
                  .slideY(begin: -0.2, end: 0),
              const SizedBox(height: 16),
              Text(
                'Qari',
                style: theme.textTheme.displayLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
                textAlign: TextAlign.center,
              )
                  .animate()
                  .fadeIn(delay: 200.ms, duration: 500.ms),
              const SizedBox(height: 8),
              Text(
                'Choose your language',
                style: theme.textTheme.titleMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                ),
                textAlign: TextAlign.center,
              )
                  .animate()
                  .fadeIn(delay: 400.ms, duration: 500.ms),
              Text(
                'اپنی زبان منتخب کریں',
                style: TextStyle(
                  fontSize: 16,
                  fontFamily: AppConstants.urduFontFamily,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                ),
                textAlign: TextAlign.center,
                textDirection: TextDirection.rtl,
              )
                  .animate()
                  .fadeIn(delay: 500.ms, duration: 500.ms),
              const Spacer(),

              // ─── Language Cards ──────────────────────────────────────
              ...AppConstants.supportedLanguages.map((lang) {
                final isSelected = _selected == lang.code;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: _LanguageCard(
                    language: lang,
                    isSelected: isSelected,
                    isSaving: _isSaving && isSelected,
                    onTap: () => _selectLanguage(lang),
                  ),
                )
                    .animate()
                    .fadeIn(
                      delay: Duration(milliseconds: 600 + AppConstants.supportedLanguages.indexOf(lang) * 100),
                      duration: 400.ms,
                    )
                    .slideY(begin: 0.1, end: 0);
              }),

              const Spacer(flex: 2),
            ],
          ),
        ),
      ),
    );
  }
}

/// A large tappable card for language selection.
class _LanguageCard extends StatelessWidget {
  final AppLanguage language;
  final bool isSelected;
  final bool isSaving;
  final VoidCallback onTap;

  const _LanguageCard({
    required this.language,
    required this.isSelected,
    required this.isSaving,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: isSaving ? null : onTap,
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          decoration: BoxDecoration(
            color: isSelected
                ? theme.colorScheme.primary.withValues(alpha: 0.08)
                : theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
            border: Border.all(
              color: isSelected
                  ? theme.colorScheme.primary
                  : theme.colorScheme.outline.withValues(alpha: 0.3),
              width: isSelected ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              // Language icon/flag area
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Text(
                    _flagEmoji(language.code),
                    style: const TextStyle(fontSize: 24),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              // Language name
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      language.nativeName,
                      style: theme.textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                      textDirection: language.textDirection,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      language.name,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                      ),
                    ),
                  ],
                ),
              ),
              // Selection indicator
              if (isSaving)
                SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: theme.colorScheme.primary,
                  ),
                )
              else if (isSelected)
                Icon(
                  Icons.check_circle_rounded,
                  color: theme.colorScheme.primary,
                  size: 28,
                )
              else
                Icon(
                  Icons.radio_button_unchecked,
                  color: theme.colorScheme.outline.withValues(alpha: 0.4),
                  size: 28,
                ),
            ],
          ),
        ),
      ),
    );
  }

  String _flagEmoji(String code) {
    switch (code) {
      case 'en':
        return '🇬🇧';
      case 'ur':
        return '🇵🇰';
      case 'hi':
        return '🇮🇳';
      default:
        return '🌐';
    }
  }
}
