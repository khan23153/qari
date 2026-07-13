import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';
import 'package:record/record.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../data/services/recording_service.dart';
import '../../../../data/services/audio_service.dart';
import '../../../../data/repositories/recitation_repository.dart';
import '../../../../data/repositories/corpus_repository.dart';
import '../../../../data/repositories/local_corpus_repository.dart';
import '../../../../data/models/recitation_model.dart';
import '../../../../data/models/word_model.dart';
import '../../../../core/utils/idempotency.dart';
import '../../../../data/services/api_client.dart';
import '../widgets/live_waveform.dart';
import '../widgets/recitation_results.dart';
import '../widgets/word_comparison_sheet.dart';

/// S8: AI Recitation Sandbox (core USP) — state machine:
/// Listen -> Record -> Analyzing -> Results
/// Live waveform, words tint green/red in place, score header,
/// red word tap -> A/B audio comparison bottom sheet,
/// failure states (mic denial, too noisy, low confidence -> NO red marks).
class RecitationPage extends ConsumerStatefulWidget {
  final int? surahNumber;
  final int? ayahNumber;

  const RecitationPage({super.key, this.surahNumber, this.ayahNumber});

  @override
  ConsumerState<RecitationPage> createState() => _RecitationPageState();
}

class _RecitationPageState extends ConsumerState<RecitationPage>
    with SingleTickerProviderStateMixin {
  RecitationState _state = RecitationState.idle;
  final RecordingService _recordingService = RecordingService();
  final AudioService _audioService = AudioService();
  final RecitationRepository _recitationRepo = RecitationRepository();

  // Recording state
  String? _recordingPath;
  int _recordingDuration = 0;
  Timer? _durationTimer;
  Stream<Amplitude>? _amplitudeStream;
  StreamSubscription<Amplitude>? _amplitudeSubscription;
  final List<double> _waveformSamples = [];

  // Results
  RecitationResult? _result;
  String? _errorMessage;

  // Target ayah
  int _surahNumber = 1;
  int _ayahNumber = 1;
  String _ayahText = 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ';
  List<String> _ayahWords = const [];

  // Reference audio playback
  bool _isPlayingReference = false;

  @override
  void initState() {
    super.initState();
    if (widget.surahNumber != null) {
      _surahNumber = widget.surahNumber!;
      _ayahNumber = widget.ayahNumber ?? 1;
    }
    _loadTargetAyahText();
  }

  /// Loads the actual target ayah text from the bundled corpus so the screen
  /// shows the correct ayah the user tapped in the reader (falls back to the
  /// default bismillah if the surah/ayah isn't in the local bundle).
  Future<void> _loadTargetAyahText() async {
    try {
      final ayahs = await LocalCorpusRepository().getAyahs(_surahNumber);
      AyahModel? match;
      for (final a in ayahs) {
        if (a.ayahNumber == _ayahNumber) {
          match = a;
          break;
        }
      }
      final ayah = match;
      if (ayah != null && mounted) {
        setState(() {
          _ayahText = ayah.ayahText;
          _ayahWords = ayah.words.map((w) => w.text).toList();
        });
      }
    } catch (e) {
      debugPrint('Recitation: could not load target ayah text: $e');
    }
  }

  @override
  void dispose() {
    _durationTimer?.cancel();
    _amplitudeSubscription?.cancel();
    _recordingService.dispose();
    _audioService.dispose();
    super.dispose();
  }

  // ─── State Machine Transitions ──────────────────────────────────────────

  Future<void> _startListening() async {
    // Play reference audio for the user to listen first
    await Haptics.vibrate(HapticsType.selection);
    setState(() => _state = RecitationState.listening);

    // Prefer the real per-ayah audio_url returned by the backend (a working
    // quran.com CDN link). The hardcoded audioCdnUrl ('https://audio.qari.app')
    // does not resolve, which is what produced the "0 source error" toast.
    String? referenceUrl;
    try {
      final ayah = await CorpusRepository().getAyah(_surahNumber, _ayahNumber);
      referenceUrl = ayah.audioUrl;
    } catch (e) {
      debugPrint('Recitation: could not fetch reference audio url: $e');
    }
    debugPrint('Recitation reference audio url: $referenceUrl');

    if (mounted) {
      try {
        if (referenceUrl != null && referenceUrl.isNotEmpty) {
          try {
            await _audioService.playUrl(referenceUrl);
          } catch (e) {
            // The backend url may point at a dead host ("0 source error") —
            // retry with the reliable constructed everyayah.com CDN url.
            debugPrint('Recitation reference url failed, retrying CDN: $e');
            await _audioService.playAyah(
              surahNumber: _surahNumber,
              ayahNumber: _ayahNumber,
            );
          }
        } else {
          // Fallback to the constructed CDN url.
          await _audioService.playAyah(
            surahNumber: _surahNumber,
            ayahNumber: _ayahNumber,
          );
        }
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not play reference audio: $e'),
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }

    if (mounted) setState(() => _isPlayingReference = false);
  }

  Future<void> _startRecording() async {
    _amplitudeSubscription?.cancel();
    await Haptics.vibrate(HapticsType.medium);
    setState(() => _state = RecitationState.recording);

    // Check mic permission
    final hasPermission = await _recordingService.hasPermission();
    if (!hasPermission) {
      final granted = await _recordingService.requestPermission();
      if (!granted) {
        setState(() => _state = RecitationState.errorMicDenied);
        return;
      }
    }

    // Start recording
    final path = await _recordingService.startRecording();
    if (path == null) {
      setState(() => _state = RecitationState.errorMicDenied);
      return;
    }

    _recordingPath = path;
    _recordingDuration = 0;
    _waveformSamples.clear();

    // Start duration timer
    _durationTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      setState(() => _recordingDuration++);
      if (_recordingDuration >= AppConstants.maxRecordingDurationSeconds) {
        _stopAndAnalyze();
      }
    });

    // Start amplitude stream for waveform
    _amplitudeStream = _recordingService.getAmplitudeStream();
    _amplitudeSubscription = _amplitudeStream!.listen((amplitude) {
      // Convert dB to normalized 0-1 value
      final normalized = ((amplitude.current + 60) / 60).clamp(0.0, 1.0);
      setState(() {
        _waveformSamples.add(normalized);
        // Keep last 100 samples
        if (_waveformSamples.length > 100) {
          _waveformSamples.removeAt(0);
        }
      });
    });
  }

  Future<void> _stopAndAnalyze() async {
    _durationTimer?.cancel();
    await Haptics.vibrate(HapticsType.selection);

    setState(() => _state = RecitationState.analyzing);

    // Stop recording
    final path = await _recordingService.stopRecording();
    if (path == null) {
      setState(() {
        _state = RecitationState.errorLowConfidence;
        _errorMessage = 'Recording failed. Please try again.';
      });
      return;
    }

    _recordingPath = path;

    // Upload and poll for results
    try {
      final sessionId = await _recitationRepo.uploadRecitation(
        filePath: path,
        surahNumber: _surahNumber,
        ayahNumber: _ayahNumber,
        idempotencyKey: IdempotencyKey.generate(),
      );

      // Poll for results
      final result = await _recitationRepo.pollForResult(
        sessionId,
        onPolling: (attempt, max) {
          // Could update a progress indicator
        },
      );

      // Check for low confidence
      if (!result.isConfident) {
        setState(() => _state = RecitationState.errorLowConfidence);
        return;
      }

      // Check for too noisy
      if (result.wordVerdicts.isEmpty) {
        setState(() => _state = RecitationState.errorTooNoisy);
        return;
      }

      setState(() {
        _state = RecitationState.results;
        _result = result;
      });
    } catch (e) {
      debugPrint('Recitation analysis error: $e');
      // Surface the real error + any backend status code so the user can
      // debug the network/timeout (e.g. check the exact API error code).
      final message = e is ApiException
          ? 'Analysis failed'
              '${e.statusCode != null ? ' (HTTP ${e.statusCode})' : ''}'
              '${e.errorCode != null ? ' [${e.errorCode}]' : ''}: '
              '${e.message}'
          : 'We couldn\'t analyze your recitation: $e';
      setState(() {
        _state = RecitationState.errorAnalysisFailed;
        _errorMessage = message;
      });
    }
  }

  Future<void> _cancelRecording() async {
    _durationTimer?.cancel();
    await _recordingService.cancelRecording();
    setState(() {
      _state = RecitationState.idle;
      _recordingDuration = 0;
      _waveformSamples.clear();
    });
  }

  void _reset() {
    setState(() {
      _state = RecitationState.idle;
      _result = null;
      _errorMessage = null;
      _recordingDuration = 0;
      _waveformSamples.clear();
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
        ayahWords: _ayahWords,
        audioService: _audioService,
      ),
    );
  }

  // ─── Build ───────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // ─── Header ───────────────────────────────────────────────
            _buildHeader(theme),

            // ─── State Content ────────────────────────────────────────
            Expanded(
              child: _buildStateContent(theme),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back_rounded),
            onPressed: () => Navigator.of(context).pop(),
          ),
          Expanded(
            child: Column(
              children: [
                Text(
                  'AI Recitation',
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  'Surah $_surahNumber:$_ayahNumber',
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

  Widget _buildStateContent(ThemeData theme) {
    switch (_state) {
      case RecitationState.idle:
        return _IdleState(
          ayahText: _ayahText,
          onListen: _startListening,
          onRecord: _startRecording,
          theme: theme,
        );
      case RecitationState.listening:
        return _ListeningState(
          ayahText: _ayahText,
          isPlaying: _isPlayingReference,
          onRecord: _startRecording,
          onReplay: _startListening,
          theme: theme,
        );
      case RecitationState.recording:
        return _RecordingState(
          ayahText: _ayahText,
          duration: _recordingDuration,
          maxDuration: AppConstants.maxRecordingDurationSeconds,
          waveformSamples: _waveformSamples,
          onStop: _stopAndAnalyze,
          onCancel: _cancelRecording,
          theme: theme,
        );
      case RecitationState.analyzing:
        return _AnalyzingState(theme: theme);
      case RecitationState.results:
        return RecitationResults(
          result: _result!,
          ayahWords: _ayahWords,
          onWordTapped: _onWordTapped,
          onRetry: _reset,
          theme: theme,
        );
      case RecitationState.errorMicDenied:
        return _ErrorState(
          icon: Icons.mic_off_rounded,
          title: 'Microphone Access Denied',
          message: 'Please allow microphone access in your device settings to use the recitation feature.',
          onRetry: _reset,
          theme: theme,
        );
      case RecitationState.errorTooNoisy:
        return _ErrorState(
          icon: Icons.graphic_eq_rounded,
          title: 'Too Noisy',
          message: 'We couldn\'t hear you clearly. Please find a quieter place and try again.',
          onRetry: _reset,
          theme: theme,
        );
      case RecitationState.errorLowConfidence:
        return _ErrorState(
          icon: Icons.help_outline_rounded,
          title: 'Low Confidence',
          message: _errorMessage ?? 'We couldn\'t analyze your recitation with enough confidence. Please try again in a quieter environment.',
          onRetry: _reset,
          theme: theme,
          showNoRedMarks: true,
        );
      case RecitationState.errorAnalysisFailed:
        return _ErrorState(
          icon: Icons.cloud_off_rounded,
          title: 'Analysis Failed',
          message: _errorMessage ?? 'Something went wrong while analyzing your recitation.',
          onRetry: _reset,
          theme: theme,
        );
    }
  }

  void _showInfoDialog(ThemeData theme) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('How Recitation Works'),
        content: const Text(
          '1. Listen to the reference recitation\n'
          '2. Record yourself reciting the same ayah\n'
          '3. Our AI analyzes your pronunciation\n'
          '4. Words turn green (correct) or red (needs work)\n'
          '5. Tap red words to compare your audio with the reference',
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

// ─── State Widgets ─────────────────────────────────────────────────────────

/// Idle state — initial screen with Listen and Record buttons.
class _IdleState extends StatelessWidget {
  final String ayahText;
  final VoidCallback onListen;
  final VoidCallback onRecord;
  final ThemeData theme;

  const _IdleState({
    required this.ayahText,
    required this.onListen,
    required this.onRecord,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Ayah to recite
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: theme.colorScheme.primary.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                children: [
                  Text(
                    'Recite this ayah:',
                    style: theme.textTheme.labelMedium?.copyWith(
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Directionality(
                    textDirection: TextDirection.rtl,
                    child: Text(
                      ayahText,
                      style: AppTheme.arabicTextStyle(
                        fontSize: 32,
                        color: theme.colorScheme.onSurface,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
            )
                .animate()
                .fadeIn(duration: 400.ms)
                .slideY(begin: 0.05, end: 0),

            const SizedBox(height: 32),

            // Listen button
            FilledButton.tonalIcon(
              onPressed: onListen,
              icon: const Icon(Icons.headphones_rounded, size: 28),
              label: const Text('Listen First', style: TextStyle(fontSize: 16)),
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(56),
              ),
            )
                .animate()
                .fadeIn(delay: 200.ms, duration: 400.ms),

            const SizedBox(height: 16),

            // Record button (direct)
            OutlinedButton.icon(
              onPressed: onRecord,
              icon: const Icon(Icons.mic_rounded, size: 28),
              label: const Text('Record Now', style: TextStyle(fontSize: 16)),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(56),
              ),
            )
                .animate()
                .fadeIn(delay: 300.ms, duration: 400.ms),
          ],
        ),
      ),
    );
  }
}

/// Listening state — playing reference audio.
class _ListeningState extends StatelessWidget {
  final String ayahText;
  final bool isPlaying;
  final VoidCallback onRecord;
  final VoidCallback onReplay;
  final ThemeData theme;

  const _ListeningState({
    required this.ayahText,
    required this.isPlaying,
    required this.onRecord,
    required this.onReplay,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Animated speaker icon
            Icon(
              Icons.graphic_eq_rounded,
              size: 80,
              color: theme.colorScheme.primary,
            )
                .animate(onComplete: (c) => c.repeat())
                .scale(
                  begin: const Offset(1, 1),
                  end: const Offset(1.1, 1.1),
                  duration: 800.ms,
                ),

            const SizedBox(height: 24),

            Text(
              'Listening...',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            )
                .animate()
                .fadeIn(duration: 300.ms),

            const SizedBox(height: 24),

            // Ayah text
            Directionality(
              textDirection: TextDirection.rtl,
              child: Text(
                ayahText,
                style: AppTheme.arabicTextStyle(
                  fontSize: 28,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                ),
                textAlign: TextAlign.center,
              ),
            ),

            const SizedBox(height: 32),

            // Replay button
            TextButton.icon(
              onPressed: onReplay,
              icon: const Icon(Icons.replay_rounded),
              label: const Text('Replay'),
            ),

            const SizedBox(height: 16),

            // Record button
            FilledButton.icon(
              onPressed: onRecord,
              icon: const Icon(Icons.mic_rounded, size: 28),
              label: const Text('Start Recording', style: TextStyle(fontSize: 16)),
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(56),
              ),
            )
                .animate()
                .fadeIn(delay: 500.ms, duration: 400.ms),
          ],
        ),
      ),
    );
  }
}

/// Recording state — live waveform, timer, stop button.
class _RecordingState extends StatelessWidget {
  final String ayahText;
  final int duration;
  final int maxDuration;
  final List<double> waveformSamples;
  final VoidCallback onStop;
  final VoidCallback onCancel;
  final ThemeData theme;

  const _RecordingState({
    required this.ayahText,
    required this.duration,
    required this.maxDuration,
    required this.waveformSamples,
    required this.onStop,
    required this.onCancel,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const SizedBox(height: 32),

        // Recording indicator
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: const BoxDecoration(
                color: Colors.red,
                shape: BoxShape.circle,
              ),
            )
                .animate(onComplete: (c) => c.repeat())
                .fadeIn(duration: 500.ms)
                .then()
                .fadeOut(duration: 500.ms),
            const SizedBox(width: 8),
            Text(
              'Recording...',
              style: theme.textTheme.titleLarge?.copyWith(
                color: Colors.red,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),

        const SizedBox(height: 8),

        // Timer
        Text(
          '${(duration ~/ 60).toString().padLeft(2, '0')}:${(duration % 60).toString().padLeft(2, '0')}',
          style: theme.textTheme.displaySmall?.copyWith(
            fontWeight: FontWeight.w800,
            fontFeatures: [const FontFeature.tabularFigures()],
          ),
        ),

        const SizedBox(height: 8),

        // Max duration progress
        Text(
          'Max ${maxDuration ~/ 60}:${(maxDuration % 60).toString().padLeft(2, '0')}',
          style: theme.textTheme.labelSmall?.copyWith(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
          ),
        ),

        const SizedBox(height: 32),

        // Live waveform
        LiveWaveform(
          samples: waveformSamples,
          color: Colors.red,
          height: 120,
        ),

        const SizedBox(height: 32),

        // Ayah text (for reference while reciting)
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Directionality(
            textDirection: TextDirection.rtl,
            child: Text(
              ayahText,
              style: AppTheme.arabicTextStyle(
                fontSize: 26,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
              ),
              textAlign: TextAlign.center,
            ),
          ),
        ),

        const Spacer(),

        // Stop and Cancel buttons
        Padding(
          padding: const EdgeInsets.all(32),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: onCancel,
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size.fromHeight(56),
                    foregroundColor: theme.colorScheme.error,
                  ),
                  child: const Text('Cancel'),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: FilledButton.icon(
                  onPressed: onStop,
                  icon: const Icon(Icons.stop_rounded, size: 28),
                  label: const Text('Done', style: TextStyle(fontSize: 16)),
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
}

/// Analyzing state — loading animation.
class _AnalyzingState extends StatelessWidget {
  final ThemeData theme;

  const _AnalyzingState({required this.theme});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Animated analyzing icon
          SizedBox(
            width: 80,
            height: 80,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  strokeWidth: 4,
                  color: theme.colorScheme.primary,
                ),
                Icon(Icons.auto_awesome_rounded, size: 32, color: theme.colorScheme.primary),
              ],
            ),
          )
              .animate(onComplete: (c) => c.repeat())
              .rotate(duration: 2.seconds),

          const SizedBox(height: 24),

          Text(
            'Analyzing your recitation...',
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          )
              .animate()
              .fadeIn(duration: 400.ms),

          const SizedBox(height: 8),

          Text(
            'Our AI is checking your pronunciation and tajweed',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          )
              .animate()
              .fadeIn(delay: 200.ms, duration: 400.ms),
        ],
      ),
    );
  }
}

/// Error state — mic denied, too noisy, or low confidence.
class _ErrorState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final VoidCallback onRetry;
  final ThemeData theme;
  final bool showNoRedMarks;

  const _ErrorState({
    required this.icon,
    required this.title,
    required this.message,
    required this.onRetry,
    required this.theme,
    this.showNoRedMarks = false,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 64, color: theme.colorScheme.error.withValues(alpha: 0.5))
                .animate()
                .fadeIn(duration: 400.ms)
                .scale(
                  begin: const Offset(0.8, 0.8),
                  end: const Offset(1, 1),
                  duration: 400.ms,
                ),

            const SizedBox(height: 24),

            Text(
              title,
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w700,
              ),
              textAlign: TextAlign.center,
            )
                .animate()
                .fadeIn(delay: 200.ms, duration: 400.ms),

            const SizedBox(height: 12),

            Text(
              message,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            )
                .animate()
                .fadeIn(delay: 300.ms, duration: 400.ms),

            if (showNoRedMarks) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surface,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: theme.colorScheme.outline.withValues(alpha: 0.2),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.info_outline_rounded, size: 18,
                        color: theme.colorScheme.onSurface.withValues(alpha: 0.5)),
                    const SizedBox(width: 8),
                    Flexible(
                      child: Text(
                        'No red marks shown — we don\'t want to mislead you when unsure.',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                        ),
                      ),
                    ),
                  ],
                ),
              )
                  .animate()
                  .fadeIn(delay: 500.ms, duration: 400.ms),
            ],

            const SizedBox(height: 32),

            FilledButton(
              onPressed: onRetry,
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(52),
              ),
              child: const Text('Try Again'),
            )
                .animate()
                .fadeIn(delay: 600.ms, duration: 400.ms),
          ],
        ),
      ),
    );
  }
}
