// Islamic Library models and repository against fixtures captured from the
// real FastAPI responses (`/v1/library/...`), so mobile and backend cannot
// drift apart silently.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qari/data/services/api_client.dart';
import 'package:qari/features/library/data/library_models.dart';
import 'package:qari/features/library/data/library_repository.dart';

String fixture(String name) =>
    File('test/fixtures/library/$name.json').readAsStringSync();

Map<String, dynamic> fixtureMap(String name) =>
    jsonDecode(fixture(name)) as Map<String, dynamic>;

class _FakeAdapter implements HttpClientAdapter {
  _FakeAdapter(this.routes);

  /// Request path (as passed to Dio) → (status, fixture name or raw body).
  final Map<String, (int, String)> routes;
  final List<RequestOptions> requests = [];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    final hit = routes[options.path];
    if (hit == null) {
      return ResponseBody.fromString('{"title":"Not Found"}', 404, headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      });
    }
    final (status, body) = hit;
    return ResponseBody.fromString(
      body.startsWith('{') || body.startsWith('[') ? body : fixture(body),
      status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  group('models parse real API responses', () {
    test('categories and collections', () {
      final cats = [
        for (final c in jsonDecode(fixture('categories')) as List<dynamic>)
          LibraryCategory.fromJson(c as Map<String, dynamic>),
      ];
      expect(cats.map((c) => c.slug),
          ['hadith', 'tafsir', 'fiqh', 'rijal', 'daif_mawdu']);
      expect(cats.firstWhere((c) => c.slug == 'fiqh').collectionCount, 0);

      final page = LibraryPage.fromJson(
          fixtureMap('collections_all'), LibraryCollection.fromJson);
      final bukhari = page.items.firstWhere((c) => c.slug == 'bukhari');
      expect(bukhari.isReadable, isTrue);
      expect(bukhari.bookCount, 97);
      final silsila = page.items.firstWhere((c) => c.slug == 'silsilat-al-daifa');
      expect(silsila.isReadable, isFalse, reason: 'catalogued, text planned');
      expect(silsila.authorDeathAh, 1420);
    });

    test('hadith detail: grades, chain order, defects with verbatim source', () {
      final h = HadithDetail.fromJson(fixtureMap('hadith_tirmidhi_4'));
      expect(h.grades.map((g) => g.label), [
        'Sahih Lighairihi — Ahmad Shakir',
        'Sahih — al-Albani',
        "Daif — Zubair 'Ali Za'i",
      ]);
      expect(h.grades.map((g) => g.rulingType),
          [RulingType.sahih, RulingType.sahih, RulingType.daif]);
      expect(h.chain.first.role, 'compiler');
      expect(h.chain.last.role, 'prophet');
      expect(h.defects, hasLength(2));
      final first = h.defects.first;
      expect(first.cause, 'su_al_hifz');
      expect(first.sourceBook, 'Taqrib al-Tahdhib, no. 2600');
      expect(first.reviewStatus, ReviewStatus.verifiedFromSource);
      expect(first.sourceTextAr, contains(first.quoteAr!));
    });

    test('ambiguous narrator keeps candidates', () {
      final h = HadithDetail.fromJson(fixtureMap('hadith_abudawud_2201'));
      final sufyan = h.chain.firstWhere((n) => n.isAmbiguous);
      expect(sufyan.narratorId, isNull);
      expect(sufyan.candidates, ['sufyan-ibn-uyaynah', 'sufyan-al-thawri']);
      expect(sufyan.reliability, Reliability.unknown);
    });

    test('narrator profile with Taqrib entry and derived links', () {
      final n = NarratorProfile.fromJson(fixtureMap('narrator_sufyan_ibn_uyaynah'));
      expect(n.reliability, Reliability.thiqah);
      expect(n.tabaqah, 8);
      expect(n.deathYearAh, 198);
      expect(n.rulings.single.sourceBook, 'Taqrib al-Tahdhib, no. 2451');
      expect(n.rulings.single.sourceTextAr, contains('سفيان ابن عيينة'));
      expect(n.teachers.single.id, 'yahya-ibn-said-al-ansari');
      expect(n.students.single.id, 'al-humaydi');
    });

    test('gharib and search', () {
      final g = GharibEntry.fromJson(fixtureMap('gharib_niyyah'));
      expect(g.rootAr, 'ن و ي');
      expect(g.transliteration, 'an-niyyāt');
      final r = LibrarySearchResult.fromJson(fixtureMap('search_sufyan'));
      expect(r.narrators.map((n) => n.id).toSet(),
          {'sufyan-ibn-uyaynah', 'sufyan-al-thawri'});
      expect(r.isEmpty, isFalse);
    });
  });

  group('ApiLibraryRepository', () {
    late _FakeAdapter adapter;
    late ApiLibraryRepository repo;

    setUp(() {
      adapter = _FakeAdapter({
        '/library/categories': (200, 'categories'),
        '/library/collections': (200, 'collections_all'),
        '/library/collections/bukhari/books': (200, 'books_bukhari'),
        '/library/hadiths': (200, 'hadiths_weak'),
        '/library/hadiths/tirmidhi:4': (200, 'hadith_tirmidhi_4'),
        '/library/narrators/sufyan-ibn-uyaynah': (200, 'narrator_sufyan_ibn_uyaynah'),
        '/library/gharib/${Uri.encodeComponent('بِالنِّيَّاتِ،')}': (200, 'gharib_niyyah'),
        '/library/search': (200, 'search_sufyan'),
      });
      final dio = Dio(BaseOptions(baseUrl: 'https://aiquranic.com/v1'))
        ..httpClientAdapter = adapter;
      repo = ApiLibraryRepository(dio: dio);
    });

    test('uses /v1/library paths and query parameters', () async {
      expect((await repo.categories()), hasLength(5));
      final weak = await repo.hadiths(graded: 'weak');
      expect(weak.items.map((h) => h.id), ['tirmidhi:4', 'tirmidhi:172']);
      expect(adapter.requests.last.queryParameters['graded'], 'weak');
      expect(adapter.requests.last.uri.toString(),
          startsWith('https://aiquranic.com/v1/library/hadiths'));
      final h = await repo.hadith('tirmidhi:4');
      expect(h.number, 4);
      final books = await repo.books('bukhari');
      expect(books.items.first.nameEn, 'Revelation');
      final n = await repo.narrator('sufyan-ibn-uyaynah');
      expect(n.nameEn, "Sufyan ibn 'Uyaynah");
      final s = await repo.search('Sufyan');
      expect(adapter.requests.last.queryParameters['q'], 'Sufyan');
      expect(s.narrators, hasLength(2));
    });

    test('gharib: encoded word hits, a 404 is simply "no entry"', () async {
      final g = await repo.gharib('بِالنِّيَّاتِ،');
      expect(g?.id, 'niyyah');
      expect(await repo.gharib('الصَّلاَةُ'), isNull);
    });

    test('other failures surface as ApiException', () async {
      expect(() => repo.hadith('muslim:8'), throwsA(isA<ApiException>()));
    });
  });
}
