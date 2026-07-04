import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:async';

/// S8. AI Recitation Sandbox — the core USP screen.
/// State machine: Listen → Record → Analyzing → Results.
class RecitationPage extends ConsumerStatefulWidget {
  const RecitationPage({super.key});

  @override
  ConsumerState<RecitationPage> createState() => _RecitationPageState();
}

enum RecitationState { listen, recording, analyzing, results }

class _RecitationPageState extends ConsumerState<RecitationPage> {
  RecitationState _state = RecitationState.listen;
  final List<String> _targetAyah = ['قُلْ', 'أَعُوذُ', 'بِرَبِّ', 'النَّاسِ'];
  final List<String> _wordVerdicts = []; // populated after analysis

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Practice')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Target ayah
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text('Recite:', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 12),
                    Directionality(
                      textDirection: TextDirection.rtl,
                      child: Wrap(
                        spacing: 8,
                        children: _targetAyah.asMap().entries.map((entry) {
                          final idx = entry.key;
                          final word = entry.value;
                          Color? color;
                          if (_state == RecitationState.results && idx < _wordVerdicts.length) {
                            final verdict = _wordVerdicts[idx];
                            color = verdict == 'correct' ? Colors.green : Colors.red;
                          }
                          return Text(
                            word,
                            style: TextStyle(
                              fontFamily: 'QuranUthmani',
                              fontSize: 28,
                              color: color,
                              decoration: _state == RecitationState.results && idx < _wordVerdicts.length && _wordVerdicts[idx] == 'omitted'
                                  ? TextDecoration.lineThrough
                                  : null,
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const Spacer(),
            // State-dependent UI
            _buildStateUI(context),
          ],
        ),
      ),
    );
  }

  Widget _buildStateUI(BuildContext context) {
    return switch (_state) {
      RecitationState.listen => Column(
        children: [
          const Icon(Icons.headphones, size: 48),
          const SizedBox(height: 8),
          const Text('Listen to the ayah first'),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: () => setState(() => _state = RecitationState.recording),
            icon: const Icon(Icons.mic),
            label: const Text('Start Reciting'),
          ),
        ],
      ),
      RecitationState.recording => Column(
        children: [
          // Live waveform placeholder
          Container(
            height: 80,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Center(child: Icon(Icons.graphic_eq, size: 48)),
          ),
          const SizedBox(height: 16),
          const Text('Recording...'),
          const SizedBox(height: 24),
          FilledButton.icon(
            onPressed: _stopRecording,
            icon: const Icon(Icons.stop),
            label: const Text('Stop'),
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
          ),
        ],
      ),
      RecitationState.analyzing => Column(
        children: [
          const CircularProgressIndicator(),
          const SizedBox(height: 16),
          Text('Sun rahe hain... ✨', style: Theme.of(context).textTheme.titleMedium),
        ],
      ),
      RecitationState.results => Column(
        children: [
          Text('18/20 words 👏', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              FilledButton(onPressed: _reset, child: const Text('Try Again')),
              const SizedBox(width: 16),
              FilledButton.tonal(onPressed: _reset, child: const Text('Next Ayah')),
            ],
          ),
        ],
      ),
    };
  }

  void _stopRecording() {
    setState(() => _state = RecitationState.analyzing);
    // Simulate analysis delay
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        // Simulated results
        _wordVerdicts.clear();
        _wordVerdicts.addAll(['correct', 'correct', 'mispronounced', 'correct']);
        setState(() => _state = RecitationState.results);
      }
    });
  }

  void _reset() {
    setState(() {
      _state = RecitationState.listen;
      _wordVerdicts.clear();
    });
  }
}
