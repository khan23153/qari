import '../../../data/models/recitation_session_record.dart';

/// How firmly a Mushaf page is held, from the last time it was recited.
enum PageStrength {
  /// Never recited in Safha yet.
  notRecited,

  /// Last recited with no mistakes.
  strong,

  /// One or two mistakes last time.
  shaky,

  /// Three or more mistakes last time.
  weak,
}

/// What the app knows about one page.
class PageState {
  const PageState({
    required this.page,
    required this.strength,
    this.lastRecited,
    this.lastMistakes = 0,
  });

  final int page;
  final PageStrength strength;
  final DateTime? lastRecited;
  final int lastMistakes;

  bool get recited => strength != PageStrength.notRecited;
}

/// The reciter's memory of all 604 Mushaf pages, built from their real
/// recitation history (newest session per page wins).
class HifzMap {
  HifzMap._(this._pages, this._now);

  static const int pageCount = 604;

  /// A page not revised for this long is due again even if it was strong.
  static const Duration revisitAfter = Duration(days: 7);

  final Map<int, PageState> _pages;
  final DateTime _now;

  /// [pageOf] maps an ayah to its page; it fills in records saved before
  /// sessions kept their pages, and mistakes saved without one.
  factory HifzMap.fromHistory(
    List<RecitationSessionRecord> records, {
    int? Function(int surah, int ayah)? pageOf,
    DateTime? now,
  }) {
    final sorted = [...records]
      ..sort((a, b) => b.recordedAt.compareTo(a.recordedAt));
    final pages = <int, PageState>{};
    for (final r in sorted) {
      final covered = <int>{...r.pages};
      if (covered.isEmpty && pageOf != null) {
        for (var a = r.ayahFrom; a <= r.ayahTo; a++) {
          final p = pageOf(r.surahNumber, a);
          if (p != null) covered.add(p);
        }
      }
      final mistakesByPage = <int, int>{};
      for (final m in r.mistakes) {
        final p = m.page ??
            (pageOf != null && m.surahNumber != null && m.ayahNumber != null
                ? pageOf(m.surahNumber!, m.ayahNumber!)
                : null);
        if (p != null) mistakesByPage[p] = (mistakesByPage[p] ?? 0) + 1;
      }
      for (final p in covered) {
        if (p < 1 || p > pageCount || pages.containsKey(p)) continue;
        final n = mistakesByPage[p] ?? 0;
        pages[p] = PageState(
          page: p,
          strength: n == 0
              ? PageStrength.strong
              : (n <= 2 ? PageStrength.shaky : PageStrength.weak),
          lastRecited: r.recordedAt,
          lastMistakes: n,
        );
      }
    }
    return HifzMap._(pages, now ?? DateTime.now());
  }

  PageState stateOf(int page) =>
      _pages[page] ??
      PageState(page: page, strength: PageStrength.notRecited);

  int get recitedCount => _pages.length;

  /// Whether a recited page should be revised now: it had mistakes last
  /// time, or it has not been revised for [revisitAfter].
  bool isDue(PageState s) {
    if (!s.recited) return false;
    if (s.strength != PageStrength.strong) return true;
    final last = s.lastRecited;
    return last == null || _now.difference(last) >= revisitAfter;
  }

  /// Today's revision: due pages, weakest first, then the most mistakes,
  /// then the longest since last revised.
  List<PageState> todaysRevision({int count = 3}) {
    final due = _pages.values.where(isDue).toList()
      ..sort((a, b) {
        final byStrength = b.strength.index.compareTo(a.strength.index);
        if (byStrength != 0) return byStrength;
        final byMistakes = b.lastMistakes.compareTo(a.lastMistakes);
        if (byMistakes != 0) return byMistakes;
        final la = a.lastRecited ?? DateTime(0);
        final lb = b.lastRecited ?? DateTime(0);
        return la.compareTo(lb);
      });
    return due.take(count).toList();
  }

  int get dueCount => _pages.values.where(isDue).length;
}
