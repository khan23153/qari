import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../data/models/recitation_model.dart';
import '../../../../data/models/recitation_stream_event.dart';
import '../../../../data/models/word_model.dart';
import '../../../../data/repositories/corpus_repository.dart';
import '../../../../data/repositories/local_corpus_repository.dart';
import '../../../../data/services/audio_service.dart';
import '../../../../data/services/streaming_recitation_service.dart';
import '../widgets/memorization_ayah_view.dart';
import '../widgets/mic_visualizer.dart';
import '../widgets/recitation_results.dart';
import '../widgets/word_comparison_sheet.dart';

/// UI phases for the live (real-time) recitation experience.
enum LiveRecitationUiState { setup, live, results, error }

/// Upgraded AI Recitation section — real-time voice tracking + Memorization
/// (Hifz) Mode, replicating Tarteel-style live feedback.
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

  int _surah = 1;
  int _ayah = 1;
  int _ayahCount = 7;
  List<String> _words = const [];
  final Map<int, LiveWordStatus> _statuses = {};

  final List<double> _levels = [];
  RecitationResult? _result;
  String? _errorMessage;

  int _elapsedSeconds = 0;
  Timer? _elapsedTimer;

  StreamSubscription<RecitationStreamEvent>? _eventSub;
  StreamSubscription<double>? _ampSub;
  StreamSubscription<LiveConnectionState>? _connSub;

  @override
  void initState() {
    super.initState();
    if (widget.surahNumber != null) {
      _surah = widget.surahNumber!;
      _ayah = widget.ayahNumber ?? 1;
    }
    _loadAyah();

    _eventSub = _service.events.listen(_onEvent);
    _ampSub = _service.amplitude.listen(_onAmplitude);
    _connSub = _service.connectionState.listen(_onConnectionState);
  }

  @override
  void dispose() {
    _elapsedTimer?.cancel();
    _eventSub?.cancel();
    _ampSub?.cancel();
    _connSub?.cancel();
    _service.dispose();
    _audioService.dispose();
    super.dispose();
  }

  // ─── Data loading ─────────────────────────────────────────────────────────

  Future<void> _loadAyah() async {
    try {
      final ayahs = await LocalCorpusRepository().getAyahs(_surah);
      _ayahCount = ayahs.isNotEmpty ? ayahs.length : _ayahCount;
      AyahModel? match;
      for (final a in ayahs) {
        if (a.ayahNumber == _ayah) {
          match = a;
          break;
        }
      }
      if (match != null && mounted) {
        setState(() {
          _words = match!.words.map((w) => w.text).toList();
          _statuses.clear();
        });
      }
    } catch (e) {
      debugPrint('LiveRecitation: could not load ayah text: $e');
    }
  }

  // ─── Streaming event handlers ───────────────────────────────────────────

  void _onEvent(RecitationStreamEvent event) {
    if (!mounted) return;
    switch (event.type) {
      case RecitationStreamEventType.ready:
        // Prefer the backend's reference words so indices stay in sync; fall
        // back to the locally-loaded ayah words if the server sent none.
        if (event.words.isNotEmpty) {
          setState(() {
            _words = event.words.map((w) => w.text).toList();
            _statuses.clear();
          });
        }
        break;
      case RecitationStreamEventType.word:
        final idx = event.wordIndex;
        if (idx != null) {
          if (event.status == LiveWordStatus.error ||
              event.status == LiveWordStatus.skipped) {
            Haptics.vibrate(HapticsType.warning);
          }
          setState(() => _statuses[idx] = event.status);
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

  void _onAmplitude(double level) {
    if (!mounted) return;
    setState(() {
      _levels.add(level);
      if (_levels.length > 240) _levels.removeAt(0);
    });
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

  // ─── Session control ──────────────────────────────────────────────────────

  Future<void> _start() async {
    await Haptics.vibrate(HapticsType.medium);
    setState(() {
      _ui = LiveRecitationUiState.live;
      _statuses.clear();
      _levels.clear();
      _elapsedSeconds = 0;
      _errorMessage = null;
      _result = null;
    });

    _elapsedTimer?.cancel();
    // Count-up only — NO auto-stop. The session stays active indefinitely for
    // hands-free recitation until the user manually taps Stop.
    _elapsedTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _elapsedSeconds++);
    });

    try {
      await _service.start(
        surahNumber: _surah,
        ayahNumber: _ayah,
        memorizationMode: _memorizationMode,
      );
    } on MicPermissionDeniedException {
      _elapsedTimer?.cancel();
      setState(() {
        _ui = LiveRecitationUiState.error;
        _errorMessage =
            'Microphone access denied. Enable it in Settings to use live recitation.';
      });
    } catch (e) {
      _elapsedTimer?.cancel();
      setState(() {
        _ui = LiveRecitationUiState.error;
        _errorMessage = 'Could not start the live session: $e';
      });
    }
  }

  Future<void> _stop() async {
    await Haptics.vibrate(HapticsType.selection);
    _elapsedTimer?.cancel();
    final ev = await _service.stop();
    if (_ui == LiveRecitationUiState.results) return; // already handled via stream
    _finishWith(ev?.result);
  }

  void _finishWith(RecitationResult? result) {
    _elapsedTimer?.cancel();
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
      final st = _statuses[i] ?? LiveWordStatus.pending;
      final correct = st == LiveWordStatus.matched;
      if (correct) matched++;
      verdicts.add(WordVerdict(
        word: _words[i],
        wordIndex: i,
        isCorrect: correct,
        expectedText: _words[i],
        errorType: correct
            ? null
            : (st == LiveWordStatus.pending ? 'skipped' : st.name),
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
    _elapsedTimer?.cancel();
    await _service.cancel();
    if (mounted) setState(() => _ui = LiveRecitationUiState.setup);
  }

  void _reset() {
    setState(() {
      _ui = LiveRecitationUiState.setup;
      _result = null;
      _statuses.clear();
      _levels.clear();
      _errorMessage = null;
      _elapsedSeconds = 0;
    });
  }

  Future<void> _playReference() async {
    try {
      String? url;
      try {
        final ayah = await CorpusRepository().getAyah(_surah, _ayah);
        url = ayah.audioUrl;
      } catch (_) {}
      if (url != null && url.isNotEmpty) {
        try {
          await _audioService.playUrl(url);
          return;
        } catch (_) {}
      }
      await _audioService.playAyah(surahNumber: _surah, ayahNumber: _ayah);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not play reference audio: $e')),
        );
      }
    }
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

  int get _activeIndex {
    for (var i = 0; i < _words.length; i++) {
      if (!(_statuses[i]?.isResolved ?? false)) return i;
    }
    return -1;
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
                levels: _levels,
                active: _service.isActive,
                color: theme.colorScheme.primary,
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(ThemeData theme) {
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
                  style: theme.textTheme.titleLarge
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
                Text(
                  'Live · Surah $_surah:$_ayah',
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
          // Target selector
          Align(
            child: ActionChip(
              avatar: const Icon(Icons.menu_book_rounded, size: 18),
              label: Text('Surah $_surah · Ayah $_ayah'),
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
                        style: theme.textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w600),
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
              color: theme.colorScheme.surfaceContainerHighest
                  .withValues(alpha: 0.25),
              borderRadius: BorderRadius.circular(20),
            ),
            child: _words.isEmpty
                ? Text('Loading ayah…',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodyMedium)
                : MemorizationAyahView(
                    words: _words,
                    statuses: _statuses,
                    memorizationMode: _memorizationMode,
                  ),
          ),
          const SizedBox(height: 28),

          FilledButton.tonalIcon(
            onPressed: _playReference,
            icon: const Icon(Icons.headphones_rounded),
            label: const Text('Listen First'),
            style: FilledButton.styleFrom(
              minimumSize: const Size.fromHeight(52),
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _start,
            icon: const Icon(Icons.mic_rounded, size: 26),
            label: const Text('Start Reciting', style: TextStyle(fontSize: 16)),
            style: FilledButton.styleFrom(
              minimumSize: const Size.fromHeight(56),
            ),
          ),
        ],
      ),
    );
  }

  // ─── Live ───────────────────────────────────────────────────────────────
  Widget _buildLive(ThemeData theme) {
    final connecting = _service.state == LiveConnectionState.connecting;
    return Column(
      children: [
        // Status bar
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (connecting) ...[
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
                  'LIVE · ${_formatDuration(_elapsedSeconds)}',
                  style: theme.textTheme.labelLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                    fontFeatures: const [FontFeature.tabularFigures()],
                  ),
                ),
              ],
              const SizedBox(width: 12),
              _ModePill(memorization: _memorizationMode, theme: theme),
            ],
          ),
        ),

        // Ayah with live word-by-word feedback
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: MemorizationAyahView(
              words: _words,
              statuses: _statuses,
              memorizationMode: _memorizationMode,
              fontSize: 34,
              activeIndex: _activeIndex,
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
                  label: const Text('Stop & Review',
                      style: TextStyle(fontSize: 16)),
                  style: FilledButton.styleFrom(
                    minimumSize: const Size.fromHeight(56),
                  ),
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
                size: 64,
                color: theme.colorScheme.error.withValues(alpha: 0.6)),
            const SizedBox(height: 20),
            Text(
              'Something went wrong',
              style: theme.textTheme.headlineSmall
                  ?.copyWith(fontWeight: FontWeight.w700),
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
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(52),
              ),
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
    int tempAyah = _ayah;
    int tempCount = _ayahCount;

    Future<void> refreshCount(StateSetter setSheet, int surah) async {
      try {
        final ayahs = await LocalCorpusRepository().getAyahs(surah);
        if (ayahs.isNotEmpty) {
          setSheet(() {
            tempCount = ayahs.length;
            if (tempAyah > tempCount) tempAyah = 1;
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
                  Text('Choose what to recite',
                      style: theme.textTheme.titleLarge
                          ?.copyWith(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: _NumberDropdown(
                          label: 'Surah',
                          value: tempSurah,
                          count: 114,
                          onChanged: (v) {
                            setSheet(() => tempSurah = v);
                            refreshCount(setSheet, v);
                          },
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: _NumberDropdown(
                          label: 'Ayah',
                          value: tempAyah,
                          count: tempCount,
                          onChanged: (v) => setSheet(() => tempAyah = v),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  FilledButton(
                    onPressed: () {
                      Navigator.pop(context);
                      setState(() {
                        _surah = tempSurah;
                        _ayah = tempAyah;
                        _ayahCount = tempCount;
                        _words = const [];
                        _statuses.clear();
                      });
                      _loadAyah();
                    },
                    style: FilledButton.styleFrom(
                      minimumSize: const Size.fromHeight(52),
                    ),
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
          '• Memorization Mode hides the ayah and reveals each word only after '
          'you recite it correctly.',
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

  String _formatDuration(int seconds) {
    final m = (seconds ~/ 60).toString().padLeft(2, '0');
    final s = (seconds % 60).toString().padLeft(2, '0');
    return '$m:$s';
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
            memorization
                ? Icons.visibility_off_rounded
                : Icons.track_changes_rounded,
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
