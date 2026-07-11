// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'lesson_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_LessonModel _$LessonModelFromJson(Map<String, dynamic> json) => _LessonModel(
      lessonId: (json['lesson_id'] as num).toInt(),
      moduleNumber: (json['module_number'] as num).toInt(),
      lessonNumber: (json['lesson_number'] as num).toInt(),
      title: json['title'] as String,
      titleUrdu: json['title_urdu'] as String?,
      titleHinglish: json['title_hinglish'] as String?,
      description: json['description'] as String,
      descriptionUrdu: json['description_urdu'] as String?,
      descriptionHinglish: json['description_hinglish'] as String?,
      xpReward: (json['xp_reward'] as num?)?.toInt() ?? 10,
      estimatedMinutes: (json['estimated_minutes'] as num?)?.toInt() ?? 5,
      isCompleted: json['is_completed'] as bool? ?? false,
      isLocked: json['is_locked'] as bool? ?? false,
      iconName: json['icon_name'] as String? ?? 'book',
      concepts: (json['concepts'] as List<dynamic>?)
              ?.map((e) => LessonConcept.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      quizQuestions: (json['quiz_questions'] as List<dynamic>?)
              ?.map(
                  (e) => QuizQuestionModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );

Map<String, dynamic> _$LessonModelToJson(_LessonModel instance) =>
    <String, dynamic>{
      'lesson_id': instance.lessonId,
      'module_number': instance.moduleNumber,
      'lesson_number': instance.lessonNumber,
      'title': instance.title,
      'title_urdu': instance.titleUrdu,
      'title_hinglish': instance.titleHinglish,
      'description': instance.description,
      'description_urdu': instance.descriptionUrdu,
      'description_hinglish': instance.descriptionHinglish,
      'xp_reward': instance.xpReward,
      'estimated_minutes': instance.estimatedMinutes,
      'is_completed': instance.isCompleted,
      'is_locked': instance.isLocked,
      'icon_name': instance.iconName,
      'concepts': instance.concepts,
      'quiz_questions': instance.quizQuestions,
    };

_LessonConcept _$LessonConceptFromJson(Map<String, dynamic> json) =>
    _LessonConcept(
      id: json['id'] as String,
      title: json['title'] as String,
      explanation: json['explanation'] as String,
      explanationUrdu: json['explanation_urdu'] as String?,
      arabicExample: json['arabic_example'] as String?,
      transliteration: json['transliteration'] as String?,
      translation: json['translation'] as String?,
      posGroup: json['pos_group'] as String?,
      grammarNote: json['grammar_note'] as String?,
      imageUrl: json['image_url'] as String?,
    );

Map<String, dynamic> _$LessonConceptToJson(_LessonConcept instance) =>
    <String, dynamic>{
      'id': instance.id,
      'title': instance.title,
      'explanation': instance.explanation,
      'explanation_urdu': instance.explanationUrdu,
      'arabic_example': instance.arabicExample,
      'transliteration': instance.transliteration,
      'translation': instance.translation,
      'pos_group': instance.posGroup,
      'grammar_note': instance.grammarNote,
      'image_url': instance.imageUrl,
    };

_QuizQuestionModel _$QuizQuestionModelFromJson(Map<String, dynamic> json) =>
    _QuizQuestionModel(
      id: json['id'] as String,
      type: $enumDecode(_$QuizTypeEnumMap, json['type']),
      question: json['question'] as String,
      questionArabic: json['question_arabic'] as String?,
      options: (json['options'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      correctAnswer: json['correct_answer'] as String?,
      matchPairs: (json['match_pairs'] as List<dynamic>?)
          ?.map((e) => MatchPair.fromJson(e as Map<String, dynamic>))
          .toList(),
      blankAnswer: json['blank_answer'] as String?,
      explanation: json['explanation'] as String?,
      hint: json['hint'] as String?,
    );

Map<String, dynamic> _$QuizQuestionModelToJson(_QuizQuestionModel instance) =>
    <String, dynamic>{
      'id': instance.id,
      'type': _$QuizTypeEnumMap[instance.type]!,
      'question': instance.question,
      'question_arabic': instance.questionArabic,
      'options': instance.options,
      'correct_answer': instance.correctAnswer,
      'match_pairs': instance.matchPairs,
      'blank_answer': instance.blankAnswer,
      'explanation': instance.explanation,
      'hint': instance.hint,
    };

const _$QuizTypeEnumMap = {
  QuizType.mcq: 'mcq',
  QuizType.dragMatch: 'drag_match',
  QuizType.fillBlank: 'fill_blank',
  QuizType.trueFalse: 'true_false',
};

_MatchPair _$MatchPairFromJson(Map<String, dynamic> json) => _MatchPair(
      left: json['left'] as String,
      right: json['right'] as String,
    );

Map<String, dynamic> _$MatchPairToJson(_MatchPair instance) =>
    <String, dynamic>{
      'left': instance.left,
      'right': instance.right,
    };
