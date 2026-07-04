import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../data/services/local_storage_service.dart';
import 'path_select_page.dart';

/// S1. Language Select — first launch screen.
/// Three large cards: English, اردو, Hinglish (Roman).
class LanguageSelectPage extends ConsumerStatefulWidget {
  const LanguageSelectPage({super.key});

  @override
  ConsumerState<LanguageSelectPage> createState() => _LanguageSelectPageState();
}

class _LanguageSelectPageState extends ConsumerState<LanguageSelectPage> {
  String? _selected;

  Future<void> _select(String langCode, String displayLabel) async {
    await Haptics.selectionClick();
    setState(() => _selected = langCode);
    await LocalStorageService.instance.setAppLanguage(langCode);

    // Brief delay for visual feedback
    await Future.delayed(const Duration(milliseconds: 300));

    if (mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const PathSelectPage()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 48),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'Choose your language',
                style: Theme.of(context).textTheme.headlineMedium,
                textAlign: TextAlign.center,
              ),
              Text(
                'اپنی زبان منتخب کریں',
                style: Theme.of(context).textTheme.titleLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 48),
              _languageCard(
                context,
                code: 'en',
                label: 'English',
                subtitle: 'Continue in English',
                isSelected: _selected == 'en',
                onTap: () => _select('en', 'English'),
              ),
              const SizedBox(height: 16),
              _languageCard(
                context,
                code: 'ur',
                label: 'اردو',
                subtitle: 'اردو میں جاری رکھیں',
                isSelected: _selected == 'ur',
                onTap: () => _select('ur', 'اردو'),
                isRtl: true,
              ),
              const SizedBox(height: 16),
              _languageCard(
                context,
                code: 'hi_latn',
                label: 'Hinglish (Roman)',
                subtitle: 'Hinglish mein seekhein',
                isSelected: _selected == 'hi_latn',
                onTap: () => _select('hi_latn', 'Hinglish'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _languageCard(
    BuildContext context, {
    required String code,
    required String label,
    required String subtitle,
    required bool isSelected,
    required VoidCallback onTap,
    bool isRtl = false,
  }) {
    return Card(
      elevation: isSelected ? 4 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: isSelected
            ? BorderSide(color: Theme.of(context).colorScheme.primary, width: 2)
            : BorderSide.none,
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              Text(
                label,
                style: Theme.of(context).textTheme.headlineSmall,
                textDirection: isRtl ? TextDirection.rtl : TextDirection.ltr,
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
                textDirection: isRtl ? TextDirection.rtl : TextDirection.ltr,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
