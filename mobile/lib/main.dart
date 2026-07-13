import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';

import 'core/theme/app_theme.dart';
import 'core/constants/app_constants.dart';
import 'core/providers.dart';
import 'data/services/local_storage_service.dart';
import 'data/services/api_client.dart';
import 'data/models/auth_model.dart';
import 'features/update/app_update_service.dart';
import 'features/update/app_update_dialog.dart';
import 'features/auth/presentation/pages/login_page.dart';
import 'features/onboarding/presentation/pages/language_select_page.dart';
import 'features/home/presentation/pages/home_page.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // In release builds, a widget that throws during build is replaced by the
  // framework's default ErrorWidget, which renders as a BLANK GREY screen
  // with no information. Replace it with a visible, scrollable error so a
  // UI bug (e.g. in the Quran reader) is diagnosable instead of silent.
  ErrorWidget.builder = (details) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Text(
            'UI error:\n${details.exception}\n\n${details.stack}',
            style: const TextStyle(color: Colors.red, fontSize: 12),
          ),
        ),
      ),
    );
  };

  // Catch async/Dart errors and show them instead of hard-crashing.
  runZonedGuarded(() async {

    FlutterError.onError = (details) {
      debugPrint('FlutterError: ${details.exception}\n${details.stack}');
    };

    // Lock orientation to portrait for consistent Quran reading
    await SystemChrome.setPreferredOrientations([
      DeviceOrientation.portraitUp,
    ]);

    // Initialize Firebase (safe — may be unconfigured)
    try {
      await Firebase.initializeApp();
    } catch (e) {
      debugPrint('Firebase init skipped: $e');
    }

    runApp(
      const ProviderScope(
        child: QariApp(),
      ),
    );
  }, (error, stack) {
    debugPrint('Uncaught error: $error\n$stack');
    runApp(
      MaterialApp(
        debugShowCheckedModeBanner: false,
        home: Scaffold(
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Text(
                'App error:\n\n$error\n\n$stack',
                style: const TextStyle(fontSize: 13, color: Colors.red),
              ),
            ),
          ),
        ),
      ),
    );
  });
}

class QariApp extends ConsumerStatefulWidget {
  const QariApp({super.key});

  @override
  ConsumerState<QariApp> createState() => _QariAppState();
}

class _QariAppState extends ConsumerState<QariApp> {
  bool _isLoading = true;
  Widget? _initialPage;
  bool _updateShown = false;
  final AppUpdateService _updateService = AppUpdateService(ApiClient());
  final GlobalKey<NavigatorState> _navigatorKey = GlobalKey<NavigatorState>();

  @override
  void initState() {
    super.initState();
    _checkAuthStatus();
  }

  /// Decide the entry screen:
  ///   • no auth token            → Login
  ///   • token but not onboarded → Language select (then path select)
  ///   • token + onboarded       → Home
  Future<void> _checkAuthStatus() async {
    final storage = LocalStorageService();
    final token = await storage.getAuthToken();
    final lang = await storage.getSelectedLanguage();
    // Apply the persisted language (defaults to English) so the choice
    // survives app restarts.
    ref.read(appLocaleProvider.notifier).state = AppConstants.localeForCode(lang);

    Widget page;
    if (token == null || token.isEmpty) {
      page = LoginPage(onAuthenticated: _handleAuthenticated);
    } else if (!(await storage.isOnboarded())) {
      page = const LanguageSelectPage();
    } else {
      page = const HomePage();
    }

    setState(() {
      _initialPage = page;
      _isLoading = false;
    });
    _checkForUpdate();
  }

  /// Called after a successful signup/login. Replaces the whole auth stack
  /// with the correct post-auth screen so the user actually lands there
  /// (rather than being popped back onto the LoginPage root route).
  void _handleAuthenticated(AuthResult result) {
    if (!mounted) return;
    final page = result.isOnboarded
        ? const HomePage()
        : const LanguageSelectPage();
    _navigatorKey.currentState?.pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => page),
      (route) => false,
    );
  }

  /// Ask the backend whether a newer app build is available and, if so,
  /// show the OTA update dialog.  Fails soft — never blocks the app.
  Future<void> _checkForUpdate() async {
    if (_updateShown) return;
    final decision = await _updateService.checkForUpdate();
    if (decision == null || !mounted) return;
    _updateShown = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      showDialog(
        context: context,
        barrierDismissible: !decision.mandatory,
        builder: (_) => AppUpdateDialog(
          service: _updateService,
          release: decision.release,
          mandatory: decision.mandatory,
        ),
      );
    });
    // Independently of a binary update, detect backend *content* changes so
    // the app auto-refreshes its cached data when the backend is updated.
    _checkBackendDataVersion(decision.release.dataVersion);
  }

  /// If the backend's ``data_version`` advanced past what we last saw, the
  /// corpus/content changed server-side — bump our stored version and let the
  /// user know content was refreshed.  Content is fetched live, so this just
  /// ensures caches/in-flight reads pick up the new data.
  Future<void> _checkBackendDataVersion(int latest) async {
    if (latest <= 0) return;
    final storage = LocalStorageService();
    final seen = await storage.getBackendDataVersion();
    if (latest > seen) {
      await storage.setBackendDataVersion(latest);
      if (seen > 0 && mounted) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('New content is available — refreshing.'),
              duration: Duration(seconds: 3),
            ),
          );
        });
      }
    }
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
      navigatorKey: _navigatorKey,
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
      home: _initialPage ?? const HomePage(),
    );
  }
}
