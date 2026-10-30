import 'package:flutter/material.dart';

import '../../data/library_models.dart';
import '../library_theme.dart';
import '../widgets/library_widgets.dart';
import 'hadith_reader_page.dart';

/// The books (chapters) of one collection.
class CollectionPage extends StatelessWidget {
  const CollectionPage({super.key, required this.env, required this.collection});

  final LibraryEnv env;
  final LibraryCollection collection;

  @override
  Widget build(BuildContext context) {
    return LibraryThemed(
      env: env,
      builder: (context, p) => Scaffold(
        backgroundColor: p.paper,
        appBar: AppBar(title: Text(collection.nameEn)),
        body: LibraryAsync<LibraryPage<LibraryBook>>(
          palette: p,
          load: () => env.repository.books(collection.slug),
          builder: (context, page) => ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
            itemCount: page.items.length,
            separatorBuilder: (_, __) => Divider(color: p.border, height: 1),
            itemBuilder: (context, i) {
              final b = page.items[i];
              return ListTile(
                key: ValueKey('book-${b.number}'),
                leading: CircleAvatar(
                  backgroundColor: p.card,
                  foregroundColor: p.ink,
                  child: Text('${b.number}', style: const TextStyle(fontSize: 13)),
                ),
                title: Text(b.nameEn, style: TextStyle(color: p.ink)),
                subtitle: Text(
                  '#${b.hadithFirst}–${b.hadithLast} · ${b.hadithCount} hadith',
                  style: TextStyle(color: p.muted, fontSize: 12),
                ),
                trailing: Icon(Icons.chevron_right_rounded, color: p.muted),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => BookHadithsPage(env: env, collection: collection, book: b),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

/// One book's hadith, fetched page by page.
class BookHadithsPage extends StatefulWidget {
  const BookHadithsPage({
    super.key,
    required this.env,
    required this.collection,
    required this.book,
  });

  final LibraryEnv env;
  final LibraryCollection collection;
  final LibraryBook book;

  @override
  State<BookHadithsPage> createState() => _BookHadithsPageState();
}

class _BookHadithsPageState extends State<BookHadithsPage> {
  final List<HadithSummary> _items = [];
  int _page = 0;
  bool _hasNext = true;
  bool _loading = false;
  Object? _error;

  @override
  void initState() {
    super.initState();
    _loadMore();
  }

  Future<void> _loadMore() async {
    if (_loading || !_hasNext) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final page = await widget.env.repository.bookHadiths(
        widget.collection.slug,
        widget.book.number,
        page: _page + 1,
      );
      if (!mounted) return;
      setState(() {
        _items.addAll(page.items);
        _page = page.page;
        _hasNext = page.hasNext;
      });
    } catch (e) {
      if (mounted) setState(() => _error = e);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return LibraryThemed(
      env: widget.env,
      builder: (context, p) => Scaffold(
        backgroundColor: p.paper,
        appBar: AppBar(title: Text(widget.book.nameEn)),
        body: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
          children: [
            for (final h in _items) ...[
              HadithSummaryTile(
                hadith: h,
                palette: p,
                collectionName: widget.collection.nameEn,
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => HadithReaderPage(env: widget.env, hadithId: h.id),
                  ),
                ),
              ),
              const SizedBox(height: 10),
            ],
            if (_loading)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: CircularProgressIndicator(),
                ),
              )
            else if (_error != null)
              TextButton(onPressed: _loadMore, child: const Text("Couldn't load. Try again"))
            else if (_hasNext)
              TextButton(onPressed: _loadMore, child: const Text('Load more')),
          ],
        ),
      ),
    );
  }
}
