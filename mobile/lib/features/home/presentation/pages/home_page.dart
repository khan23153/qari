import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../data/services/local_storage_service.dart';
import '../../../quran_reader/presentation/pages/surah_list_page.dart';
import '../../../recitation/presentation/pages/recitation_page.dart';
import '../../../profile/presentation/pages/profile_page.dart';
import '../widgets/streak_card.dart';
import '../widgets/continue_card.dart';
import '../widgets/daily_goal_ring.dart';
import '../widgets/learning_path_map.dart';
import '../../../flashcards/presentation/pages/flashcard_page.dart';
import '../../../qibla/presentation/pages/qibla_page.dart';
import '../../../tasbih/presentation/pages/tasbih_page.dart';
import '../../../../core/theme/serene_decorations.dart';

/// S3: Home screen with bottom nav (4 tabs: Home, Quran, Practice, Profile).
/// Home tab shows streak, XP, continue card, flashcards due, daily goal ring,
/// and a Duolingo-style vertical learning path map.
class HomePage extends ConsumerStatefulWidget {
  const HomePage({super.key});

  @override
  ConsumerState<HomePage> createState() => _HomePageState();
}

class _HomePageState extends ConsumerState<HomePage> {
  int _currentIndex = 0;

  final List<Widget> _pages = const [
    HomeTab(),
    SurahListPage(),
    QiblaPage(),
    TasbihPage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: _buildBottomNav(context),
      floatingActionButton: _buildPracticeFAB(context),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
    );
  }

  Widget _buildBottomNav(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      decoration: BoxDecoration(
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: BottomAppBar(
        shape: const CircularNotchedRectangle(),
        notchMargin: 8,
        elevation: 0,
        child: SizedBox(
          height: 64,
          child: Row(
            children: [
              _navItem(Icons.home_rounded, 'Home', 0),
              _navItem(Icons.menu_book_rounded, 'Quran', 1),
              const SizedBox(width: 48), // Space for FAB
              _navItem(Icons.explore_rounded, 'Qibla', 2),
              _navItem(Icons.auto_awesome_rounded, 'Tasbih', 3),
            ],
          ),
        ),
      ),
    );
  }

  Widget _navItem(IconData icon, String label, int index) {
    final theme = Theme.of(context);
    final isSelected = _currentIndex == index;

    return Expanded(
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () async {
          await Haptics.vibrate(HapticsType.selection);
          setState(() => _currentIndex = index);
        },
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 24,
              color: isSelected
                  ? theme.colorScheme.primary
                  : theme.colorScheme.onSurface.withValues(alpha: 0.4),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                color: isSelected
                    ? theme.colorScheme.primary
                    : theme.colorScheme.onSurface.withValues(alpha: 0.4),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPracticeFAB(BuildContext context) {
    final theme = Theme.of(context);

    return GestureDetector(
      onTap: () async {
        await Haptics.vibrate(HapticsType.medium);
        Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const RecitationPage()),
        );
      },
      child: Container(
        width: 64,
        height: 64,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              theme.colorScheme.primary,
              theme.colorScheme.primary.withValues(alpha: 0.8),
            ],
          ),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: theme.colorScheme.primary.withValues(alpha: 0.3),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: const Icon(
          Icons.mic_rounded,
          color: Colors.white,
          size: 32,
        ),
      ),
    );
  }
}

/// The Home tab content — streak, XP, continue, flashcards, goal ring, path map.
class HomeTab extends ConsumerStatefulWidget {
  const HomeTab({super.key});

  @override
  ConsumerState<HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends ConsumerState<HomeTab> {
  String _selectedLanguage = 'en';

  @override
  void initState() {
    super.initState();
    _loadLanguage();
  }

  Future<void> _loadLanguage() async {
    final storage = LocalStorageService();
    final lang = await storage.getSelectedLanguage();
    if (mounted && lang != null) {
      setState(() => _selectedLanguage = lang);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUrdu = _selectedLanguage == 'ur';

    return Scaffold(
      body: SereneBackground(
        child: SafeArea(
          child: RefreshIndicator(
          onRefresh: () async {
            await Haptics.vibrate(HapticsType.medium);
            // Trigger refresh — in production this would call the API
            await Future.delayed(const Duration(seconds: 1));
          },
          child: CustomScrollView(
            slivers: [
              // ─── Header ──────────────────────────────────────────────
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
                  child: Row(
                    children: [
                      Text(
                        isUrdu ? 'السلام علیکم' : 'Assalamu Alaikum',
                        style: theme.textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                        textDirection: isUrdu ? TextDirection.rtl : TextDirection.ltr,
                      ),
                      IconButton(
                        onPressed: () => Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => const ProfilePage(),
                          ),
                        ),
                        icon: Icon(
                          Icons.person_rounded,
                          color: theme.colorScheme.primary,
                        ),
                        tooltip: 'Profile',
                      ),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.primary.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.local_fire_department_rounded,
                              color: Colors.orange.shade700,
                              size: 20,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '7',
                              style: theme.textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w700,
                                color: Colors.orange.shade700,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // ─── XP Bar ──────────────────────────────────────────────
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  child: _XpBar(
                    currentXp: 340,
                    weeklyGoal: 500,
                  ),
                ),
              ),

              // ─── Continue Card ───────────────────────────────────────
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 8, 20, 8),
                  child: ContinueCard(
                    lessonTitle: isUrdu ? 'اسباق ۳: فعل' : 'Lesson 3: Fi\'l (Verbs)',
                    moduleNumber: 1,
                    progressPercent: 0.6,
                    onTap: () {
                      // Navigate to lesson player
                    },
                  ),
                ),
              ),

              // ─── Flashcards Due + Daily Goal Ring ────────────────────
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 8, 20, 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: _FlashcardsDueCard(
                          dueCount: 12,
                          onTap: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => const FlashcardPage(),
                              ),
                            );
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: DailyGoalRing(
                          current: 3,
                          goal: 5,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // ─── Learning Path Map ───────────────────────────────────
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
                  child: Text(
                    isUrdu ? 'سیکھنے کا راستہ' : 'Learning Path',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                    textDirection: isUrdu ? TextDirection.rtl : TextDirection.ltr,
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: const LearningPathMap(),
                ),
              ),

              const SliverToBoxAdapter(child: SizedBox(height: 32)),
            ],
          ),
        ),
      ),
      ),
    );
  }
}

/// XP progress bar widget.
class _XpBar extends StatelessWidget {
  final int currentXp;
  final int weeklyGoal;

  const _XpBar({required this.currentXp, required this.weeklyGoal});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final progress = (currentXp / weeklyGoal).clamp(0.0, 1.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.bolt_rounded, color: Colors.amber.shade700, size: 18),
            const SizedBox(width: 6),
            Text(
              '$currentXp / $weeklyGoal XP',
              style: theme.textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const Spacer(),
            Text(
              'This week',
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: LinearProgressIndicator(
            value: progress,
            minHeight: 8,
            backgroundColor: Colors.amber.withValues(alpha: 0.15),
            valueColor: AlwaysStoppedAnimation(Colors.amber.shade700),
          ),
        ),
      ],
    );
  }
}

/// Flashcards due card.
class _FlashcardsDueCard extends StatelessWidget {
  final int dueCount;
  final VoidCallback onTap;

  const _FlashcardsDueCard({required this.dueCount, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
            border: Border.all(
              color: theme.colorScheme.outline.withValues(alpha: 0.2),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.style_rounded, color: theme.colorScheme.secondary, size: 20),
                  const SizedBox(width: 6),
                  Text(
                    'Flashcards',
                    style: theme.textTheme.labelMedium?.copyWith(
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                '$dueCount',
                style: theme.textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: theme.colorScheme.secondary,
                ),
              ),
              Text(
                'due today',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
