import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../core/constants/app_constants.dart';
import '../../../data/services/local_storage_service.dart';
import '../../home/presentation/pages/home_page.dart';

/// S2: Welcome/Path Select — Warm illustration + two large stacked buttons.
/// 'Zero Se Shuru Karein' (foundation) / 'Direct Quran Par Jayein' (quran_direct).
class PathSelectPage extends ConsumerStatefulWidget {
  final AppLanguage selectedLanguage;

  const PathSelectPage({super.key, required this.selectedLanguage});

  @override
  ConsumerState<PathSelectPage> createState() => _PathSelectPageState();
}

class _PathSelectPageState extends ConsumerState<PathSelectPage> {
  bool _isSaving = false;

  Future<void> _selectPath(LearningPath path) async {
    if (_isSaving) return;
    setState(() => _isSaving = true);

    await Haptics.selection();

    final storage = LocalStorageService();
    await storage.setSelectedPath(path.name);
    await storage.setOnboardingComplete(true);

    await Future.delayed(const Duration(milliseconds: 400));

    if (!mounted) return;

    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const HomePage()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUrdu = widget.selectedLanguage.code == 'ur';

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(flex: 1),

              // ─── Warm Illustration ───────────────────────────────────
              Container(
                height: 200,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(24),
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      theme.colorScheme.primary.withValues(alpha: 0.15),
                      theme.colorScheme.primary.withValues(alpha: 0.05),
                    ],
                  ),
                ),
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    // Decorative Islamic pattern
                    Icon(
                      Icons.auto_stories_rounded,
                      size: 80,
                      color: theme.colorScheme.primary,
                    )
                        .animate()
                        .fadeIn(duration: 800.ms)
                        .scale(
                          begin: const Offset(0.8, 0.8),
                          end: const Offset(1, 1),
                          duration: 600.ms,
                        ),
                    Positioned(
                      bottom: 16,
                      child: Text(
                        'بسم الله الرحمن الرحيم',
                        style: AppTheme.arabicTextStyle(
                          fontSize: 20,
                          color: theme.colorScheme.primary,
                        ),
                        textDirection: TextDirection.rtl,
                      )
                          .animate()
                          .fadeIn(delay: 400.ms, duration: 600.ms),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),

              // ─── Welcome Text ────────────────────────────────────────
              Text(
                isUrdu ? 'خوش آمدید' : 'Welcome to Qari',
                style: theme.textTheme.displaySmall?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
                textAlign: TextAlign.center,
                textDirection: isUrdu ? TextDirection.rtl : TextDirection.ltr,
              )
                  .animate()
                  .fadeIn(delay: 300.ms, duration: 500.ms),
              const SizedBox(height: 8),
              Text(
                isUrdu
                    ? 'اپنا راستہ منتخب کریں'
                    : 'Choose your learning path',
                style: theme.textTheme.titleMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                ),
                textAlign: TextAlign.center,
                textDirection: isUrdu ? TextDirection.rtl : TextDirection.ltr,
              )
                  .animate()
                  .fadeIn(delay: 500.ms, duration: 500.ms),
              const Spacer(flex: 1),

              // ─── Path Buttons ────────────────────────────────────────
              _PathButton(
                icon: Icons.foundation_rounded,
                title: isUrdu ? 'صفر سے شروع کریں' : 'Zero Se Shuru Karein',
                subtitle: isUrdu
                    ? 'بنیادی عربی گرائمر سے آغاز'
                    : 'Start from foundation — learn Arabic grammar step by step',
                color: theme.colorScheme.primary,
                isSaving: _isSaving,
                onTap: () => _selectPath(LearningPath.foundation),
              )
                  .animate()
                  .fadeIn(delay: 700.ms, duration: 500.ms)
                  .slideY(begin: 0.1, end: 0),
              const SizedBox(height: 16),
              _PathButton(
                icon: Icons.menu_book_rounded,
                title: isUrdu
                    ? 'براہ راست قرآن پڑھیں'
                    : 'Direct Quran Par Jayein',
                subtitle: isUrdu
                    ? 'براہ راست قرآن پڑھنا شروع کریں'
                    : 'Jump straight into reading the Quran with AI assistance',
                color: theme.colorScheme.secondary,
                isSaving: _isSaving,
                onTap: () => _selectPath(LearningPath.quranDirect),
              )
                  .animate()
                  .fadeIn(delay: 800.ms, duration: 500.ms)
                  .slideY(begin: 0.1, end: 0),
              const SizedBox(height: 24),

              // ─── Tertiary Text ───────────────────────────────────────
              Text(
                isUrdu
                    ? 'آپ بعد میں کبھی بھی تبدیل کر سکتے ہیں'
                    : 'Aap baad mein kabhi bhi switch kar sakte hain',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.45),
                  fontStyle: FontStyle.italic,
                ),
                textAlign: TextAlign.center,
                textDirection: isUrdu ? TextDirection.rtl : TextDirection.ltr,
              )
                  .animate()
                  .fadeIn(delay: 1000.ms, duration: 500.ms),
              const Spacer(flex: 1),
            ],
          ),
        ),
      ),
    );
  }
}

/// A large stacked button for path selection.
class _PathButton extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final bool isSaving;
  final VoidCallback onTap;

  const _PathButton({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
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
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
            border: Border.all(
              color: color.withValues(alpha: 0.3),
              width: 1.5,
            ),
          ),
          child: Row(
            children: [
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(icon, color: color, size: 28),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: theme.textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w700,
                        color: color,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                      ),
                    ),
                  ],
                ),
              ),
              if (isSaving)
                SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: color,
                  ),
                )
              else
                Icon(Icons.arrow_forward_rounded, color: color),
            ],
          ),
        ),
      ),
    );
  }
}
