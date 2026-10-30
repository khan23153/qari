import 'package:flutter/material.dart';

import '../../data/library_models.dart';
import '../library_theme.dart';

/// Loads [load] once and renders loading / error-with-retry / data states.
class LibraryAsync<T> extends StatefulWidget {
  const LibraryAsync({
    super.key,
    required this.load,
    required this.builder,
    required this.palette,
  });

  final Future<T> Function() load;
  final Widget Function(BuildContext context, T data) builder;
  final LibraryPalette palette;

  @override
  State<LibraryAsync<T>> createState() => _LibraryAsyncState<T>();
}

class _LibraryAsyncState<T> extends State<LibraryAsync<T>> {
  late Future<T> _future = widget.load();

  @override
  Widget build(BuildContext context) {
    final p = widget.palette;
    return FutureBuilder<T>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const Center(
            child: Padding(
              padding: EdgeInsets.all(32),
              child: CircularProgressIndicator(),
            ),
          );
        }
        if (snap.hasError) {
          // Transparent Material: this state can render before any Scaffold
          // (e.g. while the library home loads its shelves).
          return Material(
            type: MaterialType.transparency,
            child: Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.cloud_off_rounded, color: p.muted, size: 36),
                  const SizedBox(height: 8),
                  Text(
                    "Couldn't load this right now.",
                    textAlign: TextAlign.center,
                    style: TextStyle(color: p.ink, fontSize: 15),
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: () => setState(() => _future = widget.load()),
                    child: const Text('Try again'),
                  ),
                ],
              ),
            ),
          ),
          );
        }
        return widget.builder(context, snap.data as T);
      },
    );
  }
}

/// `[Grade — Scholar]`, tinted by the scholar's ruling.
class GradeBadge extends StatelessWidget {
  const GradeBadge({super.key, required this.grade, required this.palette});

  final ScholarGrade grade;
  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) {
    final color = palette.ruling(grade.rulingType);
    final source = grade.sourceBook ?? grade.sourceDataset;
    return Tooltip(
      message: grade.basis == 'inclusion_in_sahih'
          ? 'Included by the compiler in ${grade.sourceBook}'
          : source == null
              ? grade.scholar
              : 'Source: $source',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: palette.badge(color),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: color.withValues(alpha: 0.55)),
        ),
        child: Text(
          grade.label,
          style: TextStyle(
            color: color,
            fontSize: 13,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

class GradeBadges extends StatelessWidget {
  const GradeBadges({super.key, required this.grades, required this.palette});

  final List<ScholarGrade> grades;
  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) {
    if (grades.isEmpty) {
      return Text(
        'No scholar grade recorded for this narration yet.',
        style: TextStyle(color: palette.muted, fontSize: 13),
      );
    }
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (var i = 0; i < grades.length; i++)
          GradeBadge(
            key: ValueKey('grade-badge-$i'),
            grade: grades[i],
            palette: palette,
          ),
      ],
    );
  }
}

/// Whether a record is copied from its source or awaits a scholar's check.
class ReviewPill extends StatelessWidget {
  const ReviewPill({super.key, required this.status, required this.palette});

  final ReviewStatus status;
  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) {
    final verified = status == ReviewStatus.verifiedFromSource;
    final color =
        palette.ruling(verified ? RulingType.sahih : RulingType.daif);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: palette.badge(color),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            verified ? Icons.verified_rounded : Icons.pending_actions_rounded,
            size: 14,
            color: color,
          ),
          const SizedBox(width: 4),
          Text(
            verified ? 'Verified from source' : 'Pending scholar review',
            style: TextStyle(
              color: color,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

/// One cited reason a chain is weak or fabricated.
class DefectCard extends StatelessWidget {
  const DefectCard({
    super.key,
    required this.defect,
    required this.palette,
    this.onNarratorTap,
  });

  final HadithDefect defect;
  final LibraryPalette palette;
  final VoidCallback? onNarratorTap;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final severe = defect.cause == 'kadhdhab_matruk';
    final color = p.ruling(severe ? RulingType.mawdu : RulingType.daif);
    return Material(
      color: p.card,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: p.border),
      ),
      clipBehavior: Clip.antiAlias,
      child: Container(
      decoration: BoxDecoration(
        border: Border(left: BorderSide(color: color, width: 4)),
      ),
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(Icons.report_gmailerrorred_rounded, color: color, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  defect.causeLabelEn,
                  style: TextStyle(
                    color: p.ink,
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Text(
                defect.causeLabelAr,
                textDirection: TextDirection.rtl,
                style: TextStyle(color: p.muted, fontSize: 14),
              ),
            ],
          ),
          if (defect.narratorNameAr != null) ...[
            const SizedBox(height: 8),
            InkWell(
              onTap: onNarratorTap,
              borderRadius: BorderRadius.circular(8),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Row(
                  children: [
                    Icon(Icons.person_outline_rounded, size: 16, color: p.muted),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        defect.narratorNameAr!,
                        textDirection: TextDirection.rtl,
                        textAlign: TextAlign.start,
                        style: TextStyle(color: p.ink, fontSize: 15),
                      ),
                    ),
                    if (onNarratorTap != null)
                      Icon(Icons.chevron_right_rounded, color: p.muted),
                  ],
                ),
              ),
            ),
          ],
          if (defect.quoteAr != null) ...[
            const SizedBox(height: 8),
            Text(
              '«${defect.quoteAr}»',
              textDirection: TextDirection.rtl,
              style: TextStyle(
                color: p.ink,
                fontSize: 18,
                height: 1.7,
                fontFamily: libraryArabicFont,
              ),
            ),
          ],
          const SizedBox(height: 6),
          Text(
            '— ${defect.scholar}, ${defect.sourceBook}',
            style: TextStyle(
              color: p.muted,
              fontSize: 13,
              fontStyle: FontStyle.italic,
            ),
          ),
          if (defect.explanationEn != null) ...[
            const SizedBox(height: 6),
            Text(
              defect.explanationEn!,
              style: TextStyle(color: p.ink, fontSize: 14, height: 1.4),
            ),
          ],
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerLeft,
            child: ReviewPill(status: defect.reviewStatus, palette: p),
          ),
        ],
      ),
      ),
    );
  }
}

/// The matn as tappable words; catalogued gharib words carry a dotted
/// underline. Tapping any word asks for its classical meaning.
class MatnView extends StatelessWidget {
  const MatnView({
    super.key,
    required this.text,
    required this.gharibWords,
    required this.palette,
    required this.onWordTap,
  });

  final String text;
  final List<String> gharibWords;
  final LibraryPalette palette;
  final ValueChanged<String> onWordTap;

  @override
  Widget build(BuildContext context) {
    final words = text.split(RegExp(r'\s+')).where((w) => w.isNotEmpty).toList();
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Wrap(
        spacing: 6,
        runSpacing: 4,
        children: [
          for (var i = 0; i < words.length; i++)
            _MatnWord(
              key: ValueKey('matn-word-$i'),
              word: words[i],
              gharib: isGharibToken(words[i], gharibWords),
              palette: palette,
              onTap: () => onWordTap(words[i]),
            ),
        ],
      ),
    );
  }
}

class _MatnWord extends StatelessWidget {
  const _MatnWord({
    super.key,
    required this.word,
    required this.gharib,
    required this.palette,
    required this.onTap,
  });

  final String word;
  final bool gharib;
  final LibraryPalette palette;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 1, vertical: 2),
        child: Text(
          word,
          style: TextStyle(
            color: palette.ink,
            fontSize: 25,
            height: 1.9,
            fontFamily: libraryArabicFont,
            decoration: gharib ? TextDecoration.underline : null,
            decorationStyle: TextDecorationStyle.dotted,
            decorationColor: palette.accent,
            decorationThickness: 2,
          ),
        ),
      ),
    );
  }
}

/// The chain drawn top-down from the Prophet ﷺ to the compiler, each node
/// striped by the narrator's ruled reliability (and labelled, never colour
/// alone).
class IsnadTree extends StatelessWidget {
  const IsnadTree({
    super.key,
    required this.chain,
    required this.palette,
    required this.onNodeTap,
  });

  /// Transmission order: compiler first, Prophet ﷺ last.
  final List<IsnadNode> chain;
  final LibraryPalette palette;
  final ValueChanged<IsnadNode> onNodeTap;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final topDown = chain.reversed.toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (var i = 0; i < topDown.length; i++) ...[
          if (i > 0)
            SizedBox(
              height: 26,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.arrow_downward_rounded, size: 18, color: p.muted),
                  if (topDown[i].termAr != null) ...[
                    const SizedBox(width: 6),
                    Text(
                      topDown[i].termAr!,
                      textDirection: TextDirection.rtl,
                      style: TextStyle(color: p.muted, fontSize: 13),
                    ),
                  ],
                ],
              ),
            ),
          _IsnadNodeTile(
            key: ValueKey('isnad-node-${topDown[i].position}'),
            node: topDown[i],
            palette: p,
            onTap: topDown[i].role == 'narrator'
                ? () => onNodeTap(topDown[i])
                : null,
          ),
        ],
      ],
    );
  }
}

class _IsnadNodeTile extends StatelessWidget {
  const _IsnadNodeTile({
    super.key,
    required this.node,
    required this.palette,
    required this.onTap,
  });

  final IsnadNode node;
  final LibraryPalette palette;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final stripe = p.reliability(node.reliability);
    final status = node.isAmbiguous
        ? 'Ambiguous · ${node.candidates.length} candidates'
        : reliabilityLabel(node.reliability);
    return Material(
      color: p.card,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: p.border),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Container(
          decoration: BoxDecoration(
            border: Border(left: BorderSide(color: stripe, width: 5)),
          ),
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      node.nameAr,
                      textDirection: TextDirection.rtl,
                      style: TextStyle(
                        color: p.ink,
                        fontSize: 19,
                        height: 1.5,
                        fontFamily: libraryArabicFont,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      status,
                      style: TextStyle(
                        color: p.muted,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              if (onTap != null) Icon(Icons.chevron_right_rounded, color: p.muted),
            ],
          ),
        ),
      ),
    );
  }
}

class HadithSummaryTile extends StatelessWidget {
  const HadithSummaryTile({
    super.key,
    required this.hadith,
    required this.palette,
    required this.onTap,
    this.collectionName,
  });

  final HadithSummary hadith;
  final LibraryPalette palette;
  final VoidCallback onTap;
  final String? collectionName;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    return Material(
      color: p.card,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: p.border),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                '${collectionName ?? hadith.collection} · #${hadith.number}',
                style: TextStyle(
                  color: p.muted,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                hadith.matnAr,
                textDirection: TextDirection.rtl,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: p.ink,
                  fontSize: 20,
                  height: 1.7,
                  fontFamily: libraryArabicFont,
                ),
              ),
              if (hadith.translationText != null) ...[
                const SizedBox(height: 4),
                Text(
                  hadith.translationText!,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(color: p.muted, fontSize: 13, height: 1.35),
                ),
              ],
              const SizedBox(height: 10),
              GradeBadges(grades: hadith.grades, palette: p),
            ],
          ),
        ),
      ),
    );
  }
}

class CollectionTile extends StatelessWidget {
  const CollectionTile({
    super.key,
    required this.collection,
    required this.palette,
    required this.onTap,
  });

  final LibraryCollection collection;
  final LibraryPalette palette;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final c = collection;
    final readable = c.isReadable;
    final subtitle = [
      c.authorEn,
      if (c.authorDeathAh != null) 'd. ${c.authorDeathAh} AH',
      if (c.hadithCount != null) '${c.hadithCount} hadith',
    ].join(' · ');
    return Material(
      color: p.card,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: p.border),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: readable ? onTap : null,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 12, 10, 12),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      c.nameAr,
                      textDirection: TextDirection.rtl,
                      style: TextStyle(
                        color: p.ink,
                        fontSize: 20,
                        height: 1.5,
                        fontFamily: libraryArabicFont,
                      ),
                    ),
                    Text(
                      c.nameEn,
                      style: TextStyle(
                        color: p.ink,
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: TextStyle(color: p.muted, fontSize: 12),
                    ),
                    if (!readable) ...[
                      const SizedBox(height: 6),
                      Text(
                        'Catalogued · text coming soon',
                        style: TextStyle(
                          color: p.muted,
                          fontSize: 12,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              if (readable) Icon(Icons.chevron_right_rounded, color: p.muted),
            ],
          ),
        ),
      ),
    );
  }
}
