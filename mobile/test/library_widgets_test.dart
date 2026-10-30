// Islamic Library UI: shelves, reader, scholar grade badges, defect cards,
// gharib sheet, isnad tree, narrator sheet, search, entry card, and contrast
// on every Mushaf paper preset.
//
// Hosts run under AppTheme.darkTheme on purpose: library routes and sheets
// must take their colours from the chosen paper, never from the app theme.
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/core/theme/app_theme.dart';
import 'package:qari/features/library/data/library_models.dart';
import 'package:qari/features/library/data/library_repository.dart';
import 'package:qari/features/library/presentation/library_theme.dart';
import 'package:qari/features/library/presentation/pages/hadith_reader_page.dart';
import 'package:qari/features/library/presentation/pages/library_home_page.dart';
import 'package:qari/features/library/presentation/pages/library_search_page.dart';
import 'package:qari/features/library/presentation/widgets/library_entry_card.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:shared_preferences/shared_preferences.dart';

final _fixtures = <String, Object?>{};

Object? _fx(String name) => _fixtures.putIfAbsent(
      name,
      () => jsonDecode(File('test/fixtures/library/$name.json').readAsStringSync()),
    );

Map<String, dynamic> _map(String name) => _fx(name)! as Map<String, dynamic>;

class FakeLibraryRepository implements LibraryRepository {
  final List<String> gharibLookups = [];

  static const _hadiths = {
    'bukhari:1': 'hadith_bukhari_1',
    'abudawud:2201': 'hadith_abudawud_2201',
    'tirmidhi:4': 'hadith_tirmidhi_4',
    'tirmidhi:172': 'hadith_tirmidhi_172',
  };
  static const _narrators = {
    'sufyan-ibn-uyaynah': 'narrator_sufyan_ibn_uyaynah',
    'sulayman-ibn-qarm': 'narrator_sulayman_ibn_qarm',
  };

  @override
  Future<List<LibraryCategory>> categories() async => [
        for (final c in _fx('categories')! as List<dynamic>)
          LibraryCategory.fromJson(c as Map<String, dynamic>),
      ];

  @override
  Future<LibraryPage<LibraryCollection>> collections({
    String? category,
    int page = 1,
    int pageSize = 50,
  }) async {
    final all = LibraryPage.fromJson(_map('collections_all'), LibraryCollection.fromJson);
    final items = all.items.where((c) => category == null || c.category == category).toList();
    return LibraryPage(items: items, total: items.length, page: 1, hasNext: false);
  }

  @override
  Future<LibraryPage<LibraryBook>> books(String slug, {int page = 1, int pageSize = 100}) async =>
      LibraryPage.fromJson(_map('books_bukhari'), LibraryBook.fromJson);

  @override
  Future<LibraryPage<HadithSummary>> bookHadiths(String slug, int book,
          {int page = 1, int pageSize = 20}) async =>
      LibraryPage.fromJson(_map('hadiths_weak'), HadithSummary.fromJson);

  @override
  Future<LibraryPage<HadithSummary>> hadiths({String graded = 'all', int page = 1, int pageSize = 20}) async =>
      LibraryPage.fromJson(_map('hadiths_weak'), HadithSummary.fromJson);

  @override
  Future<HadithDetail> hadith(String id) async => HadithDetail.fromJson(_map(_hadiths[id]!));

  @override
  Future<NarratorProfile> narrator(String id) async {
    final name = _narrators[id];
    if (name == null) throw StateError('no fixture for $id');
    return NarratorProfile.fromJson(_map(name));
  }

  @override
  Future<GharibEntry?> gharib(String word) async {
    gharibLookups.add(word);
    return bareArabicWord(word).contains('نيات') ? GharibEntry.fromJson(_map('gharib_niyyah')) : null;
  }

  @override
  Future<LibrarySearchResult> search(String query) async =>
      LibrarySearchResult.fromJson(_map('search_sufyan'));
}

LibraryEnv _env(MushafTheme theme, [FakeLibraryRepository? repo]) {
  final controller = MushafThemeController();
  unawaited(controller.select(theme));
  return LibraryEnv(repository: repo ?? FakeLibraryRepository(), themeController: controller);
}

Widget _app(Widget home) => MaterialApp(theme: AppTheme.darkTheme, home: home);

Future<void> _tall(WidgetTester tester) async {
  tester.view.physicalSize = const Size(900, 7000);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

double _contrast(Color fg, Color bg) {
  final a = Color.alphaBlend(fg, bg).computeLuminance();
  final b = bg.computeLuminance();
  return (math.max(a, b) + 0.05) / (math.min(a, b) + 0.05);
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  group('palette contrast on every paper preset', () {
    for (final t in MushafTheme.all) {
      test(t.id, () {
        final p = LibraryPalette(t);
        expect(_contrast(p.ink, p.card), greaterThanOrEqualTo(4.5));
        expect(_contrast(p.muted, p.card), greaterThanOrEqualTo(4.5));
        for (final r in RulingType.values) {
          final c = p.ruling(r);
          expect(_contrast(c, p.badge(c)), greaterThanOrEqualTo(4.5),
              reason: '$r badge text on ${t.id}');
        }
        for (final r in Reliability.values.where((r) => r != Reliability.prophet)) {
          expect(_contrast(p.reliability(r), p.card), greaterThanOrEqualTo(3.0),
              reason: '$r stripe on ${t.id}');
        }
        expect(ThemeData.estimateBrightnessForColor(p.card),
            ThemeData.estimateBrightnessForColor(p.paper));
      });
    }
  });

  group('library home', () {
    testWidgets('shows one tab per non-empty shelf and lists collections', (tester) async {
      await _tall(tester);
      await tester.pumpWidget(_app(LibraryHomePage(env: _env(MushafTheme.parchment))));
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('library-tab-hadith')), findsOneWidget);
      expect(find.byKey(const ValueKey('library-tab-tafsir')), findsOneWidget);
      expect(find.byKey(const ValueKey('library-tab-rijal')), findsOneWidget);
      expect(find.byKey(const ValueKey('library-tab-daif_mawdu')), findsOneWidget);
      expect(find.byKey(const ValueKey('library-tab-fiqh')), findsNothing,
          reason: 'no collections on that shelf yet');
      expect(find.text('Sahih al-Bukhari'), findsOneWidget);
      expect(find.text('Muwatta Malik'), findsOneWidget);
      // The page paints the chosen paper even under the dark app theme.
      final scaffold = tester.widget<Scaffold>(find.byType(Scaffold).first);
      expect(scaffold.backgroundColor, MushafTheme.parchment.background);
    });

    testWidgets('catalogued-only collections are marked, not tappable', (tester) async {
      await _tall(tester);
      await tester.pumpWidget(_app(LibraryHomePage(env: _env(MushafTheme.classic))));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('library-tab-tafsir')));
      await tester.pumpAndSettle();
      expect(find.text('Tafsir al-Qur\'an al-\'Azim'), findsOneWidget);
      expect(find.text('Catalogued · text coming soon'), findsNWidgets(3));
    });

    testWidgets('weak & fabricated shelf lists critical works and graded narrations',
        (tester) async {
      await _tall(tester);
      await tester.pumpWidget(_app(LibraryHomePage(env: _env(MushafTheme.night))));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('library-tab-daif_mawdu')));
      await tester.pumpAndSettle();
      expect(find.text('Al-Mawdu\'at'), findsOneWidget);
      expect(find.text('Silsilat al-Ahadith al-Da\'ifa wa al-Mawdu\'a'), findsOneWidget);
      expect(find.byKey(const ValueKey('weak-hadith-tirmidhi:4')), findsOneWidget);
      expect(find.byKey(const ValueKey('weak-hadith-tirmidhi:172')), findsOneWidget);
      expect(find.text('Mawdu — al-Albani'), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('weak-hadith-tirmidhi:172')));
      await tester.pumpAndSettle();
      expect(find.byType(HadithReaderPage), findsOneWidget);
    });
  });

  group('hadith reader', () {
    testWidgets('shows every scholar grade and cited defects', (tester) async {
      await _tall(tester);
      final env = _env(MushafTheme.classic);
      await tester.pumpWidget(_app(HadithReaderPage(env: env, hadithId: 'tirmidhi:4')));
      await tester.pumpAndSettle();

      expect(find.text('Sahih Lighairihi — Ahmad Shakir'), findsOneWidget);
      expect(find.text('Sahih — al-Albani'), findsOneWidget);
      expect(find.text("Daif — Zubair 'Ali Za'i"), findsOneWidget);
      expect(find.byKey(const ValueKey('defect-card-0')), findsOneWidget);
      expect(find.byKey(const ValueKey('defect-card-1')), findsOneWidget);
      expect(find.text("— Ibn Hajar al-'Asqalani, Taqrib al-Tahdhib, no. 2600"), findsOneWidget);
      expect(find.text('Weak memory or precision'), findsNWidgets(2));
      expect(find.text('Verified from source'), findsWidgets);

      // Badge text is the ruling hue, readable on its tint.
      final p = env.palette;
      final daif = tester.widget<Text>(find.text("Daif — Zubair 'Ali Za'i"));
      expect(daif.style!.color, p.ruling(RulingType.daif));
      final scaffold = tester.widget<Scaffold>(find.byType(Scaffold).first);
      expect(scaffold.backgroundColor, MushafTheme.classic.background);
    });

    testWidgets('fabricated hadith shows compiler note and liar defect', (tester) async {
      await _tall(tester);
      await tester.pumpWidget(_app(HadithReaderPage(env: _env(MushafTheme.night), hadithId: 'tirmidhi:172')));
      await tester.pumpAndSettle();
      expect(find.text('Mawdu — al-Albani'), findsOneWidget);
      expect(find.text("Compiler's note"), findsOneWidget);
      expect(find.text('Liar or abandoned narrator'), findsOneWidget);
      expect(find.text('«كذبه أحمد وغيره»'), findsOneWidget);
    });

    testWidgets('tapping a matn word opens the gharib sheet on the paper', (tester) async {
      await _tall(tester);
      final repo = FakeLibraryRepository();
      final env = _env(MushafTheme.parchment, repo);
      await tester.pumpWidget(_app(HadithReaderPage(env: env, hadithId: 'bukhari:1')));
      await tester.pumpAndSettle();

      // Word 2 of the matn is «بِالنِّيَّاتِ،», a catalogued gharib word.
      final word = tester.widget<Text>(find.descendant(
        of: find.byKey(const ValueKey('matn-word-2')),
        matching: find.byType(Text),
      ));
      expect(word.style!.decoration, TextDecoration.underline);
      await tester.tap(find.byKey(const ValueKey('matn-word-2')));
      await tester.pumpAndSettle();

      expect(repo.gharibLookups.single, word.data);
      expect(find.text('ن و ي'), findsOneWidget);
      expect(find.text('an-niyyāt'), findsOneWidget);
      expect(find.textContaining('Nihayah'), findsOneWidget);
      final sheet = tester.widget<BottomSheet>(find.byType(BottomSheet));
      expect(sheet.backgroundColor, MushafTheme.parchment.background);

      // A word with no entry says so instead of guessing.
      Navigator.of(tester.element(find.text('an-niyyāt'))).pop();
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('matn-word-0')));
      await tester.pumpAndSettle();
      expect(find.text('No classical Gharib entry is catalogued for this word yet.'), findsOneWidget);
    });

    testWidgets('isnad runs from the Prophet ﷺ down to the compiler', (tester) async {
      await _tall(tester);
      await tester.pumpWidget(_app(HadithReaderPage(env: _env(MushafTheme.classic), hadithId: 'bukhari:1')));
      await tester.pumpAndSettle();
      final prophet = tester.getTopLeft(find.byKey(const ValueKey('isnad-node-7')));
      final sufyan = tester.getTopLeft(find.byKey(const ValueKey('isnad-node-2')));
      final compiler = tester.getTopLeft(find.byKey(const ValueKey('isnad-node-0')));
      expect(prophet.dy, lessThan(sufyan.dy));
      expect(sufyan.dy, lessThan(compiler.dy));
      expect(find.text('Thiqah · trustworthy'), findsWidgets);
      expect(find.text('Sahabi · Companion'), findsOneWidget);
    });

    testWidgets('tapping a narrator opens the rijal profile', (tester) async {
      await _tall(tester);
      await tester.pumpWidget(_app(HadithReaderPage(env: _env(MushafTheme.night), hadithId: 'bukhari:1')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('isnad-node-2')));
      await tester.pumpAndSettle();

      expect(find.text('سفيان بن عيينة'), findsOneWidget);
      expect(find.text("Ibn Hajar al-'Asqalani, Taqrib al-Tahdhib, no. 2451"), findsOneWidget);
      expect(find.text('Tabaqah 8 (Ibn Hajar)'), findsOneWidget);
      expect(find.text('Died 198 AH'), findsOneWidget);
      expect(find.text('يحيى بن سعيد بن قيس الأنصاري'), findsOneWidget);
      expect(find.text('عبد الله بن الزبير الحميدي'), findsOneWidget);
      await tester.tap(find.text('Full entry in the source'));
      await tester.pumpAndSettle();
      expect(find.textContaining('سفيان ابن عيينة ابن أبي عمران'), findsOneWidget);
    });

    testWidgets('an ambiguous narrator lists candidates', (tester) async {
      await _tall(tester);
      await tester.pumpWidget(_app(HadithReaderPage(env: _env(MushafTheme.minimal), hadithId: 'abudawud:2201')));
      await tester.pumpAndSettle();
      expect(find.text('Ambiguous · 2 candidates'), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('isnad-node-2')));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('candidate-sufyan-ibn-uyaynah')), findsOneWidget);
      expect(find.byKey(const ValueKey('candidate-sufyan-al-thawri')), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('candidate-sufyan-ibn-uyaynah')));
      await tester.pumpAndSettle();
      expect(find.text('سفيان بن عيينة'), findsOneWidget);
    });
  });

  testWidgets('search finds narrators', (tester) async {
    await _tall(tester);
    await tester.pumpWidget(_app(LibrarySearchPage(env: _env(MushafTheme.classic))));
    await tester.enterText(find.byKey(const ValueKey('library-search-field')), 'Sufyan');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('search-narrator-sufyan-ibn-uyaynah')), findsOneWidget);
    expect(find.byKey(const ValueKey('search-narrator-sufyan-al-thawri')), findsOneWidget);
  });

  testWidgets('home entry card opens the library', (tester) async {
    await _tall(tester);
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.lightTheme,
      home: Scaffold(
        body: LibraryEntryCard(envBuilder: () => _env(MushafTheme.classic)),
      ),
    ));
    expect(find.text('Islamic Library'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('library-entry-card')));
    await tester.pumpAndSettle();
    expect(find.byType(LibraryHomePage), findsOneWidget);
    expect(find.text('Sahih al-Bukhari'), findsOneWidget);
  });
}
