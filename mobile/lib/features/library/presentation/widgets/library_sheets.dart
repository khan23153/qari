import 'package:flutter/material.dart';

import '../../data/library_models.dart';
import '../library_theme.dart';
import 'library_widgets.dart';

/// Opens a library sheet. The builder is wrapped in [LibraryThemed] because a
/// modal route only inherits themes from the navigator, not from the page
/// that opened it.
Future<void> showLibrarySheet(
  BuildContext context, {
  required LibraryEnv env,
  required Widget Function(BuildContext context, LibraryPalette palette) builder,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    backgroundColor: env.palette.paper,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
    ),
    builder: (_) => LibraryThemed(
      env: env,
      builder: (context, palette) => ConstrainedBox(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.sizeOf(context).height * 0.85,
        ),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
          child: builder(context, palette),
        ),
      ),
    ),
  );
}

class _Handle extends StatelessWidget {
  const _Handle(this.palette);

  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) => Center(
        child: Container(
          width: 42,
          height: 4,
          margin: const EdgeInsets.only(bottom: 14),
          decoration: BoxDecoration(
            color: palette.ink.withValues(alpha: 0.18),
            borderRadius: BorderRadius.circular(2),
          ),
        ),
      );
}

/// Gharib al-Hadith / morphology for one tapped word.
Future<void> showGharibSheet(BuildContext context, LibraryEnv env, String word) {
  return showLibrarySheet(
    context,
    env: env,
    builder: (context, p) => Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Handle(p),
        Text(
          word,
          key: const ValueKey('gharib-sheet-word'),
          textAlign: TextAlign.center,
          textDirection: TextDirection.rtl,
          style: TextStyle(
            color: p.ink,
            fontSize: 32,
            height: 1.6,
            fontFamily: libraryArabicFont,
          ),
        ),
        const SizedBox(height: 8),
        LibraryAsync<GharibEntry?>(
          palette: p,
          load: () => env.repository.gharib(word),
          builder: (context, entry) => entry == null
              ? Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Text(
                    'No classical Gharib entry is catalogued for this word yet.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: p.muted, fontSize: 14),
                  ),
                )
              : _GharibBody(entry: entry, palette: p),
        ),
      ],
    ),
  );
}

class _GharibBody extends StatelessWidget {
  const _GharibBody({required this.entry, required this.palette});

  final GharibEntry entry;
  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    Widget row(String label, String value, {bool arabic = false}) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 110,
                child: Text(
                  label,
                  style: TextStyle(
                    color: p.muted,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Expanded(
                child: Text(
                  value,
                  textDirection: arabic ? TextDirection.rtl : TextDirection.ltr,
                  style: TextStyle(
                    color: p.ink,
                    fontSize: arabic ? 20 : 15,
                    height: arabic ? 1.6 : 1.35,
                    fontFamily: arabic ? libraryArabicFont : null,
                  ),
                ),
              ),
            ],
          ),
        );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        row('Root', entry.rootAr, arabic: true),
        row('Transliteration', entry.transliteration),
        row('Meaning', entry.glossEn),
        if (entry.definitionAr != null)
          row('Classical', entry.definitionAr!, arabic: true),
        const SizedBox(height: 8),
        Text(
          entry.sourceBook,
          style: TextStyle(
            color: p.muted,
            fontSize: 12,
            fontStyle: FontStyle.italic,
          ),
        ),
        const SizedBox(height: 8),
        Align(
          alignment: Alignment.centerLeft,
          child: ReviewPill(status: entry.reviewStatus, palette: p),
        ),
      ],
    );
  }
}

/// Ilm al-Rijal profile for one narrator.
Future<void> showNarratorSheet(BuildContext context, LibraryEnv env, String narratorId) {
  return showLibrarySheet(
    context,
    env: env,
    builder: (context, p) => Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Handle(p),
        LibraryAsync<NarratorProfile>(
          palette: p,
          load: () => env.repository.narrator(narratorId),
          builder: (context, n) => _NarratorBody(narrator: n, palette: p),
        ),
      ],
    ),
  );
}

/// For a chain node whose narrator is ambiguous or not yet identified.
Future<void> showUnresolvedNarratorSheet(
  BuildContext context,
  LibraryEnv env,
  IsnadNode node,
) {
  return showLibrarySheet(
    context,
    env: env,
    builder: (sheetContext, p) => Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Handle(p),
        Text(
          node.nameAr,
          textDirection: TextDirection.rtl,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: p.ink,
            fontSize: 26,
            height: 1.6,
            fontFamily: libraryArabicFont,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          node.isAmbiguous
              ? 'This name is shared by more than one narrator. The library '
                  'lists the candidates instead of guessing.'
              : 'This narrator is not yet identified in the library.',
          textAlign: TextAlign.center,
          style: TextStyle(color: p.muted, fontSize: 14, height: 1.4),
        ),
        for (final candidate in node.candidates) ...[
          const SizedBox(height: 10),
          OutlinedButton(
            key: ValueKey('candidate-$candidate'),
            style: OutlinedButton.styleFrom(
              foregroundColor: p.ink,
              side: BorderSide(color: p.border),
            ),
            onPressed: () {
              Navigator.of(sheetContext).pop();
              showNarratorSheet(context, env, candidate);
            },
            child: Text(candidate),
          ),
        ],
      ],
    ),
  );
}

class _NarratorBody extends StatelessWidget {
  const _NarratorBody({required this.narrator, required this.palette});

  final NarratorProfile narrator;
  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    final n = narrator;
    final color = p.reliability(n.reliability);
    final facts = [
      if (n.kunyaAr != null) 'Kunya: ${n.kunyaAr}',
      'Generation: ${_generation(n.generation)}',
      if (n.tabaqah != null) 'Tabaqah ${n.tabaqah} (Ibn Hajar)',
      if (n.birthYearAh != null) 'Born ${n.birthYearAh} AH',
      if (n.deathYearAh != null)
        'Died ${n.deathYearAh} AH'
      else if (n.deathNote != null)
        'Died ${n.deathNote}',
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          n.nameAr,
          textAlign: TextAlign.center,
          textDirection: TextDirection.rtl,
          style: TextStyle(
            color: p.ink,
            fontSize: 28,
            height: 1.6,
            fontFamily: libraryArabicFont,
          ),
        ),
        Text(
          n.nameEn,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: p.ink,
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Center(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
            decoration: BoxDecoration(
              color: p.badge(color),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: color.withValues(alpha: 0.55)),
            ),
            child: Text(
              reliabilityLabel(n.reliability),
              style: TextStyle(
                color: color,
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        for (final f in facts)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 2),
            child: Text(f, style: TextStyle(color: p.ink, fontSize: 14)),
          ),
        const SizedBox(height: 14),
        Text(
          "Jarh wa Ta'dil",
          style: TextStyle(
            color: p.ink,
            fontSize: 16,
            fontWeight: FontWeight.w700,
          ),
        ),
        for (final r in n.rulings) ...[
          const SizedBox(height: 8),
          // A Material (not a coloured Container) so the ExpansionTile below
          // can paint its ink on it.
          Material(
            color: p.card,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: BorderSide(color: p.border),
            ),
            child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  r.rulingAr,
                  textDirection: TextDirection.rtl,
                  style: TextStyle(
                    color: p.ink,
                    fontSize: 19,
                    height: 1.6,
                    fontFamily: libraryArabicFont,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  r.rulingEn,
                  style: TextStyle(color: p.ink, fontSize: 14, height: 1.35),
                ),
                const SizedBox(height: 6),
                Text(
                  [r.scholar, if (r.sourceBook != null) r.sourceBook].join(', '),
                  style: TextStyle(
                    color: p.muted,
                    fontSize: 12,
                    fontStyle: FontStyle.italic,
                  ),
                ),
                const SizedBox(height: 6),
                Align(
                  alignment: Alignment.centerLeft,
                  child: ReviewPill(status: r.reviewStatus, palette: p),
                ),
                if (r.sourceTextAr != null)
                  Theme(
                    data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
                    child: ExpansionTile(
                      key: ValueKey('ruling-source-${n.id}'),
                      tilePadding: EdgeInsets.zero,
                      iconColor: p.muted,
                      collapsedIconColor: p.muted,
                      title: Text(
                        'Full entry in the source',
                        style: TextStyle(color: p.ink, fontSize: 13, fontWeight: FontWeight.w600),
                      ),
                      children: [
                        Text(
                          r.sourceTextAr!,
                          textDirection: TextDirection.rtl,
                          style: TextStyle(
                            color: p.ink,
                            fontSize: 17,
                            height: 1.7,
                            fontFamily: libraryArabicFont,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
            ),
          ),
        ],
        if (n.teachers.isNotEmpty) ...[
          const SizedBox(height: 14),
          _PeopleList(title: 'Narrates from', people: n.teachers, palette: p),
        ],
        if (n.students.isNotEmpty) ...[
          const SizedBox(height: 10),
          _PeopleList(title: 'Narrated to', people: n.students, palette: p),
        ],
      ],
    );
  }

  static String _generation(String g) => switch (g) {
        'sahabi' => 'Sahabah (Companions)',
        'tabii' => "Tabi'un (Successors)",
        'atba_al_tabiin' => "Atba' al-Tabi'in",
        'taba_atba' => "Those after the Atba' al-Tabi'in",
        _ => g,
      };
}

class _PeopleList extends StatelessWidget {
  const _PeopleList({
    required this.title,
    required this.people,
    required this.palette,
  });

  final String title;
  final List<NarratorBrief> people;
  final LibraryPalette palette;

  @override
  Widget build(BuildContext context) {
    final p = palette;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          title,
          style: TextStyle(
            color: p.muted,
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 4),
        Wrap(
          spacing: 8,
          runSpacing: 6,
          children: [
            for (final person in people)
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: p.card,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: p.reliability(person.reliability)),
                ),
                child: Text(
                  person.nameAr,
                  textDirection: TextDirection.rtl,
                  style: TextStyle(color: p.ink, fontSize: 15),
                ),
              ),
          ],
        ),
      ],
    );
  }
}
