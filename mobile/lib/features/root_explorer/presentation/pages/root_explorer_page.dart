import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../data/repositories/corpus_repository.dart';

/// S6: Root Explorer — root in large Arabic + core meaning, visual tree
/// with derived words as leaves.
class RootExplorerPage extends ConsumerStatefulWidget {
  final int? rootId;
  final String? rootArabic;

  const RootExplorerPage({super.key, this.rootId, this.rootArabic});

  @override
  ConsumerState<RootExplorerPage> createState() => _RootExplorerPageState();
}

class _RootExplorerPageState extends ConsumerState<RootExplorerPage> {
  final _searchController = TextEditingController();
  RootDetail? _rootDetail;
  bool _isLoading = false;
  String? _error;

  // Sample root data for demonstration
  final _sampleRoot = RootDetail(
    rootId: 1,
    rootArabic: 'ك ت ب',
    rootTransliteration: 'k-t-b',
    coreMeaning: 'to write, record, inscription',
    coreMeaningUrdu: 'لکھنا، تحریر کرنا',
    derivedWords: [
      DerivedWord(word: 'كَتَبَ', transliteration: 'kataba', meaning: 'he wrote', posGroup: 'fiil_madi', surahNumber: 2, ayahNumber: 28, frequency: 319),
      DerivedWord(word: 'كِتَاب', transliteration: 'kitāb', meaning: 'book, writing', posGroup: 'ism', surahNumber: 2, ayahNumber: 2, frequency: 261),
      DerivedWord(word: 'كَاتِب', transliteration: 'kātib', meaning: 'writer, scribe', posGroup: 'ism', surahNumber: 2, ayahNumber: 282, frequency: 8),
      DerivedWord(word: 'مَكْتُوب', transliteration: 'maktūb', meaning: 'written, decreed', posGroup: 'ism', surahNumber: 7, ayahNumber: 145, frequency: 12),
      DerivedWord(word: 'مَكْتَب', transliteration: 'maktab', meaning: 'office, desk', posGroup: 'ism', surahNumber: null, ayahNumber: null, frequency: 3),
      DerivedWord(word: 'كُتُب', transliteration: 'kutub', meaning: 'books (plural)', posGroup: 'ism', surahNumber: 2, ayahNumber: 3, frequency: 45),
      DerivedWord(word: 'كِتَابَة', transliteration: 'kitāba', meaning: 'writing (act)', posGroup: 'ism', surahNumber: null, ayahNumber: null, frequency: 5),
    ],
  );

  @override
  void initState() {
    super.initState();
    _loadRoot();
  }

  Future<void> _loadRoot() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      if (widget.rootId != null) {
        final repo = CorpusRepository();
        _rootDetail = await repo.getRoot(widget.rootId!);
      } else {
        // Use sample data
        await Future.delayed(const Duration(milliseconds: 300));
        _rootDetail = _sampleRoot;
      }
    } catch (e) {
      // Fallback to sample data
      _rootDetail = _sampleRoot;
    }

    if (mounted) {
      setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // ─── Header ───────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back_rounded),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                  Expanded(
                    child: Text(
                      'Root Explorer',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // ─── Search Bar ───────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: TextField(
                controller: _searchController,
                decoration: InputDecoration(
                  hintText: 'Search root (e.g. كتب, ktb)...',
                  prefixIcon: const Icon(Icons.search_rounded),
                ),
              ),
            ),

            const SizedBox(height: 16),

            // ─── Content ──────────────────────────────────────────────
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _error != null
                      ? Center(child: Text(_error!))
                      : _rootDetail != null
                          ? _buildRootTree(theme)
                          : const Center(child: Text('No root found')),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRootTree(ThemeData theme) {
    final root = _rootDetail!;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          // ─── Root Display (large) ──────────────────────────────────
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(32),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  theme.colorScheme.primary.withValues(alpha: 0.1),
                  theme.colorScheme.primary.withValues(alpha: 0.03),
                ],
              ),
              borderRadius: BorderRadius.circular(24),
            ),
            child: Column(
              children: [
                // Root letters
                Directionality(
                  textDirection: TextDirection.rtl,
                  child: Text(
                    root.rootArabic,
                    style: AppTheme.arabicTextStyle(
                      fontSize: 48,
                      fontWeight: FontWeight.w700,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                )
                    .animate()
                    .fadeIn(duration: 500.ms)
                    .scale(
                      begin: const Offset(0.8, 0.8),
                      end: const Offset(1, 1),
                      duration: 500.ms,
                      curve: Curves.elasticOut,
                    ),
                const SizedBox(height: 12),
                Text(
                  root.rootTransliteration,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontStyle: FontStyle.italic,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  root.coreMeaning,
                  style: theme.textTheme.bodyLarge?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.8),
                  ),
                  textAlign: TextAlign.center,
                ),
                if (root.coreMeaningUrdu != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    root.coreMeaningUrdu!,
                    style: AppTheme.urduTextStyle(
                      fontSize: 16,
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                    ),
                    textDirection: TextDirection.rtl,
                  ),
                ],
              ],
            ),
          ),

          const SizedBox(height: 24),

          // ─── Tree Structure ────────────────────────────────────────
          // Trunk
          _TreeConnector(label: '${root.derivedWords.length} derived words', theme: theme),

          const SizedBox(height: 16),

          // Derived words as leaves
          ...root.derivedWords.asMap().entries.map((entry) {
            final index = entry.key;
            final word = entry.value;
            return _DerivedWordLeaf(
              word: word,
              isLeft: index % 2 == 0,
              theme: theme,
              onTap: () async {
                await Haptics.vibrate(HapticsType.selection);
                // Could navigate to ayah or word detail
              },
            )
                .animate()
                .fadeIn(
                  delay: Duration(milliseconds: 300 + index * 80),
                  duration: 400.ms,
                )
                .slideX(
                  begin: index % 2 == 0 ? -0.1 : 0.1,
                  end: 0,
                  duration: 400.ms,
                );
          }),

          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

/// Tree connector line with label.
class _TreeConnector extends StatelessWidget {
  final String label;
  final ThemeData theme;

  const _TreeConnector({required this.label, required this.theme});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 3,
          height: 30,
          color: theme.colorScheme.primary.withValues(alpha: 0.3),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          decoration: BoxDecoration(
            color: theme.colorScheme.primary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            label,
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        Container(
          width: 3,
          height: 20,
          color: theme.colorScheme.primary.withValues(alpha: 0.3),
        ),
      ],
    );
  }
}

/// A derived word leaf in the tree.
class _DerivedWordLeaf extends StatelessWidget {
  final DerivedWord word;
  final bool isLeft;
  final ThemeData theme;
  final VoidCallback onTap;

  const _DerivedWordLeaf({
    required this.word,
    required this.isLeft,
    required this.theme,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final config = AppTheme.getGrammarConfig(word.posGroup ?? 'default');

    return Padding(
      padding: EdgeInsets.only(
        left: isLeft ? 0 : 40,
        right: isLeft ? 40 : 0,
        bottom: 12,
      ),
      child: Material(
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
                color: config.color.withValues(alpha: 0.2),
              ),
            ),
            child: Row(
              children: [
                // Arabic word
                Directionality(
                  textDirection: TextDirection.rtl,
                  child: Text(
                    word.word,
                    style: AppTheme.arabicTextStyle(
                      fontSize: 28,
                      color: config.color,
                      decoration: AppTheme.toTextDecoration(config.underlineStyle),
                      decorationColor: config.color,
                      decorationStyle: config.underlineStyle == UnderlineStyle.dotted
                          ? TextDecorationStyle.dotted
                          : TextDecorationStyle.solid,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                // Meaning and info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        word.transliteration,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          fontStyle: FontStyle.italic,
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                        ),
                      ),
                      Text(
                        word.meaning ?? '—',
                        style: theme.textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Row(
                        children: [
                          if (word.surahNumber != null)
                            Text(
                              '${word.surahNumber}:${word.ayahNumber}',
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: theme.colorScheme.primary,
                              ),
                            ),
                          if (word.surahNumber != null) const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: config.color.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              config.label,
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                                color: config.color,
                              ),
                            ),
                          ),
                          const Spacer(),
                          Text(
                            '${word.frequency}×',
                            style: theme.textTheme.labelSmall?.copyWith(
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
