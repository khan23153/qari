import 'package:flutter/material.dart';

import '../../../recitation/presentation/mushaf/mushaf_theme.dart';
import '../../data/library_models.dart';
import '../library_theme.dart';
import '../widgets/library_widgets.dart';
import 'collection_page.dart';
import 'hadith_reader_page.dart';
import 'library_search_page.dart';

/// Islamic Library home: one tab per shelf that has collections.
class LibraryHomePage extends StatelessWidget {
  const LibraryHomePage({super.key, required this.env});

  final LibraryEnv env;

  @override
  Widget build(BuildContext context) {
    return LibraryThemed(
      env: env,
      builder: (context, p) => ColoredBox(
        color: p.paper,
        child: LibraryAsync<List<LibraryCategory>>(
        palette: p,
        load: env.repository.categories,
        builder: (context, categories) {
          final shelves = categories.where((c) => c.collectionCount > 0).toList();
          return DefaultTabController(
            length: shelves.length,
            child: Scaffold(
              backgroundColor: p.paper,
              appBar: AppBar(
                title: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Islamic Library',
                      style: TextStyle(
                        color: p.ink,
                        fontSize: 19,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      'المكتبة الإسلامية',
                      style: TextStyle(color: p.muted, fontSize: 13),
                    ),
                  ],
                ),
                actions: [
                  IconButton(
                    tooltip: 'Search the library',
                    icon: const Icon(Icons.search_rounded),
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => LibrarySearchPage(env: env)),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Page theme',
                    icon: const Icon(Icons.palette_outlined),
                    onPressed: () => MushafThemeController.showSheet(
                      context,
                      controller: env.themeController,
                    ),
                  ),
                ],
                bottom: TabBar(
                  isScrollable: true,
                  tabAlignment: TabAlignment.start,
                  tabs: [
                    for (final c in shelves)
                      Tab(key: ValueKey('library-tab-${c.slug}'), text: c.nameEn),
                  ],
                ),
              ),
              body: TabBarView(
                children: [
                  for (final c in shelves) _ShelfView(env: env, category: c),
                ],
              ),
            ),
          );
        },
      ),
      ),
    );
  }
}

class _ShelfView extends StatelessWidget {
  const _ShelfView({required this.env, required this.category});

  final LibraryEnv env;
  final LibraryCategory category;

  bool get _isCriticism => category.slug == 'daif_mawdu';

  @override
  Widget build(BuildContext context) {
    final p = env.palette;
    return LibraryAsync<LibraryPage<LibraryCollection>>(
      palette: p,
      load: () => env.repository.collections(category: category.slug),
      builder: (context, page) => ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
        children: [
          Text(
            category.nameAr,
            textDirection: TextDirection.rtl,
            style: TextStyle(color: p.muted, fontSize: 15),
          ),
          const SizedBox(height: 10),
          for (final c in page.items) ...[
            CollectionTile(
              key: ValueKey('collection-${c.slug}'),
              collection: c,
              palette: p,
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => CollectionPage(env: env, collection: c),
                ),
              ),
            ),
            const SizedBox(height: 10),
          ],
          if (_isCriticism) _WeakHadithSection(env: env),
        ],
      ),
    );
  }
}

/// Narrations at least one named scholar graded da'if or mawdu', each with
/// every scholar's grade shown side by side.
class _WeakHadithSection extends StatelessWidget {
  const _WeakHadithSection({required this.env});

  final LibraryEnv env;

  @override
  Widget build(BuildContext context) {
    final p = env.palette;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 12),
        Text(
          'Narrations graded weak by scholars',
          style: TextStyle(
            color: p.ink,
            fontSize: 17,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          "Listed when at least one named scholar graded it da'if or mawdu'. "
          'Open one to see every grade and the cited reasons.',
          style: TextStyle(color: p.muted, fontSize: 13, height: 1.35),
        ),
        const SizedBox(height: 10),
        LibraryAsync<LibraryPage<HadithSummary>>(
          palette: p,
          load: () => env.repository.hadiths(graded: 'weak'),
          builder: (context, page) => Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              for (final h in page.items) ...[
                HadithSummaryTile(
                  key: ValueKey('weak-hadith-${h.id}'),
                  hadith: h,
                  palette: p,
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => HadithReaderPage(env: env, hadithId: h.id),
                    ),
                  ),
                ),
                const SizedBox(height: 10),
              ],
            ],
          ),
        ),
      ],
    );
  }
}
