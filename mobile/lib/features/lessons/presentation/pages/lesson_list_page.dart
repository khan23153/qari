import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// S4. Module 1 Lesson List — Duolingo-style vertical learning path.
class LessonListPage extends ConsumerWidget {
  const LessonListPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final lessons = [
      {'title': 'Arabic Alphabet: Alif, Baa, Taa', 'type': 'alphabet', 'completed': true, 'xp': 10},
      {'title': 'Makhraj: Where Sounds Come From', 'type': 'makhraj', 'completed': true, 'xp': 15},
      {'title': 'Ism, Fi\'l, Harf — Three Word Types', 'type': 'grammar_card', 'completed': true, 'xp': 10},
      {'title': 'Gender: Masculine & Feminine', 'type': 'grammar_card', 'completed': false, 'xp': 10},
      {'title': 'Plural Forms', 'type': 'grammar_card', 'completed': false, 'xp': 10},
      {'title': 'Quiz: Alphabet Recognition', 'type': 'quiz', 'completed': false, 'xp': 20},
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Module 1: Foundation')),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: lessons.length,
        itemBuilder: (context, i) {
          final lesson = lessons[i];
          final isCompleted = lesson['completed'] as bool;
          final isCurrent = !isCompleted && (i == 0 || lessons[i - 1]['completed'] as bool);

          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Card(
              elevation: isCurrent ? 4 : 1,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: isCurrent
                    ? BorderSide(color: Theme.of(context).colorScheme.primary, width: 2)
                    : BorderSide.none,
              ),
              child: ListTile(
                contentPadding: const EdgeInsets.all(16),
                leading: _lessonIcon(isCompleted, isCurrent, lesson['type'] as String),
                title: Text(lesson['title'] as String, style: Theme.of(context).textTheme.titleMedium),
                subtitle: Text('+${lesson['xp']} XP'),
                trailing: isCompleted
                    ? const Icon(Icons.check_circle, color: Colors.green)
                    : isCurrent
                        ? const Icon(Icons.play_circle_fill)
                        : const Icon(Icons.lock, color: Colors.grey),
                onTap: isCurrent || isCompleted ? () {
                  // Navigate to lesson player
                } : null,
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _lessonIcon(bool completed, bool current, String type) {
    final icon = switch (type) {
      'alphabet' => Icons.abc,
      'makhraj' => Icons.record_voice_over,
      'grammar_card' => Icons.school,
      'quiz' => Icons.quiz,
      _ => Icons.book,
    };
    return CircleAvatar(
      backgroundColor: completed
          ? Colors.green
          : current
              ? Theme.of(context).colorScheme.primaryContainer
              : Colors.grey.shade200,
      child: Icon(icon, color: completed ? Colors.white : (current ? Theme.of(context).colorScheme.primary : Colors.grey)),
    );
  }
}

// Fix: need BuildContext
// Actually use a stateless builder pattern
