import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';

import '../../core/constants/app_constants.dart';
import '../models/recitation_stream_event.dart';

/// Connection state of a live recitation streaming session.
enum LiveConnectionState { idle, connecting, listening, finishing, closed, error }

/// Streams microphone audio continuously to the backend `/ws/recitation/stream`
/// WebSocket and surfaces real-time word-by-word match events.
///
/// This powers the upgraded AI Recitation section (real-time tracking +
/// Memorization Mode). It is completely separate from [RecordingService]
/// (single-file record → upload), so the Quran reader's per-ayah "Recite" flow
/// is unaffected.
class StreamingRecitationService {
  final AudioRecorder _recorder = AudioRecorder();

  WebSocket? _socket;
  StreamSubscription<Uint8List>? _audioSub;
  StreamSubscription? _socketSub;
  Timer? _pingTimer;

  final StreamController<RecitationStreamEvent> _events =
      StreamController<RecitationStreamEvent>.broadcast();
  final StreamController<double> _amplitude =
      StreamController<double>.broadcast();
  final StreamController<LiveConnectionState> _connection =
      StreamController<LiveConnectionState>.broadcast();

  Completer<RecitationStreamEvent?>? _finalCompleter;
  LiveConnectionState _state = LiveConnectionState.idle;

  /// Real-time backend events (ready / word / final / error).
  Stream<RecitationStreamEvent> get events => _events.stream;

  /// Normalized (0–1) mic loudness per audio chunk for the live visualizer.
  Stream<double> get amplitude => _amplitude.stream;

  /// Connection lifecycle updates.
  Stream<LiveConnectionState> get connectionState => _connection.stream;

  LiveConnectionState get state => _state;
  bool get isActive =>
      _state == LiveConnectionState.listening ||
      _state == LiveConnectionState.connecting;

  void _setState(LiveConnectionState s) {
    _state = s;
    if (!_connection.isClosed) _connection.add(s);
  }

  Future<bool> hasPermission() async {
    final status = await Permission.microphone.status;
    return status.isGranted;
  }

  Future<bool> requestPermission() async {
    final status = await Permission.microphone.request();
    return status.isGranted;
  }

  /// Opens the WebSocket, sends the `start` handshake, and begins streaming
  /// microphone audio. Throws on permission denial or connection failure.
  Future<void> start({
    required int surahNumber,
    required int ayahNumber,
    int? ayahFrom,
    int? ayahTo,
    required bool memorizationMode,
  }) async {
    if (isActive) return;
    _setState(LiveConnectionState.connecting);

    if (!await hasPermission()) {
      final granted = await requestPermission();
      if (!granted) {
        _setState(LiveConnectionState.error);
        throw const MicPermissionDeniedException();
      }
    }

    // --- Connect the WebSocket (trust the VPS self-signed cert) ---
    final httpClient = HttpClient()
      ..badCertificateCallback =
          (cert, host, port) => host == AppConstants.trustedSelfSignedHost;
    try {
      _socket = await WebSocket.connect(
        AppConstants.recitationStreamWsUrl,
        customClient: httpClient,
      );
    } catch (e) {
      _setState(LiveConnectionState.error);
      throw StreamingConnectionException('Could not connect: $e');
    }

    _socketSub = _socket!.listen(
      _onSocketData,
      onError: (Object e) {
        debugPrint('StreamingRecitation socket error: $e');
        _setState(LiveConnectionState.error);
      },
      onDone: () {
        debugPrint('StreamingRecitation socket closed');
        if (_state != LiveConnectionState.finishing) {
          _setState(LiveConnectionState.closed);
        }
      },
      cancelOnError: false,
    );

    // --- Handshake ---
    _socket!.add(jsonEncode({
      'type': 'start',
      'surah_number': surahNumber,
      'ayah_number': ayahNumber,
      'ayah_from': ayahFrom ?? ayahNumber,
      'ayah_to': ayahTo ?? ayahNumber,
      'mode': memorizationMode ? 'memorization' : 'tracking',
      'sample_rate': AppConstants.liveRecitationSampleRate,
    }));

    // --- Start the continuous PCM audio stream ---
    final audioStream = await _recorder.startStream(
      const RecordConfig(
        encoder: AudioEncoder.pcm16bits,
        sampleRate: AppConstants.liveRecitationSampleRate,
        numChannels: 1,
      ),
    );

    _audioSub = audioStream.listen((chunk) {
      _emitAmplitude(chunk);
      final sock = _socket;
      if (sock != null && sock.readyState == WebSocket.open) {
        sock.add(chunk);
      }
    });

    // --- Keep-alive pings so long hands-free sessions never drop ---
    _pingTimer = Timer.periodic(
      const Duration(seconds: AppConstants.liveRecitationPingIntervalSeconds),
      (_) {
        final sock = _socket;
        if (sock != null && sock.readyState == WebSocket.open) {
          sock.add(jsonEncode({'type': 'ping'}));
        }
      },
    );

    _setState(LiveConnectionState.listening);
  }

  void _onSocketData(dynamic data) {
    if (data is! String) return;
    try {
      final json = jsonDecode(data) as Map<String, dynamic>;
      final event = RecitationStreamEvent.fromJson(json);
      if (!_events.isClosed) _events.add(event);
      if (event.type == RecitationStreamEventType.finalResult) {
        _finalCompleter?.complete(event);
        _finalCompleter = null;
      }
    } catch (e) {
      debugPrint('StreamingRecitation decode error: $e');
    }
  }

  /// Computes an RMS loudness (0–1) from a PCM16 little-endian chunk.
  void _emitAmplitude(Uint8List chunk) {
    if (chunk.length < 2) return;
    final samples = chunk.buffer.asInt16List(
      chunk.offsetInBytes,
      chunk.lengthInBytes ~/ 2,
    );
    if (samples.isEmpty) return;
    var sumSq = 0.0;
    for (final s in samples) {
      final v = s / 32768.0;
      sumSq += v * v;
    }
    final rms = math.sqrt(sumSq / samples.length);
    // Map RMS to a lively 0–1 range (recitation is fairly quiet at the mic).
    final normalized = (rms * 3.2).clamp(0.0, 1.0);
    if (!_amplitude.isClosed) _amplitude.add(normalized);
  }

  /// Stops recording, tells the backend to finalize, and awaits the final
  /// result (bounded by [timeout]). Returns the final result event if received.
  Future<RecitationStreamEvent?> stop({
    Duration timeout = const Duration(seconds: 20),
  }) async {
    if (_state == LiveConnectionState.idle ||
        _state == LiveConnectionState.closed) {
      return null;
    }
    _setState(LiveConnectionState.finishing);

    // Stop capturing audio first.
    await _audioSub?.cancel();
    _audioSub = null;
    _pingTimer?.cancel();
    try {
      await _recorder.stop();
    } catch (e) {
      debugPrint('StreamingRecitation recorder stop error: $e');
    }

    _finalCompleter = Completer<RecitationStreamEvent?>();
    final sock = _socket;
    if (sock != null && sock.readyState == WebSocket.open) {
      sock.add(jsonEncode({'type': 'stop'}));
    } else {
      _finalCompleter?.complete(null);
    }

    RecitationStreamEvent? finalEvent;
    try {
      finalEvent = await _finalCompleter!.future.timeout(timeout);
    } on TimeoutException {
      debugPrint('StreamingRecitation: timed out waiting for final result');
    } finally {
      _finalCompleter = null;
      await _closeSocket();
      _setState(LiveConnectionState.closed);
    }
    return finalEvent;
  }

  /// Aborts the session without waiting for a final result.
  Future<void> cancel() async {
    _pingTimer?.cancel();
    await _audioSub?.cancel();
    _audioSub = null;
    try {
      await _recorder.cancel();
    } catch (_) {}
    await _closeSocket();
    _setState(LiveConnectionState.closed);
  }

  Future<void> _closeSocket() async {
    await _socketSub?.cancel();
    _socketSub = null;
    try {
      await _socket?.close();
    } catch (_) {}
    _socket = null;
  }

  Future<void> dispose() async {
    await cancel();
    await _recorder.dispose();
    await _events.close();
    await _amplitude.close();
    await _connection.close();
  }
}

/// Thrown when microphone permission is denied.
class MicPermissionDeniedException implements Exception {
  const MicPermissionDeniedException();
  @override
  String toString() => 'Microphone permission denied';
}

/// Thrown when the streaming WebSocket cannot be established.
class StreamingConnectionException implements Exception {
  final String message;
  const StreamingConnectionException(this.message);
  @override
  String toString() => message;
}
