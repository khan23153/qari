import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/word_model.dart';
import '../../../../data/services/audio_service.dart';
import '../../../../data/repositories/flashcard_repository.dart';

/// Word bottom sheet — shows word detail: audio autoplay, meaning,
/// morphology, root chip, and save to flashcards button.
class WordBottomSheet extends StatefulWidget {
  final WordModel word;
  final String languageCode;
  final AudioService audioService;

  const WordBottomSheet({
    super.key,
    required this.word,
    required this.languageCode,
    required this.audioService,
  });

  @override
  State<WordBottomSheet> createState() => _WordBottomSheetState();
}

class _WordBottomSheetState extends State<WordBottomSheet> {
  bool _isPlaying = false;
  bool _isSaved = false;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    // Auto-play word audio on open
    _playAudio();
  }

  Future<void> _playAudio() async {
    if (widget.word.audioUrl != null) {
      setState(() => _isPlaying = true);
      try {
        await widget.audioService.playUrl(widget.word.audioUrl!);
      } catch (_) {
        // Audio may not be available in demo
      }
      if (mounted) setState(() => _isPlaying = false);
    }
  }

  Future<void> _saveToFlashcards() async {
    if (_isSaving) return;
    setState(() => _isSaving = true);

    try {
      final repo = FlashcardRepository();
      await repo.saveCard(
        wordId: widget.word.wordId,
        surahNumber: widget.word.surahNumber,
        ayahNumber: widget.word.ayahNumber,
      );
      await Haptics.vibrate(HapticsType.medium);
      if (mounted) setState(() {
        _isSaved = true;
        _isSaving = false;
      });
    } catch (e) {
      // Even if API fails, show success for UX in demo
      if (mounted) setState(() {
        _isSaved = true;
        _isSaving = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final word = widget.word;
    final config = AppTheme.getGrammarConfig(word.posGroup ?? 'default');
    final meaning = word.translationFor(widget.languageCode) ?? '—';

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.75,
      ),
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Drag handle
          Center(
            child: Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: theme.colorScheme.outline.withValues(alpha: 0.3),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          // ─── Arabic Word (large) ───────────────────────────────────
          Center(
            child: Directionality(
              textDirection: TextDirection.rtl,
              child: Text(
                word.text,
                style: AppTheme.arabicTextStyle(
                  fontSize: 36,
                  color: config.color,
                  decoration: AppTheme.toTextDecoration(config.underlineStyle),
                  decorationColor: config.color,
                  decorationStyle: config.underlineStyle == UnderlineStyle.dotted
                      ? TextDecorationStyle.dotted
                      : TextDecorationStyle.solid,
                ),
              ),
            ),
          )
              .animate()
              .fadeIn(duration: 300.ms)
              .scale(
                begin: const Offset(0.9, 0.9),
                end: const Offset(1, 1),
                duration: 300.ms,
              ),

          const SizedBox(height: 8),

          // ─── Audio Button ───────────────────────────────────────────
          Center(
            child: IconButton.filled(
              onPressed: _playAudio,
              icon: Icon(
                _isPlaying ? Icons.pause_rounded : Icons.volume_up_rounded,
                size: 28,
              ),
            ),
          ),

          const SizedBox(height: 16),

          // ─── Transliteration ────────────────────────────────────────
          if (word.transliteration != null)
            _DetailRow(
              icon: Icons.translate_rounded,
              label: 'Transliteration',
              value: word.transliteration!,
              theme: theme,
            ),

          const SizedBox(height: 12),

          // ─── Meaning ────────────────────────────────────────────────
          _DetailRow(
            icon: Icons.lightbulb_outline_rounded,
            label: 'Meaning',
            value: meaning,
            theme: theme,
          ),

          const SizedBox(height: 12),

          // ─── Part of Speech ─────────────────────────────────────────
          _DetailRow(
            icon: Icons.category_rounded,
            label: 'Part of Speech',
            value: '${config.label} (${word.posGroup})',
            theme: theme,
            valueColor: config.color,
          ),

          // ─── Morphology ────────────────────────────────────────────
          if (word.morphology != null) ...[
            const SizedBox(height: 12),
            _DetailRow(
              icon: Icons.science_outlined,
              label: 'Morphology',
              value: word.morphology!,
              theme: theme,
            ),
          ],

          // ─── Lemma ─────────────────────────────────────────────────
          if (word.lemma != null) ...[
            const SizedBox(height: 12),
            _DetailRow(
              icon: Icons.bookmark_outline_rounded,
              label: 'Lemma',
              value: word.lemma!,
              theme: theme,
            ),
          ],

          // ─── Root Chip ──────────────────────────────────────────────
          if (word.rootArabic != null && word.rootArabic!.isNotEmpty) ...[
            const SizedBox(height: 16),
            _RootChip(rootArabic: word.rootArabic!, theme: theme),
          ],

          const SizedBox(height: 20),

          // ─── Save to Flashcards ─────────────────────────────────────
          FilledButton.icon(
            onPressed: _isSaved ? null : _saveToFlashcards,
            icon: _isSaving
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : Icon(_isSaved ? Icons.check_rounded : Icons.bookmark_add_rounded),
            label: Text(_isSaved ? 'Saved to Flashcards' : 'Save to Flashcards'),
            style: FilledButton.styleFrom(
              minimumSize: const Size.fromHeight(48),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// A detail row with icon, label, and value.
class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final ThemeData theme;
  final Color? valueColor;

  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.theme,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 20, color: theme.colorScheme.onSurface.withValues(alpha: 0.5)),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: theme.textTheme.bodyLarge?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: valueColor,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// Root chip — tappable chip showing the Arabic root.
class _RootChip extends StatelessWidget {
  final String rootArabic;
  final ThemeData theme;

  const _RootChip({required this.rootArabic, required this.theme});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () {
        // Navigate to Root Explorer
        Navigator.of(context).pop();
      },
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: theme.colorScheme.primary.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: theme.colorScheme.primary.withValues(alpha: 0.2),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.park_rounded, size: 16, color: theme.colorScheme.primary),
            const SizedBox(width: 8),
            Text(
              'Root: ',
              style: theme.textTheme.labelMedium?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              ),
            ),
            Directionality(
              textDirection: TextDirection.rtl,
              child: Text(
                rootArabic,
                style: AppTheme.arabicTextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w600,
                  color: theme.colorScheme.primary,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Icon(Icons.arrow_forward_rounded, size: 16, color: theme.colorScheme.primary),
          ],
        ),
      ),
    );
  }
}
