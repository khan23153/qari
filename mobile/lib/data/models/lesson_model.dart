import 'package:freezed_annotation/freezed_annotation.dart';

part 'lesson_model.freezed.dart';
part 'lesson_model.g.dart';

/// Represents a learning module/lesson in the foundation path.
@freezed
abstract class LessonModel with _$LessonModel {
  const factory LessonModel({
    @JsonKey(name: 'lesson_id') required int lessonId,
    @JsonKey(name: 'module_number') required int moduleNumber,
    @JsonKey(name: 'lesson_number') required int lessonNumber,
    required String title,
    @JsonKey(name: 'title_urdu') String? titleUrdu,
    @JsonKey(name: 'title_hinglish') String? titleHinglish,
    required String description,
    @JsonKey(name: 'description_urdu') String? descriptionUrdu,
    @JsonKey(name: 'description_hinglish') String? descriptionHinglish,
    @JsonKey(name: 'xp_reward') @Default(10) int xpReward,
    @JsonKey(name: 'estimated_minutes') @Default(5) int estimatedMinutes,
    @JsonKey(name: 'is_completed') @Default(false) bool isCompleted,
    @JsonKey(name: 'is_locked') @Default(false) bool isLocked,
    @JsonKey(name: 'icon_name') @Default('book') String iconName,
    @JsonKey(name: 'concepts') @Default([]) List<LessonConcept> concepts,
    @JsonKey(name: 'quiz_questions') @Default([]) List<QuizQuestionModel> quizQuestions,
  }) = _LessonModel;

  factory LessonModel.fromJson(Map<String, dynamic> json) =>
      _$LessonModelFromJson(json);
}

/// Represents a single concept within a lesson.
@freezed
abstract class LessonConcept with _$LessonConcept {
  const factory LessonConcept({
    required String id,
    required String title,
    required String explanation,
    @JsonKey(name: 'explanation_urdu') String? explanationUrdu,
    @JsonKey(name: 'arabic_example') String? arabicExample,
    @JsonKey(name: 'transliteration') String? transliteration,
    @JsonKey(name: 'translation') String? translation,
    @JsonKey(name: 'pos_group') String? posGroup,
    @JsonKey(name: 'grammar_note') String? grammarNote,
    @JsonKey(name: 'image_url') String? imageUrl,
  }) = _LessonConcept;

  factory LessonConcept.fromJson(Map<String, dynamic> json) =>
      _$LessonConceptFromJson(json);
}

/// Represents a quiz question in a lesson.
@freezed
abstract class QuizQuestionModel with _$QuizQuestionModel {
  const factory QuizQuestionModel({
    required String id,
    required QuizType type,
    required String question,
    @JsonKey(name: 'question_arabic') String? questionArabic,
    @JsonKey(name: 'options') @Default([]) List<String> options,
    @JsonKey(name: 'correct_answer') String? correctAnswer,
    @JsonKey(name: 'match_pairs') List<MatchPair>? matchPairs,
    @JsonKey(name: 'blank_answer') String? blankAnswer,
    @JsonKey(name: 'explanation') String? explanation,
    @JsonKey(name: 'hint') String? hint,
  }) = _QuizQuestionModel;

  factory QuizQuestionModel.fromJson(Map<String, dynamic> json) =>
      _$QuizQuestionModelFromJson(json);
}

/// Quiz question types.
enum QuizType {
  @JsonValue('mcq') mcq,
  @JsonValue('drag_match') dragMatch,
  @JsonValue('fill_blank') fillBlank,
  @JsonValue('true_false') trueFalse,
}

/// Represents a match pair for drag-match questions.
@freezed
abstract class MatchPair with _$MatchPair {
  const factory MatchPair({
    required String left,
    required String right,
  }) = _MatchPair;

  factory MatchPair.fromJson(Map<String, dynamic> json) =>
      _$MatchPairFromJson(json);
}

/// Extension for lesson convenience.
extension LessonModelX on LessonModel {
  /// Title for the user's language.
  String titleFor(String langCode) {
    switch (langCode) {
      case 'ur':
        return titleUrdu ?? title;
      case 'hi':
        return titleHinglish ?? title;
      default:
        return title;
    }
  }

  /// Description for the user's language.
  String descriptionFor(String langCode) {
    switch (langCode) {
      case 'ur':
        return descriptionUrdu ?? description;
      case 'hi':
        return descriptionHinglish ?? description;
      default:
        return description;
    }
  }

  /// Total number of screens (concepts + quizzes).
  int get totalScreens => concepts.length + quizQuestions.length;
}
