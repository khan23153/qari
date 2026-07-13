import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../lib/features/recitation/presentation/pages/recitation_page.dart';

void main() {
  testWidgets('RecitationPage from reader shows ayah text + Listen/Record buttons',
      (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: RecitationPage(surahNumber: 1, ayahNumber: 1),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // Header shows the Surah:Ayah context
    expect(find.text('Surah 1:1'), findsOneWidget);
    expect(find.text('AI Recitation'), findsOneWidget);

    // Target arabic ayah text is displayed (RTL arabic content present)
    final hasArabicText = find
        .byWidgetPredicate(
          (w) =>
              w is Directionality &&
              w.textDirection == TextDirection.rtl &&
              w.child is Text,
        )
        .evaluate()
        .isNotEmpty;
    expect(hasArabicText, isTrue,
        reason: 'The target arabic ayah text should be displayed');

    // Core recording components are present
    expect(find.text('Listen First'), findsOneWidget);
    expect(find.text('Record Now'), findsOneWidget);
  });
}
