import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:haptic_feedback/haptic_feedback.dart';
import 'package:share_plus/share_plus.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/models/word_model.dart';
import '../../../data/models/surah_model.dart';
import '../../../data/services/local_storage_service.dart';
import '../../../data/services/audio_service.dart';
import '../widgets/ayah_widget.dart';
import '../widgets/word_bottom_sheet.dart';
import '../widgets/grammar_legend.dart';

/// S5: Quran Reader (flagship) — ayah-by-ayah vertical scroll, words as
/// individual tap targets, color-coded per pos_group, toggleable density,
/// grammar colors ON/OFF and tajweed colors ON/OFF (mutually exclusive),
/// word tap -> bottom sheet, ayah action row, sticky header.
class QuranReaderPage extends ConsumerStatefulWidget {
  final int surahNumber;
  final String surahName;

  const QuranReaderPage({
    super.key,
    required this.surahNumber,
    required this.surahName,
  });

  @override
  ConsumerState<QuranReaderPage> createState() => _QuranReaderPageState();
}

class _QuranReaderPageState extends ConsumerState<QuranReaderPage> {
  // Settings state
  bool _grammarColorsEnabled = true;
  bool _tajweedColorsEnabled = false;
  int _densityLevel = 1; // 0=Arabic only, 1=+translit, 2=+word meaning, 3=+full translation
  double _arabicFontSize = AppConstants.arabicFontDefaultSize;
  String _selectedLanguage = 'en';

  // Audio
  final AudioService _audioService = AudioService();
  int? _playingAyahIndex;
  double _playbackSpeed = AppConstants.defaultPlaybackSpeed;

  // Sample ayah data for demonstration
  late final List<AyahModel> _ayahs;

  @override
  void initState() {
    super.initState();
    _loadSettings();
    _ayahs = _generateSampleAyahs(widget.surahNumber);
  }

  Future<void> _loadSettings() async {
    final storage = LocalStorageService();
    await storage.ensureInitialized();
    final grammar = await storage.getGrammarColorsEnabled();
    final tajweed = await storage.getTajweedColorsEnabled();
    final density = await storage.getDensityLevel();
    final lang = await storage.getSelectedLanguage();

    if (mounted) {
      setState(() {
        _grammarColorsEnabled = grammar;
        _tajweedColorsEnabled = tajweed;
        _densityLevel = density;
        _selectedLanguage = lang ?? 'en';
      });
    }
  }

  Future<void> _toggleGrammarColors() async {
    await Haptics.selection();
    setState(() {
      _grammarColorsEnabled = !_grammarColorsEnabled;
      if (_grammarColorsEnabled) {
        _tajweedColorsEnabled = false; // Mutually exclusive
      }
    });
    final storage = LocalStorageService();
    await storage.setGrammarColorsEnabled(_grammarColorsEnabled);
    await storage.setTajweedColorsEnabled(_tajweedColorsEnabled);
  }

  Future<void> _toggleTajweedColors() async {
    await Haptics.selection();
    setState(() {
      _tajweedColorsEnabled = !_tajweedColorsEnabled;
      if (_tajweedColorsEnabled) {
        _grammarColorsEnabled = false; // Mutually exclusive
      }
    });
    final storage = LocalStorageService();
    await storage.setTajweedColorsEnabled(_tajweedColorsEnabled);
    await storage.setGrammarColorsEnabled(_grammarColorsEnabled);
  }

  void _cycleDensity() async {
    await Haptics.selection();
    setState(() {
      _densityLevel = (_densityLevel + 1) % 4;
    });
    final storage = LocalStorageService();
    await storage.setDensityLevel(_densityLevel);
  }

  void _onWordTapped(WordModel word) {
    Haptics.impact();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => WordBottomSheet(
        word: word,
        languageCode: _selectedLanguage,
        audioService: _audioService,
      ),
    );
  }

  Future<void> _playAyahAudio(int index) async {
    await Haptics.selection();
    final ayah = _ayahs[index];

    if (_playingAyahIndex == index && _audioService.isPlaying) {
      await _audioService.pause();
      setState(() => _playingAyahIndex = null);
      return;
    }

    setState(() => _playingAyahIndex = index);

    try {
      if (ayah.audioUrl != null) {
        await _audioService.playUrl(ayah.audioUrl!);
      } else {
        // Use constructed URL
        await _audioService.playAyah(
          surahNumber: ayah.surahNumber,
          ayahNumber: ayah.ayahNumber,
        );
      }
    } catch (e) {
      // Handle error silently — audio may not be available in demo
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Audio not available: $e'),
            duration: const Duration(seconds: 2),
          ),
        );
      }
    }

    setState(() => _playingAyahIndex = null);
  }

  void _showSpeedSelector() {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Playback Speed',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              children: AppConstants.supportedPlaybackSpeeds.map((speed) {
                final isSelected = speed == _playbackSpeed;
                return ChoiceChip(
                  label: Text('${speed}x'),
                  selected: isSelected,
                  onSelected: (_) {
                    setState(() => _playbackSpeed = speed);
                    _audioService.setSpeed(speed);
                    Navigator.pop(context);
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  void _shareAyah(AyahModel ayah) {
    final text = '${ayah.ayahText}\n\n'
        '${ayah.translationFor(_selectedLanguage) ?? ""}\n\n'
        'Surah ${widget.surahName} ${ayah.reference}';
    Share.share(text);
  }

  @override
  void dispose() {
    _audioService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // ─── Sticky Header ────────────────────────────────────────
            _buildStickyHeader(theme),

            // ─── Settings Bar ─────────────────────────────────────────
            _buildSettingsBar(theme),

            // ─── Ayah List ────────────────────────────────────────────
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                itemCount: _ayahs.length,
                itemBuilder: (context, index) {
                  final ayah = _ayahs[index];
                  final isPlaying = _playingAyahIndex == index;

                  return AyahWidget(
                    ayah: ayah,
                    languageCode: _selectedLanguage,
                    arabicFontSize: _arabicFontSize,
                    densityLevel: _densityLevel,
                    grammarColorsEnabled: _grammarColorsEnabled,
                    tajweedColorsEnabled: _tajweedColorsEnabled,
                    isPlaying: isPlaying,
                    onWordTapped: _onWordTapped,
                    onPlayTapped: () => _playAyahAudio(index),
                    onReciteTapped: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => RecitationPageRoute(
                            surahNumber: ayah.surahNumber,
                            ayahNumber: ayah.ayahNumber,
                          ),
                        ),
                      );
                    },
                    onContextStoryTapped: () => _showContextStory(ayah),
                    onShareTapped: () => _shareAyah(ayah),
                    onSpeedTapped: _showSpeedSelector,
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStickyHeader(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(
          bottom: BorderSide(
            color: theme.colorScheme.outline.withValues(alpha: 0.15),
          ),
        ),
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back_rounded),
            onPressed: () => Navigator.of(context).pop(),
          ),
          Expanded(
            child: Column(
              children: [
                Directionality(
                  textDirection: TextDirection.rtl,
                  child: Text(
                    widget.surahName,
                    style: AppTheme.arabicTextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Text(
                  'Surah ${widget.surahNumber}',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                  ),
                ),
              ],
            ),
          ),
          // Font size controls
          IconButton(
            icon: const Icon(Icons.text_decrease_rounded, size: 20),
            onPressed: () {
              setState(() {
                _arabicFontSize = (_arabicFontSize - 2).clamp(
                  AppConstants.arabicFontMinSize,
                  AppConstants.arabicFontMaxSize,
                );
              });
            },
          ),
          IconButton(
            icon: const Icon(Icons.text_increase_rounded, size: 20),
            onPressed: () {
              setState(() {
                _arabicFontSize = (_arabicFontSize + 2).clamp(
                  AppConstants.arabicFontMinSize,
                  AppConstants.arabicFontMaxSize,
                );
              });
            },
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsBar(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(
          bottom: BorderSide(
            color: theme.colorScheme.outline.withValues(alpha: 0.1),
          ),
        ),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            // Density toggle
            _SettingChip(
              icon: Icons.layers_rounded,
              label: _densityLabel(_densityLevel),
              onTap: _cycleDensity,
            ),
            const SizedBox(width: 8),
            // Grammar colors toggle
            _SettingChip(
              icon: Icons.palette_rounded,
              label: 'Grammar',
              isActive: _grammarColorsEnabled,
              activeColor: theme.colorScheme.primary,
              onTap: _toggleGrammarColors,
            ),
            const SizedBox(width: 8),
            // Tajweed colors toggle
            _SettingChip(
              icon: Icons.colorize_rounded,
              label: 'Tajweed',
              isActive: _tajweedColorsEnabled,
              activeColor: Colors.purple,
              onTap: _toggleTajweedColors,
            ),
            const SizedBox(width: 8),
            // Legend
            _SettingChip(
              icon: Icons.info_outline_rounded,
              label: 'Legend',
              onTap: () => _showLegend(theme),
            ),
          ],
        ),
      ),
    );
  }

  String _densityLabel(int level) {
    switch (level) {
      case 0:
        return 'Arabic';
      case 1:
        return '+ Translit';
      case 2:
        return '+ Meaning';
      case 3:
        return '+ Translation';
      default:
        return 'Arabic';
    }
  }

  void _showLegend(ThemeData theme) {
    showModalBottomSheet(
      context: context,
      builder: (context) => const GrammarLegend(),
    );
  }

  void _showContextStory(AyahModel ayah) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.3),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              Text(
                'Context & Story',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 16),
              Expanded(
                child: ListView(
                  controller: scrollController,
                  children: [
                    Directionality(
                      textDirection: TextDirection.rtl,
                      child: Text(
                        ayah.ayahText,
                        style: AppTheme.arabicTextStyle(fontSize: 24),
                        textAlign: TextAlign.justify,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      ayah.contextStory ??
                          ayah.translationFor(_selectedLanguage) ??
                          'Context story not available for this ayah.',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(height: 1.6),
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
}

/// A toggle chip in the settings bar.
class _SettingChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isActive;
  final Color? activeColor;
  final VoidCallback onTap;

  const _SettingChip({
    required this.icon,
    required this.label,
    this.isActive = false,
    this.activeColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = isActive ? (activeColor ?? theme.colorScheme.primary) : null;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: isActive
                ? color!.withValues(alpha: 0.1)
                : theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isActive
                  ? color!.withValues(alpha: 0.3)
                  : theme.colorScheme.outline.withValues(alpha: 0.2),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 16, color: color ?? theme.colorScheme.onSurface.withValues(alpha: 0.6)),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: color ?? theme.colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Placeholder route for recitation from Quran reader.
/// In production, this would navigate to the RecitationPage with ayah context.
class RecitationPageRoute extends StatelessWidget {
  final int surahNumber;
  final int ayahNumber;

  const RecitationPageRoute({
    super.key,
    required this.surahNumber,
    required this.ayahNumber,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Recite')),
      body: Center(
        child: Text('Recitation for $surahNumber:$ayahNumber'),
      ),
    );
  }
}

// ─── Sample Data Generation ───────────────────────────────────────────────

List<AyahModel> _generateSampleAyahs(int surahNumber) {
  if (surahNumber == 1) {
    return [
      AyahModel(
        ayahId: 1,
        surahNumber: 1,
        ayahNumber: 1,
        ayahText: 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ',
        translationEn: 'In the name of Allah, the Entirely Merciful, the Especially Merciful.',
        translationUr: 'اللہ کے نام سے جو نہایت مہربان رحم والا ہے',
        transliteration: 'bismi llāhi r-raḥmāni r-raḥīmi',
        isBismillah: true,
        words: [
          WordModel(wordId: 1, surahNumber: 1, ayahNumber: 1, wordNumber: 1, text: 'بِسْمِ', transliteration: 'bismi', translationEn: 'In the name', posGroup: 'harf_jarr', rootArabic: 'سم'),
          WordModel(wordId: 2, surahNumber: 1, ayahNumber: 1, wordNumber: 2, text: 'ٱللَّهِ', transliteration: 'Allāhi', translationEn: 'of Allah', posGroup: 'ism', rootArabic: 'اله'),
          WordModel(wordId: 3, surahNumber: 1, ayahNumber: 1, wordNumber: 3, text: 'ٱلرَّحْمَٰنِ', transliteration: 'ar-raḥmāni', translationEn: 'the Most Gracious', posGroup: 'ism', rootArabic: 'رحم'),
          WordModel(wordId: 4, surahNumber: 1, ayahNumber: 1, wordNumber: 4, text: 'ٱلرَّحِيمِ', transliteration: 'ar-raḥīmi', translationEn: 'the Most Merciful', posGroup: 'ism', rootArabic: 'رحم'),
        ],
      ),
      AyahModel(
        ayahId: 2,
        surahNumber: 1,
        ayahNumber: 2,
        ayahText: 'ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ',
        translationEn: 'All praise is due to Allah, Lord of the worlds.',
        translationUr: 'تمام تعریفیں اللہ ہی کے لیے ہیں جو تمام جہانوں کا پروردگار ہے',
        transliteration: 'al-ḥamdu lillāhi rabbi l-ʿālamīna',
        words: [
          WordModel(wordId: 5, surahNumber: 1, ayahNumber: 2, wordNumber: 1, text: 'ٱلْحَمْدُ', transliteration: 'al-ḥamdu', translationEn: 'All praise', posGroup: 'ism', rootArabic: 'حمد'),
          WordModel(wordId: 6, surahNumber: 1, ayahNumber: 2, wordNumber: 2, text: 'لِلَّهِ', transliteration: 'lillāhi', translationEn: 'is for Allah', posGroup: 'harf_jarr', rootArabic: 'اله'),
          WordModel(wordId: 7, surahNumber: 1, ayahNumber: 2, wordNumber: 3, text: 'رَبِّ', transliteration: 'rabbi', translationEn: 'Lord', posGroup: 'ism', rootArabic: 'ربب'),
          WordModel(wordId: 8, surahNumber: 1, ayahNumber: 2, wordNumber: 4, text: 'ٱلْعَٰلَمِينَ', transliteration: 'al-ʿālamīna', translationEn: 'of the worlds', posGroup: 'ism', rootArabic: 'علم'),
        ],
      ),
      AyahModel(
        ayahId: 3,
        surahNumber: 1,
        ayahNumber: 3,
        ayahText: 'ٱلرَّحْمَٰنِ ٱلرَّحِيمِ',
        translationEn: 'The Entirely Merciful, the Especially Merciful.',
        translationUr: 'بہت مہربان نہایت رحم والا',
        transliteration: 'ar-raḥmāni r-raḥīmi',
        words: [
          WordModel(wordId: 9, surahNumber: 1, ayahNumber: 3, wordNumber: 1, text: 'ٱلرَّحْمَٰنِ', transliteration: 'ar-raḥmāni', translationEn: 'the Most Gracious', posGroup: 'ism', rootArabic: 'رحم'),
          WordModel(wordId: 10, surahNumber: 1, ayahNumber: 3, wordNumber: 2, text: 'ٱلرَّحِيمِ', transliteration: 'ar-raḥīmi', translationEn: 'the Most Merciful', posGroup: 'ism', rootArabic: 'رحم'),
        ],
      ),
      AyahModel(
        ayahId: 4,
        surahNumber: 1,
        ayahNumber: 4,
        ayahText: 'مَٰلِكِ يَوْمِ ٱلدِّينِ',
        translationEn: 'Sovereign of the Day of Recompense.',
        translationUr: 'روز جزا کا مالک',
        transliteration: 'māliki yawmi d-dīni',
        words: [
          WordModel(wordId: 11, surahNumber: 1, ayahNumber: 4, wordNumber: 1, text: 'مَٰلِكِ', transliteration: 'māliki', translationEn: 'Master/King', posGroup: 'ism', rootArabic: 'ملك'),
          WordModel(wordId: 12, surahNumber: 1, ayahNumber: 4, wordNumber: 2, text: 'يَوْمِ', transliteration: 'yawmi', translationEn: 'of the Day', posGroup: 'ism', rootArabic: 'يوم'),
          WordModel(wordId: 13, surahNumber: 1, ayahNumber: 4, wordNumber: 3, text: 'ٱلدِّينِ', transliteration: 'ad-dīni', translationEn: 'of Judgment/Religion', posGroup: 'ism', rootArabic: 'دين'),
        ],
      ),
      AyahModel(
        ayahId: 5,
        surahNumber: 1,
        ayahNumber: 5,
        ayahText: 'إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ',
        translationEn: 'It is You we worship and You we ask for help.',
        translationUr: 'ہم تیری ہی عبادت کرتے ہیں اور تیری ہی مدد چاہتے ہیں',
        transliteration: 'iyyāka naʿbudu wa-iyyāka nastaʿīnu',
        words: [
          WordModel(wordId: 14, surahNumber: 1, ayahNumber: 5, wordNumber: 1, text: 'إِيَّاكَ', transliteration: 'iyyāka', translationEn: 'You (alone)', posGroup: 'ism', rootArabic: 'اي'),
          WordModel(wordId: 15, surahNumber: 1, ayahNumber: 5, wordNumber: 2, text: 'نَعْبُدُ', transliteration: 'naʿbudu', translationEn: 'we worship', posGroup: 'fiil_mudari', rootArabic: 'عبد'),
          WordModel(wordId: 16, surahNumber: 1, ayahNumber: 5, wordNumber: 3, text: 'وَ', transliteration: 'wa', translationEn: 'and', posGroup: 'harf', rootArabic: null),
          WordModel(wordId: 17, surahNumber: 1, ayahNumber: 5, wordNumber: 4, text: 'إِيَّاكَ', transliteration: 'iyyāka', translationEn: 'You (alone)', posGroup: 'ism', rootArabic: 'اي'),
          WordModel(wordId: 18, surahNumber: 1, ayahNumber: 5, wordNumber: 5, text: 'نَسْتَعِينُ', transliteration: 'nastaʿīnu', translationEn: 'we seek help', posGroup: 'fiil_mudari', rootArabic: 'عون'),
        ],
      ),
    ];
  }

  // Default: generate placeholder ayahs for other surahs
  return [
    AyahModel(
      ayahId: surahNumber * 1000 + 1,
      surahNumber: surahNumber,
      ayahNumber: 1,
      ayahText: 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ',
      translationEn: 'In the name of Allah, the Entirely Merciful, the Especially Merciful.',
      transliteration: 'bismi llāhi r-raḥmāni r-raḥīmi',
      isBismillah: true,
      words: [
        WordModel(wordId: 1, surahNumber: surahNumber, ayahNumber: 1, wordNumber: 1, text: 'بِسْمِ', transliteration: 'bismi', translationEn: 'In the name', posGroup: 'harf_jarr', rootArabic: 'سم'),
        WordModel(wordId: 2, surahNumber: surahNumber, ayahNumber: 1, wordNumber: 2, text: 'ٱللَّهِ', transliteration: 'Allāhi', translationEn: 'of Allah', posGroup: 'ism', rootArabic: 'اله'),
        WordModel(wordId: 3, surahNumber: surahNumber, ayahNumber: 1, wordNumber: 3, text: 'ٱلرَّحْمَٰنِ', transliteration: 'ar-raḥmāni', translationEn: 'the Most Gracious', posGroup: 'ism', rootArabic: 'رحم'),
        WordModel(wordId: 4, surahNumber: surahNumber, ayahNumber: 1, wordNumber: 4, text: 'ٱلرَّحِيمِ', transliteration: 'ar-raḥīmi', translationEn: 'the Most Merciful', posGroup: 'ism', rootArabic: 'رحم'),
      ],
    ),
  ];
}
