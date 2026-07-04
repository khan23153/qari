import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/services.dart';
import 'package:firebase_core/firebase_core.dart';

import 'core/theme/app_theme.dart';
import 'core/constants/app_constants.dart';
import 'features/onboarding/presentation/pages/language_select_page.dart';
import 'features/home/presentation/pages/home_page.dart';
import 'data/services/local_storage_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Set preferred orientations
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
  ]);

  // Initialize Firebase
  await Firebase.initializeApp();

  // Initialize local storage
  await LocalStorageService.instance.init();

  runApp(const ProviderScope(child: QariApp()));
}

class QariApp extends ConsumerWidget {
  const QariApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final hasOnboarded = LocalStorageService.instance.hasOnboarded;
    final themeMode = LocalStorageService.instance.themeMode;

    return MaterialApp(
      title: 'Qari',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      highContrastTheme: AppTheme.highContrastTheme,
      themeMode: themeMode,
      locale: Locale(LocalStorageService.instance.appLanguage),
      supportedLocales: const [
        Locale('en'),
        Locale('ur'),
        Locale('hi'),
      ],
      home: hasOnboarded ? const HomePage() : const LanguageSelectPage(),
    );
  }
}
