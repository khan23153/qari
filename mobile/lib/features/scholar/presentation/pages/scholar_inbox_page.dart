import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';

/// Scholar inbox page — list of user's submitted questions and responses.
class ScholarInboxPage extends ConsumerStatefulWidget {
  const ScholarInboxPage({super.key});

  @override
  ConsumerState<ScholarInboxPage> createState() => _ScholarInboxPageState();
}

class _ScholarInboxPageState extends ConsumerState<ScholarInboxPage> {
  final List<_ScholarQuestion> _questions = _sampleQuestions;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

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
                      'My Questions',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // ─── Questions List ───────────────────────────────────────
            Expanded(
              child: _questions.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.inbox_outlined, size: 64,
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.2)),
                          const SizedBox(height: 16),
                          Text(
                            'No questions yet',
                            style: theme.textTheme.titleMedium?.copyWith(
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Ask a scholar to get started',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.3),
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: _questions.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (context, index) {
                        final q = _questions[index];
                        return _QuestionTile(question: q, theme: theme)
                            .animate()
                            .fadeIn(
                              delay: Duration(milliseconds: index * 80),
                              duration: 400.ms,
                            )
                            .slideY(begin: 0.05, end: 0);
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

/// A question tile in the inbox.
class _QuestionTile extends StatelessWidget {
  final _ScholarQuestion question;
  final ThemeData theme;

  const _QuestionTile({required this.question, required this.theme});

  @override
  Widget build(BuildContext context) {
    final hasResponse = question.answer != null;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        border: Border.all(
          color: hasResponse
              ? theme.colorScheme.primary.withValues(alpha: 0.2)
              : theme.colorScheme.outline.withValues(alpha: 0.15),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Status and topics
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: hasResponse
                      ? theme.colorScheme.primary.withValues(alpha: 0.1)
                      : Colors.orange.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  hasResponse ? 'Answered' : 'Pending',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: hasResponse
                        ? theme.colorScheme.primary
                        : Colors.orange.shade700,
                  ),
                ),
              ),
              const Spacer(),
              Text(
                _formatDate(question.askedAt),
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Question text
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.help_outline_rounded, size: 18,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.4)),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  question.question,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),

          // Topic chips
          if (question.topics.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 4,
              children: question.topics.map((t) => Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: theme.colorScheme.secondary.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  t,
                  style: TextStyle(
                    fontSize: 10,
                    color: theme.colorScheme.secondary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              )).toList(),
            ),
          ],

          // Answer
          if (hasResponse) ...[
            const SizedBox(height: 12),
            const Divider(),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.school_rounded, size: 18,
                    color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        question.scholarName ?? 'Scholar',
                        style: theme.textTheme.labelMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: theme.colorScheme.primary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        question.answer!,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          height: 1.6,
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);
    if (diff.inHours < 1) return 'Just now';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return '${date.day}/${date.month}/${date.year}';
  }
}

/// Scholar question data.
class _ScholarQuestion {
  final String question;
  final List<String> topics;
  final DateTime askedAt;
  final String? answer;
  final String? scholarName;

  _ScholarQuestion({
    required this.question,
    required this.topics,
    required this.askedAt,
    this.answer,
    this.scholarName,
  });
}

final _sampleQuestions = <_ScholarQuestion>[
  _ScholarQuestion(
    question: 'What is the correct way to pronounce the letter ق (Qaf) from its makhraj?',
    topics: ['Tajweed', 'Pronunciation'],
    askedAt: DateTime.now().subtract(const Duration(hours: 3)),
    answer: 'The letter Qaf (ق) is pronounced from the very back of the tongue, near the soft palate. It is a plosive letter — the sound is built up and released. Practice by placing the back of your tongue against the soft palate and releasing it sharply.',
    scholarName: 'Sh. Abdullah Hassan',
  ),
  _ScholarQuestion(
    question: 'When should I stretch the madd in recitation?',
    topics: ['Tajweed', 'Qirat'],
    askedAt: DateTime.now().subtract(const Duration(days: 2)),
    answer: 'Natural madd (madd tabi\'i) is stretched for 2 counts. Secondary madd can be 4 or 6 counts depending on the type. Madd muttasil (connected) is 4-6 counts, madd munfasil (separated) is 2-4 counts.',
    scholarName: 'Sh. Abdullah Hassan',
  ),
  _ScholarQuestion(
    question: 'Is it permissible to combine Dhuhr and Asr prayers during travel?',
    topics: ['Other'],
    askedAt: DateTime.now().subtract(const Duration(hours: 8)),
  ),
];
