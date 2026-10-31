import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../data/repositories/local_corpus_repository.dart';
import '../../hifz/similar_verses.dart';
import '../mushaf/mushaf_theme.dart';
import '../mushaf/surah_titles.dart';

/// "Surah name 7:161" for a "surah:ayah" reference.
String similarVerseLabel(String ref) {
  final parts = ref.split(':');
  final surah = int.tryParse(parts.first);
  final name = surahNameEnglish(surah);
  return name == null ? ref : '$name $ref';
}

/// Shown on the live page when the words heard left the expected ayah for
/// one of its similar ayahs.
class SimilarVerseBanner extends StatelessWidget {
  const SimilarVerseBanner({
    super.key,
    required this.slip,
    required this.theme,
    required this.onDismiss,
  });

  final SimilarVerseSlip slip;
  final MushafTheme theme;
  final VoidCallback onDismiss;

  @override
  Widget build(BuildContext context) {
    final t = theme;
    return Semantics(
      liveRegion: true,
      child: Container(
        key: const ValueKey<String>('similar-verse-banner'),
        margin: const EdgeInsets.fromLTRB(16, 6, 16, 0),
        padding: const EdgeInsets.fromLTRB(14, 10, 6, 10),
        decoration: BoxDecoration(
          color: Color.alphaBlend(t.accent.withValues(alpha: 0.14), t.card),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: t.accent.withValues(alpha: 0.6)),
        ),
        child: Row(
          children: [
            Icon(Icons.compare_arrows_rounded, color: t.accent),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Similar verse',
                    style: TextStyle(
                      color: t.text,
                      fontWeight: FontWeight.w700,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'You continued into ${similarVerseLabel(slip.to)} '
                    'while reciting ${slip.from}.',
                    style: TextStyle(color: t.mutedInk, fontSize: 13),
                  ),
                ],
              ),
            ),
            TextButton(
              onPressed: () => showSimilarVerseCompare(
                context,
                slip.from,
                slip.to,
                theme: t,
              ),
              child: Text('Compare', style: TextStyle(color: t.accent)),
            ),
            IconButton(
              tooltip: 'Dismiss',
              onPressed: onDismiss,
              icon: Icon(Icons.close_rounded, color: t.mutedInk, size: 20),
            ),
          ],
        ),
      ),
    );
  }
}

/// Opens a sheet with both ayahs; words that are not in the other ayah are
/// marked, so the reciter sees exactly where the two part ways.
Future<void> showSimilarVerseCompare(
  BuildContext context,
  String a,
  String b, {
  MushafTheme theme = MushafTheme.classic,
  LocalCorpusRepository? corpus,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    backgroundColor: theme.background,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
    ),
    builder: (_) => _CompareSheet(
      a: a,
      b: b,
      theme: theme,
      corpus: corpus ?? LocalCorpusRepository(),
    ),
  );
}

class _CompareSheet extends StatefulWidget {
  const _CompareSheet({
    required this.a,
    required this.b,
    required this.theme,
    required this.corpus,
  });

  final String a;
  final String b;
  final MushafTheme theme;
  final LocalCorpusRepository corpus;

  @override
  State<_CompareSheet> createState() => _CompareSheetState();
}

class _CompareSheetState extends State<_CompareSheet> {
  late final Future<(List<String>, List<String>)> _words = _load();

  Future<List<String>> _ayahWords(String ref) async {
    final parts = ref.split(':');
    final surah = int.parse(parts[0]);
    final ayah = int.parse(parts[1]);
    final ayahs = await widget.corpus.getAyahs(surah);
    final match = ayahs.where((x) => x.ayahNumber == ayah);
    if (match.isEmpty) return const [];
    return [
      for (final w in match.first.words)
        if (SimilarVerseIndex.skeleton(w.text).isNotEmpty) w.text,
    ];
  }

  Future<(List<String>, List<String>)> _load() async =>
      (await _ayahWords(widget.a), await _ayahWords(widget.b));

  @override
  Widget build(BuildContext context) {
    final t = widget.theme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
      child: FutureBuilder<(List<String>, List<String>)>(
        future: _words,
        builder: (context, snap) {
          final data = snap.data;
          return Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: t.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Where the two verses part',
                style: TextStyle(
                  color: t.text,
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Words that are not in the other verse are marked.',
                style: TextStyle(color: t.mutedInk, fontSize: 13),
              ),
              const SizedBox(height: 16),
              if (data == null)
                const Padding(
                  padding: EdgeInsets.all(24),
                  child: Center(child: CircularProgressIndicator()),
                )
              else ...[
                _AyahBlock(
                  label: similarVerseLabel(widget.a),
                  words: data.$1,
                  other: data.$2,
                  theme: t,
                ),
                const SizedBox(height: 14),
                _AyahBlock(
                  label: similarVerseLabel(widget.b),
                  words: data.$2,
                  other: data.$1,
                  theme: t,
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _AyahBlock extends StatelessWidget {
  const _AyahBlock({
    required this.label,
    required this.words,
    required this.other,
    required this.theme,
  });

  final String label;
  final List<String> words;
  final List<String> other;
  final MushafTheme theme;

  @override
  Widget build(BuildContext context) {
    final t = theme;
    final otherSet = other.map(SimilarVerseIndex.skeleton).toSet();
    final base = AppTheme.arabicTextStyle(fontSize: 22, color: t.text);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: t.card,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: t.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            label,
            style: TextStyle(
              color: t.accent,
              fontWeight: FontWeight.w700,
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 8),
          Text.rich(
            TextSpan(
              children: [
                for (final w in words) ...[
                  TextSpan(
                    text: w,
                    style: otherSet.contains(SimilarVerseIndex.skeleton(w))
                        ? base
                        : base.copyWith(
                            color: t.accent,
                            backgroundColor: t.accent.withValues(alpha: 0.14),
                          ),
                  ),
                  const TextSpan(text: ' '),
                ],
              ],
            ),
            textDirection: TextDirection.rtl,
            style: base.copyWith(height: 1.9),
          ),
        ],
      ),
    );
  }
}
