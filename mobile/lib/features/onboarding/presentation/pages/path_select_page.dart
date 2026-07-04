import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../data/services/local_storage_service.dart';
import '../../home/presentation/pages/home_page.dart';

/// S2. Welcome / Path Select — two large stacked buttons.
/// "Zero Se Shuru Karein" (foundation) or "Direct Quran Par Jayein" (quran_direct).
class PathSelectPage extends ConsumerWidget {
  const PathSelectPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Warm illustration placeholder
              Icon(
                Icons.menu_book,
                size: 80,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: 24),
              Text(
                'Welcome to Qari',
                style: Theme.of(context).textTheme.headlineMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Aap kaise shuru karna chahenge?',
                style: Theme.of(context).textTheme.titleMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 40),
              // Foundation path
              _pathCard(
                context,
                icon: Icons.eco,
                title: 'Zero Se Shuru Karein',
                subtitle: 'Alphabet aur grammar se seekhna shuru karein',
                onTap: () => _selectPath(context, 'foundation'),
              ),
              const SizedBox(height: 16),
              // Quran direct path
              _pathCard(
                context,
                icon: Icons.book,
                title: 'Direct Quran Par Jayein',
                subtitle: 'Word-by-word matlab ke saath padhein',
                onTap: () => _selectPath(context, 'quran_direct'),
              ),
              const SizedBox(height: 24),
              Text(
                'Aap baad mein kabhi bhi switch kar sakte hain.',
                style: Theme.of(context).textTheme.bodySmall,
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _pathCard(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Icon(icon, size: 40, color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
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

  Future<void> _selectPath(BuildContext context, String path) async {
    await Haptics.selectionClick();
    await LocalStorageService.instance.setStartingPath(path);
    await LocalStorageService.instance.setOnboarded(true);

    if (context.mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const HomePage()),
      );
    }
  }
}
