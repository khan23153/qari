import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../lib/data/models/lesson_model.dart';
import '../lib/features/lessons/presentation/pages/lesson_list_page.dart';

void main() {
  testWidgets('lesson fill-blank TextField builds under pushed route',
      (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          localizationsDelegates: const [
            DefaultMaterialLocalizations.delegate,
            DefaultWidgetsLocalizations.delegate,
          ],
          supportedLocales: const [Locale('en'), Locale('ur'), Locale('ar')],
          home: const LessonListPage(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    final harakat = find.text('Harakat (Vowel Marks)');
    expect(harakat, findsOneWidget);
    await tester.tap(harakat);
    await tester.pumpAndSettle();

    // Advance past concept screen.
    final cont = find.text('Continue');
    if (cont.evaluate().isNotEmpty) {
      await tester.tap(cont.first);
      await tester.pumpAndSettle();
    }

    expect(find.byType(TextField), findsWidgets,
        reason: 'fill-blank TextField built without MaterialLocalizations error');
  });
}
