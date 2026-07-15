import 'package:flutter/material.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../data/repositories/recitation_repository.dart';
import '../../../../data/services/recording_service.dart';
import 'live_recitation_page.dart';

/// Tarteel-style "verse lookup": recite any part of the Quran and the app
/// identifies which verse (surah:ayah) you are reciting, using the Quran
/// ASR model on the backend.
class VerseIdentifierPage extends StatefulWidget {
  const VerseIdentifierPage({super.key});

  @override
  State<VerseIdentifierPage> createState() => _VerseIdentifierPageState();
}

class _VerseIdentifierPageState extends State<VerseIdentifierPage> {
  final RecordingService _recording = RecordingService();
  final RecitationRepository _repo = RecitationRepository();

  bool _isRecording = false;
  bool _isIdentifying = false;
  String? _error;
  String? _transcript;
  List<Map<String, dynamic>> _candidates = const [];

  @override
  void dispose() {
    _recording.cancelRecording();
    super.dispose();
  }

  Future<void> _toggleRecording() async {
    if (_isIdentifying) return;
    if (_isRecording) {
      final path = await _recording.stopRecording();
      if (path == null || path.isEmpty) {
        setState(() {
          _isRecording = false;
          _error = 'Recording failed. Please try again.';
        });
        return;
      }
      await _identify(path);
    } else {
      final path = await _recording.startRecording();
      if (path == null) {
        setState(() => _error = 'Microphone permission is required.');
        return;
      }
      Haptics.vibrate(HapticsType.medium);
      setState(() {
        _isRecording = true;
        _error = null;
        _candidates = const [];
        _transcript = null;
      });
    }
  }

  Future<void> _identify(String path) async {
    setState(() {
      _isRecording = false;
      _isIdentifying = true;
      _error = null;
    });
    try {
      final result = await _repo.identifyVerse(filePath: path, topK: 5);
      if (!mounted) return;
      setState(() {
        _isIdentifying = false;
        _transcript = result['transcript'] as String?;
        _candidates = (result['candidates'] as List<dynamic>? ?? [])
            .map((c) => c as Map<String, dynamic>)
            .toList();
        _error = result['message'] as String?;
      });
    } catch (e) {
      if (!mounted) return;
      final msg = e.toString();
      setState(() {
        _isIdentifying = false;
        _error = msg.contains('503')
            ? 'Verse identification needs the Quran AI model, which is not '
                'available on this server right now. Try again later.'
            : 'Could not identify the verse. Please recite more clearly.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Find a Verse'),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: theme.colorScheme.primary.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                Icon(Icons.search_rounded,
                    color: theme.colorScheme.primary, size: 22),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Recite any verse — even a few words — and Qari will tell '
                    'you exactly which verse it is.',
                    style: theme.textTheme.bodySmall,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),

          // Record / stop button
          Center(
            child: GestureDetector(
              onTap: _toggleRecording,
              child: Container(
                width: 110,
                height: 110,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _isRecording
                      ? theme.colorScheme.error
                      : theme.colorScheme.primary,
                  boxShadow: [
                    BoxShadow(
                      color: (_isRecording
                              ? theme.colorScheme.error
                              : theme.colorScheme.primary)
                          .withValues(alpha: 0.35),
                      blurRadius: 24,
                      spreadRadius: 4,
                    ),
                  ],
                ),
                child: _isIdentifying
                    ? const CircularProgressIndicator(color: Colors.white)
                    : Icon(
                        _isRecording ? Icons.stop_rounded : Icons.mic_rounded,
                        color: Colors.white,
                        size: 48,
                      ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Center(
            child: Text(
              _isRecording
                  ? 'Listening… tap to stop'
                  : _isIdentifying
                      ? 'Identifying…'
                      : 'Tap to recite',
              style: theme.textTheme.labelMedium?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              ),
            ),
          ),

          if (_error != null && !_isIdentifying) ...[
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: theme.colorScheme.error.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: theme.colorScheme.error.withValues(alpha: 0.3),
                ),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline_rounded,
                      color: theme.colorScheme.error),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      _error!,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.error,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],

          if (_transcript != null && _transcript!.isNotEmpty) ...[
            const SizedBox(height: 24),
            Text('Heard:',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                )),
            const SizedBox(height: 4),
            Directionality(
              textDirection: TextDirection.rtl,
              child: Text(
                _transcript!,
                style: AppTheme.arabicTextStyle(fontSize: 24),
                textAlign: TextAlign.right,
              ),
            ),
          ],

          if (_candidates.isNotEmpty) ...[
            const SizedBox(height: 28),
            Text(
              'Possible verses',
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            ..._candidates.map((c) => _CandidateTile(candidate: c)),
          ],
        ],
      ),
    );
  }
}

class _CandidateTile extends StatelessWidget {
  final Map<String, dynamic> candidate;
  const _CandidateTile({required this.candidate});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final surah = candidate['surah_number'] as int? ?? 0;
    final ayah = candidate['ayah_number'] as int? ?? 0;
    final score = (candidate['score'] as num? ?? 0).toDouble();
    final text = candidate['text'] as String? ?? '';

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            Haptics.vibrate(HapticsType.light);
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => LiveRecitationPage(
                  surahNumber: surah,
                  ayahNumber: ayah,
                ),
              ),
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primary.withValues(alpha: 0.12),
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      '${(score * 100).toInt()}%',
                      style: theme.textTheme.labelMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '$surah:$ayah',
                        style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 2),
                      Directionality(
                        textDirection: TextDirection.rtl,
                        child: Text(
                          text,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: AppTheme.arabicTextStyle(fontSize: 20),
                          textAlign: TextAlign.right,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right_rounded),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
