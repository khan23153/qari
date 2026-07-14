import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../data/models/recitation_model.dart';
import '../../../../data/models/recitation_stream_event.dart';
import '../../../../data/models/word_model.dart';
import '../../../../data/repositories/local_corpus_repository.dart';
import '../../../../data/services/audio_service.dart';
import '../../../../data/services/streaming_recitation_service.dart';
import '../widgets/memorization_ayah_view.dart';
import '../widgets/mic_visualizer.dart';
import '../widgets/recitation_results.dart';
import '../widgets/word_comparison_sheet.dart';

/// UI phases for the live (real-time) recitation experience.
enum LiveRecitationUiState { setup, live, results, error }

/// What block of Quran the user is reciting continuously.
enum RecitationScope { page, surah }

/// Upgraded AI Recitation section — real-time voice tracking + Memorization
/// (Hifz) Mode, replicating Tarteel-style live feedback. Supports continuous
/// recitation of a full Mushaf **page** or a full **surah**: every ayah's words
/// are combined into one continuous array so the ML backend tracks the user
/// seamlessly across ayah boundaries (no stop/start between ayahs).
///
/// This is a **separate** page from the legacy [RecitationPage] used by the
/// Quran reader's per-ayah "Recite" button, which is intentionally left
/// untouched. Only the home "AI Recitation" entry routes here.
class LiveRecitationPage extends StatefulWidget {
  final int? surahNumber;
  final int? ayahNumber;

  const LiveRecitationPage({super.key, this.surahNumber, this.ayahNumber});

  @override
  State<LiveRecitationPage> createState() => _LiveRecitationPageState();
}

class _LiveRecitationPageState extends State<LiveRecitationPage> {
  final StreamingRecitationService _service = StreamingRecitationService();
  final AudioService _audioService = AudioService();

  LiveRecitationUiState _ui = LiveRecitationUiState.setup;
  bool _memorizationMode = true;

  RecitationScope _scope = RecitationScope.page;
  int _surah = 1;
  int _ayah = 1;
  int _page = 1;
  int _ayahCount = 7;

  /// Flat word array across all ayahs being recited (the whole page/surah).
  List<String> _words = const [];

  /// Ordered (surah, ayah) references for the loaded block — sent to the
  /// backend so it can resolve the concatenated reference list.
  List<(int, int)> _ayahRefs = const [];

  /// 0-based index of the LAST word of each ayah in [_words] (for markers).
  List<int> _ayahBoundaries = const [];

  /// Ayah-number labels aligned 1:1 with [_ayahBoundaries].
  List<String> _ayahLabels = const [];

  /// Per-word granular state. Each entry owns its own notifiers so a word
  /// status change rebuilds ONLY that word widget — never the whole Wrap.
  List<HifzWordState> _wordStates = const [];

  /// Index of the next word the reciter is expected to say. In Memorization
  /// Mode the placeholder dot at this index is revealed (as Arabic text) and
  /// the index is incremented whenever the backend confirms a correct word.
  int _currentWordIndex = 0;

  /// Word index currently flashing (temporarily tinted) after a mistake. -1
  /// when nothing is flashing.
  int _flashIndex = -1;
  Timer? _flashTimer;

  /// Stable keys (one per word) so we can scroll the active word to center.
  List<GlobalKey> _wordKeys = const [];

  /// Drives the auto-scroll so the active word stays in view as words wrap.
  final ScrollController _scrollController = ScrollController();

  RecitationResult? _result;
  String? _errorMessage;

  StreamSubscription<RecitationStreamEvent>? _eventSub;
  StreamSubscription<LiveConnectionState>? _connSub;

  @override
  void initState() {
    super.initState();
    if (widget.surahNumber != null) {
      _scope = RecitationScope.surah;
      _surah = widget.surahNumber!;
      _ayah = widget.ayahNumber ?? 1;
    }
    _loadScope();

    _eventSub = _service.events.listen(_onEvent);
    _connSub = _service.connectionState.listen(_onConnectionState);
  }

  @override
  void dispose() {
    _flashTimer?.cancel();
    _eventSub?.cancel();
    _connSub?.cancel();
    for (final s in _wordStates) {
      s.dispose();
    }
    _scrollController.dispose();
    _service.dispose();
    _audioService.dispose();
    super.dispose();
  }

  /// (Re)initialises the per-word tracking state and regenerates one stable
  /// [GlobalKey] per word so the live view can scroll the active word to center.
  void _resetWordTracking() {
    _flashTimer?.cancel();
    for (final s in _wordStates) {
      s.dispose();
    }
    _currentWordIndex = 0;
    _flashIndex = -1;
    _wordKeys = List.generate(_words.length, (_) => GlobalKey());
    _wordStates = List.generate(
      _words.length,
      (_) => HifzWordState(),
    );
    // The first word is the "active" (expected-next) word.
    if (_wordStates.isNotEmpty) {
      _wordStates[0].isActive.value = true;
    }
  }

  // ─── Data loading ─────────────────────────────────────────────────────────

  /// Loads the target block (a full Mushaf page or a full surah) from the
  /// bundled corpus, flattens it into a single continuous word array, and
  /// records where each ayah ends (for the end-of-ayah markers).
  Future<void> _loadScope() async {
    try {
      List<AyahModel> ayahs;
      if (_scope == RecitationScope.page) {
        ayahs = await LocalCorpusRepository().getAyahsByPage(_page);
      } else {
        ayahs = await LocalCorpusRepository().getAyahs(_surah);
      }
      if (ayahs.isEmpty) return;

      final words = <String>[];
      final refs = <(int, int)>[];
      final boundaries = <int>[];
      final labels = <String>[];

      for (final a in ayahs) {
        final ayahWords = a.words.map((w) => w.text).toList();
        words.addAll(ayahWords);
        refs.add((a.surahNumber, a.ayahNumber));
        if (ayahWords.isNotEmpty) {
          boundaries.add(words.length - 1);
          labels.add(a.ayahNumber.toString());
        }
      }

      if (mounted) {
        setState(() {
          _words = words;
          _ayahRefs = refs;
          _ayahBoundaries = boundaries;
          _ayahLabels = labels;
          _ayahCount = ayahs.length;
          _resetWordTracking();
        });
      }
    } catch (e) {
      debugPrint('LiveRecitation: could not load scope: $e');
    }
  }

  // ─── Streaming event handlers ───────────────────────────────────────────

  void _onEvent(RecitationStreamEvent event) {
    if (!mounted) return;
    switch (event.type) {
      case RecitationStreamEventType.ready:
        // Prefer the backend's reference words (with tashkeel) so indices stay
        // in sync; fall back to the locally-loaded ayah words if the server
        // sent none or the count differs.
        if (event.words.isNotEmpty && event.words.length == _words.length) {
          setState(() {
            _words = event.words.map((w) => w.text).toList();
            _resetWordTracking();
          });
        }
        break;
      case RecitationStreamEventType.word:
        final idx = event.wordIndex;
        if (idx == null || idx < 0 || idx >= _wordStates.length) return;

        final isMistake =
            event.status == LiveWordStatus.error || event.status == LiveWordStatus.skipped;
        if (isMistake) Haptics.vibrate(HapticsType.warning);

        if (_memorizationMode) {
          if (event.status == LiveWordStatus.matched) {
            // Reveal the correctly spoken word (only this cell rebuilds) and
            // advance the pointer. No page-level setState → the Wrap is intact.
            _wordStates[idx].status.value = LiveWordStatus.matched;
            _wordStates[idx].isActive.value = false;
            _advanceCurrentIndex();
            _scrollToCurrent();
          } else {
            // Incorrect word: flash the current placeholder, don't reveal it.
            _flashIndex = _currentWordIndex;
            _wordStates[_flashIndex].isFlashing.value = true;
            _scheduleFlash();
          }
        } else {
          _wordStates[idx].status.value = event.status;
          if (isMistake) {
            _flashIndex = idx;
            _wordStates[idx].isFlashing.value = true;
            _scheduleFlash();
          }
        }
        break;
      case RecitationStreamEventType.finalResult:
        _finishWith(event.result);
        break;
      case RecitationStreamEventType.error:
        setState(() {
          _ui = LiveRecitationUiState.error;
          _errorMessage = event.detail ?? 'Streaming error';
        });
        break;
      case RecitationStreamEventType.pong:
      case RecitationStreamEventType.unknown:
        break;
    }
  }

  void _onConnectionState(LiveConnectionState state) {
    if (!mounted) return;
    if (state == LiveConnectionState.error &&
        _ui == LiveRecitationUiState.live) {
      setState(() {
        _ui = LiveRecitationUiState.error;
        _errorMessage ??=
            'Lost connection to the live engine. Check your network and retry.';
      });
    }
  }

  /// Advances [_currentWordIndex] past any already-revealed leading words and
  /// marks the newly-active word so only it shows the "you are here" highlight.
  void _advanceCurrentIndex() {
    while (_currentWordIndex < _wordStates.length &&
        _wordStates[_currentWordIndex].status.value.isResolved) {
      _currentWordIndex++;
    }
    if (_currentWordIndex < _wordStates.length) {
      _wordStates[_currentWordIndex].isActive.value = true;
    }
  }

  /// Briefly highlights a mistaken word (red/amber), then clears the flash.
  void _scheduleFlash() {
    _flashTimer?.cancel();
    _flashTimer = Timer(const Duration(milliseconds: 900), () {
      if (mounted && _flashIndex >= 0 && _flashIndex < _wordStates.length) {
        _wordStates[_flashIndex].isFlashing.value = false;
      }
      _flashIndex = -1;
    });
  }

  /// Smoothly scrolls the active word to the upper third of the viewport, but
  /// ONLY when it enters the bottom 30% — so we don't fight the user's own
  /// scrolling on every word.
  void _scrollToCurrent() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (_currentWordIndex < 0 || _currentWordIndex >= _wordKeys.length) return;
      final ctx = _wordKeys[_currentWordIndex].currentContext;
      if (ctx == null) return;
      final box = ctx.findRenderObject() as RenderBox?;
      if (box == null) return;

      final position = Scrollable.of(ctx).position;
      final viewportHeight = position.viewportDimension;
      if (viewportHeight <= 0) return;

      final wordTop = box.localToGlobal(Offset.zero).dy;
      final containerBox =
          position.context.storageContext.findRenderObject() as RenderBox?;
      final containerTop = containerBox?.localToGlobal(Offset.zero).dy ?? 0.0;
      final rel = wordTop - containerTop; // word offset within the viewport

      // Blueprint: if the active word enters the bottom 30% of the viewport,
      // animate it to ~33% from the top (upper third).
      if (rel > viewportHeight * 0.70) {
        final delta = rel - viewportHeight * 0.33;
        position.animateTo(
          position.pixels + delta,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
        );
      }
    });
  }

  // ─── Session control ──────────────────────────────────────────────────────

  Future<void> _start() async {
    await Haptics.vibrate(HapticsType.medium);
    setState(() {
      _ui = LiveRecitationUiState.live;
      _resetWordTracking();
      _errorMessage = null;
      _result = null;
    });

    try {
      await _service.start(
        surahNumber: _surah,
        ayahNumber: _ayah,
        ayahFrom: _scope == RecitationScope.surah ? 1 : _ayah,
        ayahTo: _scope == RecitationScope.surah ? _ayahCount : _ayah,
        ayahRefs: _ayahRefs,
        memorizationMode: _memorizationMode,
      );
    } on MicPermissionDeniedException {
      setState(() {
        _ui = LiveRecitationUiState.error;
        _errorMessage =
            'Microphone access denied. Enable it in Settings to use live recitation.';
      });
    } catch (e) {
      setState(() {
        _ui = LiveRecitationUiState.error;
        _errorMessage = 'Could not start the live session: $e';
      });
    }
  }

  Future<void> _stop() async {
    await Haptics.vibrate(HapticsType.selection);
    final ev = await _service.stop();
    if (_ui == LiveRecitationUiState.results) return; // already handled via stream
    _finishWith(ev?.result);
  }

  void _finishWith(RecitationResult? result) {
    if (!mounted) return;
    setState(() {
      _result = result ?? _synthesizeResult();
      _ui = LiveRecitationUiState.results;
    });
  }

  /// Builds a result from the live word statuses when the backend final payload
  /// didn't arrive (e.g. connection dropped) so the user still sees feedback.
  RecitationResult _synthesizeResult() {
    final verdicts = <WordVerdict>[];
    var matched = 0;
    for (var i = 0; i < _words.length; i++) {
      final st = i < _wordStates.length
          ? _wordStates[i].status.value
          : LiveWordStatus.pending;
      final correct = st == LiveWordStatus.matched;
      if (correct) matched++;
      verdicts.add(WordVerdict(
        word: _words[i],
        wordIndex: i,
        isCorrect: correct,
        expectedText: _words[i],
        errorType: correct ? null : (st == LiveWordStatus.pending ? 'skipped' : st.name),
      ));
    }
    final acc = _words.isEmpty ? 0.0 : matched / _words.length;
    return RecitationResult(
      sessionId: 'local',
      surahNumber: _surah,
      ayahNumber: _ayah,
      overallScore: acc,
      accuracyScore: acc,
      pronunciationScore: acc,
      fluencyScore: acc,
      wordVerdicts: verdicts,
      createdAt: DateTime.now(),
      confidence: _words.isEmpty ? 0.0 : 1.0,
      feedback: 'Live session complete.',
    );
  }

  Future<void> _cancel() async {
    await _service.cancel();
    if (mounted) {
      setState(() {
        _ui = LiveRecitationUiState.setup;
        _resetWordTracking();
      });
    }
  }

  void _reset() {
    setState(() {
      _ui = LiveRecitationUiState.setup;
      _result = null;
      _errorMessage = null;
      _resetWordTracking();
    });
  }

  void _onWordTapped(WordVerdict verdict) {
    if (verdict.isCorrect) return;
    Haptics.vibrate(HapticsType.medium);
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => WordComparisonSheet(
        verdict: verdict,
        ayahWords: _words,
        audioService: _audioService,
      ),
    );
  }

  // ─── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(theme),
            Expanded(child: _buildBody(theme)),
            if (_ui == LiveRecitationUiState.live)
              MicVisualizer(
                amplitude: _service.amplitude,
                active: true,
                color: theme.colorScheme.primary,
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(ThemeData theme) {
    final subtitle = _scope == RecitationScope.page
        ? 'Live · Page $_page'
        : 'Live · Surah $_surah (full)';
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 4),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back_rounded),
            onPressed: () => Navigator.of(context).maybePop(),
          ),
          Expanded(
            child: Column(
              children: [
                Text(
                  'AI Recitation',
                  style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
                ),
                Text(
                  subtitle,
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.info_outline_rounded),
            onPressed: () => _showInfoDialog(theme),
          ),
        ],
      ),
    );
  }

  Widget _buildBody(ThemeData theme) {
    switch (_ui) {
      case LiveRecitationUiState.setup:
        return _buildSetup(theme);
      case LiveRecitationUiState.live:
        return _buildLive(theme);
      case LiveRecitationUiState.results:
        return RecitationResults(
          result: _result!,
          ayahWords: _words,
          onWordTapped: _onWordTapped,
          onRetry: _reset,
          theme: theme,
        );
      case LiveRecitationUiState.error:
        return _buildError(theme);
    }
  }

  // ─── Setup ──────────────────────────────────────────────────────────────
  Widget _buildSetup(ThemeData theme) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Scope selector (Page / Surah)
          Container(
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: theme.colorScheme.outline.withValues(alpha: 0.2),
              ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: _ScopeTab(
                    label: 'Page (Mushaf)',
                    icon: Icons.menu_book_rounded,
                    selected: _scope == RecitationScope.page,
                    onTap: () {
                      if (_scope != RecitationScope.page) {
                        setState(() {
                          _scope = RecitationScope.page;
                          _loadScope();
                        });
                      }
                    },
                    theme: theme,
                  ),
                ),
                Expanded(
                  child: _ScopeTab(
                    label: 'Full Surah',
                    icon: Icons.auto_stories_rounded,
                    selected: _scope == RecitationScope.surah,
                    onTap: () {
                      if (_scope != RecitationScope.surah) {
                        setState(() {
                          _scope = RecitationScope.surah;
                          _loadScope();
                        });
                      }
                    },
                    theme: theme,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Target selector for the chosen scope.
          if (_scope == RecitationScope.page)
            _PageStepper(theme: theme, page: _page, onChanged: (p) {
              setState(() {
                _page = p;
                _loadScope();
              });
            })
          else
            Align(
              child: ActionChip(
                avatar: const Icon(Icons.auto_stories_rounded, size: 18),
                label: Text('Surah $_surah'),
                onPressed: _openTargetPicker,
              ),
            ),
          const SizedBox(height: 20),

          // Memorization Mode toggle
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: theme.colorScheme.primary.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                Icon(Icons.visibility_off_rounded,
                    size: 22, color: theme.colorScheme.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Memorization Mode',
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        _memorizationMode
                            ? 'Words are hidden and revealed as you recite them correctly.'
                            : 'Words stay visible and highlight as you recite.',
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Switch(
                  value: _memorizationMode,
                  onChanged: (v) => setState(() => _memorizationMode = v),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Ayah preview
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.25),
              borderRadius: BorderRadius.circular(20),
            ),
            child: _words.isEmpty
                ? Text('Loading…', textAlign: TextAlign.center, style: theme.textTheme.bodyMedium)
                : MemorizationAyahView(
                    words: _words,
                    wordStates: _wordStates,
                    memorizationMode: _memorizationMode,
                    ayahBoundaries: _ayahBoundaries,
                    ayahLabels: _ayahLabels,
                  ),
          ),
          const SizedBox(height: 28),

          FilledButton.icon(
            onPressed: _start,
            icon: const Icon(Icons.mic_rounded, size: 26),
            label: const Text('Start Reciting', style: TextStyle(fontSize: 16)),
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(56)),
          ),
        ],
      ),
    );
  }

  // ─── Live ───────────────────────────────────────────────────────────────
  Widget _buildLive(ThemeData theme) {
    return Column(
      children: [
        // Status bar (self-managed LIVE timer + connecting indicator) so the
        // page never setStates on a 1s tick (which would rebuild the Wrap).
        _LiveStatusBadge(
          memorization: _memorizationMode,
          connectionState: _service.connectionState,
        ),

        // Ayah with live word-by-word feedback (whole page/surah). Per-word
        // notifiers mean a match reveal rebuilds only that one cell.
        Expanded(
          child: SingleChildScrollView(
            controller: _scrollController,
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: MemorizationAyahView(
              words: _words,
              wordStates: _wordStates,
              memorizationMode: _memorizationMode,
              fontSize: 30,
              wordKeys: _wordKeys,
              ayahBoundaries: _ayahBoundaries,
              ayahLabels: _ayahLabels,
            ),
          ),
        ),

        // Controls
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: _cancel,
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size.fromHeight(56),
                    foregroundColor: theme.colorScheme.error,
                  ),
                  child: const Text('Cancel'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: FilledButton.icon(
                  onPressed: _stop,
                  icon: const Icon(Icons.stop_rounded, size: 26),
                  label: const Text('Stop & Review', style: TextStyle(fontSize: 16)),
                  style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(56)),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ─── Error ──────────────────────────────────────────────────────────────
  Widget _buildError(ThemeData theme) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline_rounded,
                size: 64, color: theme.colorScheme.error.withValues(alpha: 0.6)),
            const SizedBox(height: 20),
            Text(
              'Something went wrong',
              style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            Text(
              _errorMessage ?? 'Please try again.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 28),
            FilledButton(
              onPressed: _reset,
              style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(52)),
              child: const Text('Try Again'),
            ),
          ],
        ),
      ),
    );
  }

  // ─── Target picker ───────────────────────────────────────────────────────
  Future<void> _openTargetPicker() async {
    int tempSurah = _surah;
    int tempCount = _ayahCount;

    Future<void> refreshCount(StateSetter setSheet, int surah) async {
      try {
        final ayahs = await LocalCorpusRepository().getAyahs(surah);
        if (ayahs.isNotEmpty) {
          setSheet(() {
            tempCount = ayahs.length;
          });
        }
      } catch (_) {}
    }

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) {
        final theme = Theme.of(context);
        return StatefulBuilder(
          builder: (context, setSheet) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: 20 + MediaQuery.of(context).viewInsets.bottom,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text('Choose a surah',
                      style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 16),
                  _NumberDropdown(
                    label: 'Surah',
                    value: tempSurah,
                    count: AppConstants.totalSurahs,
                    onChanged: (v) {
                      setSheet(() => tempSurah = v);
                      refreshCount(setSheet, v);
                    },
                  ),
                  const SizedBox(height: 24),
                  FilledButton(
                    onPressed: () {
                      Navigator.pop(context);
                      setState(() {
                        _surah = tempSurah;
                        _ayahCount = tempCount;
                        _resetWordTracking();
                      });
                      _loadScope();
                    },
                    style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(52)),
                    child: const Text('Set'),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _showInfoDialog(ThemeData theme) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Live Recitation'),
        content: const Text(
          '• Recite continuously — the mic keeps listening hands-free until you '
          'tap Stop (great while walking or driving).\n\n'
          '• Words are tracked in real time: green = correct, red = '
          'mispronounced, amber = skipped.\n\n'
          '• Memorization Mode hides the text and reveals each word only after '
          'you recite it correctly — across a full Mushaf page or surah.\n\n'
          '• Circular numbers mark where each ayah ends.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }
}

/// Live status bar: shows the LIVE timer (count-up, never auto-stops) and a
/// connecting indicator. Owns its own 1s timer + connection subscription so the
/// parent page doesn't need to [setState] every second (which would otherwise
/// rebuild the word Wrap).
class _LiveStatusBadge extends StatefulWidget {
  final bool memorization;
  final Stream<LiveConnectionState> connectionState;

  const _LiveStatusBadge({
    required this.memorization,
    required this.connectionState,
  });

  @override
  State<_LiveStatusBadge> createState() => _LiveStatusBadgeState();
}

class _LiveStatusBadgeState extends State<_LiveStatusBadge> {
  int _elapsed = 0;
  Timer? _timer;
  bool _connecting = true;
  StreamSubscription<LiveConnectionState>? _connSub;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _elapsed++);
    });
    _connSub = widget.connectionState.listen((s) {
      if (!mounted) return;
      final connecting =
          s == LiveConnectionState.connecting || s == LiveConnectionState.idle;
      if (connecting != _connecting) setState(() => _connecting = connecting);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _connSub?.cancel();
    super.dispose();
  }

  String _formatDuration(int seconds) {
    final m = (seconds ~/ 60).toString().padLeft(2, '0');
    final s = (seconds % 60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 4, 20, 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (_connecting) ...[
            const SizedBox(
              width: 14,
              height: 14,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            const SizedBox(width: 8),
            Text('Connecting…', style: theme.textTheme.labelMedium),
          ] else ...[
            Icon(Icons.circle, size: 10, color: theme.colorScheme.error)
                .animate(onComplete: (c) => c.repeat(reverse: true))
                .fadeIn(duration: 700.ms)
                .fadeOut(duration: 700.ms),
            const SizedBox(width: 8),
            Text(
              'LIVE · ${_formatDuration(_elapsed)}',
              style: theme.textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w700,
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
            ),
          ],
          const SizedBox(width: 12),
          _ModePill(memorization: widget.memorization, theme: theme),
        ],
      ),
    );
  }
}

class _ScopeTab extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;
  final ThemeData theme;

  const _ScopeTab({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    final fg = selected
        ? theme.colorScheme.onPrimary
        : theme.colorScheme.onSurface.withValues(alpha: 0.7);
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: selected ? theme.colorScheme.primary : Colors.transparent,
            borderRadius: BorderRadius.circular(11),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 18, color: fg),
              const SizedBox(width: 8),
              Text(
                label,
                style: theme.textTheme.labelMedium?.copyWith(
                  color: fg,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PageStepper extends StatelessWidget {
  final ThemeData theme;
  final int page;
  final ValueChanged<int> onChanged;

  const _PageStepper({
    required this.theme,
    required this.page,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: theme.colorScheme.outline.withValues(alpha: 0.2),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          IconButton(
            icon: const Icon(Icons.remove_circle_outline_rounded),
            onPressed: page > 1 ? () => onChanged(page - 1) : null,
          ),
          Expanded(
            child: Column(
              children: [
                Text(
                  'Mushaf Page',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                  ),
                ),
                Text(
                  '$page / ${AppConstants.totalQuranPages}',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.add_circle_outline_rounded),
            onPressed: page < AppConstants.totalQuranPages
                ? () => onChanged(page + 1)
                : null,
          ),
        ],
      ),
    );
  }
}

class _ModePill extends StatelessWidget {
  final bool memorization;
  final ThemeData theme;
  const _ModePill({required this.memorization, required this.theme});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: theme.colorScheme.primary.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            memorization ? Icons.visibility_off_rounded : Icons.track_changes_rounded,
            size: 14,
            color: theme.colorScheme.primary,
          ),
          const SizedBox(width: 4),
          Text(
            memorization ? 'Hifz' : 'Tracking',
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

class _NumberDropdown extends StatelessWidget {
  final String label;
  final int value;
  final int count;
  final ValueChanged<int> onChanged;

  const _NumberDropdown({
    required this.label,
    required this.value,
    required this.count,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final safeValue = value.clamp(1, count < 1 ? 1 : count);
    return InputDecorator(
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<int>(
          isExpanded: true,
          value: safeValue,
          items: [
            for (var i = 1; i <= (count < 1 ? 1 : count); i++)
              DropdownMenuItem(value: i, child: Text('$i')),
          ],
          onChanged: (v) {
            if (v != null) onChanged(v);
          },
        ),
      ),
    );
  }
}
