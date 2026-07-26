import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../data/models/lesson_model.dart';
import '../../../../data/services/curriculum_service.dart';
import 'lesson_player_page.dart';

/// Learn hub — the full offline curriculum in three tracks:
///   1. Foundation (read Arabic: letters, harakat, long vowels)
///   2. Quran Grammar (word types, roots, pronouns, verbs, iḍāfa)
///   3. Quran Vocabulary (60 levels of the most frequent words — the
///      subtitle shows the honest cumulative % of the Quran you can
///      recognise after each level)
/// Progress + unlocking are local (LocalStorageService), so learning works
/// entirely offline.
class LessonListPage extends ConsumerStatefulWidget {
  final int moduleNumber;

  const LessonListPage({super.key, this.moduleNumber = 1});

  @override
  ConsumerState<LessonListPage> createState() => _LessonListPageState();
}

class _LessonListPageState extends ConsumerState<LessonListPage> {
  List<LessonModel> _foundation = const [];
  List<LessonModel> _grammar = const [];
  List<LessonModel> _vocab = const [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final svc = CurriculumService.instance;
    final vocab = await svc.vocabLessons();
    final done = await svc.completedIds();
    if (!mounted) return;
    setState(() {
      _foundation = svc.withProgress(svc.foundationLessons, done);
      _grammar = svc.withProgress(svc.grammarLessons, done);
      _vocab = svc.withProgress(vocab, done);
      _loading = false;
    });
  }

  Future<void> _open(LessonModel lesson) async {
    final completed = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => LessonPlayerPage(lesson: lesson)),
    );
    if (completed == true) _load();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Learn Quran')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _sectionHeader(theme, 'Foundation', 'Learn to read Arabic'),
                ..._foundation.map(_tile),
                const SizedBox(height: 16),
                _sectionHeader(theme, 'Quran Grammar',
                    'Understand how Quran sentences work'),
                ..._grammar.map(_tile),
                const SizedBox(height: 16),
                _sectionHeader(theme, 'Quran Vocabulary',
                    'The most frequent words first — every level grows the % '
                    'of the Quran you understand'),
                ..._vocab.map(_tile),
                const SizedBox(height: 24),
              ],
            ),
    );
  }

  Widget _sectionHeader(ThemeData theme, String title, String subtitle) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10, top: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w800,
            ),
          ),
          Text(
            subtitle,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.55),
            ),
          ),
        ],
      ),
    );
  }

  Widget _tile(LessonModel lesson) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: _LessonTile(lesson: lesson, onTap: () => _open(lesson)),
    );
  }
}

/// A lesson tile in the list.
class _LessonTile extends StatelessWidget {
  final LessonModel lesson;
  final VoidCallback onTap;

  const _LessonTile({required this.lesson, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: lesson.isLocked ? null : onTap,
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
            border: Border.all(
              color: lesson.isCompleted
                  ? theme.colorScheme.primary.withValues(alpha: 0.3)
                  : theme.colorScheme.outline.withValues(alpha: 0.2),
            ),
          ),
          child: Row(
            children: [
              // Status icon
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: lesson.isCompleted
                      ? theme.colorScheme.primary
                      : lesson.isLocked
                          ? theme.colorScheme.outline.withValues(alpha: 0.1)
                          : theme.colorScheme.primary.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: lesson.isCompleted
                    ? const Icon(Icons.check_rounded, color: Colors.white)
                    : lesson.isLocked
                        ? Icon(Icons.lock_rounded,
                            color: theme.colorScheme.outline)
                        : Icon(Icons.play_arrow_rounded,
                            color: theme.colorScheme.primary),
              ),
              const SizedBox(width: 16),
              // Lesson info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      lesson.title,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      lesson.description,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color:
                            theme.colorScheme.onSurface.withValues(alpha: 0.55),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${lesson.estimatedMinutes} min • +${lesson.xpReward} XP',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color:
                            theme.colorScheme.onSurface.withValues(alpha: 0.4),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
