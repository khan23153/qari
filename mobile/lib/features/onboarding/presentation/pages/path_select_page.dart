import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/serene_decorations.dart';
import '../../../../data/repositories/user_repository.dart';
import '../../../../data/services/local_storage_service.dart';
import '../../../home/presentation/pages/home_page.dart';
import '../../../recitation/presentation/mushaf/mushaf_theme.dart';
import '../../onboarding_answers.dart';

/// S2: "Set up Safha" — four short questions after the language screen.
///
/// Each answer changes the app: where the lessons start, which tab Home
/// opens on, the daily goal on Home, and the Mushaf paper used for
/// recitation (see [OnboardingAnswers]). Skip keeps the defaults.
class PathSelectPage extends ConsumerStatefulWidget {
  final AppLanguage selectedLanguage;

  /// Sends the starting path to the server. Defaults to the real API; tests
  /// pass a stub. Failures never block the user.
  final Future<void> Function(OnboardingAnswers answers)? syncWithServer;

  /// Called after the answers are saved. Defaults to opening Home on the
  /// tab that matches the learner's focus.
  final void Function(OnboardingAnswers answers)? onFinished;

  const PathSelectPage({
    super.key,
    required this.selectedLanguage,
    this.syncWithServer,
    this.onFinished,
  });

  @override
  ConsumerState<PathSelectPage> createState() => _PathSelectPageState();
}

class _PathSelectPageState extends ConsumerState<PathSelectPage> {
  static const int _steps = 4;

  int _step = 0;
  bool _isSaving = false;

  ArabicReading? _reading;
  StudyFocus? _focus;
  int? _dailyGoal;
  String? _paper;

  _Copy get _t => _Copy.of(widget.selectedLanguage.code);

  bool get _answered => switch (_step) {
        0 => _reading != null,
        1 => _focus != null,
        2 => _dailyGoal != null,
        _ => _paper != null,
      };

  OnboardingAnswers get _answers {
    const d = OnboardingAnswers();
    return OnboardingAnswers(
      reading: _reading ?? d.reading,
      focus: _focus ?? d.focus,
      dailyGoal: _dailyGoal ?? d.dailyGoal,
      mushafThemeId: _paper ?? d.mushafThemeId,
    );
  }

  void _pick(VoidCallback change) {
    HapticFeedback.selectionClick();
    setState(change);
  }

  void _next() {
    if (_step < _steps - 1) {
      setState(() => _step++);
    } else {
      _finish();
    }
  }

  Future<void> _finish() async {
    if (_isSaving) return;
    setState(() => _isSaving = true);
    final answers = _answers;

    // Local first: routing reads these flags, so the learner gets in even
    // when the server is unreachable.
    await saveOnboardingAnswers(answers);
    try {
      final sync = widget.syncWithServer ?? _syncWithServer;
      await sync(answers);
    } catch (e) {
      debugPrint('onboarding sync failed: $e');
    }

    if (!mounted) return;
    // Saved: stop the spinner before leaving, so it never runs forever if
    // this page stays on screen (a test, or a slow route change).
    setState(() => _isSaving = false);
    final done = widget.onFinished;
    if (done != null) {
      done(answers);
      return;
    }
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => HomePage(initialTab: answers.homeTab)),
      (route) => false,
    );
  }

  Future<void> _syncWithServer(OnboardingAnswers answers) async {
    final lang = await LocalStorageService().getSelectedLanguage() ?? 'en';
    await UserRepository().finishOnboarding(
      appLanguage: lang,
      startingPath: answers.backendPath,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final t = _t;
    final last = _step == _steps - 1;

    return Directionality(
      textDirection: widget.selectedLanguage.textDirection,
      child: Scaffold(
        body: SereneBackground(
          showSilhouette: false,
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(24, 12, 24, 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _Header(
                    title: t.setUp,
                    stepLabel: t.step(_step + 1, _steps),
                    step: _step,
                    steps: _steps,
                    skipLabel: t.skip,
                    onSkip: _isSaving ? null : _finish,
                  ),
                  const SizedBox(height: 28),
                  Expanded(
                    child: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 260),
                      transitionBuilder: (child, animation) => FadeTransition(
                        opacity: animation,
                        child: SlideTransition(
                          position: Tween<Offset>(
                            begin: const Offset(0, 0.04),
                            end: Offset.zero,
                          ).animate(animation),
                          child: child,
                        ),
                      ),
                      child: KeyedSubtree(
                        key: ValueKey<int>(_step),
                        child: _question(theme, t),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      if (_step > 0) ...[
                        TextButton(
                          onPressed:
                              _isSaving ? null : () => setState(() => _step--),
                          child: Text(t.back),
                        ),
                        const SizedBox(width: 8),
                      ],
                      Expanded(
                        child: FilledButton(
                          onPressed: _answered && !_isSaving ? _next : null,
                          style: FilledButton.styleFrom(
                            minimumSize: const Size.fromHeight(54),
                          ),
                          child: _isSaving
                              ? const SizedBox(
                                  width: 22,
                                  height: 22,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : Text(last ? t.start : t.next),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _question(ThemeData theme, _Copy t) {
    switch (_step) {
      case 0:
        return _Question(
          title: t.readingQ,
          children: [
            for (final r in ArabicReading.values)
              _Choice(
                icon: _readingIcon(r),
                title: t.reading(r).$1,
                subtitle: t.reading(r).$2,
                selected: _reading == r,
                onTap: () => _pick(() => _reading = r),
              ),
          ],
        );
      case 1:
        return _Question(
          title: t.focusQ,
          children: [
            for (final f in StudyFocus.values)
              _Choice(
                icon: _focusIcon(f),
                title: t.focus(f).$1,
                subtitle: t.focus(f).$2,
                selected: _focus == f,
                onTap: () => _pick(() => _focus = f),
              ),
          ],
        );
      case 2:
        return _Question(
          title: t.goalQ,
          subtitle: t.goalNote,
          children: [
            for (final g in OnboardingAnswers.dailyGoalOptions)
              _Choice(
                leading: Text(
                  '$g',
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: theme.colorScheme.primary,
                  ),
                ),
                title: t.lessons(g),
                subtitle: t.goalPace(g),
                selected: _dailyGoal == g,
                onTap: () => _pick(() => _dailyGoal = g),
              ),
          ],
        );
      default:
        return _Question(
          title: t.paperQ,
          subtitle: t.paperNote,
          children: [
            for (final p in MushafTheme.all)
              _Choice(
                leading: _PaperSwatch(theme: p),
                title: p.label,
                subtitle: p.arabicLabel,
                selected: _paper == p.id,
                onTap: () => _pick(() => _paper = p.id),
              ),
          ],
        );
    }
  }

  static IconData _readingIcon(ArabicReading r) => switch (r) {
        ArabicReading.notYet => Icons.abc_rounded,
        ArabicReading.slowly => Icons.menu_book_outlined,
        ArabicReading.fluent => Icons.auto_stories_rounded,
      };

  static IconData _focusIcon(StudyFocus f) => switch (f) {
        StudyFocus.read => Icons.menu_book_rounded,
        StudyFocus.memorize => Icons.mic_rounded,
        StudyFocus.understand => Icons.school_rounded,
        StudyFocus.hadith => Icons.library_books_rounded,
      };
}

class _Header extends StatelessWidget {
  final String title;
  final String stepLabel;
  final int step;
  final int steps;
  final String skipLabel;
  final VoidCallback? onSkip;

  const _Header({
    required this.title,
    required this.stepLabel,
    required this.step,
    required this.steps,
    required this.skipLabel,
    required this.onSkip,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final muted = theme.colorScheme.onSurface.withValues(alpha: 0.6);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  Text(
                    stepLabel,
                    style: theme.textTheme.bodySmall?.copyWith(color: muted),
                  ),
                ],
              ),
            ),
            TextButton(onPressed: onSkip, child: Text(skipLabel)),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            for (var i = 0; i < steps; i++) ...[
              if (i > 0) const SizedBox(width: 6),
              Expanded(
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 240),
                  height: 5,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(3),
                    color: i <= step
                        ? theme.colorScheme.primary
                        : theme.colorScheme.primary.withValues(alpha: 0.15),
                  ),
                ),
              ),
            ],
          ],
        ),
      ],
    );
  }
}

class _Question extends StatelessWidget {
  final String title;
  final String? subtitle;
  final List<Widget> children;

  const _Question({required this.title, this.subtitle, required this.children});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListView(
      padding: EdgeInsets.zero,
      children: [
        Text(
          title,
          style: theme.textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w800,
            height: 1.2,
          ),
        ).animate().fadeIn(duration: 300.ms),
        if (subtitle != null) ...[
          const SizedBox(height: 8),
          Text(
            subtitle!,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
            ),
          ),
        ],
        const SizedBox(height: 20),
        for (var i = 0; i < children.length; i++) ...[
          if (i > 0) const SizedBox(height: 12),
          children[i],
        ],
      ],
    );
  }
}

/// One answer card. Selected cards fill with the accent tint and show a check.
class _Choice extends StatelessWidget {
  final IconData? icon;
  final Widget? leading;
  final String title;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;

  const _Choice({
    this.icon,
    this.leading,
    required this.title,
    required this.subtitle,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final accent = theme.colorScheme.primary;
    return Semantics(
      button: true,
      selected: selected,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: selected
                  ? accent.withValues(alpha: 0.12)
                  : theme.colorScheme.surface.withValues(alpha: 0.7),
              borderRadius:
                  BorderRadius.circular(AppConstants.cardBorderRadius),
              border: Border.all(
                color: selected ? accent : accent.withValues(alpha: 0.22),
                width: selected ? 2 : 1.2,
              ),
            ),
            child: Row(
              children: [
                SizedBox(
                  width: 48,
                  height: 48,
                  child: Center(
                    child: leading ??
                        Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                            color: accent.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Icon(icon, color: accent, size: 26),
                        ),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        subtitle,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurface
                              .withValues(alpha: 0.65),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                AnimatedOpacity(
                  duration: const Duration(milliseconds: 200),
                  opacity: selected ? 1 : 0,
                  child: Icon(Icons.check_circle_rounded, color: accent),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// A small page of the paper: its colour with a line of Arabic in its ink.
class _PaperSwatch extends StatelessWidget {
  final MushafTheme theme;

  const _PaperSwatch({required this.theme});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 40,
      height: 48,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: theme.background,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: theme.border),
      ),
      child: Text(
        'بسم',
        textDirection: TextDirection.rtl,
        style: AppTheme.arabicTextStyle(fontSize: 15, color: theme.text),
      ),
    );
  }
}

/// The flow's words in English, Urdu and Arabic.
class _Copy {
  final String code;

  const _Copy._(this.code);

  factory _Copy.of(String code) =>
      _Copy._(code == 'ur' || code == 'ar' ? code : 'en');

  String _p(String en, String ur, String ar) =>
      code == 'ur' ? ur : (code == 'ar' ? ar : en);

  String get setUp => _p('Set up Safha', 'صفحہ ترتیب دیں', 'إعداد صفحة');
  String step(int n, int of) =>
      _p('Step $n of $of', 'مرحلہ $n از $of', 'الخطوة $n من $of');
  String get skip => _p('Skip', 'چھوڑیں', 'تخطٍّ');
  String get back => _p('Back', 'واپس', 'رجوع');
  String get next => _p('Continue', 'آگے', 'متابعة');
  String get start => _p('Start', 'شروع کریں', 'ابدأ');

  String get readingQ => _p(
        'Can you read the Arabic of the Quran?',
        'کیا آپ قرآن کی عربی پڑھ سکتے ہیں؟',
        'هل تستطيع قراءة القرآن بالعربية؟',
      );

  (String, String) reading(ArabicReading r) => switch (r) {
        ArabicReading.notYet => (
            _p('Not yet', 'ابھی نہیں', 'ليس بعد'),
            _p(
              'Start with the letters and vowel marks',
              'حروف اور حرکات سے شروع کریں',
              'ابدأ بالحروف والحركات',
            ),
          ),
        ArabicReading.slowly => (
            _p('Slowly', 'آہستہ آہستہ', 'ببطء'),
            _p(
              'I can read, but it takes effort',
              'پڑھ لیتا ہوں مگر محنت لگتی ہے',
              'أقرأ ولكن بجهد',
            ),
          ),
        ArabicReading.fluent => (
            _p('Yes, fluently', 'جی ہاں، روانی سے', 'نعم، بطلاقة'),
            _p(
              'Take me straight to the Mushaf',
              'مجھے سیدھا مصحف پر لے جائیں',
              'خذني إلى المصحف مباشرة',
            ),
          ),
      };

  String get focusQ => _p(
        'What do you want to do most?',
        'آپ سب سے زیادہ کیا کرنا چاہتے ہیں؟',
        'ما الذي تريد فعله أكثر؟',
      );

  (String, String) focus(StudyFocus f) => switch (f) {
        StudyFocus.read => (
            _p('Read every day', 'روزانہ تلاوت', 'القراءة كل يوم'),
            _p(
              'Open the Mushaf and keep a daily habit',
              'مصحف کھولیں اور روزانہ کی عادت بنائیں',
              'افتح المصحف وحافظ على وردك اليومي',
            ),
          ),
        StudyFocus.memorize => (
            _p('Memorize (Hifz)', 'حفظ', 'الحفظ'),
            _p(
              'Recite from memory and watch the words come back',
              'یاد سے پڑھیں اور الفاظ واپس ظاہر ہوتے دیکھیں',
              'اقرأ من حفظك وشاهد الكلمات تظهر',
            ),
          ),
        StudyFocus.understand => (
            _p('Understand the Arabic', 'عربی سمجھیں', 'فهم العربية'),
            _p(
              'Lessons in Quranic words and grammar',
              'قرآنی الفاظ اور گرامر کے اسباق',
              'دروس في كلمات القرآن وقواعده',
            ),
          ),
        StudyFocus.hadith => (
            _p('Study hadith', 'حدیث کا مطالعہ', 'دراسة الحديث'),
            _p(
              "Hadith with every scholar's grade",
              'ہر عالم کے درجے کے ساتھ احادیث',
              'أحاديث مع حكم كل عالم',
            ),
          ),
      };

  String get goalQ => _p(
        'How many lessons a day?',
        'روزانہ کتنے اسباق؟',
        'كم درسًا في اليوم؟',
      );

  String get goalNote => _p(
        'This becomes your daily goal on Home.',
        'یہ ہوم پر آپ کا روزانہ ہدف ہوگا۔',
        'سيكون هذا هدفك اليومي في الصفحة الرئيسية.',
      );

  String lessons(int n) => switch (code) {
        'ur' => n == 1 ? '1 سبق' : '$n اسباق',
        'ar' => n == 1 ? 'درس واحد' : (n <= 10 ? '$n دروس' : '$n درسًا'),
        _ => n == 1 ? '1 lesson' : '$n lessons',
      };

  String goalPace(int n) => switch (n) {
        1 => _p('Light', 'ہلکا', 'خفيف'),
        3 => _p('Steady', 'مستقل', 'منتظم'),
        5 => _p('Serious', 'سنجیدہ', 'جاد'),
        _ => _p('Intense', 'بھرپور', 'مكثف'),
      };

  String get paperQ => _p(
        'Choose your Mushaf paper',
        'اپنے مصحف کا کاغذ منتخب کریں',
        'اختر ورق المصحف',
      );

  String get paperNote => _p(
        'Used when you recite. You can change it any time from the page settings.',
        'تلاوت کے دوران استعمال ہوگا۔ صفحے کی ترتیبات سے کبھی بھی بدل سکتے ہیں۔',
        'يُستخدم أثناء التلاوة، ويمكنك تغييره في أي وقت من إعدادات الصفحة.',
      );
}
