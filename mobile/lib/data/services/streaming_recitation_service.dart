import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

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

  /// Buffered PCM16 audio that is flushed to the socket on a fixed cadence
  /// (see [_flushInterval]) so each WS message carries a real, non-empty chunk
  /// (fixes the earlier "0s duration" payload bug and avoids chatty micro-frames).
  final BytesBuilder _audioBuffer = BytesBuilder();
  Timer? _flushTimer;
  // Buffered PCM16 is flushed to the socket every 250ms so each WS frame
  // carries a real, non-empty audio window (fixes the earlier "0s duration"
  // payload bug and keeps the ASR fed continuously).
  static const Duration _flushInterval = Duration(milliseconds: 250);

  final StreamController<RecitationStreamEvent> _events =
      StreamController<RecitationStreamEvent>.broadcast();
  final StreamController<double> _amplitude =
      StreamController<double>.broadcast();
  final StreamController<LiveConnectionState> _connection =
      StreamController<LiveConnectionState>.broadcast();

  Completer<RecitationStreamEvent?>? _finalCompleter;
  LiveConnectionState _state = LiveConnectionState.idle;

  /// Total PCM bytes sent to the server (for debugging the "Duration: 0s" bug).
  int _totalSentBytes = 0;
  int _chunkCount = 0;
  DateTime? _firstChunkAt;

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

  /// Total PCM bytes sent to the server so far (0 ⇒ no mic audio captured /
  /// no binary frames delivered → "Duration: 0s"). Exposed for live diagnostics.
  int get sentBytes => _totalSentBytes;

  /// Number of microphone chunks received from the recorder (0 ⇒ the recorder
  /// is producing no data → OS blocked capture despite the permission).
  int get micChunks => _chunkCount;

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
  ///
  /// [ayahRefs] is the explicit ordered list of `(surah, ayah)` the user will
  /// recite continuously (a full Mushaf page or a whole surah). When omitted we
  /// fall back to a single-surah range built from [surahNumber]/[ayahNumber].
  Future<void> start({
    required int surahNumber,
    required int ayahNumber,
    int? ayahFrom,
    int? ayahTo,
    List<(int, int)>? ayahRefs,
    required bool memorizationMode,
    List<String>? words,
  }) async {
    if (isActive) return;
    _setState(LiveConnectionState.connecting);
    _totalSentBytes = 0;
    _chunkCount = 0;
    _firstChunkAt = null;

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
      debugPrint('[Streaming] connecting to ${AppConstants.recitationStreamWsUrl}');
      _socket = await WebSocket.connect(
        AppConstants.recitationStreamWsUrl,
        customClient: httpClient,
      );
    } catch (e) {
      _setState(LiveConnectionState.error);
      debugPrint('[Streaming] WS CONNECT FAILED: $e');
      throw StreamingConnectionException('Could not connect: $e');
    }

    _socketSub = _socket!.listen(
      _onSocketData,
      onError: (Object e, StackTrace? st) {
        // A WebSocket-level error (handshake failure, 400/500, dropped
        // connection). Surface it loudly so "Duration 0s" can be diagnosed.
        debugPrint('[Streaming] WS ERROR: $e');
        if (st != null) debugPrint('$st');
        _setState(LiveConnectionState.error);
      },
      onDone: () {
        debugPrint('[Streaming] WS CLOSED (done). state=${_state.name}');
        if (_state != LiveConnectionState.finishing) {
          _setState(LiveConnectionState.closed);
        }
      },
      cancelOnError: false,
    );

    // --- Handshake ---
    // Send the explicit ordered ayah sequence so the backend can resolve the
    // concatenated reference list and track words seamlessly across ayah
    // boundaries (full-page / full-surah continuous recitation). Also send the
    // client's resolved word list as a fallback reference so the backend can
    // still score when its own reference store is empty (prevents "0 of 0").
    final List<List<int>> refs = ayahRefs == null
        ? []
        : ayahRefs.map((r) => [r.$1, r.$2]).toList();
    _socket!.add(jsonEncode({
      'type': 'start',
      'surah_number': surahNumber,
      'ayah_number': ayahNumber,
      'ayah_from': ayahFrom ?? ayahNumber,
      'ayah_to': ayahTo ?? ayahNumber,
      if (refs.isNotEmpty) 'ayahs': refs,
      if (words != null && words.isNotEmpty) 'words': words,
      'mode': memorizationMode ? 'memorization' : 'tracking',
      'sample_rate': AppConstants.liveRecitationSampleRate,
    }));
    debugPrint('[Streaming] sent start handshake '
        '(surah=$surahNumber, ayah=$ayahNumber, refs=${refs.length}, '
        'clientWords=${(words?.length) ?? 0})');

    // --- Start the continuous PCM audio stream ---
    try {
      final audioStream = await _recorder.startStream(
        const RecordConfig(
          encoder: AudioEncoder.pcm16bits,
          sampleRate: AppConstants.liveRecitationSampleRate,
          numChannels: 1,
        ),
      );
      debugPrint('[Streaming] mic recorder STARTED (stream open).');

      _audioSub = audioStream.listen(
        (chunk) {
          _emitAmplitude(chunk);
          // ACHTUNG: if this logs 0-length chunks continuously, the local
          // recorder is broken (no mic data).
          _chunkCount++;
          _firstChunkAt ??= DateTime.now();
          if (chunk.isNotEmpty) {
            _audioBuffer.add(chunk);
          }
          if (_chunkCount <= 5 || _chunkCount % 50 == 0) {
            debugPrint('[Streaming] mic chunk #$_chunkCount '
                'len=${chunk.length} bytes (buffered=${_audioBuffer.length})');
          }
        },
        onError: (Object e, StackTrace? st) {
          // The mic/recorder errored — the stream would otherwise die silently
          // and the backend would receive no audio (=> Duration 0s).
          debugPrint('[Streaming] MIC STREAM ERROR: $e');
          if (st != null) debugPrint('$st');
        },
        cancelOnError: false,
      );
    } catch (e, st) {
      debugPrint('[Streaming] mic startStream FAILED: $e\n$st');
      _setState(LiveConnectionState.error);
      throw StreamingConnectionException('Mic could not start: $e');
    }

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

    // --- Chunked upload: emit buffered audio every 250ms ---
    _flushTimer = Timer.periodic(_flushInterval, (_) {
      _flushAudio();
    });

    _setState(LiveConnectionState.listening);
    debugPrint('StreamingRecitation: streaming started (sentBytes tracked)');
  }

  /// Sends any buffered PCM16 audio to the server as a single binary frame.
  /// Flushing on a fixed cadence (not per raw microphone chunk) guarantees the
  /// server receives non-empty, real-duration windows.
  void _flushAudio() {
    if (_audioBuffer.isEmpty) return;
    final sock = _socket;
    if (sock != null && sock.readyState == WebSocket.open) {
      final frame = Uint8List.fromList(_audioBuffer.takeBytes());
      _totalSentBytes += frame.length;
      sock.add(frame);
      debugPrint('[Streaming] FLUSH #$_chunkCount -> sent ${frame.length} bytes '
          '(totalSent=$_totalSentBytes)');
    } else {
      debugPrint('[Streaming] FLUSH skipped: socket not open '
          '(state=${_state.name}, buffered=${_audioBuffer.length})');
      _audioBuffer.clear();
    }
  }

  void _onSocketData(dynamic data) {
    if (data is! String) {
      // Server should only send JSON; a binary frame here is unexpected.
      debugPrint('[Streaming] received non-string frame (ignored).');
      return;
    }
    try {
      final json = jsonDecode(data) as Map<String, dynamic>;
      final event = RecitationStreamEvent.fromJson(json);
      if (event.type == RecitationStreamEventType.word) {
        debugPrint('[Streaming] RX word event idx=${event.wordIndex} '
            'status=${event.status.name} expected=${event.expected}');
      } else if (event.type == RecitationStreamEventType.ready) {
        debugPrint('[Streaming] RX ready (${event.words.length} words)');
      } else if (event.type == RecitationStreamEventType.finalResult) {
        debugPrint('[Streaming] RX final (duration=${event.result?.durationSeconds}s, '
            'verdicts=${event.result?.wordVerdicts.length})');
      } else if (event.type == RecitationStreamEventType.error) {
        debugPrint('[Streaming] RX ERROR: ${event.detail}');
      }
      if (!_events.isClosed) _events.add(event);
      if (event.type == RecitationStreamEventType.finalResult) {
        _finalCompleter?.complete(event);
        _finalCompleter = null;
      }
    } catch (e) {
      debugPrint('[Streaming] decode error: $e');
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
  /// IMPORTANT: the caller must NOT navigate to results until this resolves —
  /// it blocks until the server sends the aggregated `final` payload.
  Future<RecitationStreamEvent?> stop({
    Duration timeout = const Duration(seconds: 30),
  }) async {
    if (_state == LiveConnectionState.idle ||
        _state == LiveConnectionState.closed) {
      debugPrint('[Streaming] stop() called but session not active '
          '(state=${_state.name}) — nothing to finalize.');
      return null;
    }
    _setState(LiveConnectionState.finishing);

    // Stop capturing audio first.
    await _audioSub?.cancel();
    _audioSub = null;
    _pingTimer?.cancel();
    _flushTimer?.cancel();
    _flushAudio(); // send any trailing audio before finalizing
    try {
      await _recorder.stop();
    } catch (e) {
      debugPrint('[Streaming] recorder stop error: $e');
    }

    debugPrint('[Streaming] requesting finalize from server '
        '(totalSentBytes=$_totalSentBytes, micChunks=$_chunkCount)');

    _finalCompleter = Completer<RecitationStreamEvent?>();
    final sock = _socket;
    if (sock != null && sock.readyState == WebSocket.open) {
      sock.add(jsonEncode({'type': 'stop'}));
    } else {
      debugPrint('[Streaming] cannot send stop: socket not open '
          '(state=${_state.name})');
      _finalCompleter?.complete(null);
    }

    RecitationStreamEvent? finalEvent;
    try {
      finalEvent = await _finalCompleter!.future.timeout(timeout);
    } on TimeoutException {
      debugPrint('[Streaming] TIMEOUT waiting for server final result '
          '(server did not respond in ${timeout.inSeconds}s).');
    } finally {
      _finalCompleter = null;
      await _closeSocket();
      _setState(LiveConnectionState.closed);
    }

    final r = finalEvent?.result;
    debugPrint('[Streaming] FINAL result received: '
        'duration=${r?.durationSeconds}s, '
        'verdicts=${r?.wordVerdicts.length}, '
        'score=${r?.overallScore}');
    return finalEvent;
  }

  /// Aborts the session without waiting for a final result.
  Future<void> cancel() async {
    _pingTimer?.cancel();
    _flushTimer?.cancel();
    _audioBuffer.clear();
    await _audioSub?.cancel();
    _audioSub = null;
    try {
      await _recorder.cancel();
    } catch (_) {}
    await _closeSocket();
    _setState(LiveConnectionState.closed);
  }

  Future<void> _closeSocket() async {
    _flushTimer?.cancel();
    _pingTimer?.cancel();
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
