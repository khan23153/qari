import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../lib/features/quran_reader/presentation/pages/quran_reader_page.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('QuranReaderPage renders ayah text from sample seed',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
        ],
        supportedLocales: const [Locale('en'), Locale('ur'), Locale('ar')],
        home: const QuranReaderPage(
          surahNumber: 1,
          surahName: 'الفاتحة',
        ),
      ),
    );
    // First frame: sample ayahs are seeded in initState, so content must show.
    await tester.pump();

    // Sticky header shows the surah's Arabic name.
    expect(find.text('الفاتحة'), findsOneWidget);
    // The opening ayah is rendered word-by-word (not as one string), so the
    // second word of Al-Fatihah must be visible without any network.
    expect(find.text('ٱللَّهِ'), findsWidgets);
    // Ayah number badge for the first ayah.
    expect(find.text('1'), findsWidgets);
  });
}
