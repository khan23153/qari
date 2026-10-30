import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:qari/data/services/api_client.dart';
import 'package:qari/features/library/data/fallback_library_repository.dart';
import 'package:qari/features/library/data/library_models.dart';
import 'package:qari/features/library/data/library_repository.dart';
import 'package:qari/features/library/data/local_library_repository.dart';
import 'package:qari/features/library/presentation/library_theme.dart';
import 'package:qari/features/library/presentation/pages/library_home_page.dart';
import 'package:qari/features/recitation/presentation/mushaf/mushaf_theme.dart';
import 'package:qari/main_ui_preview.dart';
import 'package:qari/features/recitation/presentation/widgets/mushaf_reveal_view.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('preview opens Tilawat without an account', (tester) async {
    await tester.pumpWidget(const QariUiPreviewApp());
    await tester.pumpAndSettle();
    expect(find.text('Log In'), findsNothing);
    await tester.tap(find.text('Tilawat'));
    await tester.pumpAndSettle();
    final page = tester.widget<MushafRevealView>(
      find.byType(MushafRevealView),
    );
    expect(page.words, isNotEmpty);
    expect(page.hideUnspoken, isFalse);
    expect(find.textContaining('Page 1'), findsWidgets);
    await tester.tap(find.byIcon(Icons.mic_rounded));
    await tester.pump();
    expect(find.textContaining('UI preview only.'), findsOneWidget);
    expect(find.textContaining('Connecting'), findsNothing);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('preview AI entry keeps Hifz without a Tilawat switch',
      (tester) async {
    await tester.pumpWidget(const QariUiPreviewApp());
    await tester.pumpAndSettle();
    await tester.tap(find.text('AI Recitation'));
    await tester.pumpAndSettle();
    final page = tester.widget<MushafRevealView>(
      find.byType(MushafRevealView),
    );
    expect(page.words, isNotEmpty);
    expect(page.hideUnspoken, isTrue);
    expect(find.text('Tilawat'), findsNothing);
    expect(find.text('Hifz'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('preview opens the Islamic Library without an account or server',
      (tester) async {
    tester.view.physicalSize = const Size(900, 3000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    // Backend not live: every API call fails, as in the field.
    final asset = File(LocalLibraryRepository.assetPath).readAsStringSync();
    final repo = FallbackLibraryRepository(
      remote: _ServerDown(),
      local: LocalLibraryRepository(loadJson: () async => asset),
    );
    LibraryEnv env() => LibraryEnv(
          repository: repo,
          themeController: MushafThemeController(),
          usingBundledData: repo.usingBundledData,
        );
    await tester.pumpWidget(QariUiPreviewApp(libraryEnvBuilder: env));
    await tester.pumpAndSettle();
    expect(find.text('Log In'), findsNothing);
    await tester.tap(find.text('Islamic Library'));
    await tester.pumpAndSettle();
    expect(find.byType(LibraryHomePage), findsOneWidget);
    expect(find.text('Sahih al-Bukhari'), findsOneWidget);
    expect(find.byKey(const ValueKey('library-offline-banner')), findsOneWidget);
    expect(find.byType(BackButton), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });
}

/// The API as it is while the backend is not deployed.
class _ServerDown implements LibraryRepository {
  Future<T> _down<T>() async => throw const ApiException(
      statusCode: 0, message: 'No connection', errorCode: 'NO_CONNECTION');

  @override
  Future<List<LibraryCategory>> categories() => _down();
  @override
  Future<LibraryPage<LibraryCollection>> collections(
          {String? category, int page = 1, int pageSize = 50}) =>
      _down();
  @override
  Future<LibraryPage<LibraryBook>> books(String slug,
          {int page = 1, int pageSize = 100}) =>
      _down();
  @override
  Future<LibraryPage<HadithSummary>> bookHadiths(String slug, int book,
          {int page = 1, int pageSize = 20}) =>
      _down();
  @override
  Future<LibraryPage<HadithSummary>> hadiths(
          {String graded = 'all', int page = 1, int pageSize = 20}) =>
      _down();
  @override
  Future<HadithDetail> hadith(String id) => _down();
  @override
  Future<NarratorProfile> narrator(String id) => _down();
  @override
  Future<GharibEntry?> gharib(String word) => _down();
  @override
  Future<LibrarySearchResult> search(String query) => _down();
}
