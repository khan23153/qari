import 'package:flutter/material.dart';

import '../../data/library_models.dart';
import '../library_theme.dart';
import '../widgets/library_sheets.dart';
import '../widgets/library_widgets.dart';

/// One hadith: scholar grades, tappable matn, translation, isnad tree and the
/// cited reasons when a scholar judged it weak or fabricated.
class HadithReaderPage extends StatelessWidget {
  const HadithReaderPage({super.key, required this.env, required this.hadithId});

  final LibraryEnv env;
  final String hadithId;

  void _openNode(BuildContext context, IsnadNode node) {
    final id = node.narratorId;
    if (id != null) {
      showNarratorSheet(context, env, id);
    } else {
      showUnresolvedNarratorSheet(context, env, node);
    }
  }

  @override
  Widget build(BuildContext context) {
    return LibraryThemed(
      env: env,
      builder: (context, p) => Scaffold(
        backgroundColor: p.paper,
        appBar: AppBar(title: Text(hadithId)),
        body: LibraryAsync<HadithDetail>(
          palette: p,
          load: () => env.repository.hadith(hadithId),
          builder: (context, h) => ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 40),
            children: [
              _Header(hadith: h, palette: p),
              const SizedBox(height: 14),
              GradeBadges(grades: h.grades, palette: p),
              const SizedBox(height: 18),
              MatnView(
                text: h.bodyAr,
                gharibWords: h.gharibWords,
                palette: p,
                onWordTap: (word) => showGharibSheet(context, env, word),
              ),
              const SizedBox(height: 4),
              Text(
                'Tap any word for its classical meaning. Dotted words have a Gharib entry.',
                style: TextStyle(color: p.muted, fontSize: 12),
              ),
              if (h.translation != null) ...[
                const SizedBox(height: 16),
                Text(
                  h.translation!.text,
                  style: TextStyle(color: p.ink, fontSize: 16, height: 1.5),
                ),
                const SizedBox(height: 4),
                Text(
                  h.translation!.licenseStatus == 'unverified'
                      ? 'Translation: ${h.translation!.source} · licence not yet verified'
                      : 'Translation: ${h.translation!.source}',
                  style: TextStyle(color: p.muted, fontSize: 12),
                ),
              ],
              if (h.compilerNoteAr != null) ...[
                const SizedBox(height: 16),
                _Section(title: "Compiler's note", palette: p),
                Text(
                  h.compilerNoteAr!,
                  textDirection: TextDirection.rtl,
                  style: TextStyle(
                    color: p.ink,
                    fontSize: 19,
                    height: 1.8,
                    fontFamily: libraryArabicFont,
                  ),
                ),
              ],
              if (h.defects.isNotEmpty) ...[
                const SizedBox(height: 20),
                _Section(title: 'Why scholars weakened this chain', palette: p),
                for (var i = 0; i < h.defects.length; i++) ...[
                  DefectCard(
                    key: ValueKey('defect-card-$i'),
                    defect: h.defects[i],
                    palette: p,
                    onNarratorTap: h.defects[i].narratorId == null
                        ? null
                        : () => showNarratorSheet(context, env, h.defects[i].narratorId!),
                  ),
                  const SizedBox(height: 10),
                ],
              ],
              const SizedBox(height: 20),
              _Section(title: 'Chain of narration (isnad)', palette: p),
              if (h.chain.isEmpty)
                Text(
                  h.isnadAr ?? 'The chain for this narration is not yet indexed.',
                  textDirection: h.isnadAr == null ? TextDirection.ltr : TextDirection.rtl,
                  style: TextStyle(color: p.muted, fontSize: 15, height: 1.6),
                )
              else
                IsnadTree(
                  chain: h.chain,
                  palette: p,
                  onNodeTap: (node) => _openNode(context, node),
                ),
              const SizedBox(height: 24),
              Text(
                'Source: ${h.sourceDataset} (${h.sourceLicense})',
                style: TextStyle(color: p.muted, fontSize: 12),
              ),
              const SizedBox(height: 6),
              Align(
                alignment: Alignment.centerLeft,
                child: ReviewPill(status: h.reviewStatus, palette: p),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.hadith, required this.palette});

  final HadithDetail hadith;
  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          hadith.collectionNameAr,
          textDirection: TextDirection.rtl,
          style: TextStyle(
            color: p.ink,
            fontSize: 22,
            height: 1.5,
            fontFamily: libraryArabicFont,
          ),
        ),
        Text(
          '${hadith.collectionNameEn} · #${hadith.number}',
          style: TextStyle(
            color: p.ink,
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        if (hadith.bookNameEn != null)
          Text(
            'Book ${hadith.bookNumber}: ${hadith.bookNameEn}',
            style: TextStyle(color: p.muted, fontSize: 13),
          ),
      ],
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.palette});

  final String title;
  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(
          title,
          style: TextStyle(
            color: palette.ink,
            fontSize: 17,
            fontWeight: FontWeight.w700,
          ),
        ),
      );
}
