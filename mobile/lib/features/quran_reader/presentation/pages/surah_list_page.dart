import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/serene_decorations.dart';
import '../../../../data/services/local_storage_service.dart';
import '../pages/quran_reader_page.dart';

/// Surah list page — browse and select surahs to read.
class SurahListPage extends ConsumerStatefulWidget {
  const SurahListPage({super.key});

  @override
  ConsumerState<SurahListPage> createState() => _SurahListPageState();
}

class _SurahListPageState extends ConsumerState<SurahListPage> {
  final _searchController = TextEditingController();
  List<_SurahInfo> _filteredSurahs = _allSurahs;
  String _selectedLanguage = 'en';

  @override
  void initState() {
    super.initState();
    _loadLanguage();
  }

  Future<void> _loadLanguage() async {
    final storage = LocalStorageService();
    await storage.ensureInitialized();
    final lang = await storage.getSelectedLanguage();
    if (mounted && lang != null) {
      setState(() => _selectedLanguage = lang);
    }
  }

  void _filterSurahs(String query) {
    setState(() {
      _filteredSurahs = _allSurahs.where((surah) {
        final q = query.toLowerCase();
        return surah.nameEnglish.toLowerCase().contains(q) ||
            surah.nameArabic.contains(query) ||
            surah.nameTranslation.toLowerCase().contains(q) ||
            surah.surahNumber.toString() == query;
      }).toList();
    });
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
      body: SereneBackground(
        child: SafeArea(
          child: Column(
          children: [
            // ─── Header ───────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Quran',
                    style: theme.textTheme.displaySmall?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Search bar
                  TextField(
                    controller: _searchController,
                    onChanged: _filterSurahs,
                    decoration: InputDecoration(
                      hintText: 'Search surah...',
                      prefixIcon: const Icon(Icons.search_rounded),
                      suffixIcon: _searchController.text.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear_rounded),
                              onPressed: () {
                                _searchController.clear();
                                _filterSurahs('');
                              },
                            )
                          : null,
                    ),
                  ),
                ],
              ),
            ),

            // ─── Surah List ───────────────────────────────────────────
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                itemCount: _filteredSurahs.length,
                itemBuilder: (context, index) {
                  final surah = _filteredSurahs[index];
                  return _SurahTile(
                    surah: surah,
                    onTap: () async {
                      await Haptics.vibrate(HapticsType.selection);
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => QuranReaderPage(
                            surahNumber: surah.surahNumber,
                            surahName: surah.nameArabic,
                          ),
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
      ),
    );
  }
}

/// A surah tile in the list.
class _SurahTile extends StatelessWidget {
  final _SurahInfo surah;
  final VoidCallback onTap;

  const _SurahTile({required this.surah, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
          margin: const EdgeInsets.only(bottom: 8),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(AppConstants.cardBorderRadius),
            border: Border.all(
              color: theme.colorScheme.outline.withValues(alpha: 0.15),
            ),
          ),
          child: Row(
            children: [
              // Surah number in decorative octagon
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Text(
                    '${surah.surahNumber}',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              // Surah names
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      surah.nameEnglish,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Text(
                      '${surah.nameTranslation} • ${surah.revelationType} • ${surah.ayahCount} ayahs',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                      ),
                    ),
                  ],
                ),
              ),
              // Arabic name
              Directionality(
                textDirection: TextDirection.rtl,
                child: Text(
                  surah.nameArabic,
                  style: AppTheme.arabicTextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w600,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Simple surah info for the list.
class _SurahInfo {
  final int surahNumber;
  final String nameArabic;
  final String nameEnglish;
  final String nameTranslation;
  final String revelationType;
  final int ayahCount;

  _SurahInfo({
    required this.surahNumber,
    required this.nameArabic,
    required this.nameEnglish,
    required this.nameTranslation,
    required this.revelationType,
    required this.ayahCount,
  });
}

/// Sample surah list (first 10 surahs for demonstration).
final _allSurahs = <_SurahInfo>[
  _SurahInfo(surahNumber: 1, nameArabic: 'الفاتحة', nameEnglish: 'Al-Fatihah', nameTranslation: 'The Opening', revelationType: 'Meccan', ayahCount: 7),
  _SurahInfo(surahNumber: 2, nameArabic: 'البقرة', nameEnglish: 'Al-Baqarah', nameTranslation: 'The Cow', revelationType: 'Medinan', ayahCount: 286),
  _SurahInfo(surahNumber: 3, nameArabic: 'آل عمران', nameEnglish: 'Aal-E-Imran', nameTranslation: 'The Family of Imran', revelationType: 'Medinan', ayahCount: 200),
  _SurahInfo(surahNumber: 4, nameArabic: 'النساء', nameEnglish: 'An-Nisa', nameTranslation: 'The Women', revelationType: 'Medinan', ayahCount: 176),
  _SurahInfo(surahNumber: 5, nameArabic: 'المائدة', nameEnglish: 'Al-Maidah', nameTranslation: 'The Table Spread', revelationType: 'Medinan', ayahCount: 120),
  _SurahInfo(surahNumber: 6, nameArabic: 'الأنعام', nameEnglish: 'Al-Anam', nameTranslation: 'The Cattle', revelationType: 'Meccan', ayahCount: 165),
  _SurahInfo(surahNumber: 7, nameArabic: 'الأعراف', nameEnglish: 'Al-Araf', nameTranslation: 'The Heights', revelationType: 'Meccan', ayahCount: 206),
  _SurahInfo(surahNumber: 8, nameArabic: 'الأنفال', nameEnglish: 'Al-Anfal', nameTranslation: 'The Spoils of War', revelationType: 'Medinan', ayahCount: 75),
  _SurahInfo(surahNumber: 9, nameArabic: 'التوبة', nameEnglish: 'At-Tawbah', nameTranslation: 'The Repentance', revelationType: 'Medinan', ayahCount: 129),
  _SurahInfo(surahNumber: 10, nameArabic: 'يونس', nameEnglish: 'Yunus', nameTranslation: 'Jonah', revelationType: 'Meccan', ayahCount: 109),
];
