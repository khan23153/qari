// The Library must work out of the box: when /v1/library is unreachable or
// not yet deployed (404), the app serves the snapshot bundled in the APK.
import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/core/theme/app_theme.dart';
import 'package:qari/data/services/api_client.dart';
import 'package:qari/features/library/data/fallback_library_repository.dart';
import 'package:qari/features/library/data/library_arabic.dart';
import 'package:qari/features/library/data/library_models.dart';
import 'package:qari/features/library/data/library_repository.dart';
import 'package:qari/features/library/data/local_library_repository.dart';
import 'package:qari/features/library/presentation/library_theme.dart';
import 'package:qari/features/library/presentation/pages/hadith_reader_page.dart';
import 'package:qari/features/library/presentation/pages/library_home_page.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:shared_preferences/shared_preferences.dart';

final _assetJson = File('assets/library/library_seed.json').readAsStringSync();

LocalLibraryRepository _local() => LocalLibraryRepository(loadJson: () async => _assetJson);

/// A remote that fails every call the same way and counts attempts.
class _FailingRemote implements LibraryRepository {
  _FailingRemote(this.error);

  final Object Function() error;
  int calls = 0;

  Future<T> _fail<T>() async {
    calls++;
    throw error();
  }

  @override
  Future<List<LibraryCategory>> categories() => _fail();
  @override
  Future<LibraryPage<LibraryCollection>> collections({String? category, int page = 1, int pageSize = 50}) => _fail();
  @override
  Future<LibraryPage<LibraryBook>> books(String slug, {int page = 1, int pageSize = 100}) => _fail();
  @override
  Future<LibraryPage<HadithSummary>> bookHadiths(String slug, int book, {int page = 1, int pageSize = 20}) =>
      _fail();
  @override
  Future<LibraryPage<HadithSummary>> hadiths({String graded = 'all', int page = 1, int pageSize = 20}) => _fail();
  @override
  Future<HadithDetail> hadith(String id) => _fail();
  @override
  Future<NarratorProfile> narrator(String id) => _fail();
  @override
  Future<GharibEntry?> gharib(String word) => _fail();
  @override
  Future<LibrarySearchResult> search(String query) => _fail();
}

/// A healthy remote: delegates to the snapshot but renames the first
/// category, so tests can tell whose data came back.
class _HealthyRemote extends LocalLibraryRepository {
  _HealthyRemote() : super(loadJson: () async => _assetJson);

  int calls = 0;
  bool gharibAlwaysNull = false;
  bool hadithNotFound = false;

  @override
  Future<List<LibraryCategory>> categories() async {
    calls++;
    final cats = await super.categories();
    final first = cats.first;
    return [
      LibraryCategory(slug: first.slug, nameEn: 'From server', nameAr: first.nameAr, collectionCount: 7),
      ...cats.skip(1),
    ];
  }

  @override
  Future<HadithDetail> hadith(String id) async {
    calls++;
    if (hadithNotFound) throw const ApiException(statusCode: 404, message: 'Not Found');
    return super.hadith(id);
  }

  @override
  Future<GharibEntry?> gharib(String word) async => gharibAlwaysNull ? null : super.gharib(word);
}

const _notDeployed = ApiException(statusCode: 404, message: 'Not Found');
const _noConnection = ApiException(statusCode: 0, message: 'No internet', errorCode: 'NO_CONNECTION');

void main() {
  group('Arabic normalisation matches the backend', () {
    test('normalizeArabic', () {
      expect(normalizeArabic('بِالنِّيَّاتِ،'), 'بالنيات');
      expect(normalizeArabic('الأَعْمَالُ'), 'الاعمال');
      expect(normalizeArabic('هِجْرَتُهُ‏'), 'هجرته');
      expect(normalizeArabic('  Sufyan  IBN '), 'sufyan ibn');
    });

    test('stripClitics', () {
      expect(stripClitics('بالنيات'), containsAllInOrder(['بالنيات', 'النيات', 'نيات']));
      expect(stripClitics('فهجرته'), containsAllInOrder(['فهجرته', 'هجرته']));
    });
  });

  group('LocalLibraryRepository (bundled snapshot)', () {
    test('the default loader reads the declared APK asset', () async {
      TestWidgetsFlutterBinding.ensureInitialized();
      final cats = await LocalLibraryRepository().categories();
      expect(cats.map((c) => c.slug), ['hadith', 'tafsir', 'fiqh', 'rijal', 'daif_mawdu']);
    });

    test('catalog, books and hadith', () async {
      final repo = _local();
      final hadith = await repo.collections(category: 'hadith');
      expect(hadith.total, 7);
      expect(hadith.items.first.slug, 'bukhari');
      final books = await repo.books('bukhari');
      expect(books.total, 97);
      expect(books.items.first.nameEn, 'Revelation');
      final t4 = await repo.hadith('tirmidhi:4');
      expect(t4.grades.map((g) => g.label), [
        'Sahih Lighairihi — Ahmad Shakir',
        'Sahih — al-Albani',
        "Daif — Zubair 'Ali Za'i",
      ]);
      final inBook = await repo.bookHadiths('tirmidhi', 1);
      expect(inBook.items.map((h) => h.id), ['tirmidhi:4']);
      final weak = await repo.hadiths(graded: 'weak');
      expect(weak.items.map((h) => h.id), ['tirmidhi:4', 'tirmidhi:172']);
      final fabricated = await repo.hadiths(graded: 'fabricated');
      expect(fabricated.items.map((h) => h.id), ['tirmidhi:172']);
    });

    test('pagination', () async {
      final page2 = await _local().collections(category: 'hadith', page: 2, pageSize: 4);
      expect(page2.items.map((c) => c.slug), ['nasai', 'ibnmajah', 'malik']);
      expect(page2.hasNext, isFalse);
    });

    test('narrator, gharib and search', () async {
      final repo = _local();
      final sufyan = await repo.narrator('sufyan-ibn-uyaynah');
      expect(sufyan.rulings.single.sourceBook, 'Taqrib al-Tahdhib, no. 2451');
      expect(sufyan.teachers.single.id, 'yahya-ibn-said-al-ansari');
      final niyyah = await repo.gharib('بِالنِّيَّاتِ،');
      expect(niyyah?.id, 'niyyah');
      expect(niyyah?.matchedForm, 'النيات');
      expect((await repo.gharib('فَهِجْرَتُهُ'))?.id, 'hijrah');
      expect(await repo.gharib('الصَّلاَةُ'), isNull);
      final s = await repo.search('Sufyan');
      expect(s.narrators.map((n) => n.id).toSet(), {'sufyan-ibn-uyaynah', 'sufyan-al-thawri'});
      expect((await repo.search('مفتاح الجنة')).hadiths.map((h) => h.id), ['tirmidhi:4']);
      expect((await repo.search('Albani')).collections.map((c) => c.slug), ['silsilat-al-daifa']);
    });

    test('records only on the server are reported, not invented', () async {
      expect(() => _local().hadith('muslim:8'), throwsA(isA<LibraryNotBundledException>()));
      expect(() => _local().books('nope'), throwsA(isA<LibraryNotBundledException>()));
    });
  });

  group('FallbackLibraryRepository', () {
    test('library route not deployed (404) → bundled data, banner on', () async {
      final remote = _FailingRemote(() => _notDeployed);
      final repo = FallbackLibraryRepository(remote: remote, local: _local());
      final cats = await repo.categories();
      expect(cats.first.nameEn, 'Hadith');
      expect(repo.usingBundledData.value, isTrue);
      expect((await repo.hadith('tirmidhi:172')).number, 172);
    });

    test('no connection, timeout and unparseable responses all fall back', () async {
      for (final error in <Object Function()>[
        () => _noConnection,
        () => const ApiException(statusCode: 503, message: 'down'),
        () => TypeError(),
        () => const FormatException('<html>'),
      ]) {
        final repo = FallbackLibraryRepository(remote: _FailingRemote(error), local: _local());
        expect((await repo.collections(category: 'hadith')).total, 7);
        expect(repo.usingBundledData.value, isTrue);
      }
    });

    test('a hanging server is cut off by the timeout budget', () async {
      final hanging = Completer<List<LibraryCategory>>();
      final remote = _HangingRemote(hanging.future);
      final repo = FallbackLibraryRepository(
        remote: remote,
        local: _local(),
        remoteTimeout: const Duration(milliseconds: 50),
      );
      final cats = await repo.categories();
      expect(cats, hasLength(5));
      expect(repo.usingBundledData.value, isTrue);
    });

    test('after a failure the server is skipped until retryAfter passes', () async {
      var now = DateTime(2026, 10, 30, 12);
      final remote = _FailingRemote(() => _noConnection);
      final repo = FallbackLibraryRepository(
        remote: remote,
        local: _local(),
        retryAfter: const Duration(minutes: 2),
        clock: () => now,
      );
      await repo.categories();
      await repo.collections();
      await repo.search('Sufyan');
      expect(remote.calls, 1, reason: 'no repeated timeouts while offline');
      now = now.add(const Duration(minutes: 3));
      await repo.categories();
      expect(remote.calls, 2, reason: 'retries the server after the window');
    });

    test('a healthy server is preferred and clears the banner', () async {
      final remote = _HealthyRemote();
      final repo = FallbackLibraryRepository(remote: remote, local: _local());
      repo.usingBundledData.value = true;
      final cats = await repo.categories();
      expect(cats.first.nameEn, 'From server');
      expect(repo.usingBundledData.value, isFalse);
    });

    test('one missing record on a healthy server is not "offline"', () async {
      final remote = _HealthyRemote()..hadithNotFound = true;
      final repo = FallbackLibraryRepository(remote: remote, local: _local());
      // Bundled → served locally, still online.
      expect((await repo.hadith('tirmidhi:4')).number, 4);
      expect(repo.usingBundledData.value, isFalse);
      // Not bundled either → the server's 404 surfaces.
      await expectLater(repo.hadith('muslim:8'), throwsA(isA<ApiException>()));
      // The server is still tried next time.
      await repo.categories();
      expect(remote.calls, 3);
    });

    test('a null gharib from the server is double-checked offline', () async {
      final remote = _HealthyRemote()..gharibAlwaysNull = true;
      final repo = FallbackLibraryRepository(remote: remote, local: _local());
      expect((await repo.gharib('بِالنِّيَّاتِ،'))?.id, 'niyyah');
      expect(await repo.gharib('الصَّلاَةُ'), isNull);
    });
  });

  group('Library UI with the API down', () {
    setUp(() => SharedPreferences.setMockInitialValues({}));

    LibraryEnv offlineEnv() {
      final repo = FallbackLibraryRepository(remote: _FailingRemote(() => _notDeployed), local: _local());
      return LibraryEnv(
        repository: repo,
        themeController: MushafThemeController(),
        usingBundledData: repo.usingBundledData,
      );
    }

    testWidgets('home shows the bundled shelves and the offline banner', (tester) async {
      tester.view.physicalSize = const Size(900, 4000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(MaterialApp(theme: AppTheme.darkTheme, home: LibraryHomePage(env: offlineEnv())));
      await tester.pumpAndSettle();
      expect(find.text('Sahih al-Bukhari'), findsOneWidget);
      expect(find.byKey(const ValueKey('library-offline-banner')), findsOneWidget);
    });

    testWidgets('no banner when the server answers', (tester) async {
      tester.view.physicalSize = const Size(900, 4000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      final repo = FallbackLibraryRepository(remote: _HealthyRemote(), local: _local());
      final env = LibraryEnv(
        repository: repo,
        themeController: MushafThemeController(),
        usingBundledData: repo.usingBundledData,
      );
      await tester.pumpWidget(MaterialApp(theme: AppTheme.darkTheme, home: LibraryHomePage(env: env)));
      await tester.pumpAndSettle();
      expect(find.text('Sahih al-Bukhari'), findsOneWidget);
      expect(find.byKey(const ValueKey('library-offline-banner')), findsNothing);
    });

    testWidgets('a bundled hadith opens fully offline', (tester) async {
      tester.view.physicalSize = const Size(900, 7000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(MaterialApp(
        theme: AppTheme.darkTheme,
        home: HadithReaderPage(env: offlineEnv(), hadithId: 'tirmidhi:172'),
      ));
      await tester.pumpAndSettle();
      expect(find.text('Mawdu — al-Albani'), findsOneWidget);
      expect(find.text('Liar or abandoned narrator'), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('isnad-node-2')));
      await tester.pumpAndSettle();
      expect(find.text('يعقوب بن الوليد المدني'), findsWidgets);
    });
  });
}

class _HangingRemote extends _FailingRemote {
  _HangingRemote(this._never) : super(() => StateError('unused'));

  final Future<List<LibraryCategory>> _never;

  @override
  Future<List<LibraryCategory>> categories() {
    calls++;
    return _never;
  }
}
