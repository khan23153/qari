import 'dart:io';
import 'package:record/record.dart';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../core/constants/app_constants.dart';

/// Recording service wrapping the `record` plugin for recitation capture.
/// Handles mic permission, file management, and recording lifecycle.
class RecordingService {
  final AudioRecorder _recorder = AudioRecorder();

  bool _isRecording = false;
  String? _currentFilePath;

  bool get isRecording => _isRecording;
  String? get currentFilePath => _currentFilePath;

  /// Checks and requests microphone permission.
  Future<bool> requestPermission() async {
    final status = await Permission.microphone.request();
    return status.isGranted;
  }

  /// Checks if microphone permission is granted.
  Future<bool> hasPermission() async {
    final status = await Permission.microphone.status;
    return status.isGranted;
  }

  /// Starts recording audio to a temporary file.
  /// Returns the file path of the recording, or null if permission denied.
  Future<String?> startRecording() async {
    if (_isRecording) {
      debugPrint('RecordingService: already recording');
      return _currentFilePath;
    }

    final hasMicPermission = await requestPermission();
    if (!hasMicPermission) {
      debugPrint('RecordingService: microphone permission denied');
      return null;
    }

    try {
      final tempDir = await getTemporaryDirectory();
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final filePath = '${tempDir.path}/recitation_$timestamp.m4a';

      await _recorder.start(
        const RecordConfig(
          encoder: AudioEncoder.aacLc,
          bitRate: 128000,
          sampleRate: 44100,
          numChannels: 1,
        ),
        path: filePath,
      );

      _isRecording = true;
      _currentFilePath = filePath;
      debugPrint('RecordingService: started recording to $filePath');
      return filePath;
    } catch (e) {
      debugPrint('RecordingService start error: $e');
      return null;
    }
  }

  /// Stops recording and returns the file path.
  Future<String?> stopRecording() async {
    if (!_isRecording) return null;

    try {
      final path = await _recorder.stop();
      _isRecording = false;
      _currentFilePath = null;
      debugPrint('RecordingService: stopped recording, file at $path');
      return path;
    } catch (e) {
      debugPrint('RecordingService stop error: $e');
      _isRecording = false;
      _currentFilePath = null;
      return null;
    }
  }

  /// Cancels the current recording and deletes the file.
  Future<void> cancelRecording() async {
    if (_isRecording) {
      await _recorder.stop();
      _isRecording = false;
    }
    if (_currentFilePath != null) {
      final file = File(_currentFilePath!);
      if (await file.exists()) {
        await file.delete();
      }
      _currentFilePath = null;
    }
  }

  /// Gets the amplitude stream for waveform visualization.
  Stream<Amplitude> getAmplitudeStream() {
    return _recorder
        .onAmplitudeChanged(const Duration(milliseconds: 100));
  }

  /// Gets the recording duration in seconds.
  int getRecordingDuration() {
    if (!_isRecording || _currentFilePath == null) return 0;
    // Duration is tracked externally by the UI timer
    return 0;
  }

  /// Maximum recording duration in seconds.
  int get maxDurationSeconds => AppConstants.maxRecordingDurationSeconds;

  /// Disposes the recorder.
  void dispose() {
    _recorder.dispose();
  }
}
