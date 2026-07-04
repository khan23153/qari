import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/constants/app_constants.dart';

/// S5. Quran Reader — the flagship screen.
/// Ayah-by-ayah vertical scroll with color-coded word-by-word grammar.
class QuranReaderPage extends ConsumerStatefulWidget {
  const QuranReaderPage({super.key});

  @override
  ConsumerState<QuranReaderPage> createState() => _QuranReaderPageState();
}

class _QuranReaderPageState extends ConsumerState<QuranReaderPage> {
  bool _grammarColorsOn = true;
  bool _tajweedColorsOn = false;
  bool _showTranslit = true;
  bool _showWordMeaning = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Quran'),
        actions: [
          IconButton(
            icon: Icon(_grammarColorsOn ? Icons.palette : Icons.palette_outlined),
            onPressed: () => setState(() {
              _grammarColorsOn = !_grammarColorsOn;
              if (_grammarColorsOn) _tajweedColorsOn = false;
            }),
            tooltip: 'Grammar colors',
          ),
          IconButton(
            icon: Icon(_tajweedColorsOn ? Icons.colorize : Icons.colorize_outlined),
            onPressed: () => setState(() {
              _tajweedColorsOn = !_tajweedColorsOn;
              if (_tajweedColorsOn) _grammarColorsOn = false;
            }),
            tooltip: 'Tajweed colors',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Surah header
            _surahHeader(context),
            // Legend chip
            if (_grammarColorsOn) _legendChip(context),
            // Ayahs (placeholder — would be populated from API)
            _ayahWidget(context, 1, 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ', [
              {'word': 'بِسْمِ', 'translit': 'bismi', 'meaning': 'In the name', 'pos': 'harf'},
              {'word': 'اللَّهِ', 'translit': 'Allahi', 'meaning': 'of Allah', 'pos': 'ism'},
              {'word': 'الرَّحْمَٰنِ', 'translit': 'ar-Rahmani', 'meaning': 'the Most Gracious', 'pos': 'ism'},
              {'word': 'الرَّحِيمِ', 'translit': 'ar-Raheemi', 'meaning': 'the Most Merciful', 'pos': 'ism'},
            ]),
            const SizedBox(height: 16),
            _ayahWidget(context, 2, 'الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ', [
              {'word': 'الْحَمْدُ', 'translit': 'al-hamdu', 'meaning': 'All praise', 'pos': 'ism'},
              {'word': 'لِلَّهِ', 'translit': 'lillahi', 'meaning': 'is for Allah', 'pos': 'harf'},
              {'word': 'رَبِّ', 'translit': 'rabbi', 'meaning': 'Lord', 'pos': 'ism'},
              {'word': 'الْعَالَمِينَ', 'translit': 'al-'aalameena', 'meaning': 'of the worlds', 'pos': 'ism'},
            ]),
          ],
        ),
      ),
    );
  }

  Widget _surahHeader(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Text('Al-Fatihah', style: Theme.of(context).textTheme.headlineSmall),
            Text('سورة الفاتحة', style: TextStyle(
              fontFamily: 'QuranUthmani',
              fontSize: 28 * LocalStorageService.instance.fontScale,
            )),
            const SizedBox(height: 4),
            Text('The Opener · 7 Ayahs · Makkah',
              style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }

  Widget _legendChip(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Wrap(
        spacing: 8,
        children: [
          _legendItem('Fi\'l', AppTheme.grammarColor('fil')),
          _legendItem('Ism', AppTheme.grammarColor('ism')),
          _legendItem('Harf', AppTheme.grammarColor('harf')),
        ],
      ),
    );
  }

  Widget _legendItem(String label, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 12, height: 12, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 12)),
      ],
    );
  }

  Widget _ayahWidget(BuildContext context, int ayahNum, String fullText, List<Map<String, String>> words) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Arabic text with per-word tap targets
            Directionality(
              textDirection: TextDirection.rtl,
              child: Wrap(
                spacing: 4,
                runSpacing: 8,
                children: words.map((w) => _wordTapTarget(context, w)).toList(),
              ),
            ),
            const SizedBox(height: 12),
            // Gloss line
            if (_showTranslit || _showWordMeaning)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Directionality(
                  textDirection: TextDirection.rtl,
                  child: Wrap(
                    spacing: 8,
                    children: words.map((w) => Text(
                      _showWordMeaning
                          ? '${w['translit']} (${w['meaning']})'
                          : w['translit']!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    )).toList(),
                  ),
                ),
              ),
            const SizedBox(height: 8),
            // Ayah action row
            Row(
              children: [
                Text('$ayahNum', style: Theme.of(context).textTheme.bodySmall),
                const Spacer(),
                IconButton(icon: const Icon(Icons.play_arrow), iconSize: 20, onPressed: () {}),
                IconButton(icon: const Icon(Icons.mic), iconSize: 20, onPressed: () {}),
                IconButton(icon: const Icon(Icons.bookmark_border), iconSize: 20, onPressed: () {}),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _wordTapTarget(BuildContext context, Map<String, String> word) {
    final posGroup = word['pos']!;
    final color = _grammarColorsOn ? AppTheme.grammarColor(posGroup) : null;

    return GestureDetector(
      onTap: () => _showWordBottomSheet(context, word),
      child: Text(
        word['word']!,
        style: TextStyle(
          fontFamily: 'QuranUthmani',
          fontSize: 26 * LocalStorageService.instance.fontScale,
          color: color,
          decoration: _grammarColorsOn && posGroup == 'fil'
              ? TextDecoration.underline
              : _grammarColorsOn && posGroup == 'harf'
                  ? TextDecoration.underline
                  : null,
          decorationStyle: posGroup == 'harf' ? TextDecorationStyle.dotted : TextDecorationStyle.solid,
          decorationColor: color,
        ),
      ),
    );
  }

  void _showWordBottomSheet(BuildContext context, Map<String, String> word) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(word['word']!, style: const TextStyle(fontFamily: 'QuranUthmani', fontSize: 32)),
            const SizedBox(height: 8),
            Text(word['translit']!, style: Theme.of(context).textTheme.titleMedium),
            Text(word['meaning']!, style: Theme.of(context).textTheme.bodyLarge),
            const SizedBox(height: 8),
            Text('POS: ${word['pos']}', style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 16),
            Row(
              children: [
                IconButton(icon: const Icon(Icons.volume_up), onPressed: () {}),
                const Spacer(),
                FilledButton.tonal(
                  onPressed: () {},
                  child: const Text('Save to Flashcards'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// Import needed for fontScale
import '../../../data/services/local_storage_service.dart';
