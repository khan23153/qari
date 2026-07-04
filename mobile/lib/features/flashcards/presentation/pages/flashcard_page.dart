import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

/// S9. Flashcards — full-screen card with SM-2 grading.
class FlashcardPage extends ConsumerStatefulWidget {
  const FlashcardPage({super.key});

  @override
  ConsumerState<FlashcardPage> createState() => _FlashcardPageState();
}

class _FlashcardPageState extends ConsumerState<FlashcardPage> {
  bool _showBack = false;
  int _currentIndex = 0;
  final _cards = [
    {'arabic': 'الْحَمْدُ', 'translit': 'al-hamdu', 'meaning': 'All praise', 'ayah': '1:2'},
    {'arabic': 'رَبِّ', 'translit': 'rabbi', 'meaning': 'Lord', 'ayah': '1:2'},
    {'arabic': 'الرَّحْمَٰنِ', 'translit': 'ar-Rahmani', 'meaning': 'the Most Gracious', 'ayah': '1:1'},
  ];

  @override
  Widget build(BuildContext context) {
    if (_currentIndex >= _cards.length) {
      return _buildSessionComplete(context);
    }

    final card = _cards[_currentIndex];
    return Scaffold(
      appBar: AppBar(
        title: Text('${_currentIndex + 1} / ${_cards.length}'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: GestureDetector(
        onTap: () => setState(() => _showBack = !_showBack),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(),
              Card(
                elevation: 4,
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    children: [
                      if (!_showBack) ...[
                        Text(
                          card['arabic']!,
                          style: const TextStyle(fontFamily: 'QuranUthmani', fontSize: 48),
                        ),
                        const SizedBox(height: 16),
                        Text('Tap to reveal', style: Theme.of(context).textTheme.bodySmall),
                      ] else ...[
                        Text(card['arabic']!, style: const TextStyle(fontFamily: 'QuranUthmani', fontSize: 36)),
                        const SizedBox(height: 16),
                        Text(card['translit']!, style: Theme.of(context).textTheme.titleLarge),
                        Text(card['meaning']!, style: Theme.of(context).textTheme.headlineSmall),
                        const SizedBox(height: 8),
                        Text('From: ${card['ayah']}', style: Theme.of(context).textTheme.bodySmall),
                        IconButton(icon: const Icon(Icons.volume_up), onPressed: () {}),
                      ],
                    ],
                  ),
                ),
              ),
              const Spacer(),
              if (_showBack) ...[
                const Text('How well did you know this?', textAlign: TextAlign.center),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: FilledButton.tonal(
                        onPressed: () => _grade(1),
                        style: FilledButton.styleFrom(backgroundColor: Colors.red.shade100),
                        child: const Text('Bhool gaya'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: FilledButton.tonal(
                        onPressed: () => _grade(3),
                        style: FilledButton.styleFrom(backgroundColor: Colors.orange.shade100),
                        child: const Text('Mushkil'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: FilledButton.tonal(
                        onPressed: () => _grade(5),
                        style: FilledButton.styleFrom(backgroundColor: Colors.green.shade100),
                        child: const Text('Aasaan'),
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSessionComplete(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Session Complete'), automaticallyImplyLeading: false),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.check_circle, size: 80, color: Colors.green),
              const SizedBox(height: 16),
              Text('Mubarak! ${_cards.length} cards reviewed', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              const Text('Next review in 1 day'),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Done'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _grade(int grade) async {
    await Haptics.selectionClick();
    setState(() {
      _currentIndex++;
      _showBack = false;
    });
  }
}
