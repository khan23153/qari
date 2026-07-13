import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/serene_decorations.dart';
import '../../../../data/models/surah_model.dart';
import '../../../../data/repositories/corpus_repository.dart';
import '../pages/quran_reader_page.dart';

/// Surah list page — browse and select surahs to read. Loads all 114 surahs
/// from the API; falls back to a bundled list when offline so the screen is
/// never empty.
class SurahListPage extends ConsumerStatefulWidget {
  const SurahListPage({super.key});

  @override
  ConsumerState<SurahListPage> createState() => _SurahListPageState();
}

class _SurahListPageState extends ConsumerState<SurahListPage> {
  final _searchController = TextEditingController();
  List<SurahModel> _surahs = _fallbackSurahs;
  List<SurahModel> _filteredSurahs = _fallbackSurahs;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSurahs();
  }  /// Loads the list of surahs from the API. The bundled list of all 114
  /// surahs is always the base so the user can browse and open every surah
  /// even if the backend returns a partial/empty list or is unreachable. Any
  /// server data is merged in (by surah number) to refresh names/counts.
  Future<void> _loadSurahs() async {
    setState(() => _isLoading = true);
    try {
      final serverSurahs = await CorpusRepository().getSurahs();
      if (mounted) {
        setState(() {
          _surahs = _mergeWithFallback(serverSurahs);
          _filteredSurahs = _surahs;
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint('SurahList: failed to load surahs, using fallback: $e');
      if (mounted) {
        setState(() {
          _surahs = _fallbackSurahs;
          _filteredSurahs = _fallbackSurahs;
          _isLoading = false;
        });
      }
    }
  }

  /// Merges server surahs into the bundled 114-surah fallback by surah number.
  /// Server data wins on a match; missing surahs keep their bundled entry so
  /// the list is always complete (114).
  List<SurahModel> _mergeWithFallback(List<SurahModel> serverSurahs) {
    if (serverSurahs.isEmpty) return List.from(_fallbackSurahs);
    final byNumber = {for (final s in serverSurahs) s.surahNumber: s};
    final merged = <SurahModel>[];
    for (final fallback in _fallbackSurahs) {
      merged.add(byNumber[fallback.surahNumber] ?? fallback);
    }
    // Include any server surah not present in the fallback (defensive).
    for (final s in serverSurahs) {
      if (!_fallbackSurahs.any((f) => f.surahNumber == s.surahNumber)) {
        merged.add(s);
      }
    }
    merged.sort((a, b) => a.surahNumber.compareTo(b.surahNumber));
    return merged;
  }

  void _filterSurahs(String query) {
    setState(() {
      final q = query.toLowerCase();
      _filteredSurahs = _surahs.where((surah) {
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
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 16, vertical: 8),
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
  final SurahModel surah;
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

/// Bundled list of all 114 surahs, used when the API is unreachable so the
/// list is never empty. Field order: number, Arabic, English, translation,
/// revelation place, ayah count.
const List<SurahModel> _fallbackSurahs = [
  SurahModel(surahId: 1, surahNumber: 1, nameArabic: 'الفاتحة', nameEnglish: 'Al-Fatihah', nameTranslation: 'The Opening', revelationType: 'Meccan', ayahCount: 7, revelationOrder: 5),
  SurahModel(surahId: 2, surahNumber: 2, nameArabic: 'البقرة', nameEnglish: 'Al-Baqarah', nameTranslation: 'The Cow', revelationType: 'Medinan', ayahCount: 286, revelationOrder: 87),
  SurahModel(surahId: 3, surahNumber: 3, nameArabic: 'آل عمران', nameEnglish: 'Aal-E-Imran', nameTranslation: 'The Family of Imran', revelationType: 'Medinan', ayahCount: 200, revelationOrder: 89),
  SurahModel(surahId: 4, surahNumber: 4, nameArabic: 'النساء', nameEnglish: 'An-Nisa', nameTranslation: 'The Women', revelationType: 'Medinan', ayahCount: 176, revelationOrder: 92),
  SurahModel(surahId: 5, surahNumber: 5, nameArabic: 'المائدة', nameEnglish: 'Al-Maidah', nameTranslation: 'The Table Spread', revelationType: 'Medinan', ayahCount: 120, revelationOrder: 112),
  SurahModel(surahId: 6, surahNumber: 6, nameArabic: 'الأنعام', nameEnglish: 'Al-An\'am', nameTranslation: 'The Cattle', revelationType: 'Meccan', ayahCount: 165, revelationOrder: 55),
  SurahModel(surahId: 7, surahNumber: 7, nameArabic: 'الأعراف', nameEnglish: 'Al-A\'raf', nameTranslation: 'The Heights', revelationType: 'Meccan', ayahCount: 206, revelationOrder: 39),
  SurahModel(surahId: 8, surahNumber: 8, nameArabic: 'الأنفال', nameEnglish: 'Al-Anfal', nameTranslation: 'The Spoils of War', revelationType: 'Medinan', ayahCount: 75, revelationOrder: 88),
  SurahModel(surahId: 9, surahNumber: 9, nameArabic: 'التوبة', nameEnglish: 'At-Tawbah', nameTranslation: 'The Repentance', revelationType: 'Medinan', ayahCount: 129, revelationOrder: 113),
  SurahModel(surahId: 10, surahNumber: 10, nameArabic: 'يونس', nameEnglish: 'Yunus', nameTranslation: 'Jonah', revelationType: 'Meccan', ayahCount: 109, revelationOrder: 51),
  SurahModel(surahId: 11, surahNumber: 11, nameArabic: 'هود', nameEnglish: 'Hud', nameTranslation: 'Hud', revelationType: 'Meccan', ayahCount: 123, revelationOrder: 52),
  SurahModel(surahId: 12, surahNumber: 12, nameArabic: 'يوسف', nameEnglish: 'Yusuf', nameTranslation: 'Joseph', revelationType: 'Meccan', ayahCount: 111, revelationOrder: 53),
  SurahModel(surahId: 13, surahNumber: 13, nameArabic: 'الرعد', nameEnglish: 'Ar-Ra\'d', nameTranslation: 'The Thunder', revelationType: 'Medinan', ayahCount: 43, revelationOrder: 96),
  SurahModel(surahId: 14, surahNumber: 14, nameArabic: 'ابراهيم', nameEnglish: 'Ibrahim', nameTranslation: 'Abraham', revelationType: 'Meccan', ayahCount: 52, revelationOrder: 72),
  SurahModel(surahId: 15, surahNumber: 15, nameArabic: 'الحجر', nameEnglish: 'Al-Hijr', nameTranslation: 'The Rocky Tract', revelationType: 'Meccan', ayahCount: 99, revelationOrder: 54),
  SurahModel(surahId: 16, surahNumber: 16, nameArabic: 'النحل', nameEnglish: 'An-Nahl', nameTranslation: 'The Bee', revelationType: 'Meccan', ayahCount: 128, revelationOrder: 70),
  SurahModel(surahId: 17, surahNumber: 17, nameArabic: 'الإسراء', nameEnglish: 'Al-Isra', nameTranslation: 'The Night Journey', revelationType: 'Meccan', ayahCount: 111, revelationOrder: 50),
  SurahModel(surahId: 18, surahNumber: 18, nameArabic: 'الكهف', nameEnglish: 'Al-Kahf', nameTranslation: 'The Cave', revelationType: 'Meccan', ayahCount: 110, revelationOrder: 69),
  SurahModel(surahId: 19, surahNumber: 19, nameArabic: 'مريم', nameEnglish: 'Maryam', nameTranslation: 'Mary', revelationType: 'Meccan', ayahCount: 98, revelationOrder: 44),
  SurahModel(surahId: 20, surahNumber: 20, nameArabic: 'طه', nameEnglish: 'Ta-Ha', nameTranslation: 'Ta-Ha', revelationType: 'Meccan', ayahCount: 135, revelationOrder: 45),
  SurahModel(surahId: 21, surahNumber: 21, nameArabic: 'الأنبياء', nameEnglish: 'Al-Anbiya', nameTranslation: 'The Prophets', revelationType: 'Meccan', ayahCount: 112, revelationOrder: 73),
  SurahModel(surahId: 22, surahNumber: 22, nameArabic: 'الحج', nameEnglish: 'Al-Hajj', nameTranslation: 'The Pilgrimage', revelationType: 'Medinan', ayahCount: 78, revelationOrder: 103),
  SurahModel(surahId: 23, surahNumber: 23, nameArabic: 'المؤمنون', nameEnglish: 'Al-Mu\'minun', nameTranslation: 'The Believers', revelationType: 'Meccan', ayahCount: 118, revelationOrder: 74),
  SurahModel(surahId: 24, surahNumber: 24, nameArabic: 'النور', nameEnglish: 'An-Nur', nameTranslation: 'The Light', revelationType: 'Medinan', ayahCount: 64, revelationOrder: 102),
  SurahModel(surahId: 25, surahNumber: 25, nameArabic: 'الفرقان', nameEnglish: 'Al-Furqan', nameTranslation: 'The Criterion', revelationType: 'Meccan', ayahCount: 77, revelationOrder: 42),
  SurahModel(surahId: 26, surahNumber: 26, nameArabic: 'الشعراء', nameEnglish: 'Ash-Shu\'ara', nameTranslation: 'The Poets', revelationType: 'Meccan', ayahCount: 227, revelationOrder: 47),
  SurahModel(surahId: 27, surahNumber: 27, nameArabic: 'النمل', nameEnglish: 'An-Naml', nameTranslation: 'The Ant', revelationType: 'Meccan', ayahCount: 93, revelationOrder: 48),
  SurahModel(surahId: 28, surahNumber: 28, nameArabic: 'القصص', nameEnglish: 'Al-Qasas', nameTranslation: 'The Stories', revelationType: 'Meccan', ayahCount: 88, revelationOrder: 49),
  SurahModel(surahId: 29, surahNumber: 29, nameArabic: 'العنكبوت', nameEnglish: 'Al-Ankabut', nameTranslation: 'The Spider', revelationType: 'Meccan', ayahCount: 69, revelationOrder: 85),
  SurahModel(surahId: 30, surahNumber: 30, nameArabic: 'الروم', nameEnglish: 'Ar-Rum', nameTranslation: 'The Romans', revelationType: 'Meccan', ayahCount: 60, revelationOrder: 84),
  SurahModel(surahId: 31, surahNumber: 31, nameArabic: 'لقمان', nameEnglish: 'Luqman', nameTranslation: 'Luqman', revelationType: 'Meccan', ayahCount: 34, revelationOrder: 57),
  SurahModel(surahId: 32, surahNumber: 32, nameArabic: 'السجدة', nameEnglish: 'As-Sajdah', nameTranslation: 'The Prostration', revelationType: 'Meccan', ayahCount: 30, revelationOrder: 75),
  SurahModel(surahId: 33, surahNumber: 33, nameArabic: 'الأحزاب', nameEnglish: 'Al-Ahzab', nameTranslation: 'The Confederates', revelationType: 'Medinan', ayahCount: 73, revelationOrder: 90),
  SurahModel(surahId: 34, surahNumber: 34, nameArabic: 'سبأ', nameEnglish: 'Saba', nameTranslation: 'Sheba', revelationType: 'Meccan', ayahCount: 54, revelationOrder: 58),
  SurahModel(surahId: 35, surahNumber: 35, nameArabic: 'فاطر', nameEnglish: 'Fatir', nameTranslation: 'The Originator', revelationType: 'Meccan', ayahCount: 45, revelationOrder: 43),
  SurahModel(surahId: 36, surahNumber: 36, nameArabic: 'يس', nameEnglish: 'Ya-Sin', nameTranslation: 'Ya-Sin', revelationType: 'Meccan', ayahCount: 83, revelationOrder: 41),
  SurahModel(surahId: 37, surahNumber: 37, nameArabic: 'الصافات', nameEnglish: 'As-Saffat', nameTranslation: 'Those who set the ranks', revelationType: 'Meccan', ayahCount: 182, revelationOrder: 56),
  SurahModel(surahId: 38, surahNumber: 38, nameArabic: 'ص', nameEnglish: 'Sad', nameTranslation: 'Sad', revelationType: 'Meccan', ayahCount: 88, revelationOrder: 38),
  SurahModel(surahId: 39, surahNumber: 39, nameArabic: 'الزمر', nameEnglish: 'Az-Zumar', nameTranslation: 'The Troops', revelationType: 'Meccan', ayahCount: 75, revelationOrder: 59),
  SurahModel(surahId: 40, surahNumber: 40, nameArabic: 'غافر', nameEnglish: 'Ghafir', nameTranslation: 'The Forgiver', revelationType: 'Meccan', ayahCount: 85, revelationOrder: 60),
  SurahModel(surahId: 41, surahNumber: 41, nameArabic: 'فصلت', nameEnglish: 'Fussilat', nameTranslation: 'Explained in detail', revelationType: 'Meccan', ayahCount: 54, revelationOrder: 61),
  SurahModel(surahId: 42, surahNumber: 42, nameArabic: 'الشورى', nameEnglish: 'Ash-Shura', nameTranslation: 'The Consultation', revelationType: 'Meccan', ayahCount: 53, revelationOrder: 62),
  SurahModel(surahId: 43, surahNumber: 43, nameArabic: 'الزخرف', nameEnglish: 'Az-Zukhruf', nameTranslation: 'The Ornaments of Gold', revelationType: 'Meccan', ayahCount: 89, revelationOrder: 63),
  SurahModel(surahId: 44, surahNumber: 44, nameArabic: 'الدخان', nameEnglish: 'Ad-Dukhan', nameTranslation: 'The Smoke', revelationType: 'Meccan', ayahCount: 59, revelationOrder: 64),
  SurahModel(surahId: 45, surahNumber: 45, nameArabic: 'الجاثية', nameEnglish: 'Al-Jathiyah', nameTranslation: 'The Kneeling', revelationType: 'Meccan', ayahCount: 37, revelationOrder: 65),
  SurahModel(surahId: 46, surahNumber: 46, nameArabic: 'الأحقاف', nameEnglish: 'Al-Ahqaf', nameTranslation: 'The Wind-Curtains', revelationType: 'Meccan', ayahCount: 35, revelationOrder: 66),
  SurahModel(surahId: 47, surahNumber: 47, nameArabic: 'محمد', nameEnglish: 'Muhammad', nameTranslation: 'Muhammad', revelationType: 'Medinan', ayahCount: 38, revelationOrder: 95),
  SurahModel(surahId: 48, surahNumber: 48, nameArabic: 'الفتح', nameEnglish: 'Al-Fath', nameTranslation: 'The Victory', revelationType: 'Medinan', ayahCount: 29, revelationOrder: 111),
  SurahModel(surahId: 49, surahNumber: 49, nameArabic: 'الحجرات', nameEnglish: 'Al-Hujurat', nameTranslation: 'The Dwellings', revelationType: 'Medinan', ayahCount: 18, revelationOrder: 106),
  SurahModel(surahId: 50, surahNumber: 50, nameArabic: 'ق', nameEnglish: 'Qaf', nameTranslation: 'Qaf', revelationType: 'Meccan', ayahCount: 45, revelationOrder: 34),
  SurahModel(surahId: 51, surahNumber: 51, nameArabic: 'الذاريات', nameEnglish: 'Adh-Dhariyat', nameTranslation: 'The Winnowing Winds', revelationType: 'Meccan', ayahCount: 60, revelationOrder: 43),
  SurahModel(surahId: 52, surahNumber: 52, nameArabic: 'الطور', nameEnglish: 'At-Tur', nameTranslation: 'The Mount', revelationType: 'Meccan', ayahCount: 49, revelationOrder: 76),
  SurahModel(surahId: 53, surahNumber: 53, nameArabic: 'النجم', nameEnglish: 'An-Najm', nameTranslation: 'The Star', revelationType: 'Meccan', ayahCount: 62, revelationOrder: 23),
  SurahModel(surahId: 54, surahNumber: 54, nameArabic: 'القمر', nameEnglish: 'Al-Qamar', nameTranslation: 'The Moon', revelationType: 'Meccan', ayahCount: 55, revelationOrder: 37),
  SurahModel(surahId: 55, surahNumber: 55, nameArabic: 'الرحمن', nameEnglish: 'Ar-Rahman', nameTranslation: 'The Beneficent', revelationType: 'Meccan', ayahCount: 78, revelationOrder: 97),
  SurahModel(surahId: 56, surahNumber: 56, nameArabic: 'الواقعة', nameEnglish: 'Al-Waqi\'ah', nameTranslation: 'The Inevitable', revelationType: 'Meccan', ayahCount: 96, revelationOrder: 46),
  SurahModel(surahId: 57, surahNumber: 57, nameArabic: 'الحديد', nameEnglish: 'Al-Hadid', nameTranslation: 'The Iron', revelationType: 'Medinan', ayahCount: 29, revelationOrder: 94),
  SurahModel(surahId: 58, surahNumber: 58, nameArabic: 'المجادلة', nameEnglish: 'Al-Mujadila', nameTranslation: 'The Pleading Woman', revelationType: 'Medinan', ayahCount: 22, revelationOrder: 105),
  SurahModel(surahId: 59, surahNumber: 59, nameArabic: 'الحشر', nameEnglish: 'Al-Hashr', nameTranslation: 'The Exile', revelationType: 'Medinan', ayahCount: 24, revelationOrder: 101),
  SurahModel(surahId: 60, surahNumber: 60, nameArabic: 'الممتحنة', nameEnglish: 'Al-Mumtahanah', nameTranslation: 'She that is to be examined', revelationType: 'Medinan', ayahCount: 13, revelationOrder: 91),
  SurahModel(surahId: 61, surahNumber: 61, nameArabic: 'الصف', nameEnglish: 'As-Saff', nameTranslation: 'The Ranks', revelationType: 'Medinan', ayahCount: 14, revelationOrder: 109),
  SurahModel(surahId: 62, surahNumber: 62, nameArabic: 'الجمعة', nameEnglish: 'Al-Jumu\'ah', nameTranslation: 'The Congregation', revelationType: 'Medinan', ayahCount: 11, revelationOrder: 110),
  SurahModel(surahId: 63, surahNumber: 63, nameArabic: 'المنافقون', nameEnglish: 'Al-Munafiqun', nameTranslation: 'The Hypocrites', revelationType: 'Medinan', ayahCount: 11, revelationOrder: 104),
  SurahModel(surahId: 64, surahNumber: 64, nameArabic: 'التغابن', nameEnglish: 'At-Taghabun', nameTranslation: 'The Mutual Disillusion', revelationType: 'Medinan', ayahCount: 18, revelationOrder: 108),
  SurahModel(surahId: 65, surahNumber: 65, nameArabic: 'الطلاق', nameEnglish: 'At-Talaq', nameTranslation: 'The Divorce', revelationType: 'Medinan', ayahCount: 12, revelationOrder: 99),
  SurahModel(surahId: 66, surahNumber: 66, nameArabic: 'التحريم', nameEnglish: 'At-Tahrim', nameTranslation: 'The Prohibition', revelationType: 'Medinan', ayahCount: 12, revelationOrder: 107),
  SurahModel(surahId: 67, surahNumber: 67, nameArabic: 'الملك', nameEnglish: 'Al-Mulk', nameTranslation: 'The Sovereignty', revelationType: 'Meccan', ayahCount: 30, revelationOrder: 77),
  SurahModel(surahId: 68, surahNumber: 68, nameArabic: 'القلم', nameEnglish: 'Al-Qalam', nameTranslation: 'The Pen', revelationType: 'Meccan', ayahCount: 52, revelationOrder: 2),
  SurahModel(surahId: 69, surahNumber: 69, nameArabic: 'الحاقة', nameEnglish: 'Al-Haqqah', nameTranslation: 'The Reality', revelationType: 'Meccan', ayahCount: 52, revelationOrder: 78),
  SurahModel(surahId: 70, surahNumber: 70, nameArabic: 'المعارج', nameEnglish: 'Al-Ma\'arij', nameTranslation: 'The Ascending Stairways', revelationType: 'Meccan', ayahCount: 44, revelationOrder: 79),
  SurahModel(surahId: 71, surahNumber: 71, nameArabic: 'نوح', nameEnglish: 'Nuh', nameTranslation: 'Noah', revelationType: 'Meccan', ayahCount: 28, revelationOrder: 71),
  SurahModel(surahId: 72, surahNumber: 72, nameArabic: 'الجن', nameEnglish: 'Al-Jinn', nameTranslation: 'The Jinn', revelationType: 'Meccan', ayahCount: 28, revelationOrder: 40),
  SurahModel(surahId: 73, surahNumber: 73, nameArabic: 'المزمل', nameEnglish: 'Al-Muzzammil', nameTranslation: 'The Enshrouded One', revelationType: 'Meccan', ayahCount: 20, revelationOrder: 3),
  SurahModel(surahId: 74, surahNumber: 74, nameArabic: 'المدثر', nameEnglish: 'Al-Muddaththir', nameTranslation: 'The Cloaked One', revelationType: 'Meccan', ayahCount: 56, revelationOrder: 4),
  SurahModel(surahId: 75, surahNumber: 75, nameArabic: 'القيامة', nameEnglish: 'Al-Qiyamah', nameTranslation: 'The Resurrection', revelationType: 'Meccan', ayahCount: 40, revelationOrder: 31),
  SurahModel(surahId: 76, surahNumber: 76, nameArabic: 'الإنسان', nameEnglish: 'Al-Insan', nameTranslation: 'Man', revelationType: 'Meccan', ayahCount: 31, revelationOrder: 98),
  SurahModel(surahId: 77, surahNumber: 77, nameArabic: 'المرسلات', nameEnglish: 'Al-Mursalat', nameTranslation: 'The Emissaries', revelationType: 'Meccan', ayahCount: 50, revelationOrder: 33),
  SurahModel(surahId: 78, surahNumber: 78, nameArabic: 'النبأ', nameEnglish: 'An-Naba', nameTranslation: 'The Tidings', revelationType: 'Meccan', ayahCount: 40, revelationOrder: 80),
  SurahModel(surahId: 79, surahNumber: 79, nameArabic: 'النازعات', nameEnglish: 'An-Nazi\'at', nameTranslation: 'Those who drag forth', revelationType: 'Meccan', ayahCount: 46, revelationOrder: 81),
  SurahModel(surahId: 80, surahNumber: 80, nameArabic: 'عبس', nameEnglish: 'Abasa', nameTranslation: 'He frowned', revelationType: 'Meccan', ayahCount: 42, revelationOrder: 24),
  SurahModel(surahId: 81, surahNumber: 81, nameArabic: 'التكوير', nameEnglish: 'At-Takwir', nameTranslation: 'The Overthrowing', revelationType: 'Meccan', ayahCount: 29, revelationOrder: 7),
  SurahModel(surahId: 82, surahNumber: 82, nameArabic: 'الإنفطار', nameEnglish: 'Al-Infitar', nameTranslation: 'The Cleaving', revelationType: 'Meccan', ayahCount: 19, revelationOrder: 82),
  SurahModel(surahId: 83, surahNumber: 83, nameArabic: 'المطففين', nameEnglish: 'Al-Mutaffifin', nameTranslation: 'The Defrauding', revelationType: 'Meccan', ayahCount: 36, revelationOrder: 86),
  SurahModel(surahId: 84, surahNumber: 84, nameArabic: 'الإنشقاق', nameEnglish: 'Al-Inshiqaq', nameTranslation: 'The Splitting Open', revelationType: 'Meccan', ayahCount: 25, revelationOrder: 83),
  SurahModel(surahId: 85, surahNumber: 85, nameArabic: 'البروج', nameEnglish: 'Al-Buruj', nameTranslation: 'The Constellations', revelationType: 'Meccan', ayahCount: 22, revelationOrder: 27),
  SurahModel(surahId: 86, surahNumber: 86, nameArabic: 'الطارق', nameEnglish: 'At-Tariq', nameTranslation: 'The Morning Star', revelationType: 'Meccan', ayahCount: 17, revelationOrder: 36),
  SurahModel(surahId: 87, surahNumber: 87, nameArabic: 'الأعلى', nameEnglish: 'Al-A\'la', nameTranslation: 'The Most High', revelationType: 'Meccan', ayahCount: 19, revelationOrder: 8),
  SurahModel(surahId: 88, surahNumber: 88, nameArabic: 'الغاشية', nameEnglish: 'Al-Ghashiyah', nameTranslation: 'The Overwhelming', revelationType: 'Meccan', ayahCount: 26, revelationOrder: 68),
  SurahModel(surahId: 89, surahNumber: 89, nameArabic: 'الفجر', nameEnglish: 'Al-Fajr', nameTranslation: 'The Dawn', revelationType: 'Meccan', ayahCount: 30, revelationOrder: 10),
  SurahModel(surahId: 90, surahNumber: 90, nameArabic: 'البلد', nameEnglish: 'Al-Balad', nameTranslation: 'The City', revelationType: 'Meccan', ayahCount: 20, revelationOrder: 35),
  SurahModel(surahId: 91, surahNumber: 91, nameArabic: 'الشمس', nameEnglish: 'Ash-Shams', nameTranslation: 'The Sun', revelationType: 'Meccan', ayahCount: 15, revelationOrder: 26),
  SurahModel(surahId: 92, surahNumber: 92, nameArabic: 'الليل', nameEnglish: 'Al-Layl', nameTranslation: 'The Night', revelationType: 'Meccan', ayahCount: 21, revelationOrder: 9),
  SurahModel(surahId: 93, surahNumber: 93, nameArabic: 'الضحى', nameEnglish: 'Ad-Duha', nameTranslation: 'The Morning Hours', revelationType: 'Meccan', ayahCount: 11, revelationOrder: 11),
  SurahModel(surahId: 94, surahNumber: 94, nameArabic: 'الشرح', nameEnglish: 'Ash-Sharh', nameTranslation: 'The Relief', revelationType: 'Meccan', ayahCount: 8, revelationOrder: 12),
  SurahModel(surahId: 95, surahNumber: 95, nameArabic: 'التين', nameEnglish: 'At-Tin', nameTranslation: 'The Fig', revelationType: 'Meccan', ayahCount: 8, revelationOrder: 28),
  SurahModel(surahId: 96, surahNumber: 96, nameArabic: 'العلق', nameEnglish: 'Al-\'Alaq', nameTranslation: 'The Clot', revelationType: 'Meccan', ayahCount: 19, revelationOrder: 1),
  SurahModel(surahId: 97, surahNumber: 97, nameArabic: 'القدر', nameEnglish: 'Al-Qadr', nameTranslation: 'The Power', revelationType: 'Meccan', ayahCount: 5, revelationOrder: 25),
  SurahModel(surahId: 98, surahNumber: 98, nameArabic: 'البينة', nameEnglish: 'Al-Bayyinah', nameTranslation: 'The Clear Proof', revelationType: 'Medinan', ayahCount: 8, revelationOrder: 100),
  SurahModel(surahId: 99, surahNumber: 99, nameArabic: 'الزلزلة', nameEnglish: 'Az-Zalzalah', nameTranslation: 'The Earthquake', revelationType: 'Medinan', ayahCount: 8, revelationOrder: 93),
  SurahModel(surahId: 100, surahNumber: 100, nameArabic: 'العاديات', nameEnglish: 'Al-\'Adiyat', nameTranslation: 'The Cavalcade', revelationType: 'Meccan', ayahCount: 11, revelationOrder: 14),
  SurahModel(surahId: 101, surahNumber: 101, nameArabic: 'القارعة', nameEnglish: 'Al-Qari\'ah', nameTranslation: 'The Calamity', revelationType: 'Meccan', ayahCount: 11, revelationOrder: 30),
  SurahModel(surahId: 102, surahNumber: 102, nameArabic: 'التكاثر', nameEnglish: 'At-Takathur', nameTranslation: 'The Abundance', revelationType: 'Meccan', ayahCount: 8, revelationOrder: 6),
  SurahModel(surahId: 103, surahNumber: 103, nameArabic: 'العصر', nameEnglish: 'Al-\'Asr', nameTranslation: 'The Time', revelationType: 'Meccan', ayahCount: 3, revelationOrder: 13),
  SurahModel(surahId: 104, surahNumber: 104, nameArabic: 'الهمزة', nameEnglish: 'Al-Humazah', nameTranslation: 'The Traducer', revelationType: 'Meccan', ayahCount: 9, revelationOrder: 32),
  SurahModel(surahId: 105, surahNumber: 105, nameArabic: 'الفيل', nameEnglish: 'Al-Fil', nameTranslation: 'The Elephant', revelationType: 'Meccan', ayahCount: 5, revelationOrder: 19),
  SurahModel(surahId: 106, surahNumber: 106, nameArabic: 'قريش', nameEnglish: 'Quraysh', nameTranslation: 'Quraysh', revelationType: 'Meccan', ayahCount: 4, revelationOrder: 29),
  SurahModel(surahId: 107, surahNumber: 107, nameArabic: 'الماعون', nameEnglish: 'Al-Ma\'un', nameTranslation: 'The Small Kindnesses', revelationType: 'Meccan', ayahCount: 7, revelationOrder: 17),
  SurahModel(surahId: 108, surahNumber: 108, nameArabic: 'الكوثر', nameEnglish: 'Al-Kawthar', nameTranslation: 'The Abundance', revelationType: 'Meccan', ayahCount: 3, revelationOrder: 15),
  SurahModel(surahId: 109, surahNumber: 109, nameArabic: 'الكافرون', nameEnglish: 'Al-Kafirun', nameTranslation: 'The Disbelievers', revelationType: 'Meccan', ayahCount: 6, revelationOrder: 18),
  SurahModel(surahId: 110, surahNumber: 110, nameArabic: 'النصر', nameEnglish: 'An-Nasr', nameTranslation: 'The Divine Support', revelationType: 'Medinan', ayahCount: 3, revelationOrder: 114),
  SurahModel(surahId: 111, surahNumber: 111, nameArabic: 'المسد', nameEnglish: 'Al-Masad', nameTranslation: 'The Palm Fiber', revelationType: 'Meccan', ayahCount: 5, revelationOrder: 21),
  SurahModel(surahId: 112, surahNumber: 112, nameArabic: 'الإخلاص', nameEnglish: 'Al-Ikhlas', nameTranslation: 'The Sincerity', revelationType: 'Meccan', ayahCount: 4, revelationOrder: 22),
  SurahModel(surahId: 113, surahNumber: 113, nameArabic: 'الفلق', nameEnglish: 'Al-Falaq', nameTranslation: 'The Daybreak', revelationType: 'Meccan', ayahCount: 5, revelationOrder: 20),
  SurahModel(surahId: 114, surahNumber: 114, nameArabic: 'الناس', nameEnglish: 'An-Nas', nameTranslation: 'Mankind', revelationType: 'Meccan', ayahCount: 6, revelationOrder: 21),
];
