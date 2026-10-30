import 'package:flutter/material.dart';

import '../../data/library_models.dart';
import '../library_theme.dart';
import '../widgets/library_sheets.dart';
import '../widgets/library_widgets.dart';
import 'collection_page.dart';
import 'hadith_reader_page.dart';

/// Search across hadith text (Arabic without tashkeel, or translation),
/// narrators and collections.
class LibrarySearchPage extends StatefulWidget {
  const LibrarySearchPage({super.key, required this.env});

  final LibraryEnv env;

  @override
  State<LibrarySearchPage> createState() => _LibrarySearchPageState();
}

class _LibrarySearchPageState extends State<LibrarySearchPage> {
  final _controller = TextEditingController();
  Future<LibrarySearchResult>? _results;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit(String query) {
    final q = query.trim();
    if (q.length < 2) return;
    setState(() => _results = widget.env.repository.search(q));
  }

  @override
  Widget build(BuildContext context) {
    final env = widget.env;
    return LibraryThemed(
      env: env,
      builder: (context, p) => Scaffold(
        backgroundColor: p.paper,
        appBar: AppBar(title: const Text('Search the library')),
        body: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
          children: [
            TextField(
              key: const ValueKey('library-search-field'),
              controller: _controller,
              autofocus: true,
              textInputAction: TextInputAction.search,
              style: TextStyle(color: p.ink),
              decoration: const InputDecoration(
                hintText: 'Hadith words, narrator or book',
                prefixIcon: Icon(Icons.search_rounded),
              ),
              onSubmitted: _submit,
            ),
            const SizedBox(height: 16),
            if (_results != null)
              FutureBuilder<LibrarySearchResult>(
                future: _results,
                builder: (context, snap) {
                  if (snap.connectionState != ConnectionState.done) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  if (snap.hasError) {
                    return Text("Couldn't search right now.", style: TextStyle(color: p.ink));
                  }
                  final r = snap.data!;
                  if (r.isEmpty) {
                    return Text('No results for “${r.query}”.', style: TextStyle(color: p.muted));
                  }
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      if (r.collections.isNotEmpty) ...[
                        _heading('Books', p),
                        for (final c in r.collections) ...[
                          CollectionTile(
                            collection: c,
                            palette: p,
                            onTap: () => Navigator.of(context).push(
                              MaterialPageRoute(builder: (_) => CollectionPage(env: env, collection: c)),
                            ),
                          ),
                          const SizedBox(height: 8),
                        ],
                      ],
                      if (r.narrators.isNotEmpty) ...[
                        _heading('Narrators', p),
                        for (final n in r.narrators)
                          ListTile(
                            key: ValueKey('search-narrator-${n.id}'),
                            title: Text(
                              n.nameAr,
                              textDirection: TextDirection.rtl,
                              style: TextStyle(color: p.ink, fontSize: 18),
                            ),
                            subtitle: Text(
                              '${n.nameEn} · ${reliabilityLabel(n.reliability)}',
                              style: TextStyle(color: p.muted),
                            ),
                            onTap: () => showNarratorSheet(context, env, n.id),
                          ),
                      ],
                      if (r.hadiths.isNotEmpty) ...[
                        _heading('Hadith', p),
                        for (final h in r.hadiths) ...[
                          HadithSummaryTile(
                            hadith: h,
                            palette: p,
                            onTap: () => Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => HadithReaderPage(env: env, hadithId: h.id),
                              ),
                            ),
                          ),
                          const SizedBox(height: 8),
                        ],
                      ],
                    ],
                  );
                },
              ),
          ],
        ),
      ),
    );
  }

  Widget _heading(String text, LibraryPalette p) => Padding(
        padding: const EdgeInsets.fromLTRB(0, 8, 0, 6),
        child: Text(
          text,
          style: TextStyle(color: p.ink, fontSize: 16, fontWeight: FontWeight.w700),
        ),
      );
}
