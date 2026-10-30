// Arabic normalisation for offline gharib lookup and search.
//
// A port of backend/core_api/app/library/arabic.py so the bundled library
// matches words exactly as the API does.

final _marks = RegExp('[ً-ٰٟـۖ-ۭ‌-‏؜]');
final _alef = RegExp('[آأإٱ]');
final _notWord = RegExp(r'[^\p{L}\p{N}\s]', unicode: true);
final _spaces = RegExp(r'\s+');

/// Strip tashkeel, tatweel and punctuation; unify alef forms; lowercase Latin.
String normalizeArabic(String text) => text
    .replaceAll(_marks, '')
    .replaceAll(_alef, 'ا')
    .replaceAll(_notWord, ' ')
    .replaceAll('_', ' ')
    .replaceAll(_spaces, ' ')
    .trim()
    .toLowerCase();

/// Candidate stems of one normalised word, most specific first: peels a
/// conjunction (و/ف), then a preposition (ب/ل/ك), then the article.
List<String> stripClitics(String word) {
  final candidates = <String>[word];

  void add(String stem) {
    if (stem.length >= 2 && !candidates.contains(stem)) candidates.add(stem);
  }

  final stems = <String>[word];
  if ((word.startsWith('و') || word.startsWith('ف')) && word.length > 3) {
    stems.add(word.substring(1));
  }
  // Iterate a snapshot, as the backend does: stems appended below are not
  // peeled again.
  for (final stem in List<String>.of(stems)) {
    add(stem);
    if (stem.startsWith('لل') && stem.length > 3) {
      add('ال${stem.substring(2)}');
      add(stem.substring(2));
    }
    if ((stem.startsWith('ب') || stem.startsWith('ل') || stem.startsWith('ك')) &&
        stem.length > 3) {
      add(stem.substring(1));
      stems.add(stem.substring(1));
    }
  }
  for (final stem in List<String>.of(candidates)) {
    if (stem.startsWith('ال') && stem.length > 3) add(stem.substring(2));
  }
  return candidates;
}
