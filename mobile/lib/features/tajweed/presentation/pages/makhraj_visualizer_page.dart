import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../data/services/audio_service.dart';

/// S7: Tajweed Theory / Makhraj Visualizer — rule card, looping video,
/// listen at different speeds, mic prompt.
class MakhrajVisualizerPage extends ConsumerStatefulWidget {
  final String? ruleName;

  const MakhrajVisualizerPage({super.key, this.ruleName});

  @override
  ConsumerState<MakhrajVisualizerPage> createState() => _MakhrajVisualizerPageState();
}

class _MakhrajVisualizerPageState extends ConsumerState<MakhrajVisualizerPage> {
  final AudioService _audioService = AudioService();
  int _selectedRuleIndex = 0;
  double _playbackSpeed = 1.0;
  bool _isPlaying = false;

  final _tajweedRules = [
    _TajweedRule(
      name: 'Idgham',
      nameArabic: 'إدغام',
      description: 'Merging of noon sakinah or tanween into the following letter. The noon sound merges into letters ي و م ن ل (yaw, waw, meem, noon, lam).',
      makhraj: 'Nasal cavity',
      exampleArabic: 'مِن وَالٍ',
      exampleTransliteration: 'min waalin',
      exampleTranslation: 'from a guardian',
      color: const Color(0xFF7B1FA2),
      videoUrl: null,
    ),
    _TajweedRule(
      name: 'Ikhfa',
      nameArabic: 'إخفاء',
      description: 'Hiding of noon sakinah or tanween. The noon sound is partially hidden before 15 letters. A light nasal sound is produced.',
      makhraj: 'Nasal cavity (light)',
      exampleArabic: 'مِن قَبْلِ',
      exampleTransliteration: 'min qabli',
      exampleTranslation: 'before',
      color: const Color(0xFFAD1457),
      videoUrl: null,
    ),
    _TajweedRule(
      name: 'Iqlab',
      nameArabic: 'إقلاب',
      description: 'Conversion of noon sakinah or tanween into meem when followed by ب (ba).',
      makhraj: 'Lips (meem position)',
      exampleArabic: 'مِن بَعْدِ',
      exampleTransliteration: 'min ba\'di',
      exampleTranslation: 'after',
      color: const Color(0xFFEF6C00),
      videoUrl: null,
    ),
    _TajweedRule(
      name: 'Qalqalah',
      nameArabic: 'قلقة',
      description: 'Echo/bounce sound on the letters ق ط ب ج د when they have sukun. Produces a slight bounce.',
      makhraj: 'Mouth (varies by letter)',
      exampleArabic: 'خَلْقٍ',
      exampleTransliteration: 'khalaqin',
      exampleTranslation: 'creation',
      color: const Color(0xFF37474F),
      videoUrl: null,
    ),
    _TajweedRule(
      name: 'Madd',
      nameArabic: 'مد',
      description: 'Elongation of vowel sounds. Natural madd (2 counts), secondary madd (4-6 counts).',
      makhraj: 'Vocal cords',
      exampleArabic: 'قَالَ',
      exampleTransliteration: 'qāla',
      exampleTranslation: 'he said',
      color: const Color(0xFF1B5E20),
      videoUrl: null,
    ),
    _TajweedRule(
      name: 'Ghunnah',
      nameArabic: 'غنة',
      description: 'Nasalization sound on meem and noon with shaddah. Held for 2 counts through the nose.',
      makhraj: 'Nasal cavity',
      exampleArabic: 'إِنَّ',
      exampleTransliteration: 'inna',
      exampleTranslation: 'indeed',
      color: const Color(0xFF00838F),
      videoUrl: null,
    ),
  ];

  @override
  void dispose() {
    _audioService.dispose();
    super.dispose();
  }

  Future<void> _playExample() async {
    await Haptics.vibrate(HapticsType.selection);
    setState(() => _isPlaying = true);
    try {
      // In production, play the actual audio
      await Future.delayed(const Duration(seconds: 2));
    } catch (_) {}
    if (mounted) setState(() => _isPlaying = false);
  }

  void _navigateToRecitation() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => Scaffold(
          appBar: AppBar(title: const Text('Practice Recitation')),
          body: const Center(child: Text('Navigate to Recitation Page')),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final rule = _tajweedRules[_selectedRuleIndex];

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // ─── Header ───────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back_rounded),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                  Expanded(
                    child: Text(
                      'Tajweed Theory',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // ─── Rule Selector ────────────────────────────────────────
            SizedBox(
              height: 48,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: _tajweedRules.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  final r = _tajweedRules[index];
                  final isSelected = index == _selectedRuleIndex;
                  return FilterChip(
                    label: Text(r.name),
                    selected: isSelected,
                    onSelected: (_) async {
                      await Haptics.vibrate(HapticsType.selection);
                      setState(() => _selectedRuleIndex = index);
                    },
                    backgroundColor: theme.colorScheme.surface,
                    selectedColor: r.color.withValues(alpha: 0.15),
                    labelStyle: TextStyle(
                      color: isSelected ? r.color : theme.colorScheme.onSurface.withValues(alpha: 0.6),
                      fontWeight: isSelected ? FontWeight.w700 : FontWeight.w400,
                    ),
                    side: BorderSide(
                      color: isSelected ? r.color.withValues(alpha: 0.3) : theme.colorScheme.outline.withValues(alpha: 0.2),
                    ),
                  );
                },
              ),
            ),

            const SizedBox(height: 8),

            // ─── Rule Card ────────────────────────────────────────────
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Rule card
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: rule.color.withValues(alpha: 0.06),
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(
                          color: rule.color.withValues(alpha: 0.2),
                        ),
                      ),
                      child: Column(
                        children: [
                          // Rule name
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                rule.name,
                                style: theme.textTheme.headlineMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                  color: rule.color,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Directionality(
                                textDirection: TextDirection.rtl,
                                child: Text(
                                  rule.nameArabic,
                                  style: AppTheme.arabicTextStyle(
                                    fontSize: 28,
                                    color: rule.color,
                                  ),
                                ),
                              ),
                            ],
                          )
                              .animate()
                              .fadeIn(duration: 400.ms),
                          const SizedBox(height: 16),

                          // Makhraj badge
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: rule.color.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.location_on_rounded, size: 16, color: rule.color),
                                const SizedBox(width: 6),
                                Text(
                                  'Makhraj: ${rule.makhraj}',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                    color: rule.color,
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 16),

                          // Description
                          Text(
                            rule.description,
                            style: theme.textTheme.bodyMedium?.copyWith(height: 1.6),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    )
                        .animate(key: ValueKey(rule.name))
                        .fadeIn(duration: 400.ms)
                        .slideY(begin: 0.05, end: 0),

                    const SizedBox(height: 20),

                    // ─── Video Placeholder (looping video area) ────────
                    Container(
                      height: 180,
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surface,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: theme.colorScheme.outline.withValues(alpha: 0.2),
                        ),
                      ),
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          // Placeholder for looping video
                          Icon(
                            Icons.play_circle_fill_rounded,
                            size: 64,
                            color: rule.color.withValues(alpha: 0.5),
                          ),
                          Positioned(
                            bottom: 8,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.black.withValues(alpha: 0.6),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Text(
                                'Makhraj demonstration video',
                                style: TextStyle(color: Colors.white, fontSize: 12),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 20),

                    // ─── Example ────────────────────────────────────────
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surface,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: theme.colorScheme.outline.withValues(alpha: 0.15),
                        ),
                      ),
                      child: Column(
                        children: [
                          Text(
                            'Example',
                            style: theme.textTheme.labelMedium?.copyWith(
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                            ),
                          ),
                          const SizedBox(height: 12),
                          Directionality(
                            textDirection: TextDirection.rtl,
                            child: Text(
                              rule.exampleArabic,
                              style: AppTheme.arabicTextStyle(
                                fontSize: 32,
                                color: rule.color,
                              ),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            rule.exampleTransliteration,
                            style: theme.textTheme.bodyLarge?.copyWith(
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                          Text(
                            '"${rule.exampleTranslation}"',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 20),

                    // ─── Listen at Different Speeds ─────────────────────
                    Text(
                      'Listen at different speeds:',
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      children: [0.5, 0.75, 1.0, 1.25, 1.5].map((speed) {
                        final isSelected = speed == _playbackSpeed;
                        return ChoiceChip(
                          label: Text('${speed}x'),
                          selected: isSelected,
                          onSelected: (_) async {
                            await Haptics.vibrate(HapticsType.selection);
                            setState(() => _playbackSpeed = speed);
                            await _audioService.setSpeed(speed);
                          },
                        );
                      }).toList(),
                    ),

                    const SizedBox(height: 16),

                    // Play button
                    FilledButton.icon(
                      onPressed: _playExample,
                      icon: Icon(_isPlaying ? Icons.pause_rounded : Icons.play_arrow_rounded),
                      label: Text(_isPlaying ? 'Playing...' : 'Listen to Example'),
                      style: FilledButton.styleFrom(
                        minimumSize: const Size.fromHeight(48),
                        backgroundColor: rule.color,
                      ),
                    ),

                    const SizedBox(height: 12),

                    // ─── Mic Prompt ─────────────────────────────────────
                    OutlinedButton.icon(
                      onPressed: _navigateToRecitation,
                      icon: const Icon(Icons.mic_rounded),
                      label: const Text('Practice This Rule'),
                      style: OutlinedButton.styleFrom(
                        minimumSize: const Size.fromHeight(48),
                        foregroundColor: rule.color,
                        side: BorderSide(color: rule.color.withValues(alpha: 0.3)),
                      ),
                    ),

                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Tajweed rule data.
class _TajweedRule {
  final String name;
  final String nameArabic;
  final String description;
  final String makhraj;
  final String exampleArabic;
  final String exampleTransliteration;
  final String exampleTranslation;
  final Color color;
  final String? videoUrl;

  _TajweedRule({
    required this.name,
    required this.nameArabic,
    required this.description,
    required this.makhraj,
    required this.exampleArabic,
    required this.exampleTransliteration,
    required this.exampleTranslation,
    required this.color,
    this.videoUrl,
  });
}
