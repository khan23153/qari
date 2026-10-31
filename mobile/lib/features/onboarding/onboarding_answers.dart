import '../../core/constants/app_constants.dart';
import '../../data/services/local_storage_service.dart';
import '../recitation/presentation/mushaf/mushaf_theme.dart';

/// How well the learner reads the Arabic of the Quran today.
enum ArabicReading { notYet, slowly, fluent }

/// What the learner wants to do most with Safha.
enum StudyFocus { read, memorize, understand, hadith }

/// The answers from the "Set up Safha" questions, and what each one changes
/// in the app. Every answer has an effect; nothing is collected for show.
class OnboardingAnswers {
  const OnboardingAnswers({
    this.reading = ArabicReading.slowly,
    this.focus = StudyFocus.read,
    this.dailyGoal = 3,
    this.mushafThemeId = 'night',
  });

  final ArabicReading reading;
  final StudyFocus focus;

  /// Lessons per day, shown by the daily goal ring on Home.
  final int dailyGoal;

  /// One of [MushafTheme.all]; the paper the recitation page opens with.
  final String mushafThemeId;

  static const List<int> dailyGoalOptions = [1, 3, 5, 10];

  /// Someone who cannot read the script yet starts with the letters
  /// (Foundation); everyone else goes straight to the Quran.
  LearningPath get path => reading == ArabicReading.notYet
      ? LearningPath.foundation
      : LearningPath.quranDirect;

  /// The backend's `starting_path` value for [path].
  String get backendPath =>
      path == LearningPath.foundation ? 'foundation' : 'quran_direct';

  /// The bottom-nav tab Home opens on after setup: 0 Home (the lessons
  /// path), 1 Quran, 2 Library. A learner who cannot read the script yet
  /// lands on the lessons whatever they want to do later, except hadith,
  /// which the Library shows with translations.
  int get homeTab {
    if (focus == StudyFocus.hadith) return 2;
    if (reading == ArabicReading.notYet) return 0;
    switch (focus) {
      case StudyFocus.read:
      case StudyFocus.memorize:
        return 1;
      case StudyFocus.understand:
      case StudyFocus.hadith:
        return 0;
    }
  }

  OnboardingAnswers copyWith({
    ArabicReading? reading,
    StudyFocus? focus,
    int? dailyGoal,
    String? mushafThemeId,
  }) =>
      OnboardingAnswers(
        reading: reading ?? this.reading,
        focus: focus ?? this.focus,
        dailyGoal: dailyGoal ?? this.dailyGoal,
        mushafThemeId: mushafThemeId ?? this.mushafThemeId,
      );
}

/// Writes the answers where the app reads them and marks onboarding done.
///
/// The local flags are the source of truth for routing (see `main.dart`), so
/// they are written first and do not depend on the server.
Future<void> saveOnboardingAnswers(
  OnboardingAnswers answers, {
  LocalStorageService? storage,
}) async {
  final s = storage ?? LocalStorageService();
  await s.setSelectedPath(answers.path.name);
  await s.setArabicReading(answers.reading.name);
  await s.setStudyFocus(answers.focus.name);
  await s.setDailyGoal(answers.dailyGoal);
  // Load first, so choosing the default (Night) still overwrites an earlier
  // stored paper instead of being skipped as "already selected".
  final papers = MushafThemeController();
  await papers.load();
  await papers.select(MushafTheme.byId(answers.mushafThemeId));
  await s.setOnboardingComplete(true);
  await s.setIsOnboarded(true);
}
