import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/lesson_model.dart';
import '../widgets/grammar_card_widget.dart';
import '../widgets/quiz_widget.dart';

/// S4: Lesson list page — shows available lessons in a module.
class LessonListPage extends ConsumerStatefulWidget {
  final int moduleNumber;

  const LessonListPage({super.key, this.moduleNumber = 1});

  @override
  ConsumerState<LessonListPage> createState() => _LessonListPageState();
}

class _LessonListPageState extends ConsumerState<LessonListPage> {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text('Module ${widget.moduleNumber}'),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _sampleLessons.length,
        itemBuilder: (context, index) {
          final lesson = _sampleLessons[index];
          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: _LessonTile(
              lesson: lesson,
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => LessonPlayerPage(lesson: lesson),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

/// Sample lessons for demonstration.
final _sampleLessons = <LessonModel>[
  LessonModel(
    lessonId: 1,
    moduleNumber: 1,
    lessonNumber: 1,
    title: 'Arabic Letters & Sounds',
    description: 'Learn the 28 Arabic letters and their basic sounds.',
    xpReward: 10,
    estimatedMinutes: 5,
    isCompleted: true,
    iconName: 'abc',
    concepts: [
      LessonConcept(
        id: 'c1',
        title: 'The Arabic Alphabet',
        explanation: 'Arabic has 28 consonant letters. Unlike English, Arabic is written from right to left (RTL). Each letter can appear differently depending on its position in a word.',
        arabicExample: 'ا ب ت ث ج ح خ',
        transliteration: 'alif baa taa thaa jeem haa khaa',
      ),
    ],
    quizQuestions: [
      QuizQuestionModel(
        id: 'q1',
        type: QuizType.mcq,
        question: 'How many letters are in the Arabic alphabet?',
        options: ['26', '28', '30', '32'],
        correctAnswer: '28',
        explanation: 'Arabic has 28 consonant letters.',
      ),
    ],
  ),
  LessonModel(
    lessonId: 2,
    moduleNumber: 1,
    lessonNumber: 2,
    title: 'Harakat (Vowel Marks)',
    description: 'Learn the three short vowels: Fatha, Kasra, Damma.',
    xpReward: 10,
    estimatedMinutes: 5,
    isCompleted: true,
    iconName: 'spellcheck',
    concepts: [
      LessonConcept(
        id: 'c1',
        title: 'Fatha (َ)',
        explanation: 'Fatha is a short "a" sound, written as a diagonal line above the letter.',
        arabicExample: 'بَ',
        transliteration: 'ba',
        posGroup: 'harf',
      ),
    ],
    quizQuestions: [
      QuizQuestionModel(
        id: 'q1',
        type: QuizType.fillBlank,
        question: 'The vowel mark َ is called ____',
        blankAnswer: 'Fatha',
        explanation: 'Fatha produces a short "a" sound.',
      ),
    ],
  ),
  LessonModel(
    lessonId: 3,
    moduleNumber: 1,
    lessonNumber: 3,
    title: "Fi'l (Verbs)",
    description: 'Learn about Arabic verbs — past, present, and imperative.',
    xpReward: 15,
    estimatedMinutes: 7,
    isCompleted: false,
    isLocked: false,
    iconName: 'play_arrow',
    concepts: [
      LessonConcept(
        id: 'c1',
        title: "Fi'l Madi (Past Tense)",
        explanation: "Fi'l Madi refers to past tense verbs. For example, كَتَبَ (kataba) means 'he wrote'. The pattern is typically Faʿala (فَعَلَ).",
        arabicExample: 'كَتَبَ',
        transliteration: 'kataba',
        translation: 'he wrote',
        posGroup: 'fiil_madi',
        grammarNote: "Fi'l are color-coded green with a solid underline.",
      ),
      LessonConcept(
        id: 'c2',
        title: "Fi'l Mudari' (Present Tense)",
        explanation: "Fi'l Mudari' refers to present/future tense verbs. For example, يَكْتُبُ (yaktubu) means 'he writes'.",
        arabicExample: 'يَكْتُبُ',
        transliteration: 'yaktubu',
        translation: 'he writes',
        posGroup: 'fiil_mudari',
        grammarNote: "Present tense verbs start with one of the letters ي ت ن أ (yaktubu, taktubu, naktubu, aktubu).",
      ),
    ],
    quizQuestions: [
      QuizQuestionModel(
        id: 'q1',
        type: QuizType.mcq,
        question: 'What does كَتَبَ (kataba) mean?',
        options: ['he read', 'he wrote', 'he ate', 'he went'],
        correctAnswer: 'he wrote',
        explanation: 'Kataba means "he wrote".',
      ),
      QuizQuestionModel(
        id: 'q2',
        type: QuizType.dragMatch,
        question: 'Match the verb to its meaning:',
        matchPairs: [
          MatchPair(left: 'كَتَبَ', right: 'he wrote'),
          MatchPair(left: 'قَرَأَ', right: 'he read'),
          MatchPair(left: 'ذَهَبَ', right: 'he went'),
        ],
        correctAnswer: '',
      ),
      QuizQuestionModel(
        id: 'q3',
        type: QuizType.fillBlank,
        question: 'The present tense of كَتَبَ is يَكْتُبُ (y____u)',
        blankAnswer: 'aktub',
        explanation: 'yaktubu = he writes',
      ),
    ],
  ),
  LessonModel(
    lessonId: 4,
    moduleNumber: 1,
    lessonNumber: 4,
    title: 'Ism (Nouns)',
    description: 'Learn about Arabic nouns and their properties.',
    xpReward: 10,
    estimatedMinutes: 5,
    isCompleted: false,
    isLocked: true,
    iconName: 'label',
    concepts: [],
    quizQuestions: [],
  ),
];

/// A lesson tile in the list.
class _LessonTile extends StatelessWidget {
  final LessonModel lesson;
  final VoidCallback onTap;

  const _LessonTile({required this.lesson, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: lesson.isLocked ? null : onTap,
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
            border: Border.all(
              color: lesson.isCompleted
                  ? theme.colorScheme.primary.withValues(alpha: 0.3)
                  : theme.colorScheme.outline.withValues(alpha: 0.2),
            ),
          ),
          child: Row(
            children: [
              // Status icon
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: lesson.isCompleted
                      ? theme.colorScheme.primary
                      : lesson.isLocked
                          ? theme.colorScheme.outline.withValues(alpha: 0.1)
                          : theme.colorScheme.primary.withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: lesson.isCompleted
                    ? const Icon(Icons.check_rounded, color: Colors.white)
                    : lesson.isLocked
                        ? Icon(Icons.lock_rounded,
                            color: theme.colorScheme.outline)
                        : Icon(Icons.play_arrow_rounded,
                            color: theme.colorScheme.primary),
              ),
              const SizedBox(width: 16),
              // Lesson info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Lesson ${lesson.lessonNumber}',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                      ),
                    ),
                    Text(
                      lesson.title,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Text(
                      '${lesson.estimatedMinutes} min • +${lesson.xpReward} XP',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
