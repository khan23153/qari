import 'package:flutter/material.dart';

import '../../../../data/repositories/local_corpus_repository.dart';
import '../../../../data/services/local_storage_service.dart';
import '../../../../data/services/recitation_history_service.dart';
import '../../hifz/hifz_map.dart';
import '../../hifz/slip_store.dart';
import '../mushaf/surah_titles.dart';
import '../recitation_mode.dart';
import '../widgets/similar_verse_widgets.dart';
import 'live_recitation_page.dart';

/// Everything the Hifz map shows.
class HifzMapData {
  const HifzMapData({
    required this.map,
    required this.slips,
    required this.pageStart,
  });

  final HifzMap map;
  final List<SlipRecord> slips;

  /// First ayah (surah, ayah) of each Mushaf page.
  final Map<int, (int, int)> pageStart;

  /// Reads the local recitation history, the slip list and the corpus.
  static Future<HifzMapData> load() async {
    final ls = await LocalStorageService.getInstance();
    final history = RecitationHistoryService(ls.prefs).getAll();
    final slips = await SlipStore(prefs: ls.prefs).all();
    final corpus = LocalCorpusRepository();
    final pageOfAyah = <(int, int), int>{};
    final pageStart = <int, (int, int)>{};
    for (var s = 1; s <= 114; s++) {
      for (final a in await corpus.getAyahs(s)) {
        final p = a.pageNumber;
        if (p == null) continue;
        pageOfAyah[(s, a.ayahNumber)] = p;
        pageStart.putIfAbsent(p, () => (s, a.ayahNumber));
      }
    }
    return HifzMapData(
      map: HifzMap.fromHistory(
        history,
        pageOf: (s, a) => pageOfAyah[(s, a)],
      ),
      slips: slips,
      pageStart: pageStart,
    );
  }
}

/// All 604 pages coloured by how firmly the reciter holds them, today's
/// revision picks, and the similar verses they mix up.
class HifzMapPage extends StatefulWidget {
  const HifzMapPage({super.key, this.load, this.onRecitePage});

  /// Defaults to [HifzMapData.load]; tests pass their own data.
  final Future<HifzMapData> Function()? load;

  /// Opens recitation on a page. Defaults to the live Hifz page.
  final void Function(BuildContext context, int page, (int, int)? start)?
      onRecitePage;

  @override
  State<HifzMapPage> createState() => _HifzMapPageState();
}

class _HifzMapPageState extends State<HifzMapPage> {
  late Future<HifzMapData> _data = (widget.load ?? HifzMapData.load)();

  void _reload() {
    setState(() => _data = (widget.load ?? HifzMapData.load)());
  }

  Future<void> _recite(int page, (int, int)? start) async {
    final open = widget.onRecitePage;
    if (open != null) {
      open(context, page, start);
      return;
    }
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => LiveRecitationPage(
          surahNumber: start?.$1,
          ayahNumber: start?.$2,
          initialMode: RecitationMode.hifz,
        ),
      ),
    );
    if (mounted) _reload();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Hifz map')),
      body: FutureBuilder<HifzMapData>(
        future: _data,
        builder: (context, snap) {
          if (snap.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  'The Hifz map could not be loaded. Pull down to try again.',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodyMedium,
                ),
              ),
            );
          }
          final data = snap.data;
          if (data == null) {
            return const Center(child: CircularProgressIndicator());
          }
          return RefreshIndicator(
            onRefresh: () async => _reload(),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
              children: [
                _Summary(map: data.map),
                const SizedBox(height: 20),
                _ReviseToday(
                  map: data.map,
                  pageStart: data.pageStart,
                  onRecite: _recite,
                ),
                const SizedBox(height: 24),
                Text(
                  'All 604 pages',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 8),
                const _Legend(),
                const SizedBox(height: 12),
                _PageGrid(
                  map: data.map,
                  onTap: (page) => _showPage(context, data, page),
                ),
                const SizedBox(height: 28),
                _SlipList(slips: data.slips),
              ],
            ),
          );
        },
      ),
    );
  }

  void _showPage(BuildContext context, HifzMapData data, int page) {
    final state = data.map.stateOf(page);
    final start = data.pageStart[page];
    final theme = Theme.of(context);
    showModalBottomSheet<void>(
      context: context,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              _pageTitle(page, start),
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 6),
            Text(_stateLine(state, data.map), style: theme.textTheme.bodyMedium),
            const SizedBox(height: 18),
            FilledButton.icon(
              onPressed: () {
                Navigator.of(ctx).pop();
                _recite(page, start);
              },
              icon: const Icon(Icons.mic_rounded),
              label: const Text('Recite this page'),
            ),
          ],
        ),
      ),
    );
  }
}

String _pageTitle(int page, (int, int)? start) {
  final name = surahNameEnglish(start?.$1);
  return name == null ? 'Page $page' : 'Page $page · $name';
}

String _ago(DateTime when) {
  final days = DateTime.now().difference(when).inDays;
  if (days <= 0) return 'today';
  if (days == 1) return 'yesterday';
  return '$days days ago';
}

String _stateLine(PageState s, HifzMap map) {
  final last = s.lastRecited;
  switch (s.strength) {
    case PageStrength.notRecited:
      return 'Not recited in Safha yet.';
    case PageStrength.strong:
      final due = map.isDue(s) ? ' Time to revise it again.' : '';
      return 'No mistakes last time${last == null ? '' : ', ${_ago(last)}'}.$due';
    case PageStrength.shaky:
    case PageStrength.weak:
      final n = s.lastMistakes;
      return '$n mistake${n == 1 ? '' : 's'} last time'
          '${last == null ? '' : ', ${_ago(last)}'}.';
  }
}

Color _tileColor(ThemeData theme, PageStrength s) {
  final accent = theme.colorScheme.primary;
  switch (s) {
    case PageStrength.notRecited:
      return theme.colorScheme.onSurface.withValues(alpha: 0.08);
    case PageStrength.strong:
      return accent;
    case PageStrength.shaky:
      return accent.withValues(alpha: 0.4);
    case PageStrength.weak:
      return theme.colorScheme.error;
  }
}

class _Summary extends StatelessWidget {
  const _Summary({required this.map});

  final HifzMap map;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final recited = map.recitedCount;
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: theme.colorScheme.primary.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: theme.colorScheme.primary.withValues(alpha: 0.25),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$recited of ${HifzMap.pageCount}',
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                Text('pages recited', style: theme.textTheme.bodySmall),
              ],
            ),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${map.dueCount}',
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: theme.colorScheme.primary,
                  ),
                ),
                Text('to revise', style: theme.textTheme.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ReviseToday extends StatelessWidget {
  const _ReviseToday({
    required this.map,
    required this.pageStart,
    required this.onRecite,
  });

  final HifzMap map;
  final Map<int, (int, int)> pageStart;
  final void Function(int page, (int, int)? start) onRecite;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final picks = map.todaysRevision();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Revise today',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 8),
        if (picks.isEmpty)
          Text(
            map.recitedCount == 0
                ? 'Recite a page in Hifz mode and it will appear here when '
                    'it needs revising.'
                : 'Nothing is due. Every page you recited was clean this '
                    'week.',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          )
        else
          for (final s in picks)
            Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: _tileColor(theme, s.strength),
                  child: Text(
                    '${s.page}',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: s.strength == PageStrength.shaky
                          ? theme.colorScheme.onSurface
                          : theme.colorScheme.onPrimary,
                    ),
                  ),
                ),
                title: Text(_pageTitle(s.page, pageStart[s.page])),
                subtitle: Text(_stateLine(s, map)),
                trailing: const Icon(Icons.mic_rounded),
                onTap: () => onRecite(s.page, pageStart[s.page]),
              ),
            ),
      ],
    );
  }
}

class _Legend extends StatelessWidget {
  const _Legend();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    Widget item(PageStrength s, String label) => Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: _tileColor(theme, s),
                borderRadius: BorderRadius.circular(3),
              ),
            ),
            const SizedBox(width: 6),
            Text(label, style: theme.textTheme.bodySmall),
          ],
        );
    return Wrap(
      spacing: 14,
      runSpacing: 6,
      children: [
        item(PageStrength.strong, 'Clean'),
        item(PageStrength.shaky, '1–2 mistakes'),
        item(PageStrength.weak, '3+ mistakes'),
        item(PageStrength.notRecited, 'Not recited'),
      ],
    );
  }
}

/// Juz n starts on page 22 + 20(n − 2) for n ≥ 2 in the Madinah Mushaf.
int _juzStart(int juz) => juz == 1 ? 1 : 22 + 20 * (juz - 2);

class _PageGrid extends StatelessWidget {
  const _PageGrid({required this.map, required this.onTap});

  final HifzMap map;
  final void Function(int page) onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return LayoutBuilder(
      builder: (context, constraints) {
        const perRow = 20;
        const gap = 3.0;
        final tile = (constraints.maxWidth - 32 - gap * (perRow - 1)) / perRow;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            for (var juz = 1; juz <= 30; juz++)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 32,
                      child: Text(
                        '$juz',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.onSurface
                              .withValues(alpha: 0.6),
                        ),
                      ),
                    ),
                    Expanded(
                      child: Wrap(
                        spacing: gap,
                        runSpacing: gap,
                        children: [
                          for (var p = _juzStart(juz);
                              p <
                                  (juz == 30
                                      ? HifzMap.pageCount + 1
                                      : _juzStart(juz + 1));
                              p++)
                            _Tile(
                              page: p,
                              size: tile,
                              state: map.stateOf(p),
                              due: map.isDue(map.stateOf(p)),
                              onTap: () => onTap(p),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
          ],
        );
      },
    );
  }
}

class _Tile extends StatelessWidget {
  const _Tile({
    required this.page,
    required this.size,
    required this.state,
    required this.due,
    required this.onTap,
  });

  final int page;
  final double size;
  final PageState state;
  final bool due;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Semantics(
      button: true,
      label: 'Page $page',
      child: GestureDetector(
        key: ValueKey<String>('hifz-page-$page'),
        onTap: onTap,
        child: Container(
          width: size,
          height: size * 1.3,
          decoration: BoxDecoration(
            color: _tileColor(theme, state.strength),
            borderRadius: BorderRadius.circular(2.5),
            border: due
                ? Border.all(color: theme.colorScheme.onSurface, width: 1)
                : null,
          ),
        ),
      ),
    );
  }
}

class _SlipList extends StatelessWidget {
  const _SlipList({required this.slips});

  final List<SlipRecord> slips;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Similar verses you mix up',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 8),
        if (slips.isEmpty)
          Text(
            'When you slide from a verse into a similar one while reciting, '
            'Safha tells you and keeps the pair here to revise.',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          )
        else
          for (final s in slips)
            Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: const Icon(Icons.compare_arrows_rounded),
                title: Text('${s.from} → ${s.to}'),
                subtitle: Text(
                  '${similarVerseLabel(s.from)} into '
                  '${similarVerseLabel(s.to)} · '
                  '${s.count} time${s.count == 1 ? '' : 's'}',
                ),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: () => showSimilarVerseCompare(context, s.from, s.to),
              ),
            ),
      ],
    );
  }
}
