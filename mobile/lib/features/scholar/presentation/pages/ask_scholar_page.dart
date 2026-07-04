import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:haptic_feedback/haptic_feedback.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../../data/services/recording_service.dart';
import 'scholar_inbox_page.dart';

/// S10: Ask a Scholar — record audio note (max 2 min) or type,
/// topic chips, disclaimer, inbox list.
class AskScholarPage extends ConsumerStatefulWidget {
  const AskScholarPage({super.key});

  @override
  ConsumerState<AskScholarPage> createState() => _AskScholarPageState();
}

class _AskScholarPageState extends ConsumerState<AskScholarPage> {
  final RecordingService _recordingService = RecordingService();
  final TextEditingController _textController = TextEditingController();

  bool _isRecording = false;
  int _recordingDuration = 0;
  Timer? _durationTimer;
  Set<String> _selectedTopics = {};
  String _inputMode = 'text'; // 'text' or 'audio'

  @override
  void dispose() {
    _durationTimer?.cancel();
    _textController.dispose();
    _recordingService.dispose();
    super.dispose();
  }

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      _durationTimer?.cancel();
      final path = await _recordingService.stopRecording();
      setState(() => _isRecording = false);
      // Path would be submitted with the question
    } else {
      final hasPermission = await _recordingService.hasPermission();
      if (!hasPermission) {
        final granted = await _recordingService.requestPermission();
        if (!granted) {
          _showPermissionError();
          return;
        }
      }
      final path = await _recordingService.startRecording();
      if (path != null) {
        setState(() {
          _isRecording = true;
          _recordingDuration = 0;
        });
        _durationTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
          setState(() {
            _recordingDuration++;
            if (_recordingDuration >= AppConstants.maxScholarAudioSeconds) {
              _toggleRecording();
            }
          });
        });
      }
    }
  }

  void _showPermissionError() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Microphone permission is required to record audio notes.'),
      ),
    );
  }

  void _submit() async {
    await Haptics.impact();

    if (_textController.text.trim().isEmpty && !_isRecording) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please type a question or record an audio note.')),
      );
      return;
    }

    // Submit question
    setState(() {
      _textController.clear();
      _selectedTopics.clear();
    });

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Your question has been submitted to a scholar. You\'ll get a response soon, Insha\'Allah.'),
        duration: Duration(seconds: 3),
      ),
    );
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
                      'Ask a Scholar',
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.inbox_rounded),
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const ScholarInboxPage()),
                    ),
                  ),
                ],
              ),
            ),

            // ─── Content ──────────────────────────────────────────────
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // ─── Disclaimer ────────────────────────────────────
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.amber.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: Colors.amber.withValues(alpha: 0.2),
                        ),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.info_outline_rounded, color: Colors.amber.shade700, size: 20),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              'This service provides general Islamic guidance. For specific fatwas or personal matters, please consult a qualified scholar in your locality.',
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                                height: 1.5,
                              ),
                            ),
                          ),
                        ],
                      ),
                    )
                        .animate()
                        .fadeIn(duration: 400.ms),

                    const SizedBox(height: 24),

                    // ─── Input Mode Toggle ──────────────────────────────
                    SegmentedButton<String>(
                      segments: const [
                        ButtonSegment(
                          value: 'text',
                          icon: Icon(Icons.edit_rounded),
                          label: Text('Type'),
                        ),
                        ButtonSegment(
                          value: 'audio',
                          icon: Icon(Icons.mic_rounded),
                          label: Text('Record'),
                        ),
                      ],
                      selected: {_inputMode},
                      onSelectionChanged: (selection) {
                        setState(() => _inputMode = selection.first);
                      },
                    ),

                    const SizedBox(height: 20),

                    // ─── Topic Chips ────────────────────────────────────
                    Text(
                      'Select topic(s):',
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: AppConstants.scholarTopics.map((topic) {
                        final isSelected = _selectedTopics.contains(topic);
                        return FilterChip(
                          label: Text(topic),
                          selected: isSelected,
                          onSelected: (selected) {
                            setState(() {
                              if (selected) {
                                _selectedTopics.add(topic);
                              } else {
                                _selectedTopics.remove(topic);
                              }
                            });
                          },
                        );
                      }).toList(),
                    ),

                    const SizedBox(height: 24),

                    // ─── Input Area ─────────────────────────────────────
                    if (_inputMode == 'text')
                      TextField(
                        controller: _textController,
                        maxLines: 6,
                        decoration: const InputDecoration(
                          hintText: 'Type your question here...',
                          alignHintWithText: true,
                        ),
                      )
                    else
                      _AudioRecordingArea(
                        isRecording: _isRecording,
                        duration: _recordingDuration,
                        maxDuration: AppConstants.maxScholarAudioSeconds,
                        onToggle: _toggleRecording,
                        theme: theme,
                      ),

                    const SizedBox(height: 24),

                    // ─── Submit Button ──────────────────────────────────
                    FilledButton.icon(
                      onPressed: _submit,
                      icon: const Icon(Icons.send_rounded),
                      label: const Text('Submit Question'),
                      style: FilledButton.styleFrom(
                        minimumSize: const Size.fromHeight(52),
                      ),
                    )
                        .animate()
                        .fadeIn(delay: 300.ms, duration: 400.ms),

                    const SizedBox(height: 32),

                    // ─── Recent Questions Link ──────────────────────────
                    OutlinedButton.icon(
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const ScholarInboxPage()),
                      ),
                      icon: const Icon(Icons.inbox_rounded),
                      label: const Text('View My Questions'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Audio recording area for scholar questions.
class _AudioRecordingArea extends StatelessWidget {
  final bool isRecording;
  final int duration;
  final int maxDuration;
  final VoidCallback onToggle;
  final ThemeData theme;

  const _AudioRecordingArea({
    required this.isRecording,
    required this.duration,
    required this.maxDuration,
    required this.onToggle,
    required this.theme,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isRecording
              ? Colors.red.withValues(alpha: 0.3)
              : theme.colorScheme.outline.withValues(alpha: 0.2),
        ),
      ),
      child: Column(
        children: [
          // Mic button
          GestureDetector(
            onTap: onToggle,
            child: Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: isRecording ? Colors.red : theme.colorScheme.primary,
                shape: BoxShape.circle,
                boxShadow: isRecording
                    ? [
                        BoxShadow(
                          color: Colors.red.withValues(alpha: 0.3),
                          blurRadius: 20,
                          spreadRadius: 4,
                        ),
                      ]
                    : [],
              ),
              child: Icon(
                isRecording ? Icons.stop_rounded : Icons.mic_rounded,
                color: Colors.white,
                size: 36,
              ),
            ),
          )
              .animate(
                autoPlay: isRecording,
                onComplete: (c) => c.repeat(),
              )
              .scale(
                begin: const Offset(1, 1),
                end: const Offset(1.05, 1.05),
                duration: 800.ms,
              ),

          const SizedBox(height: 16),

          // Timer
          Text(
            '${(duration ~/ 60).toString().padLeft(2, '0')}:${(duration % 60).toString().padLeft(2, '0')}',
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w800,
              fontFeatures: [const FontFeature.tabularFigures()],
              color: isRecording ? Colors.red : theme.colorScheme.onSurface,
            ),
          ),

          const SizedBox(height: 4),

          Text(
            isRecording
                ? 'Recording... Tap to stop'
                : 'Tap to start recording (max ${maxDuration ~/ 60} min)',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            textAlign: TextAlign.center,
          ),

          // Progress bar
          if (isRecording) ...[
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: duration / maxDuration,
                minHeight: 4,
                backgroundColor: Colors.red.withValues(alpha: 0.15),
                valueColor: const AlwaysStoppedAnimation(Colors.red),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
