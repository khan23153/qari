import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';

import 'core/theme/app_theme.dart';
import 'core/constants/app_constants.dart';
import 'core/providers.dart';
import 'data/services/local_storage_service.dart';
import 'features/onboarding/presentation/pages/language_select_page.dart';
import 'features/home/presentation/pages/home_page.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Lock orientation to portrait for consistent Quran reading
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
  ]);

  // Initialize Firebase
  try {
    await Firebase.initializeApp();
  } catch (e) {
    // Firebase may not be configured in dev — continue without it
    debugPrint('Firebase init skipped: $e');
  }

  runApp(
    const ProviderScope(
      child: QariApp(),
    ),
  );
}

class QariApp extends ConsumerStatefulWidget {
  const QariApp({super.key});

  @override
  ConsumerState<QariApp> createState() => _QariAppState();
}

class _QariAppState extends ConsumerState<QariApp> {
  bool _hasSelectedLanguage = false;
  bool _hasSelectedPath = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _checkOnboardingStatus();
  }

  Future<void> _checkOnboardingStatus() async {
    final storage = LocalStorageService();
    final lang = await storage.getSelectedLanguage();
    final path = await storage.getSelectedPath();
    setState(() {
      _hasSelectedLanguage = lang != null;
      _hasSelectedPath = path != null;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final themeMode = ref.watch(themeModeProvider);
    final locale = ref.watch(appLocaleProvider);

    if (_isLoading) {
      return MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        home: const Scaffold(
          body: Center(
            child: CircularProgressIndicator(),
          ),
        ),
      );
    }

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Qari',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      highContrastTheme: AppTheme.highContrastTheme,
      themeMode: themeMode,
      locale: locale,
      supportedLocales: AppConstants.supportedLocales,
      localizationsDelegates: const [
        DefaultMaterialLocalizations.delegate,
        DefaultWidgetsLocalizations.delegate,
      ],
      home: _hasSelectedLanguage && _hasSelectedPath
          ? const HomePage()
          : const LanguageSelectPage(),
    );
  }
}
