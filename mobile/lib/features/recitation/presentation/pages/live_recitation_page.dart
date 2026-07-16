import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../data/models/recitation_model.dart';
import '../../../../data/models/recitation_session_record.dart';
import '../../../../data/models/recitation_stream_event.dart';
import '../../../../data/models/word_model.dart';
import '../../../../data/repositories/local_corpus_repository.dart';
import '../../../../data/services/audio_service.dart';
import '../../../../data/services/local_storage_service.dart';
import '../../../../data/services/recitation_history_service.dart';
import '../../../../data/services/streaming_recitation_service.dart';
import '../widgets/mic_visualizer.dart';
import '../widgets/mushaf_reveal_view.dart';
import '../widgets/recitation_results.dart';
import '../widgets/word_comparison_sheet.dart';
import 'recitation_history_page.dart';
import 'verse_identifier_page.dart';

/// UI phases for the live (real-time) recitation experience.
enum LiveRecitationUiState { setup, live, finalizing, results, error }

/// What block of Quran the user is reciting continuously.
enum RecitationScope { page, surah }

/// Upgraded AI Recitation section — real-time voice tracking rendered as a
/// **Mushaf (physical-book) layout**. As the backend confirms each recited word
/// over the live WebSocket, the word is revealed on a blank canvas and flows
/// continuously right-to-left like a printed Quran, with inline ayah markers
/// between verses.
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

  RecitationScope _scope = RecitationScope.page;
  int _surah = 1;
  int _ayah = 1;
  int _page = 1;
  int _ayahCount = 7;

  /// For the Surah scope: the exact ayah range the user wants to recite.
  /// Defaults to the whole surah (1 .. _ayahCount).
  int _ayahFrom = 1;
  int _ayahTo = 7;

  /// Whether to colour tajweed rules on the revealed (correct) words, like the
  /// Surah reader. Persisted across sessions.
  bool _tajweedOn = false;

  /// Flat target word array across all ayahs being recited (the whole
  /// page/surah). Used to drive the backend reference + the results grid.
  List<String> _words = const [];

  /// Tajweed spans, aligned 1:1 with [_words], so each revealed word can be
  /// coloured per-letter by its tajweed rule.
  List<List<TajweedSpan>?> _wordTajweedSpans = const [];

  /// Ordered (surah, ayah) references for the loaded block — sent to the
  /// backend so it can resolve the concatenated reference list.
  List<(int, int)> _ayahRefs = const [];

  /// 0-based index of the LAST word of each ayah in [_words] (for markers).
  List<int> _ayahBoundaries = const [];

  /// Ayah-number labels aligned 1:1 with [_ayahBoundaries].
  List<String> _ayahLabels = const [];

  // ── Live reveal state (the "magic typing" canvas) ───────────────────────
  /// Words revealed so far from the live WebSocket. Starts COMPLETELY EMPTY
  /// (blank canvas) — no dots, no placeholders. Each confirmed word is appended
  /// here in recitation order.
  List<String> _revealedWords = const [];

  /// Per-revealed-word live status (matched / error / skipped) for tinting.
  List<LiveWordStatus> _revealedStatuses = const [];

  /// Per-revealed-word tajweed spans (aligned 1:1 with [_revealedWords]) so the
  /// live canvas can colour each letter by its rule as it appears.
  List<List<TajweedSpan>?> _revealedTajweedSpans = const [];

  /// Dedup guard: reference word indices already revealed (the backend may
  /// re-emit a status change for a word we already showed).
  final Set<int> _revealedIndices = {};

  /// Anchor key for the newest revealed word, so we can auto-scroll it.
  final GlobalKey _caretKey = GlobalKey();

  /// Drives the auto-scroll so the active word stays in the upper half of the
  /// viewport as words wrap.
  final ScrollController _scrollController = ScrollController();

  RecitationResult? _result;
  String? _errorMessage;

  /// Live diagnostics notifiers (updated by [_diagTimer] so only the small
  /// diagnostic Text rebuilds, not the whole reveal view).
  final ValueNotifier<int> _micChunksNotifier = ValueNotifier(0);
  final ValueNotifier<int> _sentBytesNotifier = ValueNotifier(0);
  /// Native recorder error captured from the recorder's state channel (e.g.
  /// "PCM reader failed to initialize"). Surfaced live so a swallowed setup
  /// failure is visible immediately, not just on the error screen.
  final ValueNotifier<String?> _micErrorNotifier = ValueNotifier(null);
  /// Android audio-focus grant result (from `audio_session`). `false` ⇒ the OS
  /// denied focus ⇒ the recorder is silently dead ⇒ "mic chunks: 0".
  final ValueNotifier<bool?> _focusNotifier = ValueNotifier(null);
  /// How many native audio frames actually reached the Dart `onData` callback.
  /// Surfaced live so we can tell "native posted frames but Dart never got them"
  /// (EventChannel delivery break) from "Dart got them but processing failed".
  final ValueNotifier<int> _audioOnDataNotifier = ValueNotifier(0);
  /// True once we've been "listening" for a couple seconds but the recorder has
  /// produced zero chunks — i.e. the OS is blocking mic capture. Surfaces a
  /// live warning so the user doesn't have to wait until "Stop" to find out.
  final ValueNotifier<bool> _noAudioNotifier = ValueNotifier(false);
  DateTime? _listenStartedAt;
  Timer? _diagTimer;
  /// Guards `_stop()` so repeated taps on "Stop & Review" (the old 10-click
  /// workaround) only trigger one finalize.
  bool _stopping = false;

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
    _tajweedOn = LocalStorageService().getTajweedColorsEnabledSync();
    _loadScope();

    _eventSub = _service.events.listen(_onEvent);
    _connSub = _service.connectionState.listen(_onConnectionState);
  }

  @override
  void dispose() {
    _stopDiagTimer();
    _eventSub?.cancel();
    _connSub?.cancel();
    _scrollController.dispose();
    _micChunksNotifier.dispose();
    _sentBytesNotifier.dispose();
    _micErrorNotifier.dispose();
    _focusNotifier.dispose();
    _audioOnDataNotifier.dispose();
    _noAudioNotifier.dispose();
    _service.dispose();
    _audioService.dispose();
    super.dispose();
  }

  /// Resets the reveal to a blank canvas.
  void _clearReveal() {
    _revealedWords = const [];
    _revealedStatuses = const [];
    _revealedTajweedSpans = const [];
    _revealedIndices.clear();
  }

  // ─── Data loading ─────────────────────────────────────────────────────────

  /// Loads the target block from the bundled corpus and records where each ayah
  /// ends (for inline markers). For the Surah scope this honours the selected
  /// [_ayahFrom] .. [_ayahTo] range. The live canvas stays blank until reciting.
  Future<void> _loadScope() async {
    try {
      List<AyahModel> allAyahs;
      if (_scope == RecitationScope.page) {
        allAyahs = await LocalCorpusRepository().getAyahsByPage(_page);
      } else {
        allAyahs = await LocalCorpusRepository().getAyahs(_surah);
      }
      if (allAyahs.isEmpty) return;

      // For the surah scope, restrict to the chosen ayah range.
      final ayahs = _scope == RecitationScope.surah
          ? allAyahs
              .where((a) =>
                  a.ayahNumber >= _ayahFrom && a.ayahNumber <= _ayahTo)
              .toList()
          : allAyahs;

      final words = <String>[];
      final tajweed = <List<TajweedSpan>?>[];
      final refs = <(int, int)>[];
      final boundaries = <int>[];
      final labels = <String>[];

      for (final a in ayahs) {
        for (final w in a.words) {
          words.add(w.text);
          tajweed.add(
            (w.tajweedSpans != null && w.tajweedSpans!.isNotEmpty)
                ? w.tajweedSpans
                : null,
          );
        }
        refs.add((a.surahNumber, a.ayahNumber));
        if (a.words.isNotEmpty) {
          boundaries.add(words.length - 1);
          labels.add(a.ayahNumber.toString());
        }
      }

      if (mounted) {
        setState(() {
          _words = words;
          _wordTajweedSpans = tajweed;
          _ayahRefs = refs;
          _ayahBoundaries = boundaries;
          _ayahLabels = labels;
          _ayahCount = allAyahs.length;
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
          });
        }
        break;
      case RecitationStreamEventType.word:
        final idx = event.wordIndex;
        // Append the confirmed Arabic word to the canvas. Skip duplicates and
        // empty payloads so the book flow never shows stray/blank words.
        final text = (event.expected ?? event.spoken ?? '').trim();
        if (text.isEmpty) return;
        if (idx != null && _revealedIndices.contains(idx)) return;

        // Capture the word's tajweed spans (aligned by reference index) so the
        // live canvas can colour each letter by its rule as it appears.
        final spans = (idx != null && idx >= 0 && idx < _wordTajweedSpans.length)
            ? _wordTajweedSpans[idx]
            : null;

        setState(() {
          _revealedWords = [..._revealedWords, text];
          _revealedStatuses = [..._revealedStatuses, event.status];
          _revealedTajweedSpans = [..._revealedTajweedSpans, spans];
          if (idx != null) _revealedIndices.add(idx);
        });
        _scrollToLatest();
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

  /// Smoothly scrolls the latest revealed word to the upper third of the
  /// viewport, but ONLY when it enters the bottom 30% — so we don't fight the
  /// user's own scrolling on every word.
  void _scrollToLatest() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final ctx = _caretKey.currentContext;
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

      // Blueprint: if the latest word enters the bottom 30% of the viewport,
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
    _listenStartedAt = DateTime.now();
    _noAudioNotifier.value = false;
    _stopping = false;
    setState(() {
      _ui = LiveRecitationUiState.live;
      _clearReveal();
      _errorMessage = null;
      _result = null;
    });

    try {
      await _service.start(
        surahNumber: _surah,
        ayahNumber: _ayah,
        ayahFrom: _scope == RecitationScope.surah ? _ayahFrom : _ayah,
        ayahTo: _scope == RecitationScope.surah ? _ayahTo : _ayah,
        ayahRefs: _ayahRefs,
        // Full target word list sent so the backend can score even if its own
        // reference store is empty (prevents "0 of 0 words correct").
        words: _words,
        // Reveal-as-you-speak is the ONLY behaviour on this screen.
        memorizationMode: false,
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
    _startDiagTimer();
  }

  void _startDiagTimer() {
    _stopDiagTimer();
    _diagTimer = Timer.periodic(const Duration(milliseconds: 500), (_) {
      if (!mounted) return;
      final chunks = _service.micChunks;
      _micChunksNotifier.value = chunks;
      _sentBytesNotifier.value = _service.sentBytes;
      // Capture any native recorder error (state channel) so it shows live.
      _micErrorNotifier.value = _service.micError;
      // Capture whether Android granted audio focus — a `false` here is the
      // smoking gun for a silently-dead recorder (OS/contending app blocking).
      _focusNotifier.value = _service.audioFocusGranted;
      _audioOnDataNotifier.value = _service.audioOnDataCount;
      // After ~2s of listening with zero recorder output, the OS is almost
      // certainly blocking mic capture — flag it live instead of waiting for
      // "Stop" (by which point the live UI is replaced by the error screen).
      if (_listenStartedAt != null &&
          DateTime.now().difference(_listenStartedAt!).inMilliseconds > 2000 &&
          chunks == 0 &&
          !_noAudioNotifier.value) {
        _noAudioNotifier.value = true;
      }
    });
  }

  void _stopDiagTimer() {
    _diagTimer?.cancel();
    _diagTimer = null;
    _noAudioNotifier.value = false;
    _listenStartedAt = null;
  }

  Future<void> _stop() async {
    if (_stopping) return; // idempotent: ignore repeated taps while finishing
    _stopping = true;
    _stopDiagTimer();
    await Haptics.vibrate(HapticsType.selection);
    // Show "Finalizing…" immediately so the long server-side final
    // transcription (re-processing the whole recitation, can take many seconds
    // on a slow CPU) doesn't make the button feel dead. The `final` WS event
    // will drive navigation to results; the timer is only a safety net.
    setState(() => _ui = LiveRecitationUiState.finalizing);
    unawaited(_service.stop());
    Timer(const Duration(seconds: 45), () {
      if (mounted && _ui == LiveRecitationUiState.finalizing) {
        _finishWith(_synthesizeResult());
      }
    });
  }

  void _finishWith(RecitationResult? result) {
    if (!mounted) return;
    // Idempotent: the `final` event and `_stop()`'s safety timer can both call
    // this; only the first one should navigate + persist.
    if (_ui == LiveRecitationUiState.results) return;

    // If the app never sent any microphone audio to the server, there is
    // nothing to score — surfacing a silent "0 of N / Duration: 0s" is
    // confusing. Show a clear, actionable error instead so the user knows to
    // grant mic access / free the microphone.
    if (_service.sentBytes == 0) {
      final chunks = _service.micChunks;
      // The native recorder often reports the *real* cause asynchronously
      // (unsupported sample rate, "PCM reader failed to initialize", another
      // app holding the mic). Surface it verbatim so the user isn't left
      // guessing between "permission" and "network".
      final nativeErr = _service.micError;
      final nativeDetail = nativeErr != null
          ? ' Recorder error: $nativeErr'
          : '';
      // Distinguish "the recorder produced no audio" (capture blocked by the
      // OS despite the app permission being granted) from "audio was captured
      // but never reached the server" (a transport / dropped-connection issue)
      // — the fix is very different for each.
      final captureHint = chunks == 0
          ? 'The microphone produced no audio at all.$nativeDetail '
              '${_service.audioFocusGranted == false ? 'Android denied audio '
                  'focus — another app (voice assistant, recorder, call) is '
                  'likely holding the mic. ' : ''}'
              'Open your device Settings › Apps › Qari › Permissions › '
              'Microphone and set it to "Allow", close any other app using the '
              'mic (voice assistant, recorder, phone call), then restart Qari '
              'and retry.'
          : 'Audio was captured ($chunks mic chunks) but none reached the '
              'server. The connection dropped mid-stream — check your network '
              'and retry.';
      setState(() {
        _ui = LiveRecitationUiState.error;
        _errorMessage = 'No microphone audio was captured (0 bytes sent, '
            'mic chunks: $chunks). $captureHint';
      });
      debugPrint('[LiveRecitation] 0 bytes sent → micChunks=$chunks '
          '(capture blocked: ${chunks == 0})');
      return;
    }

    // Prefer the backend's result, but if it came back with ZERO word verdicts
    // (e.g. server reference was empty, or audio never reached it) fall back to
    // the words we revealed live so the results screen is never "0 of 0". The
    // full target list (_words) is always passed as `ayahWords` to
    // RecitationResults so the word-by-word grid has the canonical text.
    final useResult = (result != null && result.wordVerdicts.isNotEmpty)
        ? result
        : _synthesizeResult();
    debugPrint('[LiveRecitation] finish: backendVerdicts='
        '${result?.wordVerdicts.length ?? -1}, '
        'revealedWords=${_revealedWords.length}, '
        'targetWords=${_words.length}');

    // Persist the session locally for history / mistake-review / streak.
    _persistSession(useResult);

    setState(() {
      _result = useResult;
      _ui = LiveRecitationUiState.results;
    });
  }

  /// Saves the completed session to the local history store (Tarteel-style
  /// "Mistake Review" + streak tracking). Captures every mispronounced /
  /// skipped word as a [RecitationMistake] for later review.
  void _persistSession(RecitationResult result) {
    try {
      final mistakes = <RecitationMistake>[];
      for (final v in result.wordVerdicts) {
        if (v.isCorrect) continue;
        final expected = v.expectedText ?? v.displayWord(_words);
        mistakes.add(RecitationMistake(
          word: v.displayWord(_words),
          expectedText: expected,
          errorType: v.errorType ?? 'error',
          surahNumber: _surah,
          ayahNumber: _ayah,
        ));
      }
      final from = _scope == RecitationScope.surah ? _ayahFrom : _ayah;
      final to = _scope == RecitationScope.surah ? _ayahTo : _ayah;
      // Fire-and-forget: the session is already shown; persistence must never
      // block the results UI.
      LocalStorageService.getInstance().then((ls) {
        RecitationHistoryService(ls.prefs).saveSession(
          scope: _scope == RecitationScope.page ? 'page' : 'surah',
          surahNumber: _surah,
          ayahFrom: from,
          ayahTo: to,
          overallScore: result.overallScore,
          correctCount: result.correctCount,
          totalCount: result.wordVerdicts.length,
          durationSeconds: result.durationSeconds,
          mistakes: mistakes,
        );
      });
    } catch (e) {
      debugPrint('LiveRecitation: could not persist session: $e');
    }
  }

  /// Builds a result from the revealed words when the backend final payload
  /// didn't arrive (e.g. connection dropped) so the user still sees feedback.
  RecitationResult _synthesizeResult() {
    final verdicts = <WordVerdict>[];
    var matched = 0;
    for (var i = 0; i < _revealedWords.length; i++) {
      final st = i < _revealedStatuses.length
          ? _revealedStatuses[i]
          : LiveWordStatus.matched;
      final correct = st == LiveWordStatus.matched;
      if (correct) matched++;
      final word = _revealedWords[i];
      verdicts.add(WordVerdict(
        word: word,
        wordIndex: i,
        isCorrect: correct,
        expectedText: word,
        errorType: correct ? null : (st.name),
      ));
    }
    final acc = _revealedWords.isEmpty ? 0.0 : matched / _revealedWords.length;
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
      confidence: _revealedWords.isEmpty ? 0.0 : 1.0,
      feedback: 'Live session complete.',
    );
  }

  Future<void> _cancel() async {
    _stopDiagTimer();
    await _service.cancel();
    if (mounted) {
      setState(() {
        _ui = LiveRecitationUiState.setup;
        _clearReveal();
      });
    }
  }

  void _reset() {
    _stopDiagTimer();
    setState(() {
      _ui = LiveRecitationUiState.setup;
      _result = null;
      _errorMessage = null;
      _clearReveal();
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
        : (_ayahFrom == _ayahTo
            ? 'Live · Surah $_surah:$_ayahFrom'
            : 'Live · Surah $_surah:$_ayahFrom-$_ayahTo');
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
          IconButton(
            icon: const Icon(Icons.history_rounded),
            tooltip: 'Recitation history',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => const RecitationHistoryPage(),
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.search_rounded),
            tooltip: 'Find a verse by reciting',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => const VerseIdentifierPage(),
              ),
            ),
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
      case LiveRecitationUiState.finalizing:
        return _buildFinalizing(theme);
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
            Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Align(
                  child: ActionChip(
                    avatar: const Icon(Icons.auto_stories_rounded, size: 18),
                    label: Text('Surah $_surah'),
                    onPressed: _openTargetPicker,
                  ),
                ),
                const SizedBox(height: 12),
                // Exact ayah range within the surah (Tarteel-style "recite a
                // specific range" — not just the whole surah).
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
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
                        child: _NumberDropdown(
                          label: 'From ayah',
                          value: _ayahFrom,
                          count: _ayahCount,
                          onChanged: (v) {
                            if (v <= _ayahTo) {
                              setState(() {
                                _ayahFrom = v;
                                _loadScope();
                              });
                            }
                          },
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        child: Text('→',
                            style: theme.textTheme.titleMedium),
                      ),
                      Expanded(
                        child: _NumberDropdown(
                          label: 'To ayah',
                          value: _ayahTo,
                          count: _ayahCount,
                          onChanged: (v) {
                            if (v >= _ayahFrom) {
                              setState(() {
                                _ayahTo = v;
                                _loadScope();
                              });
                            }
                          },
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          const SizedBox(height: 20),

          // Behaviour explanation (no toggle — reveal-as-you-speak is the only
          // behaviour).
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: theme.colorScheme.primary.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                Icon(Icons.auto_awesome_rounded,
                    size: 22, color: theme.colorScheme.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Recite and watch the words appear on the page, one by one, '
                    'as the engine confirms them.',
                    style: theme.textTheme.bodySmall,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Target preview (plain Arabic text — no dots / placeholders).
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.25),
              borderRadius: BorderRadius.circular(20),
            ),
            child: _words.isEmpty
                ? Text('Loading…', textAlign: TextAlign.center, style: theme.textTheme.bodyMedium)
                : _TargetPreview(words: _words, fontSize: 24),
          ),
          const SizedBox(height: 16),

          // Tajweed toggle (live per-letter tajweed colouring).
          _TajweedToggle(
            value: _tajweedOn,
            onChanged: (v) {
              setState(() => _tajweedOn = v);
              LocalStorageService.getInstance().then(
                (ls) => ls.setTajweedColorsEnabled(v),
              );
            },
            theme: theme,
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
        // Status bar (self-managed LIVE timer) so the page never setStates on a
        // 1s tick (which would rebuild the reveal view).
        _LiveStatusBadge(connectionState: _service.connectionState),

        // Live "no audio" warning: if the recorder produced nothing after a
        // couple seconds, tell the user immediately (the error screen would
        // otherwise hide this until they tap Stop).
        ValueListenableBuilder<bool>(
          valueListenable: _noAudioNotifier,
          builder: (context, stalled, _) => stalled
              ? Container(
                  margin: const EdgeInsets.fromLTRB(20, 4, 20, 0),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.error.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: theme.colorScheme.error.withValues(alpha: 0.4),
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.mic_off_rounded,
                          size: 18, color: theme.colorScheme.error),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _service.micError != null
                              ? 'No microphone audio. Recorder error: '
                                  '${_service.micError}'
                              : 'No microphone audio is reaching the app. If '
                                  'microphone permission is already Allowed, '
                                  'fully close Qari and reopen it, then try '
                                  'again. Also close any other app using the '
                                  'mic (voice assistant, recorder, call).',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: theme.colorScheme.error,
                            height: 1.4,
                          ),
                        ),
                      ),
                    ],
                  ),
                )
              : const SizedBox.shrink(),
        ),

        // The blank canvas → continuous Mushaf reveal. Starts empty; words are
        // appended live as the engine confirms them.
        Expanded(
          child: SingleChildScrollView(
            controller: _scrollController,
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: _revealedWords.isEmpty
                ? _BlankCanvasHint(theme: theme)
                : MushafRevealView(
                    words: _revealedWords,
                    statuses: _revealedStatuses,
                    tajweedSpans: _revealedTajweedSpans,
                    tajweedEnabled: _tajweedOn,
                    ayahBoundaries: _ayahBoundaries,
                    ayahLabels: _ayahLabels,
                    fontSize: 32,
                    caretKey: _caretKey,
                  ),
          ),
        ),

        // Live diagnostics (so "0 of N / Duration 0s" is never a black box):
        // shows mic chunks captured vs bytes actually sent to the server.
        // Only this small Text rebuilds (via ValueNotifier), not the reveal view.
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 0),
          child: ValueListenableBuilder<int>(
            valueListenable: _micChunksNotifier,
            builder: (context, chunks, _) => ValueListenableBuilder<int>(
              valueListenable: _sentBytesNotifier,
              builder: (context, sent, _) => ValueListenableBuilder<String?>(
                valueListenable: _micErrorNotifier,
                builder: (context, err, _) => ValueListenableBuilder<bool?>(
                  valueListenable: _focusNotifier,
                  builder: (context, focus, _) =>
                      ValueListenableBuilder<int>(
                    valueListenable: _audioOnDataNotifier,
                    builder: (context, _, __) {
                      final onData = _audioOnDataNotifier.value;
                      final focusStr = focus == null
                          ? ''
                          : focus
                              ? ' · focus: yes'
                              : ' · focus: NO';
                      final statusStr = _service.nativeStatus ?? 'init';
                      final onDataErr = _service.audioOnDataError;
                      final frameType = _service.lastFrameType;
                      final onDataStr = ' · onData: $onData'
                          '${frameType != null ? ' ($frameType)' : ''}'
                          '${onDataErr != null ? ' · onDataErr: $onDataErr' : ''}';
                      return Text(
                        err != null
                            ? 'diag · mic chunks: $chunks · bytes sent: $sent · '
                                '$statusStr$focusStr$onDataStr\n'
                                'recorder error: $err'
                            : 'diag · mic chunks: $chunks · bytes sent: $sent · '
                                '$statusStr$focusStr$onDataStr',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: (err != null || focus == false)
                              ? theme.colorScheme.error
                              : theme.colorScheme.onSurface
                                  .withValues(alpha: 0.4),
                        ),
                      );
                    },
                  ),
                ),
              ),
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
  Widget _buildFinalizing(ThemeData theme) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 24),
            Text(
              'Finalizing your recitation…',
              style: theme.textTheme.titleMedium
                  ?.copyWith(color: theme.colorScheme.onSurface),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'Analysing your full recitation. This can take a few seconds.',
              style: theme.textTheme.bodySmall
                  ?.copyWith(color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

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
                        _ayahFrom = 1;
                        _ayahTo = tempCount;
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
          'tap Stop.\n\n'
          '• The page starts blank. As the engine confirms each word you say, it '
          'appears on the page — right-to-left, like a real Mushaf.\n\n'
          '• Mispronounced words show in red, skipped words in amber.\n\n'
          '• Circular markers between words show where each ayah ends.',
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

/// Faint centered hint shown on the blank canvas before the first word arrives.
/// It is plain text — no dots, boxes, or placeholders.
class _BlankCanvasHint extends StatelessWidget {
  final ThemeData theme;
  const _BlankCanvasHint({required this.theme});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(
        'Start reciting — the words will appear here',
        textAlign: TextAlign.center,
        style: theme.textTheme.bodyMedium?.copyWith(
          color: theme.colorScheme.onSurface.withValues(alpha: 0.35),
        ),
      ),
    );
  }
}

/// Static RTL preview of the target block on the setup screen (plain Arabic
/// text, no masking / dots).
class _TargetPreview extends StatelessWidget {
  final List<String> words;
  final double fontSize;
  const _TargetPreview({required this.words, this.fontSize = 24});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Wrap(
        direction: Axis.horizontal,
        alignment: WrapAlignment.start,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 4,
        runSpacing: 10,
        children: [
          for (final w in words)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 2),
              child: Text(
                w,
                style: AppTheme.arabicTextStyle(
                  fontSize: fontSize,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.45),
                ),
                textAlign: TextAlign.right,
              ),
            ),
        ],
      ),
    );
  }
}

/// Live status bar: shows the LIVE timer (count-up, never auto-stops) and a
/// connecting indicator. Owns its own 1s timer + connection subscription so the
/// parent page doesn't need to [setState] every second (which would otherwise
/// rebuild the reveal view).
class _LiveStatusBadge extends StatefulWidget {
  final Stream<LiveConnectionState> connectionState;

  const _LiveStatusBadge({required this.connectionState});

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
    return GestureDetector(
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

/// Inline toggle for live per-letter tajweed colouring, mirroring the Surah
/// reader's tajweed switch so the live canvas and the reader look identical.
class _TajweedToggle extends StatelessWidget {
  final bool value;
  final ValueChanged<bool> onChanged;
  final ThemeData theme;

  const _TajweedToggle({
    required this.value,
    required this.onChanged,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    final color = theme.colorScheme.primary;
    return GestureDetector(
      onTap: () => onChanged(!value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: value ? color.withValues(alpha: 0.08) : theme.colorScheme.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: value ? color.withValues(alpha: 0.4) : theme.colorScheme.outline.withValues(alpha: 0.2),
          ),
        ),
        child: Row(
          children: [
            Icon(Icons.palette_rounded, size: 20, color: value ? color : null),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Tajweed colours',
                      style: theme.textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w600)),
                  Text(
                    'Colour each letter by its tajweed rule as it appears',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                    ),
                  ),
                ],
              ),
            ),
            Switch(
              value: value,
              onChanged: onChanged,
              activeColor: color,
            ),
          ],
        ),
      ),
    );
  }
}
