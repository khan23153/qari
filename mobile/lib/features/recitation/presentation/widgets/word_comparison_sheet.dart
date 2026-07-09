import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/recitation_model.dart';
import '../../../../data/services/audio_service.dart';

/// Word comparison sheet — A/B audio comparison for incorrect words.
/// Shows the reference audio and user's audio side by side with
/// phoneme error details.
class WordComparisonSheet extends StatefulWidget {
  final WordVerdict verdict;
  final AudioService audioService;

  const WordComparisonSheet({
    super.key,
    required this.verdict,
    required this.audioService,
  });

  @override
  State<WordComparisonSheet> createState() => _WordComparisonSheetState();
}

class _WordComparisonSheetState extends State<WordComparisonSheet> {
  bool _isPlayingReference = false;
  bool _isPlayingUser = false;

  Future<void> _playReference() async {
    await Haptics.vibrate(HapticsType.selection);
    setState(() => _isPlayingReference = true);
    try {
      if (widget.verdict.referenceAudioUrl != null) {
        await widget.audioService.playUrl(widget.verdict.referenceAudioUrl!);
      } else {
        await Future.delayed(const Duration(seconds: 2));
      }
    } catch (_) {}
    if (mounted) setState(() => _isPlayingReference = false);
  }

  Future<void> _playUserAudio() async {
    await Haptics.vibrate(HapticsType.selection);
    setState(() => _isPlayingUser = true);
    try {
      if (widget.verdict.userAudioUrl != null) {
        await widget.audioService.playUrl(widget.verdict.userAudioUrl!);
      } else {
        await Future.delayed(const Duration(seconds: 2));
      }
    } catch (_) {}
    if (mounted) setState(() => _isPlayingUser = false);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final v = widget.verdict;

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.7,
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

          // ─── Word Display ──────────────────────────────────────────
          Center(
            child: Directionality(
              textDirection: TextDirection.rtl,
              child: Text(
                v.word,
                style: AppTheme.arabicTextStyle(
                  fontSize: 36,
                  color: Colors.red,
                ),
              ),
            ),
          )
              .animate()
              .fadeIn(duration: 300.ms),

          const SizedBox(height: 4),

          // Error type badge
          if (v.errorType != null)
            Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.red.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  v.errorType!.toUpperCase(),
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: Colors.red.shade700,
                  ),
                ),
              ),
            ),

          const SizedBox(height: 20),

          // ─── A/B Audio Comparison ──────────────────────────────────
          Text(
            'Compare Audio',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 12),

          // Reference audio
          _AudioPlaybackCard(
            label: 'Reference (Qari)',
            icon: Icons.volume_up_rounded,
            color: theme.colorScheme.primary,
            isPlaying: _isPlayingReference,
            onPlay: _playReference,
            theme: theme,
          ),

          const SizedBox(height: 8),

          // User audio
          _AudioPlaybackCard(
            label: 'Your Recording',
            icon: Icons.person_rounded,
            color: Colors.red,
            isPlaying: _isPlayingUser,
            onPlay: _playUserAudio,
            theme: theme,
          ),

          // ─── Error Description ─────────────────────────────────────
          if (v.errorDescription != null) ...[
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.red.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: Colors.red.withValues(alpha: 0.15),
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.error_outline_rounded, color: Colors.red.shade700, size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      v.errorDescription!,
                      style: theme.textTheme.bodyMedium?.copyWith(height: 1.5),
                    ),
                  ),
                ],
              ),
            ),
          ],

          // ─── Phoneme Errors ────────────────────────────────────────
          if (v.phonemeErrors.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(
              'Phoneme Errors',
              style: theme.textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 8),
            ...v.phonemeErrors.map((err) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.red.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          err.expectedPhoneme,
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            color: Colors.red,
                          ),
                        ),
                      ),
                      const Icon(Icons.arrow_forward_rounded, size: 16),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.orange.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          err.actualPhoneme,
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            color: Colors.orange.shade700,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      if (err.severity == 'major')
                        Icon(Icons.priority_high_rounded,
                            size: 16, color: Colors.red.shade700),
                    ],
                  ),
                )),
          ],

          const SizedBox(height: 20),

          // ─── Practice Button ───────────────────────────────────────
          FilledButton.icon(
            onPressed: () {
              Navigator.of(context).pop();
              // Could navigate to makhraj visualizer for this phoneme
            },
            icon: const Icon(Icons.school_rounded),
            label: const Text('Practice This Sound'),
            style: FilledButton.styleFrom(
              minimumSize: const Size.fromHeight(48),
            ),
          ),
        ],
      ),
    );
  }
}

/// Audio playback card for A/B comparison.
class _AudioPlaybackCard extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final bool isPlaying;
  final VoidCallback onPlay;
  final ThemeData theme;

  const _AudioPlaybackCard({
    required this.label,
    required this.icon,
    required this.color,
    required this.isPlaying,
    required this.onPlay,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPlay,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: color.withValues(alpha: 0.2),
            ),
          ),
          child: Row(
            children: [
              // Play/pause icon
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: color,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  isPlaying ? Icons.pause_rounded : Icons.play_arrow_rounded,
                  color: Colors.white,
                  size: 24,
                ),
              ),
              const SizedBox(width: 12),
              // Label
              Expanded(
                child: Text(
                  label,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: color,
                  ),
                ),
              ),
              // Mini waveform placeholder
              if (isPlaying)
                SizedBox(
                  width: 60,
                  height: 24,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: List.generate(5, (i) {
                      return AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        width: 3,
                        height: 8 + (i % 3) * 6.0,
                        decoration: BoxDecoration(
                          color: color,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      );
                    }),
                  ),
                )
                    .animate(onComplete: (c) => c.repeat())
                    .shimmer(duration: 1.seconds),
            ],
          ),
        ),
      ),
    );
  }
}
