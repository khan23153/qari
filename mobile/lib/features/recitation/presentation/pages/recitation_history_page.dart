import 'package:flutter/material.dart';
import 'package:intl/intl.dart' hide TextDirection;

import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/recitation_session_record.dart';
import '../../../../data/services/local_storage_service.dart';
import '../../../../data/services/recitation_history_service.dart';

/// Tarteel-style "Mistake Review" + history + streak for AI Recitation.
///
/// Lists every locally-saved live recitation session, shows the current
/// consecutive-day streak, and lets the user drill into a session to review the
/// exact words they mispronounced / skipped.
class RecitationHistoryPage extends StatefulWidget {
  const RecitationHistoryPage({super.key});

  @override
  State<RecitationHistoryPage> createState() => _RecitationHistoryPageState();
}

class _RecitationHistoryPageState extends State<RecitationHistoryPage> {
  List<RecitationSessionRecord> _records = const [];
  int _streak = 0;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final ls = await LocalStorageService.getInstance();
    final svc = RecitationHistoryService(ls.prefs);
    if (mounted) {
      setState(() {
        _records = svc.getAll();
        _streak = svc.getStreak();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Recitation History'),
        centerTitle: true,
        actions: [
          if (_records.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_outline_rounded),
              tooltip: 'Clear history',
              onPressed: () async {
                final confirmed = await showDialog<bool>(
                  context: context,
                  builder: (c) => AlertDialog(
                    title: const Text('Clear all history?'),
                    content: const Text(
                      'This removes your recitation streak and saved sessions. '
                      'This cannot be undone.',
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(c, false),
                        child: const Text('Cancel'),
                      ),
                      FilledButton(
                        onPressed: () => Navigator.pop(c, true),
                        child: const Text('Clear'),
                      ),
                    ],
                  ),
                );
                if (confirmed == true) {
                  final ls = await LocalStorageService.getInstance();
                  RecitationHistoryService(ls.prefs).deleteAll();
                  _load();
                }
              },
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _records.isEmpty
              ? _EmptyState(theme: theme)
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _StreakCard(streak: _streak, sessionCount: _records.length, theme: theme),
                    const SizedBox(height: 16),
                    ..._records.map((r) => _SessionTile(record: r, theme: theme, onTap: () => _openReview(r))),
                  ],
                ),
    );
  }

  void _openReview(RecitationSessionRecord record) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => _SessionReviewSheet(record: record),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final ThemeData theme;
  const _EmptyState({required this.theme});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.history_rounded,
                size: 64, color: theme.colorScheme.onSurface.withValues(alpha: 0.3)),
            const SizedBox(height: 16),
            Text(
              'No recitations yet',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            Text(
              'Your live recitation sessions will appear here, with a streak '
              'and a review of the words you missed.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.55),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StreakCard extends StatelessWidget {
  final int streak;
  final int sessionCount;
  final ThemeData theme;

  const _StreakCard({
    required this.streak,
    required this.sessionCount,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    final color = theme.colorScheme.primary;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [color.withValues(alpha: 0.15), color.withValues(alpha: 0.05)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: Icon(Icons.local_fire_department_rounded, color: color, size: 32),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$streak',
                  style: theme.textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: color,
                  ),
                ),
                Text(
                  streak == 1 ? 'day streak' : 'day streak',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '$sessionCount',
                style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
              ),
              Text(
                'sessions',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SessionTile extends StatelessWidget {
  final RecitationSessionRecord record;
  final ThemeData theme;
  final VoidCallback onTap;

  const _SessionTile({
    required this.record,
    required this.theme,
    required this.onTap,
  });

  Color get _scoreColor {
    final s = record.overallScore;
    if (s >= 0.9) return Colors.green;
    if (s >= 0.75) return Colors.lightGreen;
    if (s >= 0.6) return Colors.orange;
    return Colors.red;
  }

  @override
  Widget build(BuildContext context) {
    final date = DateFormat('EEE d MMM, HH:mm').format(record.recordedAt);
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: _scoreColor.withValues(alpha: 0.12),
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      '${(record.overallScore * 100).toInt()}',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                        color: _scoreColor,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        record.referenceLabel,
                        style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '$date · ${record.correctCount}/${record.totalCount} correct'
                        '${record.mistakes.isNotEmpty ? ' · ${record.mistakes.length} to review' : ''}',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.55),
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right_rounded),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SessionReviewSheet extends StatelessWidget {
  final RecitationSessionRecord record;

  const _SessionReviewSheet({required this.record});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      maxChildSize: 0.92,
      minChildSize: 0.4,
      expand: false,
      builder: (context, scroll) => Column(
        children: [
          Container(
            margin: const EdgeInsets.only(top: 8),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: theme.colorScheme.outline.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Review · ${record.referenceLabel}',
                        style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                      ),
                      Text(
                        '${record.correctCount}/${record.totalCount} correct · '
                        '${DateFormat('d MMM').format(record.recordedAt)}',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.55),
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close_rounded),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: record.mistakes.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.check_circle_outline_rounded,
                              size: 56, color: Colors.green.withValues(alpha: 0.7)),
                          const SizedBox(height: 12),
                          Text(
                            'No mistakes — perfect recitation!',
                            style: theme.textTheme.titleMedium,
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView.separated(
                    controller: scroll,
                    padding: const EdgeInsets.all(20),
                    itemCount: record.mistakes.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (context, i) {
                      final m = record.mistakes[i];
                      final isSkip = m.errorType == 'skipped';
                      final color = isSkip ? const Color(0xFFEF6C00) : theme.colorScheme.error;
                      return Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: color.withValues(alpha: 0.08),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: color.withValues(alpha: 0.3)),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              isSkip ? Icons.skip_next_rounded : Icons.record_voice_over_rounded,
                              color: color,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Directionality(
                                textDirection: TextDirection.rtl,
                                child: Text(
                                  m.expectedText,
                                  style: AppTheme.arabicTextStyle(
                                    fontSize: 26,
                                    color: color,
                                  ),
                                  textAlign: TextAlign.right,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              isSkip ? 'Skipped' : 'Mispronounced',
                              style: theme.textTheme.labelSmall?.copyWith(color: color),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
