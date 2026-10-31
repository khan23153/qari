// Checking a forwarded hadith (POST /v1/library/check). Fixtures are the real
// FastAPI responses, captured from the backend's own test data.
import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:qari/features/library/data/fallback_library_repository.dart';
import 'package:qari/features/library/data/forward_check.dart';
import 'package:qari/features/library/data/library_repository.dart';
import 'package:qari/features/library/data/local_library_repository.dart';
import 'package:qari/features/library/presentation/library_theme.dart';
import 'package:qari/features/library/presentation/pages/forward_check_page.dart';
import 'package:qari/features/library/presentation/pages/library_home_page.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';

String _fixture(String name) =>
    File('test/fixtures/library/$name.json').readAsStringSync();

Map<String, dynamic> _map(String name) =>
    jsonDecode(_fixture(name)) as Map<String, dynamic>;

class _Adapter implements HttpClientAdapter {
  _Adapter(this.status, this.body);

  final int status;
  final String body;
  RequestOptions? last;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    last = options;
    return ResponseBody.fromString(body, status, headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    });
  }

  @override
  void close({bool force = false}) {}
}

ApiForwardChecker _api(int status, String body, [_Adapter? spy]) {
  final dio = Dio(BaseOptions(baseUrl: 'https://api.test/v1'));
  dio.httpClientAdapter = spy ?? _Adapter(status, body);
  return ApiForwardChecker(dio: dio);
}

class _FakeChecker implements ForwardChecker {
  _FakeChecker(this.answer);

  /// Returns the result or throws the exception it is given.
  FutureOr<ForwardCheckResult> Function(String text) answer;
  final List<String> asked = [];

  @override
  Future<ForwardCheckResult> check(String text) async {
    asked.add(text);
    return answer(text);
  }
}

class _ServerDown implements LibraryRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) =>
      Future<Never>.error(const SocketException('down'));
}

LibraryEnv _env(ForwardChecker checker) {
  final asset = File(LocalLibraryRepository.assetPath).readAsStringSync();
  return LibraryEnv(
    repository: FallbackLibraryRepository(
      remote: _ServerDown(),
      local: LocalLibraryRepository(loadJson: () async => asset),
    ),
    themeController: MushafThemeController(),
    forwardChecker: checker,
  );
}

Future<void> _pump(WidgetTester tester, Widget home) async {
  tester.view.physicalSize = const Size(1080, 4000);
  tester.view.devicePixelRatio = 2;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(MaterialApp(home: home));
  await tester.pumpAndSettle();
}

const _forward =
    'The key to Paradise is prayer and the key to prayer is ablution';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  group('API client', () {
    test('parses a match with every scholar grade', () async {
      final spy = _Adapter(200, _fixture('forward_check_found'));
      final result = await _api(0, '', spy).check(_forward);
      expect(spy.last!.method, 'POST');
      expect(spy.last!.path, '/library/check');
      expect(spy.last!.data, {'text': _forward});
      expect(result.queryLanguage, 'en');
      final m = result.matches.single;
      expect(m.band, ForwardBand.strong);
      expect(m.collectionName, "Jami' al-Tirmidhi");
      expect(m.hadith.id, 'tirmidhi:4');
      expect(m.hadith.grades.map((g) => g.scholar),
          containsAll(['al-Albani', "Zubair 'Ali Za'i"]));
      expect(result.searchedCollections, contains('Sahih al-Bukhari'));
    });

    test('no match is "not found", with the note and searched collections',
        () async {
      final result =
          await _api(200, _fixture('forward_check_not_found')).check(_forward);
      expect(result.matches, isEmpty);
      expect(result.note.toLowerCase(), contains('not found'));
      expect(result.note.toLowerCase(), contains('does not prove'));
      expect(result.searchedCollections, isNotEmpty);
    });

    test('a first-run 503 is "preparing", not a miss', () async {
      await expectLater(
        _api(503, _fixture('forward_check_preparing')).check(_forward),
        throwsA(isA<ForwardCheckException>().having(
            (e) => e.failure, 'failure', ForwardCheckFailure.preparing)),
      );
    });

    test('server errors and a missing route are "unreachable"', () async {
      for (final status in [404, 500, 502, 503]) {
        await expectLater(
          _api(status, '{"detail":"down"}').check(_forward),
          throwsA(isA<ForwardCheckException>().having(
              (e) => e.failure, 'failure', ForwardCheckFailure.unreachable)),
          reason: 'HTTP $status',
        );
      }
    });

    test('a rejected text is "invalid text"', () async {
      expect(ApiForwardChecker.failureFor(422, const {}),
          ForwardCheckFailure.invalidText);
      expect(ApiForwardChecker.failureFor(null, null),
          ForwardCheckFailure.unreachable);
    });
  });

  group('Check a forward page', () {
    testWidgets('shows the hadith, where it is found and every grade',
        (tester) async {
      final checker = _FakeChecker(
        (_) => ForwardCheckResult.fromJson(_map('forward_check_found')),
      );
      await _pump(tester, ForwardCheckPage(env: _env(checker)));

      await tester.enterText(
          find.byKey(const ValueKey('forward-input')), _forward);
      await tester.pump();
      await tester.tap(find.byKey(const ValueKey('forward-check')));
      await tester.pumpAndSettle();

      expect(checker.asked, [_forward]);
      expect(find.text('Found in the collections'), findsOneWidget);
      expect(find.text("Jami' al-Tirmidhi #4"), findsOneWidget);
      expect(find.text('Close wording'), findsOneWidget);
      expect(find.text('Sahih — al-Albani'), findsOneWidget);
      expect(find.text("Daif — Zubair 'Ali Za'i"), findsOneWidget);
      expect(
          find.textContaining('Safha does not grade hadith'), findsOneWidget);
      expect(find.byKey(const ValueKey('forward-searched')), findsOneWidget);
      expect(find.text('Open in Library'), findsOneWidget);
    });

    testWidgets('a miss says not found in these collections, not fabricated',
        (tester) async {
      final checker = _FakeChecker(
        (_) => ForwardCheckResult.fromJson(_map('forward_check_not_found')),
      );
      await _pump(tester, ForwardCheckPage(env: _env(checker)));
      await tester.enterText(find.byKey(const ValueKey('forward-input')),
          'Share this message with ten people and you will get good news');
      await tester.pump();
      await tester.tap(find.byKey(const ValueKey('forward-check')));
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('forward-not-found')), findsOneWidget);
      expect(find.text('Not found in these collections'), findsOneWidget);
      expect(find.textContaining('does not prove'), findsOneWidget);
      expect(find.textContaining('Searched: Sahih al-Bukhari'), findsOneWidget);
      expect(find.textContaining('abricated'), findsOneWidget,
          reason: 'only inside "does not prove it is fabricated"');
    });

    testWidgets('no connection says the message was not checked',
        (tester) async {
      var fail = true;
      final checker = _FakeChecker((_) {
        if (fail) {
          throw const ForwardCheckException(ForwardCheckFailure.unreachable);
        }
        return ForwardCheckResult.fromJson(_map('forward_check_found'));
      });
      await _pump(tester, ForwardCheckPage(env: _env(checker)));
      await tester.enterText(
          find.byKey(const ValueKey('forward-input')), _forward);
      await tester.pump();
      await tester.tap(find.byKey(const ValueKey('forward-check')));
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('forward-failure-unreachable')),
          findsOneWidget);
      expect(find.text("Couldn't check this message"), findsOneWidget);
      expect(find.textContaining('Not found'), findsNothing);

      fail = false;
      await tester.tap(find.text('Try again'));
      await tester.pumpAndSettle();
      expect(checker.asked, hasLength(2));
      expect(find.text("Jami' al-Tirmidhi #4"), findsOneWidget);
    });

    testWidgets('first run explains the collections are being prepared',
        (tester) async {
      final checker = _FakeChecker((_) =>
          throw const ForwardCheckException(ForwardCheckFailure.preparing));
      await _pump(tester, ForwardCheckPage(env: _env(checker)));
      await tester.enterText(
          find.byKey(const ValueKey('forward-input')), _forward);
      await tester.pump();
      await tester.tap(find.byKey(const ValueKey('forward-check')));
      await tester.pumpAndSettle();
      expect(find.text('Getting the collections ready'), findsOneWidget);
      expect(find.textContaining('Not found'), findsNothing);
    });

    testWidgets('Check stays off until there are a few words', (tester) async {
      final checker = _FakeChecker(
        (_) => ForwardCheckResult.fromJson(_map('forward_check_found')),
      );
      await _pump(tester, ForwardCheckPage(env: _env(checker)));
      await tester.enterText(find.byKey(const ValueKey('forward-input')), 'hi');
      await tester.pump();
      final button = tester
          .widget<FilledButton>(find.byKey(const ValueKey('forward-check')));
      expect(button.onPressed, isNull);
    });

    testWidgets('Paste fills the box from the clipboard', (tester) async {
      tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
        SystemChannels.platform,
        (call) async => call.method == 'Clipboard.getData'
            ? <String, dynamic>{'text': '  $_forward  '}
            : null,
      );
      addTearDown(() => tester.binding.defaultBinaryMessenger
          .setMockMethodCallHandler(SystemChannels.platform, null));
      final checker = _FakeChecker(
        (_) => ForwardCheckResult.fromJson(_map('forward_check_found')),
      );
      await _pump(tester, ForwardCheckPage(env: _env(checker)));
      await tester.tap(find.byKey(const ValueKey('forward-paste')));
      await tester.pumpAndSettle();
      final field =
          tester.widget<TextField>(find.byKey(const ValueKey('forward-input')));
      expect(field.controller!.text, _forward);
    });

    testWidgets('shared text is checked straight away', (tester) async {
      final checker = _FakeChecker(
        (_) => ForwardCheckResult.fromJson(_map('forward_check_found')),
      );
      await _pump(
          tester, ForwardCheckPage(env: _env(checker), initialText: _forward));
      expect(checker.asked, [_forward]);
      expect(find.text("Jami' al-Tirmidhi #4"), findsOneWidget);
    });

    testWidgets('Urdu and Arabic text is typed right to left', (tester) async {
      final checker = _FakeChecker(
        (_) => ForwardCheckResult.fromJson(_map('forward_check_found')),
      );
      await _pump(tester, ForwardCheckPage(env: _env(checker)));
      await tester.enterText(find.byKey(const ValueKey('forward-input')),
          'اعمال کا دارومدار نیتوں پر ہے');
      await tester.pump();
      final field =
          tester.widget<TextField>(find.byKey(const ValueKey('forward-input')));
      expect(field.textDirection, TextDirection.rtl);
    });
  });

  testWidgets('the Library home opens the forward check', (tester) async {
    final checker = _FakeChecker(
      (_) => ForwardCheckResult.fromJson(_map('forward_check_found')),
    );
    await _pump(tester, LibraryHomePage(env: _env(checker)));
    expect(find.text('Check a forwarded hadith'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('forward-check-entry')));
    await tester.pumpAndSettle();
    expect(find.byType(ForwardCheckPage), findsOneWidget);
  });
}
