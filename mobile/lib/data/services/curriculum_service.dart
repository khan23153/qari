import 'dart:convert';
import 'dart:math';

import 'package:flutter/services.dart' show rootBundle;

import '../models/lesson_model.dart';
import 'local_storage_service.dart';

/// Offline-first learning curriculum: Foundation → Grammar → Vocabulary
/// levels that progress until the learner recognises most of the Quran.
///
/// Everything is bundled in the APK (no backend dependency):
///   • Foundation + Grammar lessons are authored here as [LessonModel]s.
///   • Vocabulary levels come from `assets/vocab_curriculum.json`
///     (built by scripts/build_vocab_curriculum.py from the word-by-word
///     corpus) — each level teaches the next 10 most frequent Quran words
///     with meanings, transliteration, frequency and an example ayah, and
///     auto-generates meaning quizzes.
/// Completion + XP are stored locally (LocalStorageService) so the path
/// works fully offline; the backend can layer server progress on top later.
class CurriculumService {
  CurriculumService._();
  static final CurriculumService instance = CurriculumService._();

  List<LessonModel>? _vocabLessons;
  List<double>? _vocabCoverage;

  // ── Lesson ID ranges (stable keys for local progress) ────────────────────
  static const int foundationBase = 100;
  static const int grammarBase = 200;
  static const int vocabBase = 1000;

  // ─── Public API ──────────────────────────────────────────────────────────

  List<LessonModel> get foundationLessons => _foundation;
  List<LessonModel> get grammarLessons => _grammar;

  /// Vocabulary levels (lazy-loaded from the bundled asset).
  Future<List<LessonModel>> vocabLessons() async {
    if (_vocabLessons != null) return _vocabLessons!;
    final raw = await rootBundle.loadString('assets/vocab_curriculum.json');
    final data = jsonDecode(raw) as Map<String, dynamic>;
    final levels = data['levels'] as List<dynamic>;
    final lessons = <LessonModel>[];
    final coverage = <double>[];
    for (final lv in levels) {
      final level = lv as Map<String, dynamic>;
      lessons.add(_vocabLevelToLesson(level));
      coverage.add((level['coverage_pct'] as num).toDouble());
    }
    _vocabLessons = lessons;
    _vocabCoverage = coverage;
    return lessons;
  }

  /// Cumulative % of all Quran words covered after finishing [level] (1-based).
  double coverageForLevel(int level) {
    final c = _vocabCoverage;
    if (c == null || level < 1 || level > c.length) return 0;
    return c[level - 1];
  }

  /// Finds a curriculum lesson by its id across all tracks (or null).
  Future<LessonModel?> findLesson(int? lessonId) async {
    if (lessonId == null) return null;
    for (final l in _foundation) {
      if (l.lessonId == lessonId) return l;
    }
    for (final l in _grammar) {
      if (l.lessonId == lessonId) return l;
    }
    if (lessonId >= vocabBase) {
      final vocab = await vocabLessons();
      for (final l in vocab) {
        if (l.lessonId == lessonId) return l;
      }
    }
    return null;
  }

  /// Ordered list of every curriculum lesson (foundation → grammar → vocab).
  Future<List<LessonModel>> allLessons() async =>
      [..._foundation, ..._grammar, ...await vocabLessons()];

  /// Marks a lesson complete and awards its XP locally.
  Future<void> markCompleted(LessonModel lesson) =>
      LocalStorageService().addCompletedLesson('${lesson.lessonId}', lesson.xpReward);

  Future<Set<String>> completedIds() =>
      LocalStorageService().getCompletedLessonIds();

  /// Applies local completion + sequential unlocking to a track's lessons:
  /// the first lesson is always unlocked; each next unlocks when the
  /// previous is complete.
  List<LessonModel> withProgress(List<LessonModel> track, Set<String> done) {
    final out = <LessonModel>[];
    var previousDone = true;
    for (final lesson in track) {
      final isDone = done.contains('${lesson.lessonId}');
      out.add(lesson.copyWith(isCompleted: isDone, isLocked: !previousDone && !isDone));
      previousDone = isDone;
    }
    return out;
  }

  // ─── Vocabulary level → lesson (concepts + generated quizzes) ────────────

  LessonModel _vocabLevelToLesson(Map<String, dynamic> level) {
    final n = level['level'] as int;
    final coverage = (level['coverage_pct'] as num).toDouble();
    final words = (level['words'] as List<dynamic>)
        .map((w) => w as Map<String, dynamic>)
        .toList();

    final concepts = <LessonConcept>[];
    for (var i = 0; i < words.length; i++) {
      final w = words[i];
      final arabic = w['arabic'] as String;
      final translit = w['translit'] as String? ?? '';
      final meaning = w['meaning'] as String? ?? '';
      final count = w['count'] as int? ?? 0;
      final surah = w['surah'] as int? ?? 1;
      final ayah = w['ayah'] as int? ?? 1;
      concepts.add(LessonConcept(
        id: 'v$n-w$i',
        title: '$arabic  ·  $translit',
        explanation:
            'Meaning: "$meaning".\n\n'
            'How to learn it: read the Arabic aloud 3 times while looking at '
            'the shape of the word, then say the meaning from memory. This '
            'word appears $count times in the Quran — you will meet it '
            'constantly, so recognising it instantly is worth the effort.\n\n'
            'See it in context: Surah $surah, Ayah $ayah (open the Quran tab '
            'and find this word in that ayah — context is the strongest '
            'memory glue).',
        arabicExample: arabic,
        transliteration: translit,
        translation: meaning,
      ));
    }

    final quizzes = _generateVocabQuizzes(n, words);

    return LessonModel(
      lessonId: vocabBase + n,
      moduleNumber: 3,
      lessonNumber: n,
      title: 'Quran Words — Level $n',
      description:
          'The next ${words.length} most frequent Quran words. After this '
          'level you will recognise ${coverage.toStringAsFixed(1)}% of every '
          'word in the Quran.',
      xpReward: 15,
      estimatedMinutes: 6,
      iconName: 'translate',
      concepts: concepts,
      quizQuestions: quizzes,
    );
  }

  List<QuizQuestionModel> _generateVocabQuizzes(
      int level, List<Map<String, dynamic>> words) {
    // Deterministic per level so the quiz is stable across sessions.
    final rng = Random(level * 7919);
    final quizzes = <QuizQuestionModel>[];

    List<Map<String, dynamic>> sample(int count, {int except = -1}) {
      final pool = [
        for (var i = 0; i < words.length; i++)
          if (i != except) words[i]
      ]..shuffle(rng);
      return pool.take(count).toList();
    }

    // 1) Three word → meaning MCQs.
    final askIdx = List<int>.generate(words.length, (i) => i)..shuffle(rng);
    for (final i in askIdx.take(3)) {
      final w = words[i];
      final distractors =
          sample(3, except: i).map((d) => d['meaning'] as String).toList();
      final options = [...distractors, w['meaning'] as String]..shuffle(rng);
      quizzes.add(QuizQuestionModel(
        id: 'v$level-q${quizzes.length}',
        type: QuizType.mcq,
        question: 'What does this word mean?',
        questionArabic: w['arabic'] as String,
        options: options,
        correctAnswer: w['meaning'] as String,
        explanation:
            '${w['arabic']} (${w['translit']}) = "${w['meaning']}" — appears '
            '${w['count']} times in the Quran.',
      ));
    }

    // 2) Two meaning → word MCQs (recognise the Arabic).
    for (final i in askIdx.skip(3).take(2)) {
      final w = words[i];
      final distractors =
          sample(3, except: i).map((d) => d['arabic'] as String).toList();
      final options = [...distractors, w['arabic'] as String]..shuffle(rng);
      quizzes.add(QuizQuestionModel(
        id: 'v$level-q${quizzes.length}',
        type: QuizType.mcq,
        question: 'Which word means "${w['meaning']}"?',
        options: options,
        correctAnswer: w['arabic'] as String,
        explanation: '${w['arabic']} (${w['translit']}) = "${w['meaning']}".',
      ));
    }

    // 3) One drag-match of 4 pairs.
    final pairWords = sample(4);
    quizzes.add(QuizQuestionModel(
      id: 'v$level-q${quizzes.length}',
      type: QuizType.dragMatch,
      question: 'Match each word to its meaning:',
      matchPairs: [
        for (final w in pairWords)
          MatchPair(left: w['arabic'] as String, right: w['meaning'] as String),
      ],
      correctAnswer: '',
    ));

    return quizzes;
  }

  // ─── Foundation track ────────────────────────────────────────────────────

  static final List<LessonModel> _foundation = [
    LessonModel(
      lessonId: foundationBase + 1,
      moduleNumber: 1,
      lessonNumber: 1,
      title: 'Arabic Letters & Sounds',
      description: 'The 28 Arabic letters and their sounds.',
      xpReward: 10,
      estimatedMinutes: 6,
      iconName: 'abc',
      concepts: const [
        LessonConcept(
          id: 'f1-c1',
          title: 'The Arabic Alphabet',
          explanation:
              'Arabic has 28 consonant letters, written right-to-left. Each '
              'letter changes shape slightly depending on whether it appears '
              'at the start, middle, or end of a word. Read each row aloud — '
              'sound first, name second.',
          arabicExample: 'ا ب ت ث ج ح خ',
          transliteration: 'alif · baa · taa · thaa · jeem · haa · khaa',
        ),
        LessonConcept(
          id: 'f1-c2',
          title: 'Letters d–s',
          explanation:
              'Notice the dots: they are what distinguish otherwise identical '
              'shapes (ب ت ث differ only by dots). Dots are your best friend '
              'when reading.',
          arabicExample: 'د ذ ر ز س ش',
          transliteration: 'daal · dhaal · raa · zaay · seen · sheen',
        ),
        LessonConcept(
          id: 'f1-c3',
          title: 'The heavy (emphatic) letters',
          explanation:
              'These four letters are pronounced with a "full mouth" — the '
              'same tongue position as their light twins (س/ص, د/ض, ت/ط, '
              'ذ/ظ) but with the back of the tongue raised. Getting these '
              'right is the first step of tajweed.',
          arabicExample: 'ص ض ط ظ',
          transliteration: 'saad · daad · taa · zaa',
        ),
        LessonConcept(
          id: 'f1-c4',
          title: 'Throat letters',
          explanation:
              'Six letters come from the throat: ء ه ع ح غ خ. The pairs '
              'ع/ء and ح/ه are the hardest for new learners — listen to a '
              'reciter and copy the depth of the sound.',
          arabicExample: 'ع غ ف ق ك ل م ن ه و ي',
          transliteration: 'ayn · ghayn · faa · qaaf · kaaf · laam · meem · noon · haa · waaw · yaa',
        ),
      ],
      quizQuestions: const [
        QuizQuestionModel(
          id: 'f1-q1',
          type: QuizType.mcq,
          question: 'How many letters are in the Arabic alphabet?',
          options: ['26', '28', '30', '32'],
          correctAnswer: '28',
          explanation: 'Arabic has 28 consonant letters.',
        ),
        QuizQuestionModel(
          id: 'f1-q2',
          type: QuizType.mcq,
          question: 'What distinguishes ب from ت and ث?',
          options: [
            'The base shape',
            'The dots',
            'The direction of writing',
            'Nothing — they are the same letter'
          ],
          correctAnswer: 'The dots',
          explanation:
              'All three share one base shape; only the dots differ.',
        ),
        QuizQuestionModel(
          id: 'f1-q3',
          type: QuizType.dragMatch,
          question: 'Match the letter to its sound:',
          matchPairs: [
            MatchPair(left: 'ب', right: 'baa'),
            MatchPair(left: 'س', right: 'seen'),
            MatchPair(left: 'م', right: 'meem'),
            MatchPair(left: 'ن', right: 'noon'),
          ],
          correctAnswer: '',
        ),
      ],
    ),
    LessonModel(
      lessonId: foundationBase + 2,
      moduleNumber: 1,
      lessonNumber: 2,
      title: 'Harakat (Short Vowels)',
      description: 'Fatha, Kasra, Damma — the three short vowels.',
      xpReward: 10,
      estimatedMinutes: 5,
      iconName: 'spellcheck',
      concepts: const [
        LessonConcept(
          id: 'f2-c1',
          title: 'Fatha (َ) — "a"',
          explanation:
              'A small diagonal stroke ABOVE the letter adds a short "a": '
              'بَ = ba. Think of it as the letter opening its mouth.',
          arabicExample: 'بَ تَ نَ',
          transliteration: 'ba · ta · na',
        ),
        LessonConcept(
          id: 'f2-c2',
          title: 'Kasra (ِ) — "i"',
          explanation:
              'The same stroke BELOW the letter adds a short "i": بِ = bi. '
              'Below the line → "i" (both point down).',
          arabicExample: 'بِ تِ نِ',
          transliteration: 'bi · ti · ni',
        ),
        LessonConcept(
          id: 'f2-c3',
          title: 'Damma (ُ) — "u"',
          explanation:
              'A tiny و ABOVE the letter adds a short "u": بُ = bu. The '
              'shape literally is a miniature waaw, which itself sounds '
              'like "oo".',
          arabicExample: 'بُ تُ نُ',
          transliteration: 'bu · tu · nu',
        ),
        LessonConcept(
          id: 'f2-c4',
          title: 'Sukun (ْ) and Shadda (ّ)',
          explanation:
              'Sukun (a small circle) means NO vowel — the letter closes the '
              'syllable: بْ. Shadda (like a tiny w) DOUBLES the letter: '
              'بّ = bb. Shadda letters are held slightly longer — you will '
              'meet this again in tajweed (ghunnah).',
          arabicExample: 'ٱلرَّحْمَٰنِ',
          transliteration: 'ar-raḥmān',
          translation: 'the Most Merciful',
        ),
      ],
      quizQuestions: const [
        QuizQuestionModel(
          id: 'f2-q1',
          type: QuizType.fillBlank,
          question: 'The vowel mark َ (above the letter, sound "a") is called ____',
          blankAnswer: 'Fatha',
          explanation: 'Fatha produces the short "a" sound.',
        ),
        QuizQuestionModel(
          id: 'f2-q2',
          type: QuizType.mcq,
          question: 'What sound does بِ make?',
          options: ['ba', 'bi', 'bu', 'b'],
          correctAnswer: 'bi',
          explanation: 'Kasra below the letter gives the short "i".',
        ),
        QuizQuestionModel(
          id: 'f2-q3',
          type: QuizType.mcq,
          question: 'What does the shadda (ّ) do?',
          options: [
            'Removes the vowel',
            'Doubles the letter',
            'Makes the letter silent',
            'Adds a long "aa"'
          ],
          correctAnswer: 'Doubles the letter',
          explanation:
              'Shadda doubles the letter — pronounce it twice as long.',
        ),
      ],
    ),
    LessonModel(
      lessonId: foundationBase + 3,
      moduleNumber: 1,
      lessonNumber: 3,
      title: 'Long Vowels & Tanween',
      description: 'Stretching sounds (ا و ي) and the -n endings.',
      xpReward: 10,
      estimatedMinutes: 5,
      iconName: 'straighten',
      concepts: const [
        LessonConcept(
          id: 'f3-c1',
          title: 'Long vowels — aa, oo, ee',
          explanation:
              'After a vowel, the letters ا و ي stretch it: '
              'بَا = baa, بُو = boo, بِي = bee. In recitation this stretch '
              '(madd) is held for a measured length — usually 2 counts.',
          arabicExample: 'قَالَ · يَقُولُ · قِيلَ',
          transliteration: 'qāla · yaqūlu · qīla',
          translation: 'he said · he says · it was said',
        ),
        LessonConcept(
          id: 'f3-c2',
          title: 'Tanween — the "-n" endings',
          explanation:
              'Doubling a vowel mark at the END of a noun adds an "n" '
              'sound: بً = ban, بٍ = bin, بٌ = bun. Tanween marks an '
              'indefinite noun ("a book" vs "the book").',
          arabicExample: 'كِتَابٌ',
          transliteration: 'kitābun',
          translation: 'a book',
        ),
      ],
      quizQuestions: const [
        QuizQuestionModel(
          id: 'f3-q1',
          type: QuizType.mcq,
          question: 'How is بُو pronounced?',
          options: ['ba', 'boo', 'bee', 'bun'],
          correctAnswer: 'boo',
          explanation: 'Damma + waaw stretches the "u" into "oo".',
        ),
        QuizQuestionModel(
          id: 'f3-q2',
          type: QuizType.mcq,
          question: 'What does the tanween ٌ add to a word ending?',
          options: ['-n sound', '-m sound', 'a pause', 'a long vowel'],
          correctAnswer: '-n sound',
          explanation: 'kitābun — the double damma ends with "-un".',
        ),
      ],
    ),
  ];

  // ─── Grammar track ───────────────────────────────────────────────────────

  static final List<LessonModel> _grammar = [
    LessonModel(
      lessonId: grammarBase + 1,
      moduleNumber: 2,
      lessonNumber: 1,
      title: 'The 3 Word Types: Ism, Fiʿl, Harf',
      description: 'Every Quran word is a noun, a verb, or a particle.',
      xpReward: 15,
      estimatedMinutes: 6,
      iconName: 'category',
      concepts: const [
        LessonConcept(
          id: 'g1-c1',
          title: 'Ism (اسم) — nouns & names',
          explanation:
              'An ism names a person, place, thing, or quality — including '
              'adjectives and pronouns. Signs of an ism: it can start with '
              'ال (the), or end with tanween (-un/-in/-an).',
          arabicExample: 'ٱلْكِتَٰبُ',
          transliteration: 'al-kitābu',
          translation: 'the Book',
          posGroup: 'ism',
        ),
        LessonConcept(
          id: 'g1-c2',
          title: 'Fiʿl (فعل) — verbs',
          explanation:
              'A fiʿl is an action tied to a time: past, present, or '
              'command. Verbs never take ال or tanween.',
          arabicExample: 'خَلَقَ',
          transliteration: 'khalaqa',
          translation: 'He created',
          posGroup: 'fiil_madi',
        ),
        LessonConcept(
          id: 'g1-c3',
          title: 'Harf (حرف) — particles',
          explanation:
              'A harf is a small connector word — "in", "from", "and", '
              '"indeed". Harf words are the MOST frequent words in the '
              'Quran (مِن، فِي، إِنَّ), so you already know several from '
              'the vocabulary levels.',
          arabicExample: 'مِن · فِى · وَ · إِنَّ',
          transliteration: 'min · fī · wa · inna',
          translation: 'from · in · and · indeed',
          posGroup: 'harf',
        ),
      ],
      quizQuestions: const [
        QuizQuestionModel(
          id: 'g1-q1',
          type: QuizType.mcq,
          question: 'A word starting with ال (al-) is always…',
          options: ['an ism (noun)', 'a fiʿl (verb)', 'a harf (particle)', 'a name of Allah'],
          correctAnswer: 'an ism (noun)',
          explanation: 'Only nouns take the definite article ال.',
        ),
        QuizQuestionModel(
          id: 'g1-q2',
          type: QuizType.mcq,
          question: 'خَلَقَ (khalaqa, "He created") is a…',
          options: ['fiʿl (verb)', 'ism (noun)', 'harf (particle)', 'pronoun'],
          correctAnswer: 'fiʿl (verb)',
          explanation: 'It is an action in the past tense.',
        ),
        QuizQuestionModel(
          id: 'g1-q3',
          type: QuizType.dragMatch,
          question: 'Match the word to its type:',
          matchPairs: [
            MatchPair(left: 'ٱلْكِتَٰبُ', right: 'ism'),
            MatchPair(left: 'خَلَقَ', right: 'fiʿl'),
            MatchPair(left: 'مِن', right: 'harf'),
          ],
          correctAnswer: '',
        ),
      ],
    ),
    LessonModel(
      lessonId: grammarBase + 2,
      moduleNumber: 2,
      lessonNumber: 2,
      title: 'The Root System',
      description: 'How 3-letter roots build families of words.',
      xpReward: 15,
      estimatedMinutes: 6,
      iconName: 'account_tree',
      concepts: const [
        LessonConcept(
          id: 'g2-c1',
          title: 'Three letters, one meaning-family',
          explanation:
              'Almost every Arabic word grows from a 3-letter root that '
              'carries a core meaning. ك-ت-ب carries "writing": kataba (he '
              'wrote), kitāb (book), kātib (writer), maktūb (written). '
              'Learn one root → unlock a whole family.',
          arabicExample: 'كَتَبَ · كِتَٰب · كَاتِب',
          transliteration: 'kataba · kitāb · kātib',
          translation: 'he wrote · book · writer',
        ),
        LessonConcept(
          id: 'g2-c2',
          title: 'Roots in the Quran',
          explanation:
              'ر-ح-م carries "mercy": raḥma (mercy), ar-Raḥmān and '
              'ar-Raḥīm (two names of Allah), yarḥamu (He shows mercy). '
              'When you meet a new Quran word, look for the 3 core letters '
              'inside it — you often already know the family.',
          arabicExample: 'ٱلرَّحْمَٰنِ ٱلرَّحِيمِ',
          transliteration: 'ar-raḥmāni r-raḥīm',
          translation: 'the Most Merciful, the Especially Merciful',
        ),
      ],
      quizQuestions: const [
        QuizQuestionModel(
          id: 'g2-q1',
          type: QuizType.mcq,
          question: 'Which root do كِتَٰب (book) and كَاتِب (writer) share?',
          options: ['ك-ت-ب', 'ر-ح-م', 'ق-و-ل', 'ع-ل-م'],
          correctAnswer: 'ك-ت-ب',
          explanation: 'k-t-b is the "writing" family.',
        ),
        QuizQuestionModel(
          id: 'g2-q2',
          type: QuizType.mcq,
          question: 'ٱلرَّحْمَٰن and ٱلرَّحِيم come from the root meaning…',
          options: ['mercy', 'power', 'knowledge', 'creation'],
          correctAnswer: 'mercy',
          explanation: 'r-ḥ-m is the mercy family.',
        ),
      ],
    ),
    LessonModel(
      lessonId: grammarBase + 3,
      moduleNumber: 2,
      lessonNumber: 3,
      title: 'Pronouns (Detached)',
      description: 'huwa, hiya, anta, ana — who is speaking?',
      xpReward: 15,
      estimatedMinutes: 5,
      iconName: 'people',
      concepts: const [
        LessonConcept(
          id: 'g3-c1',
          title: 'The main pronouns',
          explanation:
              'هُوَ huwa = he · هِيَ hiya = she · أَنتَ anta = you (m) · '
              'أَنَا ana = I · نَحْنُ naḥnu = we · هُمْ hum = they. These '
              'appear constantly: قُلْ هُوَ ٱللَّهُ أَحَدٌ — "Say: He is '
              'Allah, the One."',
          arabicExample: 'هُوَ · هِيَ · أَنتَ · أَنَا · نَحْنُ · هُمْ',
          transliteration: 'huwa · hiya · anta · ana · naḥnu · hum',
          translation: 'he · she · you · I · we · they',
          posGroup: 'ism_dhamir',
        ),
      ],
      quizQuestions: const [
        QuizQuestionModel(
          id: 'g3-q1',
          type: QuizType.dragMatch,
          question: 'Match the pronoun to its meaning:',
          matchPairs: [
            MatchPair(left: 'هُوَ', right: 'he'),
            MatchPair(left: 'أَنَا', right: 'I'),
            MatchPair(left: 'نَحْنُ', right: 'we'),
            MatchPair(left: 'هُمْ', right: 'they'),
          ],
          correctAnswer: '',
        ),
        QuizQuestionModel(
          id: 'g3-q2',
          type: QuizType.mcq,
          question: 'In قُلْ هُوَ ٱللَّهُ أَحَدٌ, what does هُوَ mean?',
          options: ['He', 'She', 'You', 'We'],
          correctAnswer: 'He',
          explanation: '"Say: HE is Allah, the One." (Surah Al-Ikhlas)',
        ),
      ],
    ),
    LessonModel(
      lessonId: grammarBase + 4,
      moduleNumber: 2,
      lessonNumber: 4,
      title: 'Attached Pronouns',
      description: '-hu, -haa, -ka, -ii: "his book" in one word.',
      xpReward: 15,
      estimatedMinutes: 6,
      iconName: 'link',
      concepts: const [
        LessonConcept(
          id: 'g4-c1',
          title: 'Pronouns that stick to words',
          explanation:
              'Arabic attaches "my/your/his/her" to the END of a word: '
              'كِتَٰبُهُ kitābu-hu = his book · كِتَٰبُكَ kitābu-ka = your '
              'book · كِتَٰبِى kitābī = my book. The same endings attach to '
              'verbs and particles too: لَهُ la-hu = for him · مِنكُمْ '
              'min-kum = from you (plural).',
          arabicExample: 'رَبُّكَ · رَبُّهُمْ · رَبِّى',
          transliteration: 'rabbu-ka · rabbu-hum · rabb-ī',
          translation: 'your Lord · their Lord · my Lord',
          posGroup: 'ism_dhamir',
        ),
      ],
      quizQuestions: const [
        QuizQuestionModel(
          id: 'g4-q1',
          type: QuizType.mcq,
          question: 'رَبُّكَ (rabbuka) means…',
          options: ['your Lord', 'my Lord', 'their Lord', 'our Lord'],
          correctAnswer: 'your Lord',
          explanation: 'The ك (-ka) ending = your.',
        ),
        QuizQuestionModel(
          id: 'g4-q2',
          type: QuizType.dragMatch,
          question: 'Match the ending to its meaning:',
          matchPairs: [
            MatchPair(left: 'ـهُ', right: 'his'),
            MatchPair(left: 'ـكَ', right: 'your'),
            MatchPair(left: 'ـى', right: 'my'),
            MatchPair(left: 'ـهُمْ', right: 'their'),
          ],
          correctAnswer: '',
        ),
      ],
    ),
    LessonModel(
      lessonId: grammarBase + 5,
      moduleNumber: 2,
      lessonNumber: 5,
      title: 'Prefixes: wa-, bi-, li-, fa-, al-',
      description: 'One letter changes the meaning of the whole word.',
      xpReward: 15,
      estimatedMinutes: 6,
      iconName: 'text_fields',
      concepts: const [
        LessonConcept(
          id: 'g5-c1',
          title: 'The one-letter words',
          explanation:
              'Five tiny prefixes glue onto the next word: وَ wa = and · '
              'بِ bi = with/by · لِ li = for/to · فَ fa = so/then · '
              'ٱل al = the. بِسْمِ bi-smi = "with the name (of)" — the very '
              'first word of the Quran is a prefix + noun!',
          arabicExample: 'بِسْمِ ٱللَّهِ',
          transliteration: 'bi-smi llāhi',
          translation: 'In the name of Allah',
          posGroup: 'harf',
        ),
        LessonConcept(
          id: 'g5-c2',
          title: 'Peel the prefix, find the word',
          explanation:
              'When a word looks unknown, peel prefixes off the front: '
              'وَلِلَّهِ wa-li-llāhi = and + for + Allah. لِرَبِّهِمْ '
              'li-rabbi-him = for + their Lord. Most "long" Quran words are '
              'a short word wearing prefixes and endings.',
          arabicExample: 'وَلِلَّهِ',
          transliteration: 'wa-li-llāhi',
          translation: 'and to Allah (belongs)',
        ),
      ],
      quizQuestions: const [
        QuizQuestionModel(
          id: 'g5-q1',
          type: QuizType.mcq,
          question: 'In بِسْمِ (bismi), the prefix بِ means…',
          options: ['with / in', 'and', 'for', 'the'],
          correctAnswer: 'with / in',
          explanation: 'bi + ism = "with/in the name (of)".',
        ),
        QuizQuestionModel(
          id: 'g5-q2',
          type: QuizType.dragMatch,
          question: 'Match the prefix to its meaning:',
          matchPairs: [
            MatchPair(left: 'وَ', right: 'and'),
            MatchPair(left: 'لِ', right: 'for'),
            MatchPair(left: 'فَ', right: 'so / then'),
            MatchPair(left: 'ٱل', right: 'the'),
          ],
          correctAnswer: '',
        ),
      ],
    ),
    LessonModel(
      lessonId: grammarBase + 6,
      moduleNumber: 2,
      lessonNumber: 6,
      title: 'Past Tense Verbs (Fiʿl Māḍī)',
      description: 'khalaqa, qāla, kāna — actions already done.',
      xpReward: 15,
      estimatedMinutes: 6,
      iconName: 'history',
      concepts: const [
        LessonConcept(
          id: 'g6-c1',
          title: 'The fa-ʿa-la pattern',
          explanation:
              'Past verbs follow the rhythm faʿala: خَلَقَ khalaqa (He '
              'created), جَعَلَ jaʿala (He made), قَالَ qāla (he said). '
              'The base form means "he did it" — no separate word for "he" '
              'is needed.',
          arabicExample: 'خَلَقَ · جَعَلَ · قَالَ',
          transliteration: 'khalaqa · jaʿala · qāla',
          translation: 'He created · He made · he said',
          posGroup: 'fiil_madi',
        ),
        LessonConcept(
          id: 'g6-c2',
          title: 'Endings change the doer',
          explanation:
              'Add endings to change who acted: قَالَ qāla = he said · '
              'قَالَتْ qālat = she said · قَالُوا۟ qālū = they said · '
              'قُلْتُ qultu = I said. Spot the ending, know the doer.',
          arabicExample: 'قَالَ · قَالَتْ · قَالُوا۟',
          transliteration: 'qāla · qālat · qālū',
          translation: 'he said · she said · they said',
          posGroup: 'fiil_madi',
        ),
      ],
      quizQuestions: const [
        QuizQuestionModel(
          id: 'g6-q1',
          type: QuizType.mcq,
          question: 'قَالُوا۟ (qālū) means…',
          options: ['they said', 'he said', 'she said', 'I said'],
          correctAnswer: 'they said',
          explanation: 'The و + ا ending marks "they".',
        ),
        QuizQuestionModel(
          id: 'g6-q2',
          type: QuizType.fillBlank,
          question: 'خَلَقَ (khalaqa) means "He ____" (past tense of create)',
          blankAnswer: 'created',
          explanation: 'khalaqa = He created.',
        ),
      ],
    ),
    LessonModel(
      lessonId: grammarBase + 7,
      moduleNumber: 2,
      lessonNumber: 7,
      title: 'Present Tense Verbs (Fiʿl Muḍāriʿ)',
      description: 'yaʿlamu, taʿlamūna — actions happening now.',
      xpReward: 15,
      estimatedMinutes: 6,
      iconName: 'update',
      concepts: const [
        LessonConcept(
          id: 'g7-c1',
          title: 'The y/t/n/a starters',
          explanation:
              'Present verbs START with ي ت ن or أ: يَعْلَمُ yaʿlamu = he '
              'knows · تَعْلَمُونَ taʿlamūna = you (all) know · نَعْبُدُ '
              'naʿbudu = we worship · أَعْلَمُ aʿlamu = I know. The starter '
              'letter tells you the doer.',
          arabicExample: 'يَعْلَمُ · تَعْلَمُونَ · نَعْبُدُ',
          transliteration: 'yaʿlamu · taʿlamūna · naʿbudu',
          translation: 'he knows · you all know · we worship',
          posGroup: 'fiil_mudari',
        ),
        LessonConcept(
          id: 'g7-c2',
          title: 'From Al-Fatiha',
          explanation:
              'إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ — "You alone we '
              'worship, and You alone we ask for help." Both verbs start '
              'with نَ (na-) = "we". You recite this every prayer!',
          arabicExample: 'إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ',
          transliteration: 'iyyāka naʿbudu wa-iyyāka nastaʿīn',
          translation: 'You alone we worship, You alone we ask for help',
          posGroup: 'fiil_mudari',
        ),
      ],
      quizQuestions: const [
        QuizQuestionModel(
          id: 'g7-q1',
          type: QuizType.mcq,
          question: 'A verb starting with نَ (na-) is done by…',
          options: ['we', 'he', 'she', 'they'],
          correctAnswer: 'we',
          explanation: 'naʿbudu = WE worship.',
        ),
        QuizQuestionModel(
          id: 'g7-q2',
          type: QuizType.mcq,
          question: 'يَعْلَمُ (yaʿlamu) means…',
          options: ['he knows', 'I know', 'we know', 'you know'],
          correctAnswer: 'he knows',
          explanation: 'The يَ (ya-) starter marks "he".',
        ),
      ],
    ),
    LessonModel(
      lessonId: grammarBase + 8,
      moduleNumber: 2,
      lessonNumber: 8,
      title: 'Iḍāfa — the "of" construction',
      description: 'rabb al-ʿālamīn: two nouns chained with "of".',
      xpReward: 15,
      estimatedMinutes: 6,
      iconName: 'compare_arrows',
      concepts: const [
        LessonConcept(
          id: 'g8-c1',
          title: 'Noun + noun = "X of Y"',
          explanation:
              'Put two nouns together and Arabic reads them as "X of Y": '
              'رَبِّ ٱلْعَٰلَمِينَ rabbi l-ʿālamīn = Lord OF the worlds · '
              'يَوْمِ ٱلدِّينِ yawmi d-dīn = Day OF Judgement. The first '
              'noun never takes ال; the second usually does.',
          arabicExample: 'رَبِّ ٱلْعَٰلَمِينَ',
          transliteration: 'rabbi l-ʿālamīn',
          translation: 'Lord of the worlds',
        ),
      ],
      quizQuestions: const [
        QuizQuestionModel(
          id: 'g8-q1',
          type: QuizType.mcq,
          question: 'يَوْمِ ٱلدِّينِ (yawmi d-dīn) means…',
          options: [
            'Day of Judgement',
            'the Judgement',
            'a great day',
            'Lord of the Day'
          ],
          correctAnswer: 'Day of Judgement',
          explanation: 'Noun + noun chain = "X of Y".',
        ),
        QuizQuestionModel(
          id: 'g8-q2',
          type: QuizType.trueFalse,
          question:
              'In an iḍāfa ("X of Y"), the FIRST noun takes ال (al-).',
          options: ['True', 'False'],
          correctAnswer: 'False',
          explanation:
              'The first noun stays bare; the second takes ال — '
              'rabbi L-ʿālamīn.',
        ),
      ],
    ),
  ];
}
