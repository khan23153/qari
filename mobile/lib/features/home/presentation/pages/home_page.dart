import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../quran_reader/presentation/pages/quran_reader_page.dart';
import '../../lessons/presentation/pages/lesson_list_page.dart';
import '../../flashcards/presentation/pages/flashcard_page.dart';
import '../../recitation/presentation/pages/recitation_page.dart';
import '../../profile/presentation/pages/profile_page.dart';

/// S3. Home — main app scaffold with bottom nav (4 tabs).
/// Home · Quran · Practice (AI mic, center, elevated FAB-style) · Profile
class HomePage extends ConsumerStatefulWidget {
  const HomePage({super.key});

  @override
  ConsumerState<HomePage> createState() => _HomePageState();
}

class _HomePageState extends ConsumerState<HomePage> {
  int _currentIndex = 0;

  final _pages = const [
    HomeTab(),
    QuranReaderPage(),
    RecitationPage(),
    ProfilePage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (i) => setState(() => _currentIndex = i),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.menu_book_outlined),
            selectedIcon: Icon(Icons.menu_book),
            label: 'Quran',
          ),
          NavigationDestination(
            icon: Icon(Icons.mic_none),
            selectedIcon: Icon(Icons.mic),
            label: 'Practice',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}

/// Home tab — streak, XP, continue card, flashcards due, learning path.
class HomeTab extends StatelessWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Qari')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Streak + XP bar
            _streakCard(context),
            const SizedBox(height: 16),
            // Continue card
            _continueCard(context),
            const SizedBox(height: 16),
            // Flashcards due
            _flashcardCard(context),
            const SizedBox(height: 16),
            // Daily goal ring
            _dailyGoalCard(context),
            const SizedBox(height: 24),
            // Learning path map
            Text('Learning Path', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            _learningPath(context),
          ],
        ),
      ),
    );
  }

  Widget _streakCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const Icon(Icons.local_fire_department, color: Colors.orange, size: 32),
            const SizedBox(width: 8),
            Text('7 day streak', style: Theme.of(context).textTheme.titleMedium),
            const Spacer(),
            Text('150 XP', style: Theme.of(context).textTheme.titleMedium),
          ],
        ),
      ),
    );
  }

  Widget _continueCard(BuildContext context) {
    return Card(
      elevation: 2,
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const LessonListPage()),
          );
        },
        child: const Padding(
          padding: EdgeInsets.all(20),
          child: Row(
            children: [
              Icon(Icons.play_circle_fill, size: 48),
              SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Continue Learning', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    Text('Lesson 5: Arabic Alphabet — Ba, Ta, Tha'),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _flashcardCard(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const FlashcardPage()),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              const Icon(Icons.style, size: 32),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  '5 words yaad karne hain — 2 min',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
              ),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }

  Widget _dailyGoalCard(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            SizedBox(
              width: 48,
              height: 48,
              child: CircularProgressIndicator(
                value: 0.6,
                strokeWidth: 4,
                backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,
              ),
            ),
            const SizedBox(width: 16),
            Text('Daily Goal: 3/5 lessons', style: Theme.of(context).textTheme.bodyLarge),
          ],
        ),
      ),
    );
  }

  Widget _learningPath(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: List.generate(5, (i) {
            final isCompleted = i < 3;
            final isCurrent = i == 3;
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Row(
                children: [
                  Icon(
                    isCompleted
                        ? Icons.check_circle
                        : isCurrent
                            ? Icons.play_circle
                            : Icons.lock_circle,
                    color: isCompleted
                        ? Colors.green
                        : isCurrent
                            ? Theme.of(context).colorScheme.primary
                            : Colors.grey,
                  ),
                  const SizedBox(width: 12),
                  Text('Lesson ${i + 1}'),
                ],
              ),
            );
          }),
        ),
      ),
    );
  }
}
