import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/lesson_model.dart';
import '../../../../data/services/curriculum_service.dart';
import '../widgets/grammar_card_widget.dart';
import '../widgets/quiz_widget.dart';

/// S4: Lesson player — one concept per screen, grammar cards with color-coding,
/// quiz screens (drag-match, MCQ, fill-blank), immediate feedback with haptics,
/// lesson end XP burst.
class LessonPlayerPage extends ConsumerStatefulWidget {
  final LessonModel lesson;

  const LessonPlayerPage({super.key, required this.lesson});

  @override
  ConsumerState<LessonPlayerPage> createState() => _LessonPlayerPageState();
}

class _LessonPlayerPageState extends ConsumerState<LessonPlayerPage> {
  late final List<_ScreenData> _screens;
  int _currentIndex = 0;
  int _correctAnswers = 0;
  bool _isComplete = false;

  @override
  void initState() {
    super.initState();
    _screens = _buildScreens(widget.lesson);
  }

  List<_ScreenData> _buildScreens(LessonModel lesson) {
    final screens = <_ScreenData>[];

    // Add concept screens
    for (final concept in lesson.concepts) {
      screens.add(_ScreenData(type: _ScreenType.concept, concept: concept));
    }

    // Add quiz screens
    for (final quiz in lesson.quizQuestions) {
      screens.add(_ScreenData(type: _ScreenType.quiz, quiz: quiz));
    }

    // Add completion screen
    screens.add(_ScreenData(type: _ScreenType.complete));
    return screens;
  }

  void _nextScreen() {
    if (_currentIndex < _screens.length - 1) {
      setState(() => _currentIndex++);
    }
  }

  void _onQuizAnswered(bool isCorrect) {
    if (isCorrect) {
      _correctAnswers++;
      Haptics.vibrate(HapticsType.medium);
    } else {
      Haptics.vibrate(HapticsType.heavy);
    }
    // Auto-advance after a short delay (the quiz widget shows feedback first)
    Future.delayed(const Duration(milliseconds: 1200), () {
      if (mounted) _nextScreen();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final screen = _screens[_currentIndex];
    final progress = (_currentIndex + 1) / _screens.length;

    return PopScope(
      canPop: _isComplete,
      child: Scaffold(
        body: SafeArea(
          child: Column(
            children: [
              // ─── Progress Header ─────────────────────────────────────
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.close_rounded),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: LinearProgressIndicator(
                          value: progress,
                          minHeight: 8,
                          backgroundColor:
                              theme.colorScheme.primary.withValues(alpha: 0.15),
                          valueColor: AlwaysStoppedAnimation(
                            theme.colorScheme.primary,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Text(
                      '${_currentIndex + 1}/${_screens.length}',
                      style: theme.textTheme.labelMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),

              // ─── Screen Content ──────────────────────────────────────
              Expanded(
                child: _buildScreen(context, screen),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildScreen(BuildContext context, _ScreenData screen) {
    switch (screen.type) {
      case _ScreenType.concept:
        return _ConceptScreen(
          concept: screen.concept!,
          onNext: _nextScreen,
        );
      case _ScreenType.quiz:
        return QuizWidget(
          question: screen.quiz!,
          onAnswered: _onQuizAnswered,
        );
      case _ScreenType.complete:
        return _CompletionScreen(
          xpEarned: widget.lesson.xpReward,
          correctAnswers: _correctAnswers,
          totalQuestions: widget.lesson.quizQuestions.length,
          onDone: () async {
            // Persist completion + XP locally (offline-first curriculum);
            // pop with `true` so the list/path can refresh unlock state.
            await CurriculumService.instance.markCompleted(widget.lesson);
            if (!context.mounted) return;
            setState(() => _isComplete = true);
            Navigator.of(context).pop(true);
          },
        );
    }
  }
}

/// Internal screen data model.
class _ScreenData {
  final _ScreenType type;
  final LessonConcept? concept;
  final QuizQuestionModel? quiz;

  _ScreenData({
    required this.type,
    this.concept,
    this.quiz,
  });
}

enum _ScreenType { concept, quiz, complete }

/// A concept screen — shows one grammar concept with color-coded examples.
class _ConceptScreen extends StatelessWidget {
  final LessonConcept concept;
  final VoidCallback onNext;

  const _ConceptScreen({required this.concept, required this.onNext});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Title
          Text(
            concept.title,
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 16),

          // Explanation
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    concept.explanation,
                    style: theme.textTheme.bodyLarge?.copyWith(height: 1.6),
                  ),
                  if (concept.explanationUrdu != null) ...[
                    const SizedBox(height: 12),
                    Text(
                      concept.explanationUrdu!,
                      style: AppTheme.urduTextStyle(
                        fontSize: 16,
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                      ),
                      textDirection: TextDirection.rtl,
                    ),
                  ],

                  // Arabic example with grammar card
                  if (concept.arabicExample != null) ...[
                    const SizedBox(height: 24),
                    GrammarCardWidget(
                      arabicText: concept.arabicExample!,
                      transliteration: concept.transliteration,
                      translation: concept.translation,
                      posGroup: concept.posGroup,
                      grammarNote: concept.grammarNote,
                    ),
                  ],
                ],
              ),
            ),
          ),

          // Continue button
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: onNext,
            icon: const Icon(Icons.arrow_forward_rounded),
            label: const Text('Continue'),
            style: FilledButton.styleFrom(
              minimumSize: const Size.fromHeight(52),
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

/// Completion screen — XP burst animation.
class _CompletionScreen extends StatelessWidget {
  final int xpEarned;
  final int correctAnswers;
  final int totalQuestions;
  final VoidCallback onDone;

  const _CompletionScreen({
    required this.xpEarned,
    required this.correctAnswers,
    required this.totalQuestions,
    required this.onDone,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Trophy icon
          Icon(
            Icons.emoji_events_rounded,
            size: 80,
            color: Colors.amber.shade700,
          )
              .animate()
              .scale(
                begin: const Offset(0, 0),
                end: const Offset(1, 1),
                duration: 600.ms,
                curve: Curves.elasticOut,
              ),

          const SizedBox(height: 24),

          Text(
            'Lesson Complete!',
            style: theme.textTheme.displaySmall?.copyWith(
              fontWeight: FontWeight.w800,
            ),
          )
              .animate()
              .fadeIn(delay: 300.ms, duration: 400.ms),

          const SizedBox(height: 16),

          // XP burst
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.amber.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.bolt_rounded, color: Colors.amber.shade700, size: 28),
                const SizedBox(width: 8),
                Text(
                  '+$xpEarned XP',
                  style: theme.textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: Colors.amber.shade700,
                  ),
                ),
              ],
            ),
          )
              .animate()
              .fadeIn(delay: 500.ms, duration: 400.ms)
              .scale(
                begin: const Offset(0.5, 0.5),
                end: const Offset(1, 1),
                duration: 500.ms,
                curve: Curves.elasticOut,
              ),

          const SizedBox(height: 24),

          // Stats
          if (totalQuestions > 0)
            Text(
              '$correctAnswers / $totalQuestions correct',
              style: theme.textTheme.titleMedium?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              ),
            )
                .animate()
                .fadeIn(delay: 700.ms, duration: 400.ms),

          const SizedBox(height: 32),

          // Done button
          FilledButton(
            onPressed: onDone,
            style: FilledButton.styleFrom(
              minimumSize: const Size.fromHeight(52),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: const Text('Done'),
          )
              .animate()
              .fadeIn(delay: 900.ms, duration: 400.ms),
        ],
      ),
    );
  }
}
